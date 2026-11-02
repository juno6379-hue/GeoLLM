"""Propose source path repairs only with full-hash-backed original files.

Never updates DB/source metadata. Ambiguous hash matches retain all candidates.
"""
import json
from collections import Counter, defaultdict
from scripts.audit_dataset_locations import ROOT, DEFAULT, write


def main():
    sources=json.loads((DEFAULT/'source_manifest.json').read_text(encoding='utf-8'))
    by_hash=defaultdict(list);by_path={r['source_file']:r for r in sources}
    for row in sources: by_hash[row['sha256']].append(row['source_file'])
    candidates=[]
    for line in (DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'):
        row=json.loads(line);path=row['source_file'];h=row['source_sha256']
        if path in by_path: continue
        normalized=path.removeprefix('/app/') if path else ''
        paths=by_hash.get(h,[])
        if normalized in by_path and by_path[normalized]['sha256']==h:
            resolved=normalized;state='CONTAINER_PREFIX_AND_FULL_HASH_MATCH'
        elif len(paths)==1:
            resolved=paths[0];state='UNIQUE_FULL_HASH_MATCH'
        else:
            resolved=None;state='AMBIGUOUS_FULL_HASH' if paths else 'UNRESOLVED_NO_FULL_HASH_MATCH'
        candidates.append(dict(chunk_id=row['chunk_id'],recorded_source_file=path,recorded_source_sha256=h,resolved_source_file=resolved,matching_raw_paths=paths,resolution=state,applied=False,semantic_authority=False))
    write(DEFAULT/'source_path_repair_candidates.json',dict(candidates=candidates,counts=dict(Counter(c['resolution'] for c in candidates)),applied=False))
    print(json.dumps(dict(Counter(c['resolution'] for c in candidates))))


if __name__=='__main__': main()
