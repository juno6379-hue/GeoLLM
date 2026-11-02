"""Independently verify positional CSV revision candidates and DB delta receipts.

This module performs no DB mutation and makes no model calls.
"""
import argparse
import csv
import io
import json
import os
import math
from collections import Counter
from datetime import datetime, timezone
from scripts.audit_dataset_locations import DEFAULT, ROOT, file_sha, sha, write, mentions


def verify_candidates():
    candidate_path=DEFAULT/'csv_reextracted_revision_candidates.json'
    rows=json.loads(candidate_path.read_text(encoding='utf-8'))['rows']
    baseline=json.loads((DEFAULT/'csv_generator_fix_verification.json').read_text(encoding='utf-8'))
    if len(rows)!=6 or len({r['chunk_id'] for r in rows})!=6:raise RuntimeError('Candidate cardinality')
    if set(baseline['old_ids'])&{r['chunk_id'] for r in rows}:raise RuntimeError('Old ID reuse')
    ranges=[];checks=[];parsed_cache={}
    for row in rows:
        meta=row['metadata'];path=ROOT/meta['source_file']
        if file_sha(path)!=meta['source_sha256']:raise RuntimeError('Original source hash mismatch')
        if meta['source_file'] not in parsed_cache:
            parsed_cache[meta['source_file']]=list(csv.reader(io.StringIO(path.read_bytes().decode(meta['encoding']))))
        parsed=parsed_cache[meta['source_file']];start=meta['source_row_start'];end=meta['source_row_end']
        expected='columns: '+' | '.join(parsed[0])+'\n'+'\n'.join(' | '.join(values) for values in parsed[start:end+1])
        if expected!=row['text']:raise RuntimeError('Independent positional source text mismatch')
        if meta['source_column_names']!=parsed[0]:raise RuntimeError('Source header mismatch')
        if meta['source_locators']!=['csv-header:0',f'csv-rows:{start}-{end}']:raise RuntimeError('Source locator mismatch')
        if meta['extraction_revision']!='csv_positional_v2' or not meta['requires_new_embedding']:raise RuntimeError('Revision identity missing')
        ranges.extend(range(start,end+1));checks.append(dict(chunk_id=row['chunk_id'],content_sha256=sha(row['text'].encode()),source_sha256=meta['source_sha256'],source_file=meta['source_file'],source_locators=meta['source_locators'],source_rows=[start,end],source_id=meta['source_id'],independent_positional_text_match=True))
    if len(parsed_cache)!=1 or ranges!=list(range(1,len(next(iter(parsed_cache.values()))))):raise RuntimeError('Source row omission/duplication')
    result=dict(status='SOURCE_CANDIDATES_VERIFIED',candidate_sha256=file_sha(candidate_path),source_data_rows=len(ranges),rows=checks,old_chunk_ids=baseline['old_ids'],database_changed=False,model_called=False)
    write(DEFAULT/'csv_revision_independent_source_check.json',result)
    return result,rows


def export():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    candidate=json.loads((DEFAULT/'csv_reextracted_revision_candidates.json').read_text(encoding='utf-8'))['rows']
    expected=json.loads((DEFAULT/'csv_generator_fix_verification.json').read_text(encoding='utf-8'))
    ids=expected['old_ids']+[r['chunk_id'] for r in candidate]
    target=DEFAULT/'csv_revision_db_snapshot.json'
    if target.exists():raise RuntimeError('Refuse to overwrite DB delta snapshot')
    with psycopg2.connect(os.environ['S101_DB_URL']) as conn:
        conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT txid_current_snapshot()::text AS snapshot,current_database() AS database')
            identity=dict(cur.fetchone())
            cur.execute('''SELECT chunk_id,document_type,title,section,content,source_file,
             source_id,source_sha256,page_no,metadata,embedding IS NOT NULL AS embedded,
             vector_dims(embedding) AS embedding_dimensions, embedding::text AS embedding_text
             FROM knowledge.document_chunks WHERE chunk_id=ANY(%s) ORDER BY chunk_id''',(ids,))
            rows=[dict(r) for r in cur]
            cur.execute("""SELECT count(*) AS total_rows,
              count(*) FILTER(WHERE metadata->>'retrieval_status' IS DISTINCT FROM 'SUPERSEDED') AS active_rows,
              count(*) FILTER(WHERE metadata->>'retrieval_status'='SUPERSEDED') AS superseded_rows
              FROM knowledge.document_chunks""")
            counts=dict(cur.fetchone())
    write(target,dict(read_only=True,identity=identity,observed_at=datetime.now(timezone.utc).isoformat(),counts=counts,rows=rows))
    print(json.dumps(dict(exported=len(rows),**counts)))


def verify_delta():
    checked,candidates=verify_candidates()
    delta_path=DEFAULT/'csv_revision_db_snapshot.json'
    delta=json.loads(delta_path.read_text(encoding='utf-8'))
    existing=json.loads((DEFAULT/'csv_generator_fix_verification.json').read_text(encoding='utf-8'))
    old_ids=set(existing['old_ids']);new_ids={r['chunk_id'] for r in candidates}
    db={r['chunk_id']:r for r in delta['rows']}
    if set(db)!=old_ids|new_ids:raise RuntimeError('Unexpected DB delta IDs')
    baseline_receipt=DEFAULT/'compact_receipts.jsonl';baseline_manifest=json.loads((DEFAULT/'receipt_manifest.json').read_text(encoding='utf-8'))
    if file_sha(baseline_receipt)!=baseline_manifest['files']['compact_receipts.jsonl']:raise RuntimeError('Baseline receipt hash changed')
    original_rows={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8')) if r['chunk_id'] in old_ids}
    transaction_before_path=ROOT/'outputs/csv_document_revision_20261102_v1/before.json'
    before=json.loads(transaction_before_path.read_text(encoding='utf-8'))
    before_rows={r['chunk_id']:r for r in before['rows']}
    for cid in old_ids:
        if db[cid]['content']!=original_rows[cid]['content'] or db[cid]['source_sha256']!=original_rows[cid]['source_sha256']:raise RuntimeError('Legacy source text changed')
        if db[cid]['metadata'].get('retrieval_status')!='SUPERSEDED':raise RuntimeError('Old row remains active')
        if db[cid]['embedding_text']!=before_rows[cid]['embedding']:raise RuntimeError('Original stored embedding changed')
    expected_digest='7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab'
    new_receipts=[];new_mentions=[]
    for candidate in candidates:
        cid=candidate['chunk_id'];row=db[cid];meta=row['metadata'];expected=candidate['metadata'];embed=meta.get('embedding') or {}
        if row['content']!=candidate['text'] or row['source_sha256']!=expected['source_sha256']:raise RuntimeError('Current DB source text differs from independently verified candidate')
        if row['source_file']!=expected['source_file'] or row['source_id']!=expected['source_id']:raise RuntimeError('DB logical source identity mismatch')
        if any(meta.get(k)!=expected.get(k) for k in ['source_row_start','source_row_end','source_locators','source_column_names','extraction_revision']):raise RuntimeError('DB locator metadata mismatch')
        if not row['embedded'] or row['embedding_dimensions']!=1024:raise RuntimeError('New embedding absent or dimension mismatch')
        vector=json.loads(row['embedding_text'])
        if len(vector)!=1024 or not all(math.isfinite(v) for v in vector):raise RuntimeError('Invalid new vector values')
        if embed.get('input_sha256')!=sha(row['content'].encode()) or embed.get('model_digest')!=expected_digest or embed.get('dimension')!=1024:raise RuntimeError('Embedding generation lineage mismatch')
        if meta.get('retrieval_status')!='ACTIVE':raise RuntimeError('New row not active')
        from scripts.audit_dataset_coordinate_literals import parse
        _,pairs=parse(row['content'])
        issues=[dict(status=p['status'],reason=';'.join(sorted({a['syntax_status'] for a in p['axes'] if a['syntax_status']!='RANGE_VALID'})),start=p['start'],end=p['end']) for p in pairs if p['status']=='INVALID_OR_AMBIGUOUS_LITERAL']
        for mention in mentions(row['content']):new_mentions.append(dict(chunk_id=cid,content_sha256=sha(row['content'].encode()),source_sha256=row['source_sha256'],source_locator=expected['source_locators'],**mention))
        new_receipts.append(dict(chunk_id=cid,content_sha256=sha(row['content'].encode()),source_sha256=row['source_sha256'],source_locator=expected['source_locators'],status='VERIFIED_TEXT',reason='MATCH_FULL;MATCH_INDEPENDENT_CSV_POSITIONAL_ROWS;CURRENT_DB_DELTA_MATCH',semantic_authority=False,coordinate_authority=False,coordinate_literal_issues=issues,object_links=[],retrieval_status='ACTIVE',embedding_provenance=embed))
    counts=delta['counts']
    if counts!={'total_rows':23221,'active_rows':23215,'superseded_rows':6}:raise RuntimeError('Unexpected full corpus lifecycle counts')
    output=DEFAULT/'revision_v2';output.mkdir(exist_ok=False)
    effective=[]
    for receipt in map(json.loads,baseline_receipt.open(encoding='utf-8')):
        receipt=dict(receipt)
        receipt['retrieval_status']='SUPERSEDED' if receipt['chunk_id'] in old_ids else 'ACTIVE'
        effective.append(receipt)
    effective.extend(new_receipts)
    with (output/'compact_receipts.jsonl').open('w',encoding='utf-8') as stream:
        for receipt in effective:stream.write(json.dumps(receipt,ensure_ascii=False)+'\n')
    with (output/'mention_candidates_delta.jsonl').open('w',encoding='utf-8') as stream:
        for mention in new_mentions:stream.write(json.dumps(mention,ensure_ascii=False)+'\n')
    snapshot_manifest=dict(kind='BASELINE_PLUS_READONLY_DELTA',baseline_snapshot_sha256=baseline_manifest['snapshot_sha256'],baseline_receipt_sha256=file_sha(baseline_receipt),delta_snapshot_sha256=file_sha(delta_path),delta_snapshot_file=delta_path.relative_to(ROOT).as_posix(),counts=counts,limitations=['Non-target rows retain the verified baseline; this is a baseline plus targeted read-only delta, not a fresh full-table export.'])
    write(output/'effective_snapshot_manifest.json',snapshot_manifest)
    active=[r for r in effective if r['retrieval_status']=='ACTIVE']
    manifest=dict(complete=True,completion_scope='Stored baseline plus six verified CSV revisions; active/superseded lifecycle counts separated',files={'compact_receipts.jsonl':file_sha(output/'compact_receipts.jsonl')},audited_at=datetime.now(timezone.utc).isoformat(),snapshot_sha256=file_sha(output/'effective_snapshot_manifest.json'),snapshot_kind='BASELINE_PLUS_READONLY_DELTA',baseline_snapshot_sha256=baseline_manifest['snapshot_sha256'],delta_snapshot_sha256=file_sha(delta_path),baseline_receipt_sha256=file_sha(baseline_receipt),rows=len(effective),stored_rows=len(effective),active_rows=len(active),superseded_rows=6,status_counts=dict(Counter(r['status'] for r in effective)),active_status_counts=dict(Counter(r['status'] for r in active)),object_links=sum(len(r['object_links']) for r in effective),spatial_links_sha256=baseline_manifest['spatial_links_sha256'],source_manifest_sha256=baseline_manifest['source_manifest_sha256'],audit_environment=baseline_manifest['audit_environment'],limitations=baseline_manifest['limitations']+snapshot_manifest['limitations'],new_embedding_model_digest=expected_digest,historical_embedding_model_verified=False,delta_verifier_sha256=file_sha(ROOT/'scripts/audit_dataset_csv_revision_delta.py'))
    write(output/'receipt_manifest.json',manifest)
    write(output/'verification.json',dict(status='SOURCE_AND_CURRENT_DB_DELTA_VERIFIED',new_receipts=6,legacy_text_preserved=6,legacy_vectors_preserved=6,transaction_before_sha256=file_sha(transaction_before_path),counts=counts,independent_source_check_sha256=file_sha(DEFAULT/'csv_revision_independent_source_check.json'),candidate_sha256=checked['candidate_sha256'],baseline_receipt_unchanged=True))
    state=json.loads((DEFAULT/'status.json').read_text(encoding='utf-8'))
    write(output/'baseline_status.json',state)
    state['counts'].update(baseline_chunks_total=23215,chunks_total=len(effective),chunks_scanned=len(effective),chunks_source_text_matched=manifest['status_counts'].get('VERIFIED_TEXT',0),chunks_unverified=len(effective)-manifest['status_counts'].get('VERIFIED_TEXT',0),active_chunks_total=len(active),active_verified_text=manifest['active_status_counts'].get('VERIFIED_TEXT',0),active_unverified=manifest['active_status_counts'].get('UNVERIFIED',0),active_mismatch=manifest['active_status_counts'].get('MISMATCH',0),superseded_chunks=6,receipt_verified_text=manifest['status_counts'].get('VERIFIED_TEXT',0),receipt_unverified=manifest['status_counts'].get('UNVERIFIED',0),receipt_mismatch=manifest['status_counts'].get('MISMATCH',0))
    state['counts']['candidate_mentions']+=len(new_mentions)
    state.update(status='PARTIALLY_VERIFIED',updated_at=datetime.now(timezone.utc).isoformat(),summary='전체 원문 감사에 검증된 CSV 새6개 revision을 결합했습니다. 저장23221/활성23215/보존6을 구분하며 의미·위치 미검증 항목은 남아 있습니다.')
    state['evidence'].append(dict(path=(output/'receipt_manifest.json').relative_to(ROOT).as_posix(),sha256=file_sha(output/'receipt_manifest.json')))
    write(DEFAULT/'status.json',state)
    print(json.dumps(dict(rows=len(effective),active_rows=len(active),active_status_counts=manifest['active_status_counts'],manifest_sha256=file_sha(output/'receipt_manifest.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');parser.add_argument('--verify-delta',action='store_true');args=parser.parse_args()
    if args.export:export()
    elif args.verify_delta:verify_delta()
    else:
        result,_=verify_candidates();print(json.dumps(dict(status=result['status'],rows=len(result['rows']),source_data_rows=result['source_data_rows'])))
