"""Archive selected public MOF originals; inventory local references without promoting them to gold."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 150 * 1024 * 1024


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_document(raw):
    if raw.startswith(b'%PDF-'):
        if b'%%EOF' not in raw[-4096:]:
            raise ValueError('Incomplete PDF')
        return 'pdf'
    if raw.startswith(b'PK'):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if archive.testzip():
                raise ValueError('Corrupt ZIP member')
            return 'hwpx' if 'Contents/content.hpf' in archive.namelist() else 'zip'
    if raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        return 'hwp'
    if b'<HWPML' in raw[:4096]:
        ET.fromstring(raw)
        return 'hml'
    raise ValueError('Unsupported document or HTML error response; not archived as an original')


def fetch(url):
    if urlsplit(url).hostname != 'www.mof.go.kr' or urlsplit(url).scheme != 'https':
        raise ValueError('Only configured official HTTPS MOF URLs are accepted')
    request = urllib.request.Request(url, headers={'User-Agent':'GeoLLM-reference-archive/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        if urlsplit(response.url).hostname != 'www.mof.go.kr':
            raise ValueError('Unexpected download redirect host')
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Download exceeds archive size limit')
        return raw, {'url':url, 'resolved_url':response.url,
                     'content_type':response.headers.get('Content-Type'),
                     'content_disposition':response.headers.get('Content-Disposition'),
                     'retrieved_at':datetime.now(timezone.utc).isoformat()}


def save_artifact(base, stem, raw, extension, metadata):
    path = base / (stem + '.' + extension)
    if path.exists():
        if sha256(path.read_bytes()) != sha256(raw):
            raise ValueError(f'Existing snapshot differs: {path.name}; choose a new snapshot ID')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    return {**metadata, 'path':path.relative_to(ROOT).as_posix(), 'bytes':len(raw),
            'sha256':sha256(raw), 'format':extension}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/evaluation/maritime_reference_downloads.json')
    parser.add_argument('--snapshot',required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.snapshot):
        raise ValueError('Invalid snapshot ID')
    config = json.loads(args.config.read_text(encoding='utf-8'))
    base = (ROOT/config['storage']/args.snapshot).resolve()
    if not base.is_relative_to(ROOT/'Dataset'):
        raise ValueError('Archive must remain under Dataset')
    base.mkdir(parents=True,exist_ok=True)
    manifest_path = base/'manifest.json'
    report = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {
        'version':config['version'], 'config_sha256':sha256(args.config.read_bytes()),
        'snapshot':args.snapshot, 'gold_status':'UNREVIEWED',
        'current_law_status':'NOT_VERIFIED', 'records':[], 'existing_local':[], 'failures':[]}
    if report['config_sha256'] != sha256(args.config.read_bytes()):
        raise ValueError('Config changed; use a new snapshot ID')
    # A resumed run revalidates hashes and retains the original retrieval time.
    successful = {row['artifact_id']:row for row in report['records']}
    for row in successful.values():
        path = (ROOT/row['path']).resolve()
        if not path.is_relative_to(base) or sha256(path.read_bytes()) != row['sha256']:
            raise ValueError('Stored artifact hash/path mismatch')
    report['failures'] = []
    def checkpoint():
        manifest_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for source in config['sources']:
        items = [('page',source['page'])] + [(str(n),f"https://www.mof.go.kr/jfile/readDownloadFile.do?fileType=MOF_ARTICLE&fileTypeSeq={source['article']}&fileNum={n}") for n in source['files']]
        for number,url in items:
            identifier = source['id']+'_'+number
            if identifier in successful:
                continue
            try:
                raw, metadata = fetch(url)
                extension = 'html' if number=='page' else validate_document(raw)
                if number=='page' and b'<html' not in raw.lower():
                    raise ValueError('Not an HTML source page')
                row = save_artifact(base,identifier,raw,extension,{
                    **metadata, 'artifact_id':identifier, 'source_id':source['id'],
                    'title':source['title'], 'edition':source['edition'], 'role':source['role'],
                    'source_page':source['page'], 'review_status':'UNREVIEWED',
                    'current_law_status':'NOT_VERIFIED', 'signature_verified':False})
                report['records'].append(row)
                print(json.dumps({'saved':identifier,'format':extension,'bytes':len(raw)}),flush=True)
            except Exception as exc:
                report['failures'].append({'artifact_id':identifier,'url':url,'error':str(exc)})
                print(json.dumps({'failed':identifier,'error':str(exc)}),flush=True)
            checkpoint()
            time.sleep(.3)
    report['existing_local'] = []
    for pattern in config['existing_local_patterns']:
        for path in sorted(ROOT.glob(pattern)):
            raw=path.read_bytes()
            report['existing_local'].append({'path':path.relative_to(ROOT).as_posix(),
                'bytes':len(raw),'sha256':sha256(raw),'provenance_status':'PREEXISTING_ORIGIN_NOT_REVERIFIED',
                'action':'REUSED_NOT_DOWNLOADED','review_status':'UNREVIEWED'})
    checkpoint()
    print(json.dumps({'originals':sum(r['format']!='html' for r in report['records']),
                      'pages':sum(r['format']=='html' for r in report['records']),
                      'existing':len(report['existing_local']),'failures':len(report['failures'])}))
    return bool(report['failures'])


if __name__=='__main__':
    raise SystemExit(main())
