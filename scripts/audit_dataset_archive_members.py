"""Inventory original ZIP member metadata without extracting or modifying sources.

Nested archive contents and member CRC validation are deliberately not claimed.
"""
import json
import zipfile
from pathlib import Path
from scripts.audit_dataset_locations import ROOT, DEFAULT, file_sha, write


def main():
    results=[]
    for path in sorted((ROOT/'Dataset').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.zip','.hwpx','.docx','.xlsx'}:
            continue
        item=dict(source_file=path.relative_to(ROOT).as_posix(),sha256=file_sha(path),members=[],crc_content_verified=False,nested_contents_verified=False)
        try:
            with zipfile.ZipFile(path) as archive:
                item['members']=[dict(name=m.filename,uncompressed_bytes=m.file_size,compressed_bytes=m.compress_size,crc32=m.CRC,encrypted=bool(m.flag_bits&1),directory=m.is_dir(),nested_archive=Path(m.filename).suffix.lower() in {'.zip','.7z','.rar'}) for m in archive.infolist()]
            item['status']='DIRECT_MEMBER_METADATA_ENUMERATED'
        except Exception as exc:
            item.update(status='UNVERIFIED',error_type=type(exc).__name__)
        results.append(item)
    write(DEFAULT/'archive_members.json',dict(sources=results,archives=len(results),direct_members=sum(len(r['members']) for r in results),limitations=['Metadata listing only; compressed content CRC and nested contents not verified.']))
    write(DEFAULT/'initial_partial_attempt.json',dict(status='INTERRUPTED_BEFORE_CHUNK_AUDIT',reason='Audit initially started before export completed; stopped with chunks_scanned=0. Final audit requires completed snapshot manifest SHA and row count.',partial_observed_rows=735,logs=['audit.stdout.log','audit.stderr.log']))
    print(json.dumps(dict(archives=len(results),direct_members=sum(len(r['members']) for r in results))))


if __name__=='__main__': main()
