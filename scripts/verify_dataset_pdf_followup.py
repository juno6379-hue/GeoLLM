"""Read-only second-engine PDF checks, with exact page/span receipts.

Never remove whitespace between tokens, substitute punctuation, or repair digits.
Unknown or ambiguous mappings stay unverified. No DB/model/research access.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/dataset_location_audit_20261102/source/revision_v2'
OUT = ROOT / 'outputs/dataset_unverified_followup_20261102/pdf'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized_with_offsets(value):
    """Collapse whitespace runs to one separator; never delete token boundaries."""
    pieces, offsets = [], []
    for match in re.finditer(r'\s+|\S', value):
        pieces.append(' ' if match.group().isspace() else match.group())
        offsets.append((match.start(), match.end()))
    return ''.join(pieces), offsets


def exact_span(content, source):
    if not content.strip() or '\x00' in content or '\ufffd' in content:
        return None
    needle, _ = normalized_with_offsets(content.strip())
    haystack, offsets = normalized_with_offsets(source)
    start = haystack.find(needle)
    if start < 0 or haystack.find(needle, start + 1) >= 0:
        return None
    a, b = offsets[start][0], offsets[start + len(needle) - 1][1]
    actual = source[a:b]
    # Explicit numeric lexeme protection: 12 34 cannot equal 1234, 1 .2 != 1.2.
    numbers = lambda s: re.findall(r'\d+(?:[.,]\d+)*', s)
    if numbers(actual) != numbers(content):
        return None
    return dict(start=a, end=b, text=actual, text_sha256=digest(actual.encode()),
                numeric_lexemes=numbers(actual), numeric_lexemes_equal=True,
                all_characters_and_token_boundaries_equal=True)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def progress_counts(results, total):
    verified=sum(r['status']=='VERIFIED_TEXT' for r in results)
    return dict(target=total,scanned=len(results),verified=verified,
                unresolved=len(results)-verified,pending=total-len(results))


def run(out):
    import pymupdf
    if (out / 'receipts.jsonl').exists():
        raise RuntimeError('Existing output preserved; choose another output directory')
    out.mkdir(parents=True, exist_ok=True)
    receipts = [json.loads(s) for s in (BASE/'compact_receipts.jsonl').open(encoding='utf-8')]
    selected = {r['chunk_id']: r for r in receipts if r['status']=='UNVERIFIED'
                and r.get('retrieval_status')!='SUPERSEDED' and 'EXTRACTION_' in r['reason']}
    groups = defaultdict(list)
    with gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['chunk_id'] in selected:
                groups[row['source_file']].append(row)
    if sum(map(len, groups.values())) != len(selected):
        raise RuntimeError('Input identity mismatch')
    results = []
    for source_file, rows in groups.items():
        path = ROOT / source_file
        raw_hash = digest(path.read_bytes())
        doc = pymupdf.open(path)
        page_cache = {}
        for row in rows:
            prior = selected[row['chunk_id']]
            receipt = dict(chunk_id=row['chunk_id'], content_sha256=digest(row['content'].encode()),
                           source_file=source_file, source_sha256=raw_hash,
                           source_locator=prior['source_locator'], prior_reason=prior['reason'],
                           status='UNVERIFIED', reason='SECOND_ENGINE_NO_EXACT_SPAN',
                           semantic_authority=False, coordinate_authority=False)
            if raw_hash != row['source_sha256'] or receipt['content_sha256'] != prior['content_sha256']:
                raise RuntimeError('Original source/content changed')
            locators = prior['source_locator']
            if not isinstance(locators, list) or not all(re.fullmatch(r'page:\d+', p) for p in locators):
                receipt['reason'] = 'INVALID_PAGE_LOCATOR'
                results.append(receipt)
                continue
            pages = [int(p.split(':')[1]) for p in locators]
            for sort in (False, True):
                page_text = []
                for page in pages:
                    key = (page, sort)
                    if key not in page_cache:
                        text = doc[page-1].get_text('text', sort=sort)
                        page_cache[key] = text
                        page_path = out/'pages'/raw_hash/f'{page}_{int(sort)}.txt'
                        page_path.parent.mkdir(parents=True,exist_ok=True)
                        page_path.write_text(text,encoding='utf-8')
                    page_text.append(page_cache[key])
                text = '\n'.join(page_text)
                span = exact_span(row['content'], text)
                if span:
                    receipt.update(status='VERIFIED_TEXT', reason='INDEPENDENT_PDF_EXACT_TOKEN_SPAN',
                                   extractor=f'PyMuPDF {pymupdf.VersionBind}', sort=sort,
                                   extracted_pages_sha256=digest(text.encode()), span=span)
                    break
            results.append(receipt)
        doc.close()
        dump(out/'status.json',dict(status='RUNNING', total=len(selected), checked=len(results),
             counts=dict(Counter(r['status'] for r in results)), updated_at=datetime.now(timezone.utc).isoformat()))
        print(json.dumps(dict(source=source_file, checked=len(results)),ensure_ascii=True),flush=True)
    target = out/'receipts.jsonl'
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results),encoding='utf-8')
    status = dict(status='COMPLETE', total=len(selected), checked=len(results),
                  counts=dict(Counter(r['status'] for r in results)),
                  reasons=dict(Counter(r['reason'] for r in results)),
                  files={'receipts.jsonl':digest(target.read_bytes())},
                  updated_at=datetime.now(timezone.utc).isoformat(),
                  engine=f'PyMuPDF {pymupdf.VersionBind}',
                  progress=progress_counts(results,len(selected)),
                  summary='PDF 원문 페이지의 독립 추출 결과와 숫자·단어 경계를 보존하여 대조했습니다.',
                  limitations=['원문 일치는 실제 지명 대상·좌표·최신성의 검증과 다릅니다.',
                               '일치하지 않은 청크를 공백 제거로 통과시키지 않았습니다.'],
                  input_receipts_sha256=digest((BASE/'compact_receipts.jsonl').read_bytes()),
                  scope='Source text span only; not real-world coordinate/semantic verification',
                  original_sources_unchanged=all(digest((ROOT/s).read_bytes())==rs[0]['source_sha256'] for s,rs in groups.items()))
    dump(out/'status.json',status)
    print(json.dumps(status,ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    run(parser.parse_args().output)
