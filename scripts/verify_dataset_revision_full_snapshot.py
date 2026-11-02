"""Re-export the entire current corpus READ ONLY, then verify unaffected rows.

Gzip avoids writing another 120 MB plaintext file through the container mount.
Stored vector values outside the twelve revision rows are not revalidated here.
"""
import argparse
import gzip
import json
import os
from datetime import datetime, timezone
from scripts.audit_dataset_locations import DEFAULT, ROOT, file_sha, write

OUT=DEFAULT/'revision_v2'


def export():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    path=OUT/'full_current_document_chunks.jsonl.gz'
    if path.exists():raise RuntimeError('Refuse to overwrite full snapshot')
    with psycopg2.connect(os.environ['S101_DB_URL']) as conn:
        conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT current_database() AS database,txid_current_snapshot()::text AS snapshot')
            identity=dict(cur.fetchone())
            cur.execute('''SELECT chunk_id,document_type,title,section,content,source_file,
             source_id,source_sha256,page_no,metadata,embedding IS NOT NULL AS embedded,
             vector_dims(embedding) AS embedding_dimensions
             FROM knowledge.document_chunks ORDER BY chunk_id''')
            count=0
            with path.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as stream:
                for row in cur:
                    stream.write((json.dumps(dict(row),ensure_ascii=False,default=str)+'\n').encode());count+=1
    write(OUT/'full_current_snapshot_manifest.json',dict(read_only=True,identity=identity,rows=count,sha256=file_sha(path),encoding='gzip-jsonl',observed_at=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(rows=count,compressed_bytes=path.stat().st_size)))


def verify():
    baseline={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'))}
    with gzip.open(OUT/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') as stream:
        current={r['chunk_id']:r for r in map(json.loads,stream)}
    identity=json.loads((DEFAULT/'csv_generator_fix_verification.json').read_text(encoding='utf-8'))
    old=set(identity['old_ids']);new=set(identity['new_ids']);unaffected=set(baseline)-old
    if set(current)!=set(baseline)|new:raise RuntimeError('Full corpus identity mismatch')
    changed=[cid for cid in unaffected if baseline[cid]!=current[cid]]
    if changed:
        write(OUT/'full_snapshot_unexpected_changes.json',dict(chunk_ids=changed))
        raise RuntimeError('Unrelated corpus rows changed')
    full_manifest=json.loads((OUT/'full_current_snapshot_manifest.json').read_text(encoding='utf-8'))
    full_sha=file_sha(OUT/'full_current_document_chunks.jsonl.gz')
    if full_sha!=full_manifest['sha256'] or len(current)!=full_manifest['rows']:raise RuntimeError('Full snapshot receipt mismatch')
    delta=json.loads((DEFAULT/'csv_revision_db_snapshot.json').read_text(encoding='utf-8'))
    for row in delta['rows']:
        if current[row['chunk_id']]!={k:v for k,v in row.items() if k!='embedding_text'}:raise RuntimeError('Targeted delta changed after read-only verification')
    manifest=json.loads((OUT/'receipt_manifest.json').read_text(encoding='utf-8'))
    write(OUT/'receipt_manifest_delta_only.json',manifest)
    manifest.update(snapshot_sha256=full_sha,snapshot_kind='FULL_CURRENT_GZIP_JSONL_WITH_BASELINE_DELTA_LINEAGE',snapshot_encoding='gzip-jsonl',full_current_snapshot_manifest_sha256=file_sha(OUT/'full_current_snapshot_manifest.json'),unaffected_rows_rechecked=len(unaffected),full_current_rows_rechecked=len(current))
    manifest['limitations']=[item for item in manifest['limitations'] if not item.startswith('Non-target rows retain')]
    manifest['limitations'].append('Unchanged non-target content, metadata, provenance and embedding presence/dimension checked; non-target vector values not re-exported.')
    write(OUT/'receipt_manifest.json',manifest)
    result=dict(status='FULL_CURRENT_CORPUS_VERIFIED',total_rows=len(current),unaffected_baseline_rows_equal=len(unaffected),target_rows_equal=12,read_only_snapshot_sha256=full_sha,baseline_snapshot_sha256=file_sha(DEFAULT/'document_chunks.jsonl'),delta_snapshot_sha256=file_sha(DEFAULT/'csv_revision_db_snapshot.json'))
    write(OUT/'full_corpus_verification.json',result)
    state=json.loads((DEFAULT/'status.json').read_text(encoding='utf-8'))
    manifest_path=(OUT/'receipt_manifest.json').relative_to(ROOT).as_posix()
    state['evidence']=[dict(path=e['path'],sha256=file_sha(OUT/'receipt_manifest.json')) if e['path']==manifest_path else e for e in state['evidence']]
    write(DEFAULT/'status.json',state)
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');args=parser.parse_args()
    (export if args.export else verify)()
