"""Source-hash based Dataset reconciliation and resumable, non-authoritative ingestion.

Host: snapshot (container), extract (Dataset host), spatial (Dataset host).
Container: load, embed, snapshot. Runtime artifacts live in outputs/dataset_pipeline.
Raw records and source passages are preserved; profiles never prove extraction.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
import re
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/dataset_pipeline'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / name
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    temp.replace(target)


def connect():
    import psycopg2
    return psycopg2.connect(os.environ['S101_DB_URL'])


def snapshot():
    from psycopg2 import sql
    with connect() as conn, conn.cursor() as cur:
        cur.execute('''SELECT source_file,source_sha256,document_type,count(*),count(embedding),
          min(vector_dims(embedding)),max(vector_dims(embedding))
          FROM knowledge.document_chunks GROUP BY 1,2,3''')
        documents = [dict(zip(['source_file','source_sha256','document_type','chunks','embedded','min_dim','max_dim'], r)) for r in cur.fetchall()]
        cur.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='serving'")
        tables = {}
        for table, col in cur.fetchall():
            tables.setdefault(table, []).append(col)
        spatial = []
        for table, cols in tables.items():
            geom = next((c for c in ('geom','geometry') if c in cols), None)
            if not geom or 'provenance' not in cols:
                continue
            valid = sql.SQL('geometry_valid') if 'geometry_valid' in cols else sql.SQL('ST_IsValid({g}) AND ST_SRID({g})=4326').format(g=sql.Identifier(geom))
            query = sql.SQL('''SELECT provenance->>'source_sha256',
              coalesce(provenance->>'source_asset',provenance->>'source_file'),
              count(*), count(*) FILTER(WHERE {g} IS NOT NULL AND {valid})
              FROM serving.{t} GROUP BY 1,2''').format(g=sql.Identifier(geom),valid=valid,t=sql.Identifier(table))
            cur.execute(query)
            spatial += [dict(relation='serving.'+table,source_sha256=r[0],source_file=r[1],rows=r[2],valid=r[3]) for r in cur.fetchall()]
        dump('live_snapshot.json',dict(observed_at=time.time(),documents=documents,spatial=spatial))
        print(dict(documents=sum(d['chunks'] for d in documents),embedded=sum(d['embedded'] for d in documents),spatial_groups=len(spatial)))


def classify_coverage(source_hash, documents):
    matches = [d for d in documents if d['source_sha256'] == source_hash]
    content = [d for d in matches if d['document_type'] not in {'dataset_profile'} and not d['document_type'].endswith('_profile')]
    return dict(status='CONTENT_PRESENT_COMPLETENESS_UNVERIFIED' if content else 'PROFILE_ONLY' if matches else 'MISSING',
                chunks=sum(d['chunks'] for d in content), embedded=sum(d['embedded'] for d in content))


def sections(path):
    """Yield exact locator and source text. No page/sample cap or generated prose."""
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        from pypdf import PdfReader
        for page, obj in enumerate(PdfReader(path).pages, 1):
            yield f'page:{page}', obj.extract_text() or '', page
    elif suffix == '.xls':
        import xlrd
        book = xlrd.open_workbook(path)
        for sheet in book.sheets():
            for row in range(sheet.nrows):
                yield f'{sheet.name}!row:{row+1}', ' | '.join(str(v) for v in sheet.row_values(row)), None
    elif suffix == '.xlsx':
        import openpyxl
        book = openpyxl.load_workbook(path, read_only=True, data_only=False)
        for sheet in book:
            for row, values in enumerate(sheet.iter_rows(values_only=True), 1):
                yield f'{sheet.title}!row:{row}', ' | '.join(str(v) if v is not None else '' for v in values), None
        book.close()
    elif suffix in {'.hml','.xml'}:
        root = ET.parse(path).getroot()
        for i, node in enumerate(root.iter()):
            if node.tag.rsplit('}',1)[-1] in {'CHAR','t'} and node.text and node.text.strip():
                yield f'xml-element:{i}:{node.tag}', node.text, None
    elif suffix in {'.hwpx','.docx'}:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if (re.match(r'Contents/section\d+\.xml$',n) if suffix=='.hwpx' else n=='word/document.xml')]
            for name in names:
                tree = ET.fromstring(z.read(name))
                for i, node in enumerate(tree.iter()):
                    if node.tag.rsplit('}',1)[-1] in {'p','P'}:
                        value = ''.join(n.text or '' for n in node.iter() if n.tag.rsplit('}',1)[-1] in {'t','CHAR'})
                        yield f'{name}:paragraph:{i}', value, None
    else:
        raise ValueError('No verified text adapter: '+suffix)


def extract():
    from scripts.build_coastal_knowledge import parts
    manifest = json.loads((OUT/'raw_manifest/raw_source_manifest.json').read_text(encoding='utf-8'))['sources']
    live = json.loads((OUT/'live_snapshot.json').read_text(encoding='utf-8'))
    inventory, seen, chunks = [], set(), []
    cache=OUT/'extracted_v2'
    cache.mkdir(exist_ok=True)
    for item in manifest:
        path = ROOT/'Dataset'/item['relative_path']
        h = item['sha256']
        state = dict(source_file='Dataset/'+item['relative_path'],source_sha256=h,bytes=item['size_bytes'],
                     previous=classify_coverage(h,live['documents']))
        inventory.append(state)
        if h in seen:
            state['extraction']='DUPLICATE_HASH'
            continue
        seen.add(h)
        if state['previous']['status']=='CONTENT_PRESENT_COMPLETENESS_UNVERIFIED':
            state['extraction']='EXISTING_CONTENT_REQUIRES_COVERAGE_REVIEW'
            continue
        if path.suffix.lower() not in {'.pdf','.xls','.xlsx','.hml','.hwpx','.docx'}:
            state['extraction']='TYPE_SPECIFIC_ADAPTER_REQUIRED'
            continue
        cached=cache/(h+'.json')
        if cached.exists():
            prior=json.loads(cached.read_text(encoding='utf-8'))
            state.update(prior['state']);chunks.extend(prior['chunks'])
            continue
        chunk_start=len(chunks)
        state.update(extraction='EXTRACTED',sections=0,empty_sections=[],chunks=0)
        # Group short XML paragraphs / worksheet rows without losing individual locators.
        pending, locators, page = [], [], None
        def flush():
            if not pending:
                return
            for offset, value in parts('\n'.join(pending),size=2200):
                cid=sha(f'{h}:{locators}:{offset}:{value}'.encode())
                meta=dict(source_id='dataset:'+h,document_id='dataset:'+h,source_sha256=h,
                    source_file=state['source_file'],title=path.stem,section='; '.join(locators),page_no=page,
                    document_type='dataset_source_text',language='ko' if re.search('[가-힣]',value) else 'en',source_locators=list(locators),
                    char_offset=offset,edition_status='UNVERIFIED',extraction_method='dataset_pipeline_v1',
                    clearance_level='PUBLIC',extraction_warning='Source text; table layout and edition require review')
                chunks.append(dict(chunk_id=cid,text=value,metadata=meta))
                state['chunks']+=1
            pending.clear(); locators.clear()
        try:
            with path.open('rb') as original:
                if hashlib.file_digest(original,'sha256').hexdigest()!=h:
                    raise ValueError('Source changed after inventory; rebuild manifest')
            for locator,value,pno in sections(path):
                state['sections']+=1
                if not value.strip(' |\n\t'):
                    state['empty_sections'].append(locator)
                    continue
                if pno is not None or sum(map(len,pending))+len(value)>2000:
                    flush()
                page=pno
                pending.append(value);locators.append(locator)
            flush()
        except Exception as exc:
            state['extraction']='PARTIAL_OR_FAILED'
            state['error']=str(exc)
        if state['extraction']=='EXTRACTED':
            cached.write_text(json.dumps({'state':state,'chunks':chunks[chunk_start:]},ensure_ascii=False),encoding='utf-8')
        print(json.dumps(state,ensure_ascii=False),flush=True)
    with (OUT/'chunks.jsonl').open('w',encoding='utf-8') as f:
        for r in chunks:
            f.write(json.dumps(r,ensure_ascii=False)+'\n')
    dump('reconciliation.json',dict(sources=inventory,chunks=len(chunks),status_counts=dict(Counter(s['extraction'] for s in inventory))))


def load():
    from psycopg2.extras import Json,execute_batch
    rows=[json.loads(s) for s in (OUT/'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
    with connect() as conn, conn.cursor() as cur:
        execute_batch(cur,'''INSERT INTO knowledge.document_chunks
          (chunk_id,document_id,document_type,title,section,language,content,source_file,page_no,source_id,source_sha256,metadata)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(chunk_id) DO NOTHING''',
          [(r['chunk_id'],r['metadata']['document_id'],r['metadata']['document_type'],r['metadata']['title'],
            r['metadata']['section'],r['metadata']['language'],r['text'].replace('\x00',''),r['metadata']['source_file'],r['metadata'].get('page_no'),
            r['metadata']['source_id'],r['metadata']['source_sha256'],Json(r['metadata'])) for r in rows])
        cur.execute("""UPDATE knowledge.document_chunks SET language=CASE WHEN content ~ '[가-힣]' THEN 'ko' ELSE 'en' END,
          metadata=metadata || jsonb_build_object('language',CASE WHEN content ~ '[가-힣]' THEN 'ko' ELSE 'en' END)
          WHERE document_type='dataset_source_text'""")
    print(dict(loaded=len(rows)))


def embed():
    """Use DB as resume authority, committing every batch, not a stale progress file."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute('SELECT pg_try_advisory_lock(20261002001)')
        if not cur.fetchone()[0]:
            raise RuntimeError('Dataset embedding worker already active')
        while True:
            cur.execute("SELECT chunk_id,content,source_sha256 FROM knowledge.document_chunks WHERE document_type='dataset_source_text' AND embedding IS NULL ORDER BY chunk_id LIMIT 4")
            rows=cur.fetchall()
            if not rows:
                dump('embedding_progress.json',dict(status='COMPLETED',pending=0,observed_at=time.time()))
                break
            req=urllib.request.Request(os.environ.get('OLLAMA_EMBEDDING_URL','http://host.docker.internal:11434/api/embed'),
                data=json.dumps(dict(model='bge-m3',input=[r[1] for r in rows],options=dict(num_thread=4))).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=600) as response:
                vectors=json.load(response)['embeddings']
            if len(vectors)!=len(rows) or any(len(v)!=1024 or not all(math.isfinite(x) for x in v) for v in vectors):
                raise ValueError('Invalid bge-m3 batch')
            for row,vector in zip(rows,vectors):
                cur.execute('''UPDATE knowledge.document_chunks SET embedding=%s::vector,
                            metadata=metadata || '{"embedding_model":"bge-m3","embedding_dimension":1024,"embedding_status":"COMPLETED"}'::jsonb
                            WHERE chunk_id=%s AND source_sha256=%s AND content=%s''',
                            (json.dumps(vector),row[0],row[2],row[1]))
                if cur.rowcount!=1:
                    raise RuntimeError('Source changed during embedding')
            conn.commit()
            cur.execute("SELECT count(*),count(embedding) FROM knowledge.document_chunks WHERE document_type='dataset_source_text'")
            total,done=cur.fetchone()
            progress=dict(status='RUNNING',total=total,embedded=done,pending=total-done,observed_at=time.time())
            dump('embedding_progress.json',progress)
            print(json.dumps(progress),flush=True)


def graph():
    """Connect actual DB passages to immutable sources and actual source collections."""
    nodes,edges={},[]
    with connect() as conn,conn.cursor() as cur:
        cur.execute('SELECT chunk_id,title,source_file,source_sha256,page_no,section FROM knowledge.document_chunks WHERE source_sha256 ~ %s',('^[0-9a-f]{64}$',))
        for cid,title,path,h,page,section in cur.fetchall():
            sid='dataset:'+h
            provenance=dict(source_file=path,source_sha256=h)
            nodes[sid]=dict(id=sid,node_type='DatasetSource',name=Path(path or '').name,properties={'authority':'source_snapshot_only'},provenance=provenance)
            nodes[cid]=dict(id=cid,node_type='DocumentChunk',name=title,properties={'page_no':page,'section':section},provenance=provenance)
            edges.append(dict(subject_id=cid,predicate='derivedFromSource',object_id=sid,provenance=provenance,authority='retrieval_only'))
        cur.execute('SELECT source_sha256,source_file,count(*) FROM serving.dataset_source_records GROUP BY 1,2')
        for h,path,count in cur.fetchall():
            sid='dataset:'+h; rid='dataset_collection:'+h
            provenance=dict(source_file=path,source_sha256=h)
            nodes[sid]=dict(id=sid,node_type='DatasetSource',name=Path(path).name,properties={'authority':'source_snapshot_only'},provenance=provenance)
            nodes[rid]=dict(id=rid,node_type='DatasetRecordCollection',name=Path(path).stem,
                           properties=dict(relation='serving.dataset_source_records',source_sha256=h,rows=count),provenance=provenance)
            edges.append(dict(subject_id=rid,predicate='derivedFromSource',object_id=sid,provenance=provenance,authority='retrieval_only'))
    for name,rows in [('nodes.jsonl',nodes.values()),('edges.jsonl',edges)]:
        (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    print(dict(nodes=len(nodes),edges=len(edges)))


def audit():
    manifest=json.loads((OUT/'raw_manifest/raw_source_manifest.json').read_text(encoding='utf-8'))['sources']
    live=json.loads((OUT/'live_snapshot.json').read_text(encoding='utf-8'))
    extracted=json.loads((OUT/'reconciliation.json').read_text(encoding='utf-8')) if (OUT/'reconciliation.json').exists() else {'sources':[]}
    extra={r['source_sha256']:r for r in extracted['sources'] if r.get('extraction')!='DUPLICATE_HASH'}
    record_extraction={}
    for name in ['spatial_extraction.json','csv_extraction.json']:
        if (OUT/name).exists():
            for record in json.loads((OUT/name).read_text(encoding='utf-8')):
                if record.get('source_sha256'):
                    record_extraction.setdefault(record['source_sha256'],[]).append(record)
    links=Counter()
    if (OUT/'edges.jsonl').exists():
        for line in (OUT/'edges.jsonl').open(encoding='utf-8'):
            edge=json.loads(line);links[edge['provenance'].get('source_sha256')]+=1
    rows=[]
    for source in manifest:
        h=source['sha256']; coverage=classify_coverage(h,live['documents'])
        records=[s for s in live['spatial'] if s['source_sha256']==h]
        state=extra.get(h,{}).get('extraction','NOT_VERIFIED')
        source_records=record_extraction.get(h,[])
        if source_records:
            state='SOURCE_RECORDS_EXTRACTED' if all(r['status']=='EXTRACTED' for r in source_records) else 'PARTIAL_SOURCE_RECORDS'
        elif records and state in {'TYPE_SPECIFIC_ADAPTER_REQUIRED','NOT_VERIFIED'}:
            state='EXISTING_RECORDS_COMPLETENESS_UNVERIFIED'
        rows.append(dict(source_file='Dataset/'+source['relative_path'],source_sha256=h,
            extraction=state,empty_sections=len(extra.get(h,{}).get('empty_sections',[])),
            embedding_scope='TEXT_PASSAGES; STRUCTURED_RECORDS_USE_SQL',
            content_status=coverage['status'],chunks=coverage['chunks'],embedded=coverage['embedded'],
            spatial_records=sum(r['rows'] for r in records),valid_geometries=sum(r['valid'] for r in records),
            relations=sorted({r['relation'] for r in records}),knowledge_links=links[h],search_status='REQUIRES_QUERY_PROBE'))
    dump('audit.json',dict(observed_at=live['observed_at'],sources=rows))
    lines=['# Dataset 원본별 처리 대조','',
        '동일 SHA-256 복사본은 같은 처리 근거를 공유한다. 파일 요약은 본문 추출로 계산하지 않는다. geometry 유효성은 좌표 출처의 권위·현재성 검증과 다르다.',
        '', '| 원본 | 추출 | 본문/임베딩 | 공간 행/유효 | 지식 연결 |', '|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['source_file']} | {r['extraction']} | {r['chunks']}/{r['embedded']} | {r['spatial_records']}/{r['valid_geometries']} | {r['knowledge_links']} |")
    (OUT/'audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(dict(files=len(rows),unique_hashes=len({r['source_sha256'] for r in rows})))


def indexes():
    with connect() as conn,conn.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
        cur.execute('CREATE INDEX IF NOT EXISTS document_source_content_trgm ON knowledge.document_chunks USING gin(content gin_trgm_ops)')
        cur.execute('CREATE INDEX IF NOT EXISTS document_source_title_trgm ON knowledge.document_chunks USING gin(title gin_trgm_ops)')
        cur.execute('CREATE INDEX IF NOT EXISTS dataset_records_filename_trgm ON serving.dataset_source_records USING gin(source_file gin_trgm_ops)')
        cur.execute("CREATE INDEX IF NOT EXISTS dataset_records_properties_trgm ON serving.dataset_source_records USING gin((properties::text) gin_trgm_ops) WHERE source_member<>'CSV'")
        cur.execute('ANALYZE knowledge.document_chunks')
        cur.execute('ANALYZE serving.dataset_source_records')
    print('Dataset document and record search indexes ready')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['snapshot','extract','load','embed','graph','audit','indexes'])
    globals()[parser.parse_args().action]()
