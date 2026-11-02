"""Independently check published audit artifacts and rehash all raw sources."""
import json
from collections import Counter
from scripts.audit_dataset_locations import DEFAULT, ROOT, file_sha, sha, write


def main():
    manifest=json.loads((DEFAULT/'receipt_manifest.json').read_text(encoding='utf-8'))
    receipt_path=DEFAULT/'compact_receipts.jsonl'
    if file_sha(receipt_path)!=manifest['files']['compact_receipts.jsonl']:raise RuntimeError('Receipt hash mismatch')
    snapshot_path=DEFAULT/'document_chunks.jsonl'
    if file_sha(snapshot_path)!=manifest['snapshot_sha256']:raise RuntimeError('Snapshot hash mismatch')
    chunks={r['chunk_id']:r for r in map(json.loads,snapshot_path.open(encoding='utf-8'))}
    receipts=list(map(json.loads,receipt_path.open(encoding='utf-8')))
    if len(receipts)!=len(chunks) or len({r['chunk_id'] for r in receipts})!=len(chunks):raise RuntimeError('Receipt count/identity mismatch')
    for row in receipts:
        original=chunks[row['chunk_id']]
        if row['source_sha256']!=original['source_sha256'] or row['content_sha256']!=sha((original['content'] or '').encode()):raise RuntimeError('Content lineage mismatch')
    sources=json.loads((DEFAULT/'source_manifest.json').read_text(encoding='utf-8'))
    changed=[s['source_file'] for s in sources if file_sha(ROOT/s['source_file'])!=s['sha256']]
    if changed:raise RuntimeError('Raw source changed: '+str(changed))
    result=dict(status='ARTIFACTS_AND_RAW_HASHES_VERIFIED',raw_sources_rehashed=len(sources),raw_sources_changed=changed,receipt_rows=len(receipts),status_counts=dict(Counter(r['status'] for r in receipts)),coordinate_issue_chunks=sum(bool(r['coordinate_literal_issues']) for r in receipts),object_links=sum(len(r['object_links']) for r in receipts),snapshot_sha256=manifest['snapshot_sha256'],receipt_sha256=file_sha(receipt_path),semantic_accuracy_verified=False)
    write(DEFAULT/'final_verification.json',result);print(json.dumps(result))


if __name__=='__main__':main()
