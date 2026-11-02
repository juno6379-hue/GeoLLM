"""Read-only DOCX paragraph/table locator audit; no DB or model access."""
import argparse, gzip, hashlib, json, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from scripts.docx_source_text import paragraph_text

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/dataset_location_audit_20261102/source/revision_v2'
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return ' '.join(s.split())
def locate(raw, content):
    with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z: xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    paragraphs = [p for p in root.iter() if p.tag.rsplit('}', 1)[-1] == 'p']
    parts, spans, offset = [], [], 0
    for index, p in enumerate(paragraphs, 1):
        text = norm(paragraph_text(p))
        if not text: continue
        if parts: offset += 1
        spans.append((offset, offset + len(text), index, sha(ET.tostring(p))))
        parts.append(text); offset += len(text)
    text, needle = ' '.join(parts), norm(content)
    start = text.find(needle) if needle else -1
    if start < 0: return dict(status='UNVERIFIED', reason='NO_LITERAL_NORMALIZED_SPAN')
    if text.find(needle, start + 1) >= 0: return dict(status='UNVERIFIED', reason='AMBIGUOUS_SPAN')
    end = start + len(needle)
    if (start and not text[start-1].isspace()) or (end < len(text) and not text[end].isspace()):
        return dict(status='UNVERIFIED', reason='TOKEN_BOUNDARY_MISMATCH')
    return dict(status='VERIFIED_TEXT', reason='UNIQUE_LITERAL_NORMALIZED_SPAN',
                xml_sha256=sha(xml), normalized_char_span=[start,end],
                normalization='WHITESPACE_ONLY',
                locators=[dict(xpath=f'(//w:p)[{i}]', paragraph_xml_sha256=h)
                          for a,b,i,h in spans if a < end and b > start])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    snapshot=BASE/'full_current_document_chunks.jsonl.gz'
    manifest=BASE/'full_current_snapshot_manifest.json'
    expected='af2173717804be8f6ee9fcc40491df1951fdf33e3f180ddd1886c1c2e88e6147'
    if sha(snapshot.read_bytes())!=expected or json.loads(manifest.read_text())['sha256']!=expected:raise ValueError('Pinned snapshot changed')
    receipts={r['chunk_id']:r for line in (BASE/'compact_receipts.jsonl').open(encoding='utf-8') if (r:=json.loads(line))['status']=='UNVERIFIED'}
    results=[]; cache={}
    for line in gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8'):
        r=json.loads(line)
        if r['chunk_id'] not in receipts or Path(r['source_file']).suffix.lower()!='.docx':continue
        p=ROOT/r['source_file']
        if str(p) not in cache:cache[str(p)]=p.read_bytes()
        raw=cache[str(p)]
        result=dict(chunk_id=r['chunk_id'],source_file=r['source_file'],source_sha256=r['source_sha256'],observed_source_sha256=sha(raw),content_sha256=sha(r['content'].encode()),semantic_authority=False,coordinate_authority=False)
        receipt=receipts[r['chunk_id']]
        if receipt['source_sha256']!=r['source_sha256'] or receipt['content_sha256']!=result['content_sha256']:result.update(status='UNVERIFIED',reason='RECEIPT_IDENTITY_MISMATCH')
        elif sha(raw)!=r['source_sha256']:result.update(status='UNVERIFIED',reason='SOURCE_HASH_MISMATCH')
        else:result.update(locate(raw,r['content']))
        results.append(result)
    if sha(snapshot.read_bytes())!=expected:raise ValueError('Snapshot changed during audit')
    for filename,raw in cache.items():
        if sha(Path(filename).read_bytes())!=sha(raw):raise ValueError('Source changed during audit')
    data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results).encode()
    (args.output/'results.jsonl').write_bytes(data)
    summary=dict(total=len(results),verified=sum(r['status']=='VERIFIED_TEXT' for r in results),unverified=sum(r['status']!='VERIFIED_TEXT' for r in results),results_sha256=sha(data),input_snapshot_sha256=sha((BASE/'full_current_document_chunks.jsonl.gz').read_bytes()),db_modified=False,model_called=False,holdout_used=False,scope='BASELINE_UNVERIFIED_DOCX_ONLY_NOT_CURRENT_DB')
    summary.update(extractor_version='docx_literal_locator_v2',extractor_sha256=sha(Path(__file__).read_bytes()),paragraph_parser_sha256=sha((ROOT/'scripts/docx_source_text.py').read_bytes()),input_unchanged=True)
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
