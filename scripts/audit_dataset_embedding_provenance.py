"""Audit recorded vector lineage without model calls or re-embedding."""
import json
from collections import Counter
from scripts.audit_dataset_locations import DEFAULT, sha, write


def main():
    counts=Counter();mismatches=[]
    for row in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8')):
        meta=row.get('metadata') or {}
        counts['embedded_rows']+=bool(row['embedded'])
        counts['dimension_1024']+=row['embedding_dimensions']==1024
        for key,field in [('model_name_present','embedding_model'),('model_digest_present','embedding_model_digest'),('input_hash_present','embedding_input_sha256'),('completion_time_present','embedding_completed_at')]:
            counts[key]+=bool(meta.get(field))
        if meta.get('embedding_input_sha256'):
            matched=sha((row['content'] or '').encode())==meta['embedding_input_sha256']
            counts['input_hash_matches_current_content']+=matched
            if not matched:mismatches.append(row['chunk_id'])
    result=dict(counts=dict(counts),input_hash_mismatch_chunk_ids=mismatches,limitations=['Metadata presence is not independent validation of stored vector generation or vector-content semantics. No vectors were regenerated.'])
    write(DEFAULT/'embedding_provenance_audit.json',result);print(json.dumps(result))


if __name__=='__main__':main()
