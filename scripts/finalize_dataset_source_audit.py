"""Publish full-corpus receipts only after the read-only audit is complete.

Resolved paths are an audit overlay; stored corpus and source originals stay intact.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from scripts.audit_dataset_locations import ROOT, DEFAULT, file_sha, sha, norm, write, LIMITS


def main():
    summary=json.loads((DEFAULT/'summary.json').read_text(encoding='utf-8'))
    counts=summary['counts']
    if counts['chunks_scanned']!=counts['chunks_total']:
        raise RuntimeError('Full audit not complete')
    snapshot=json.loads((DEFAULT/'snapshot_manifest.json').read_text(encoding='utf-8'))
    if file_sha(DEFAULT/'document_chunks.jsonl')!=snapshot['sha256']:
        raise RuntimeError('Snapshot changed')
    checks=[json.loads(s) for s in (DEFAULT/'chunk_checks.jsonl').open(encoding='utf-8')]
    chunks={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'))}
    if len(checks)!=len(chunks) or {c['chunk_id'] for c in checks}!=set(chunks):
        raise RuntimeError('Chunk identity/count mismatch')
    candidates=json.loads((DEFAULT/'source_path_repair_candidates.json').read_text(encoding='utf-8'))['candidates']
    candidates={r['chunk_id']:r for r in candidates}
    variations=json.loads((DEFAULT/'mismatch_classification.json').read_text(encoding='utf-8'))['rows']
    variations={r['chunk_id']:r['v2_status'] for r in variations}
    if set(variations)!={c['chunk_id'] for c in checks if c['text_status']=='TEXT_MISMATCH'}:
        raise RuntimeError('Mismatch classification does not cover final corpus scan')
    recovered=json.loads((DEFAULT/'recovered_locator_checks.json').read_text(encoding='utf-8'))['rows']
    recovered={r['chunk_id']:r for r in recovered}
    empty_columns=json.loads((DEFAULT/'csv_empty_column_diagnosis.json').read_text(encoding='utf-8'))
    empty_columns={r['chunk_id'] for r in empty_columns if r['exact_normalized_match_after_single_trailing_empty_column_removed']}
    coordinate_issues=defaultdict(list)
    spatial_path=DEFAULT.parent/'spatial/verified_chunk_object_links_v3.jsonl'
    spatial_links=defaultdict(list)
    if spatial_path.exists():
        for line in spatial_path.open(encoding='utf-8'):
            link=json.loads(line);spatial_links[link['chunk_id']].append(link)
    for line in (DEFAULT/'explicit_coordinate_pairs.jsonl').open(encoding='utf-8'):
        pair=json.loads(line)
        if pair['status']=='INVALID_OR_AMBIGUOUS_LITERAL':
            coordinate_issues[pair['chunk_id']].append(dict(status=pair['status'],reason=';'.join(sorted({a['syntax_status'] for a in pair['axes'] if a['syntax_status']!='RANGE_VALID'})),start=pair['start'],end=pair['end']))
    archive_cache={};receipts=[];overlays=[]
    for check in checks:
        cid=check['chunk_id'];chunk=chunks[cid];candidate=candidates.get(cid)
        text_state=check['text_status'];hash_state=check['source_hash_status'];locator=check['locator']
        text_state=variations.get(cid,text_state)
        if cid in recovered:
            text_state=recovered[cid]['v2_status'];locator=recovered[cid]['locator']
        if cid in empty_columns:text_state='UNVERIFIED_CSV_TRAILING_EMPTY_COLUMN_VARIATION'
        if candidate and candidate['resolved_source_file']:
            resolved=candidate['resolved_source_file'];hash_state='MATCH_FULL_RESOLVED_PATH'
            if chunk['document_type'] in {'portrayal_catalogue','validation'}:
                if resolved not in archive_cache:
                    from scripts.build_s101_catalogue_db_rag import iter_zip_text_members
                    archive_cache[resolved]=dict(iter_zip_text_members(ROOT/resolved))
                member=(chunk.get('metadata') or {}).get('source_member')
                text=archive_cache[resolved].get(member)
                actual_member=member
                if text is None and member:
                    matches=[name for name in archive_cache[resolved] if name.replace('\\','/')==member.replace('\\','/')]
                    if len(matches)==1:
                        actual_member=matches[0];text=archive_cache[resolved][actual_member]
                prefix=f'Archive member: {member}. '
                body=chunk['content'].removeprefix(prefix)
                if text is not None and chunk['content'].startswith(prefix):
                    text_state='MATCH_NORMALIZED_ARCHIVE_MEMBER' if norm(body) in norm(text) else 'TEXT_MISMATCH'
                    locator=actual_member
            overlays.append(dict(chunk_id=cid,resolved_source_file=resolved,source_hash_status=hash_state,text_status=text_state,locator=locator,source_metadata_updated=False))
        matched=text_state.startswith('MATCH_') and hash_state.startswith('MATCH_')
        status='VERIFIED_TEXT' if matched else 'MISMATCH' if text_state=='TEXT_MISMATCH' else 'UNVERIFIED'
        object_links=[]
        for link in spatial_links.get(cid,[]):
            if (link['content_sha256']!=check['content_sha256'] or link['source_sha256']!=check['source_sha256'] or link['object_id']!=chunk['source_id']):
                raise RuntimeError('Spatial link snapshot identity mismatch')
            if (chunk.get('metadata') or {}).get('harbour_name')!=link['object_name']:
                raise RuntimeError('Harbour name differs across source snapshots')
            object_links.append(dict(source_id=link['object_id'],name=link['object_name'],relation=link['object_relation'],status='AUDIT_SNAPSHOT_LINK',geometry_role='REPRESENTATIVE_POINT',source_geometry_role=link['geometry_role'],source_field=link['source_field'],source_row_index=link['source_row_index'],predicate=link['predicate'],authority=link['authority'],raw_geometry_transform_verified=link['raw_geometry_transform_verified'],normalization=link['normalization'],source_field_sha256=link['source_field_sha256'],current_database_rechecked=False))
        receipts.append(dict(chunk_id=cid,content_sha256=check['content_sha256'],source_sha256=check['source_sha256'],source_locator=locator,status=status,reason=f'{hash_state};{text_state}',semantic_authority=False,coordinate_authority=False,coordinate_literal_issues=coordinate_issues.get(cid,[]),object_links=object_links))
    target=DEFAULT/'compact_receipts.jsonl'
    if target.exists(): raise RuntimeError('Refuse to replace published receipts')
    with target.open('w',encoding='utf-8') as stream:
        for row in receipts: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    write(DEFAULT/'resolved_source_checks.json',dict(checks=overlays,counts=dict(Counter(r['text_status'] for r in overlays))))
    write(DEFAULT/'receipt_manifest.json',dict(complete=True,completion_scope='all operational document chunks scanned, not semantic or spatial accuracy',files={'compact_receipts.jsonl':file_sha(target)},audited_at=datetime.now(timezone.utc).isoformat(),snapshot_sha256=snapshot['sha256'],source_manifest_sha256=file_sha(DEFAULT/'source_manifest.json'),spatial_links_sha256=file_sha(spatial_path) if spatial_path.exists() else None,object_links=sum(len(r['object_links']) for r in receipts),rows=len(receipts),status_counts=dict(Counter(r['status'] for r in receipts)),limitations=LIMITS,script_sha256=file_sha(DEFAULT/'audit_script_executed.py'),finalizer_sha256=file_sha(Path(__file__)),audit_environment=json.loads((DEFAULT/'audit_environment.json').read_text(encoding='utf-8')),audit_environment_sha256=file_sha(DEFAULT/'audit_environment.json')))
    print(json.dumps(dict(rows=len(receipts),status_counts=dict(Counter(r['status'] for r in receipts)))))
    state=json.loads((DEFAULT/'status.json').read_text(encoding='utf-8'))
    state.update(status='PARTIALLY_VERIFIED',summary='전체 청크 검사를 마쳤습니다. 원문 대조 확인과 미검증·불일치를 구분하며 지명·좌표 후보의 의미·위치 정확성은 별도 검증 대상입니다.',limitations=LIMITS,updated_at=datetime.now(timezone.utc).isoformat())
    state['counts']['receipt_verified_text']=sum(r['status']=='VERIFIED_TEXT' for r in receipts)
    state['counts']['receipt_unverified']=sum(r['status']=='UNVERIFIED' for r in receipts)
    state['counts']['receipt_mismatch']=sum(r['status']=='MISMATCH' for r in receipts)
    state['counts']['v1_chunks_source_text_matched']=counts['chunks_source_text_matched']
    state['counts']['v1_chunks_unverified']=counts['chunks_unverified']
    state['counts']['chunks_source_text_matched']=state['counts']['receipt_verified_text']
    state['counts']['chunks_unverified']=state['counts']['receipt_unverified']+state['counts']['receipt_mismatch']
    write(DEFAULT/'status.json',state)


if __name__=='__main__': main()
