"""Read-only operational corpus audit; no model, research, or holdout inputs.

Export inside backend, then audit on Dataset host. Per-source checkpoints are
keyed by raw hash and snapshot hash. Lexical mentions never assert coordinates.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'outputs/dataset_location_audit_20261102/source'
LIMITS = ['지명·좌표 문자열은 미검증 후보이며 객체 동일성이나 좌표 권위를 뜻하지 않습니다.',
          'PDF 본문 일치는 도표·OCR·레이아웃·최신 판·의미 완결성 검증이 아닙니다.',
          '벡터 존재와 차원 확인은 생성 모델 이력 검증이 아닙니다.',
          '미지원 원문 위치·형식과 생성 요약은 미검증입니다. 홀드아웃은 열람하지 않았습니다.']

def sha(value):
    return hashlib.sha256(value).hexdigest()

def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    for attempt in range(20):
        try:
            tmp.replace(path)
            break
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.1)

def norm(text):
    return re.sub(r'\s+', ' ', text.replace('\x00', '')).strip()

def mentions(text):
    patterns = {
        'place_suffix_candidate': r'(?<![가-힣])(?:[가-힣]{2,15})(?:항|항구|등대|방파제|해협|수로|만|도)(?![가-힣])',
        'coordinate_notation_candidate': r'(?:[NSEW북남동서위경]{1,3}\s*)?\d{1,3}\s*[°º도]\s*\d{1,2}(?:\.\d+)?\s*[′\x27분](?:\s*\d{1,2}(?:\.\d+)?\s*[″\x22초])?\s*[NSEW]?',
        'decimal_pair_candidate': r'(?<!\d)(?:1[0-7]\d|[1-9]?\d)\.\d{3,}\s*[,/]\s*(?:[1-8]?\d)\.\d{3,}(?!\d)',
    }
    return [dict(kind=kind, text=m.group(), start=m.start(), end=m.end(), authority=False)
            for kind, pattern in patterns.items() for m in re.finditer(pattern, text)]

def export(out):
    import psycopg2
    from psycopg2.extras import RealDictCursor
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'document_chunks.jsonl'
    if target.exists():
        raise RuntimeError('Refuse to overwrite snapshot; use a new output folder')
    with psycopg2.connect(os.environ['S101_DB_URL']) as conn:
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute('SELECT current_database() AS database, txid_current_snapshot()::text AS snapshot')
            identity = dict(cur.fetchone())
            cur.execute('''SELECT chunk_id,document_type,title,section,content,source_file,
              source_id,source_sha256,page_no,metadata,embedding IS NOT NULL AS embedded,
              vector_dims(embedding) AS embedding_dimensions
              FROM knowledge.document_chunks ORDER BY source_file,chunk_id''')
            count = 0
            with target.open('w', encoding='utf-8') as stream:
                for row in cur:
                    stream.write(json.dumps(dict(row), ensure_ascii=False, default=str)+'\n')
                    count += 1
    write(out/'snapshot_manifest.json', dict(read_only=True, identity=identity, rows=count,
          sha256=file_sha(target), observed_at=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(rows=count, read_only=True)))

def source_sections(path, rows):
    """Return independently re-extracted locator text, not stored chunk artifacts."""
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        from pypdf import PdfReader
        return {f'page:{i}': page.extract_text() or '' for i,page in enumerate(PdfReader(path).pages,1)}
    if suffix == '.csv':
        from scripts.build_dataset_embedding_coverage import decode_best
        text, encoding = decode_best(path.read_bytes())
        values = list(csv.reader(io.StringIO(text)))
        return {'csv_rows': values, 'csv_encoding': encoding}
    if suffix == '.shp' and any(r['document_type']=='small_harbour_guide' for r in rows):
        import shapefile
        return {'shp_records': [r.as_dict() for r in shapefile.Reader(str(path),encoding='utf-8',encodingErrors='replace').iterRecords()]}
    if suffix in {'.xls','.xlsx','.hml','.xml','.hwpx','.docx'}:
        from scripts.dataset_pipeline import sections
        return {locator:text for locator,text,_ in sections(path)}
    return {}

def compare(row, sections):
    meta = row.get('metadata') or {}
    typ = row['document_type'] or ''
    if typ.endswith('_profile') or typ == 'dataset_profile':
        return 'PROFILE_NOT_SOURCE_BODY', None
    value = row['content'] or ''
    if typ == 'small_harbour_guide' and 'shp_records' in sections:
        idx = meta.get('row_index')
        if isinstance(idx,int) and 0 <= idx < len(sections['shp_records']):
            rec=sections['shp_records'][idx]
            labels={'INTRODU':'항만 소개','VOYAGE_INF':'항해 정보','FLT_STTUS':'시설 현황','TRAFFIC_IN':'교통 정보','SEA_WETHER':'해상 기상','SUPPLY_REP':'보급 수리','EBBF_INFO':'조석 정보','TOUR_INFO':'주변 안내'}
            field=row['section']
            expected=f"{str(rec.get('NAME') or '').strip()} / {rec.get('ADR_KNM', '')} / {labels.get(field,'')}\n{str(rec.get(field) or '').strip()}"
            return ('MATCH_EXACT' if expected==value else 'TEXT_MISMATCH'),f'row:{idx};field:{field}'
    if 'csv_rows' in sections and meta.get('source_row_start') is not None:
        start,end=int(meta['source_row_start']),int(meta['source_row_end'])
        records=sections['csv_rows']
        expected='columns: '+' | '.join(records[0])+'\n'+'\n'.join(' | '.join(r) for r in records[start:end+1])
        return ('MATCH_NORMALIZED' if norm(value) in norm(expected) else 'TEXT_MISMATCH'),f'rows:{start}-{end}'
    locators=meta.get('source_locators')
    if not locators and row.get('page_no'):
        locators=[f"page:{row['page_no']}"]
    if not locators:
        return 'LOCATOR_UNSUPPORTED',None
    if any(loc not in sections for loc in locators):
        return 'LOCATOR_NOT_FOUND',locators
    expected='\n'.join(sections[loc] for loc in locators)
    return ('MATCH_NORMALIZED' if norm(value) and norm(value) in norm(expected) else 'TEXT_MISMATCH'),locators

def audit(out):
    out.mkdir(parents=True, exist_ok=True)
    snapshot=out/'document_chunks.jsonl'
    snapshot_hash=file_sha(snapshot)
    receipt=json.loads((out/'snapshot_manifest.json').read_text(encoding='utf-8'))
    if receipt['sha256']!=snapshot_hash:
        raise RuntimeError('Incomplete or changed snapshot')
    groups=defaultdict(list)
    for line in snapshot.open(encoding='utf-8'):
        row=json.loads(line);groups[row['source_file']].append(row)
    if sum(map(len,groups.values()))!=receipt['rows']:
        raise RuntimeError('Snapshot row count mismatch')
    files=sorted(p for p in (ROOT/'Dataset').rglob('*') if p.is_file())
    counts=dict(source_files=len(files),sources_hashed=0,chunks_total=sum(map(len,groups.values())),chunks_scanned=0,chunks_source_text_matched=0,chunks_unverified=0,candidate_mentions=0)
    def status(state,summary):
        write(out/'status.json',dict(status=state,updated_at=datetime.now(timezone.utc).isoformat(),counts=counts,limitations=LIMITS,evidence=[dict(path=snapshot.relative_to(ROOT).as_posix(),sha256=snapshot_hash)],summary=summary))
    status('RUNNING','원본 해시와 원문 위치별 본문 대조를 진행하고 있습니다.')
    sources=[]
    previous=json.loads((ROOT/'outputs/dataset_audit_20261031/raw_manifest/raw_source_manifest.json').read_text(encoding='utf-8'))
    prior={r['relative_path']:r['sha256'] for r in previous['sources']}
    for path in files:
        rel=path.relative_to(ROOT).as_posix();h=file_sha(path)
        sources.append(dict(source_file=rel,sha256=h,bytes=path.stat().st_size,previous_hash_equal=prior.get(path.relative_to(ROOT/'Dataset').as_posix())==h))
        counts['sources_hashed']+=1
        status('RUNNING','전체 원본 파일 해시를 대조하고 있습니다.')
    write(out/'source_manifest.json',sources)
    index={r['source_file']:r for r in sources}
    all_checks=[];all_mentions=[];extractions=[]
    for source,rows in sorted(groups.items(),key=lambda x:x[0] or ''):
        key=sha(str(source).encode());cache=out/'checkpoints'/f'{key}.json'
        info=index.get(source);h=info['sha256'] if info else None
        if cache.exists():
            result=json.loads(cache.read_text(encoding='utf-8'))
            if result['snapshot_sha256']!=snapshot_hash or result['raw_sha256']!=h:
                raise RuntimeError('Checkpoint inputs changed; use new output folder')
        else:
            sections={};error=None
            if info:
                try: sections=source_sections(ROOT/source,rows)
                except Exception as exc: error=type(exc).__name__+': '+str(exc)[:300]
            checks=[];found=[]
            for row in rows:
                content=row['content'] or '';meta=row.get('metadata') or {}
                state,loc=compare(row,sections)
                recorded=row['source_sha256']
                hash_state='MATCH_FULL' if h and recorded==h else 'MISSING_SOURCE' if not info else 'PARTIAL_HASH_UNVERIFIED' if str(recorded).startswith('partial:') else 'HASH_MISMATCH_OR_COMPOSITE'
                if row['document_type']=='small_harbour_guide' and info:
                    components=meta.get('component_hashes') or {}
                    if components and all(file_sha((ROOT/source).parent/n)==v for n,v in components.items()):
                        calculated=sha(json.dumps(components,sort_keys=True).encode())
                        hash_state='MATCH_COMPOSITE' if calculated==recorded else hash_state
                checks.append(dict(chunk_id=row['chunk_id'],document_type=row['document_type'],source_file=source,source_sha256=recorded,actual_source_sha256=h,source_hash_status=hash_state,content_sha256=sha(content.encode()),text_status=state,locator=loc,embedded=row['embedded'],embedding_dimensions=row['embedding_dimensions']))
                for mention in mentions(content):
                    found.append(dict(chunk_id=row['chunk_id'],source_file=source,source_sha256=recorded,content_sha256=sha(content.encode()),locator=loc,**mention))
            result=dict(snapshot_sha256=snapshot_hash,raw_sha256=h,source_file=source,extraction_error=error,section_count=len(sections),checks=checks,mentions=found)
            write(cache,result)
        all_checks.extend(result['checks']);all_mentions.extend(result['mentions'])
        extractions.append({k:v for k,v in result.items() if k not in {'checks','mentions'}})
        counts['chunks_scanned']=len(all_checks)
        counts['chunks_source_text_matched']=sum(c['text_status'].startswith('MATCH_') and c['source_hash_status'].startswith('MATCH_') for c in all_checks)
        counts['chunks_unverified']=counts['chunks_scanned']-counts['chunks_source_text_matched']
        counts['candidate_mentions']=len(all_mentions)
        status('RUNNING','원문 위치별 본문 대조와 지명·좌표 미검증 문자열 후보 검사를 진행하고 있습니다.')
        print(json.dumps(dict(source=source,scanned=counts['chunks_scanned'],total=counts['chunks_total']),ensure_ascii=True),flush=True)
    for name,items in [('chunk_checks',all_checks),('mention_candidates',all_mentions)]:
        with (out/f'{name}.jsonl').open('w',encoding='utf-8') as stream:
            for item in items: stream.write(json.dumps(item,ensure_ascii=False)+'\n')
    write(out/'extractions.json',extractions)
    summary=dict(counts=counts,source_hash_unchanged=sum(s['previous_hash_equal'] for s in sources),text_status=dict(Counter(c['text_status'] for c in all_checks)),source_hash_status=dict(Counter(c['source_hash_status'] for c in all_checks)),document_types=dict(Counter(c['document_type'] for c in all_checks)),null_embeddings=sum(not c['embedded'] for c in all_checks),limitations=LIMITS)
    write(out/'summary.json',summary)
    status('PARTIALLY_VERIFIED','전체 청크 검사를 마쳤습니다. 본문·원문 위치·출처 이력 및 의미 미검증 항목이 남아 있습니다.')
    print(json.dumps(summary,ensure_ascii=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=DEFAULT);parser.add_argument('--export',action='store_true')
    args=parser.parse_args();(export if args.export else audit)(args.output)
