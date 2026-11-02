"""Publish a completed text-audit snapshot without touching previous receipts."""
import argparse
import hashlib
import json
from pathlib import Path


def publish(source, destination, version):
    source, destination = Path(source), Path(destination)
    if not version or Path(version).name != version or version in ('.', '..'):
        raise ValueError('Invalid version')
    manifest_raw = (source / 'receipt_manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    raw = (source / 'compact_receipts.jsonl').read_bytes()
    sha = lambda b: hashlib.sha256(b).hexdigest()
    if manifest.get('complete') is not True or sha(raw) != manifest.get('files', {}).get('compact_receipts.jsonl'):
        raise ValueError('Incomplete or changed receipt snapshot')
    snapshot_hash = manifest.get('snapshot_sha256')
    if (type(manifest.get('rows')) is not int or manifest['rows'] <= 0
            or not isinstance(manifest.get('audited_at'), str) or not manifest['audited_at'].strip()
            or not isinstance(snapshot_hash, str) or len(snapshot_hash) != 64
            or any(c not in '0123456789abcdef' for c in snapshot_hash)):
        raise ValueError('Missing audit snapshot provenance')
    seen = set()
    for line in raw.splitlines():
        row = json.loads(line)
        if str(row['chunk_id']) in seen or row['status'] not in ('VERIFIED_TEXT', 'MISMATCH', 'UNVERIFIED'):
            raise ValueError('Duplicate or invalid receipt')
        seen.add(str(row['chunk_id']))
        for key in ('content_sha256',):
            value = row.get(key)
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Invalid identity hash')
        source_hash = row.get('source_sha256')
        if source_hash is not None and not isinstance(source_hash, str):
            raise ValueError('Invalid recorded source identity')
        if row['status'] == 'VERIFIED_TEXT' and (not isinstance(source_hash, str) or len(source_hash) != 64
                or any(c not in '0123456789abcdef' for c in source_hash)):
            raise ValueError('Verified receipt requires full source hash')
        if row.get('object_links'):
            spatial_hash = manifest.get('spatial_links_sha256')
            if not isinstance(spatial_hash, str) or len(spatial_hash) != 64 or any(c not in '0123456789abcdef' for c in spatial_hash):
                raise ValueError('Object links require spatial audit hash')
    if len(seen) != manifest.get('rows'):
        raise ValueError('Incomplete row count')
    folder = destination / version
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'receipts.jsonl').write_bytes(raw)
    published = {**manifest, 'files': {'receipts.jsonl': sha(raw)},
                 'audit_manifest_sha256': sha(manifest_raw), 'coordinate_authority': False,
                 'semantic_correctness_verified': False}
    content = (json.dumps(published, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    (folder / 'manifest.json').write_bytes(content)
    pointer = {'manifest': version+'/manifest.json', 'sha256': sha(content)}
    temporary = destination / 'current.json.tmp'
    temporary.write_text(json.dumps(pointer, indent=2)+'\n', encoding='utf-8')
    temporary.replace(destination / 'current.json')
    return pointer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--destination', type=Path, default=Path('data/source_verification'))
    args = parser.parse_args()
    print(json.dumps(publish(args.source, args.destination, args.version)))
