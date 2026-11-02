"""Prepare unapplied source-span revisions for unresolved PDF text.

Whitespace-insensitive alignment only locates a candidate; it never verifies the
old text. The candidate itself is an exact source substring with numeric checks.
"""
import gzip
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
from scripts.verify_dataset_pdf_followup import ROOT, BASE, OUT, digest, dump


def locate_candidate(content, source):
    chars = [(c,i) for i,c in enumerate(source) if not c.isspace()]
    haystack=''.join(c for c,_ in chars)
    needle=''.join(c for c in content if not c.isspace())
    if not needle or '\ufffd' in needle or '\x00' in needle:
        return None
    at=haystack.find(needle)
    if at<0 or haystack.find(needle,at+1)>=0:
        return None
    a,b=chars[at][1],chars[at+len(needle)-1][1]+1
    actual=source[a:b]
    nums=lambda s:re.findall(r'\d+(?:[.,]\d+)*',s)
    return dict(start=a,end=b,text=actual,text_sha256=digest(actual.encode()),
                original_numeric_lexemes=nums(content), source_numeric_lexemes=nums(actual),
                numeric_lexemes_equal=nums(content)==nums(actual),
                status='UNAPPLIED_REEXTRACTION_CANDIDATE',
                old_text_verified=False,requires_new_embedding=True,
                requires_visual_numeric_review=nums(content)!=nums(actual))


def main(out):
    from pypdf import PdfReader
    import pypdf
    from scripts.build_coastal_knowledge import parts
    if (out/'candidates.jsonl').exists():
        raise RuntimeError('Output already exists')
    selected={r['chunk_id']:r for s in (BASE/'compact_receipts.jsonl').open(encoding='utf-8')
              if (r:=json.loads(s))['status']=='UNVERIFIED' and 'EXTRACTION_' in r['reason']}
    groups=defaultdict(list)
    with gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') as f:
        for s in f:
            r=json.loads(s)
            if r['chunk_id'] in selected:groups[r['source_file']].append(r)
    results=[]
    for source,rows in groups.items():
        path=ROOT/source
        h=digest(path.read_bytes())
        reader=PdfReader(path)
        cache={}
        for row in rows:
            if h!=row['source_sha256']:raise RuntimeError('Source changed')
            prior=selected[row['chunk_id']]
            locators=prior['source_locator'];texts=[]
            for loc in locators:
                page=int(loc.split(':')[1])
                if page not in cache:cache[page]=reader.pages[page-1].extract_text() or ''
                texts.append(cache[page])
            text='\n'.join(texts)
            candidate=locate_candidate(row['content'],text)
            size=1100 if row['document_type']=='coastal_pilot' else 2200
            reproduced=dict(parts(text,size=size)).get(row['metadata'].get('char_offset'))==row['content']
            results.append(dict(chunk_id=row['chunk_id'],source_file=source,source_sha256=h,
                                content_sha256=digest(row['content'].encode()),source_locator=locators,
                                extracted_pages_sha256=digest(text.encode()),
                                original_extractor_reproduced=reproduced,extractor_version=pypdf.__version__,
                                candidate=candidate,status='CANDIDATE_PREPARED' if candidate else 'VISUAL_REVIEW_REQUIRED'))
        dump(out/'status.json',dict(status='RUNNING',checked=len(results),total=len(selected)))
        print(json.dumps(dict(source=source,checked=len(results)),ensure_ascii=True),flush=True)
    out.mkdir(parents=True,exist_ok=True)
    p=out/'candidates.jsonl'
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results),encoding='utf-8')
    dump(out/'status.json',dict(status='COMPLETE',checked=len(results),total=len(selected),
         counts=dict(Counter(r['status'] for r in results)),
         numeric_changed=sum(bool(r['candidate']) and not r['candidate']['numeric_lexemes_equal'] for r in results),
         original_extractor_reproduced=sum(r['original_extractor_reproduced'] for r in results),
         applied=0,old_text_verified=0,sha256=digest(p.read_bytes())))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT/'reextraction')
    main(parser.parse_args().output)
