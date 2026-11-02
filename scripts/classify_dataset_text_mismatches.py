"""Distinguish extraction whitespace/replacement variation from other mismatches.

Relaxed comparisons NEVER certify source text. They avoid conflating an extractor
variation with a demonstrated factual transcription defect.
"""
import json
import re
from collections import Counter, defaultdict
from scripts.audit_dataset_locations import ROOT, DEFAULT, source_sections, write, norm


def classify(content, expected):
    a=re.sub(r'\s+','',content.replace('\x00',''));b=re.sub(r'\s+','',expected.replace('\x00',''))
    if a and a in b:return 'UNVERIFIED_EXTRACTION_WHITESPACE_VARIATION'
    if a.replace('\ufffd','') and a.replace('\ufffd','') in b.replace('\ufffd',''):
        return 'UNVERIFIED_EXTRACTION_REPLACEMENT_VARIATION'
    typography=str.maketrans({'’':"'",'‘':"'",'“':'"','”':'"'})
    if a.translate(typography) and a.translate(typography) in b.translate(typography):
        return 'UNVERIFIED_EXTRACTION_TYPOGRAPHY_VARIATION'
    return 'TEXT_MISMATCH'


def main():
    chunks={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'))}
    grouped=defaultdict(list)
    for path in (DEFAULT/'checkpoints').glob('*.json'):
        cache=json.loads(path.read_text(encoding='utf-8'))
        for check in cache['checks']:
            if check['text_status']=='TEXT_MISMATCH':grouped[check['source_file']].append(check)
    results=[]
    for source,checks in grouped.items():
        cache_path=DEFAULT/'mismatch_checkpoints'/(checks[0]['actual_source_sha256']+'.json')
        expected_ids={c['chunk_id'] for c in checks}
        if cache_path.exists():
            cached=json.loads(cache_path.read_text(encoding='utf-8'))
            if {c['chunk_id'] for c in cached}==expected_ids and not any(c['v2_status']=='TEXT_MISMATCH' for c in cached):
                results.extend(cached);continue
        path=ROOT/source;sections={};group=[]
        if path.suffix.lower()=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(path)
            pages={int(loc.split(':')[1]) for c in checks for loc in (c['locator'] or []) if loc.startswith('page:')}
            sections={f'page:{page}':reader.pages[page-1].extract_text() or '' for page in pages}
        else:
            sections=source_sections(path,[chunks[c['chunk_id']] for c in checks])
        for check in checks:
            row=chunks[check['chunk_id']];loc=check['locator'];state='TEXT_MISMATCH'
            if isinstance(loc,list) and all(s in sections for s in loc):
                expected='\n'.join(sections[s] for s in loc)
                state=classify(row['content'] or '',expected)
            group.append(dict(chunk_id=check['chunk_id'],v1_status='TEXT_MISMATCH',v2_status=state,source_file=source,locator=loc))
        write(cache_path,group);results.extend(group)
        print(json.dumps(dict(source=source,counts=dict(Counter(r['v2_status'] for r in group))),ensure_ascii=True),flush=True)
    write(DEFAULT/'mismatch_classification.json',dict(rows=results,counts=dict(Counter(r['v2_status'] for r in results))))


if __name__=='__main__':main()
