"""Extract coastal reference PDFs and small-harbour attributes with immutable lineage.

Run extraction on the Dataset host; load the resulting artifacts with --load in
the backend. HWP originals are inventoried as alternative representations, never
silently counted as extracted. No inferred entrance coordinates are generated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/coastal_knowledge'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


def parts(text, size=1100):
    text = text.replace('\x00', '')
    text = re.sub(r'[ \t]+', ' ', text).strip()
    for start in range(0, len(text), size - 100):
        value = text[start:start + size].strip()
        if value:
            yield start, value


def extract():
    from pypdf import PdfReader
    import shapefile
    OUT.mkdir(parents=True, exist_ok=True)
    inventory, chunks, ports = [], [], []
    for path in sorted((ROOT / 'Dataset/항로서지').rglob('*')):
        if not path.is_file():
            continue
        source = path.relative_to(ROOT).as_posix()
        sha = digest(path.read_bytes())
        item = dict(source_file=source, source_sha256=sha, bytes=path.stat().st_size)
        inventory.append(item)
        if path.suffix.lower() != '.pdf':
            item['status'] = 'ALTERNATIVE_FORMAT_NOT_EXTRACTED'
            continue
        sid = 'coastal_pdf:' + sha
        reader = PdfReader(path)
        item.update(status='EXTRACTED', pages=len(reader.pages), empty_pages=[], chunks=0)
        for page_no, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            if not text.strip():
                item['empty_pages'].append(page_no)
            for offset, value in parts(text):
                meta = dict(document_id=sid, source_id=sid, source_file=source,
                            source_path=source, source_sha256=sha, title=path.stem,
                            page_no=page_no, section=f'PDF page {page_no}', char_offset=offset,
                            document_type='coastal_pilot', language='ko' if '국문' in source or '_KOR' in source else 'en',
                            version=None, edition_status='UNVERIFIED', clearance_level='PUBLIC',
                            extraction_method='pypdf', extraction_warning='page text; tables and charts require visual review')
                chunks.append(dict(chunk_id=digest(f'{sid}:{page_no}:{offset}:{value}'.encode()), text=value, metadata=meta))
                item['chunks'] += 1
        print(json.dumps(item, ensure_ascii=False), flush=True)
    shp = ROOT / 'Dataset/소형선항만 안내정보/TB_SAILER.shp'
    files = [shp.with_suffix(ext) for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']]
    hashes = {p.name: digest(p.read_bytes()) for p in files}
    sha = digest(json.dumps(hashes, sort_keys=True).encode())
    prj = shp.with_suffix('.prj').read_text()
    if not all(v in prj for v in ['Korea_2000', '127.5', '1000000', '2000000']):
        raise ValueError('Unrecognized harbour CRS; do not default to WGS84')
    reader = shapefile.Reader(str(shp), encoding='utf-8', encodingErrors='replace')
    labels = {'INTRODU':'항만 소개','VOYAGE_INF':'항해 정보','FLT_STTUS':'시설 현황',
              'TRAFFIC_IN':'교통 정보','SEA_WETHER':'해상 기상','SUPPLY_REP':'보급 수리','EBBF_INFO':'조석 정보','TOUR_INFO':'주변 안내'}
    for i, shape_record in enumerate(reader.iterShapeRecords()):
        attrs = shape_record.record.as_dict()
        sid = f'small_harbour:{sha}:{i}'
        name = str(attrs.get('NAME') or '').strip()
        geometry = shape_record.shape.__geo_interface__
        if geometry['type'] != 'Point':
            raise ValueError('Expected source harbour point')
        warnings = [key for key, value in attrs.items() if '\ufffd' in str(value)]
        port = dict(source_id=sid, source_sha256=sha, name=name, properties=attrs,
                    geometry=geometry, source_srid=5179, source_file=shp.relative_to(ROOT).as_posix(),
                    component_hashes=hashes, damaged_fields=warnings,
                    geometry_role='harbour_reference_point_not_entrance')
        ports.append(port)
        for field, label in labels.items():
            value = str(attrs.get(field) or '').strip()
            if not value:
                continue
            # DBF character fields are byte-limited; preserve and disclose source truncation.
            value = f'{name} / {attrs.get("ADR_KNM", "")} / {label}\n{value}'
            meta = dict(document_id=sid, source_id=sid, source_sha256=sha,
                        source_file=port['source_file'], title=f'{name} 소형선항만 안내',
                        section=field, document_type='small_harbour_guide', language='ko',
                        version=str(attrs.get('ORIYR') or ''), publisher=attrs.get('ORIORG'),
                        harbour_name=name, row_index=i, component_hashes=hashes,
                        extraction_warning='DBF 254-byte fields may be truncated',
                        damaged_field=field in warnings, clearance_level='PUBLIC')
            chunks.append(dict(chunk_id=digest(f'{sid}:{field}'.encode()), text=value, metadata=meta))
    inventory.append(dict(source_file=shp.relative_to(ROOT).as_posix(), source_sha256=sha,
                          status='EXTRACTED', records=len(ports), source_srid=5179,
                          damaged_records=sum(bool(p['damaged_fields']) for p in ports)))
    write_rows(OUT / 'chunks.jsonl', chunks)
    write_rows(OUT / 'ports.jsonl', ports)
    build_graph(chunks, ports)
    (OUT / 'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'chunks={len(chunks)} ports={len(ports)}', flush=True)


def build_graph(chunks, ports):
    nodes, edges = {}, []
    port_ids = {p['source_id'] for p in ports}
    for port in ports:
        nodes[port['source_id']] = dict(id=port['source_id'],node_type='HarbourGuideRecord',name=port['name'],
            properties={'relation':'serving.small_harbour_guide','geometry_role':port['geometry_role']},
            provenance={'source_file':port['source_file'],'source_sha256':port['source_sha256']})
    names = {p['name'] for p in ports if p['name']}
    # Mention relations preserve spelling; they are not entity identity or geometry claims.
    for row in chunks:
        if row['metadata']['document_type'] == 'coastal_pilot':
            names.update(re.findall(r'(?<![가-힣])([가-힣]{2,12}항)(?=[\s(（,·.은의에을]|$)', row['text']))
    for name in sorted(names):
        nid = 'coastal_name:' + digest(name.encode())[:24]
        nodes[nid] = dict(id=nid, node_type='PlaceNameMention', name=name,
                          properties={'authority':'lexical_mention_only'},
                          provenance={'source_file':'outputs/coastal_knowledge/chunks.jsonl','method':'source text mention'})
    for row in chunks:
        cid, meta = row['chunk_id'], row['metadata']
        nodes[cid] = dict(id=cid, node_type='DocumentChunk', name=meta['title'], properties=meta,
                          provenance={'source_sha256':meta['source_sha256'],'source_file':meta['source_file']})
        if meta['source_id'] in port_ids:
            edges.append(dict(subject_id=cid,predicate='describesHarbourRecord',object_id=meta['source_id'],
                              provenance={'chunk_id':cid,'source_sha256':meta['source_sha256'],'section':meta['section']},
                              authority='retrieval_only'))
        for name in names:
            if name in row['text']:
                edges.append(dict(subject_id=cid,predicate='mentionsPlaceName',
                                  object_id='coastal_name:' + digest(name.encode())[:24],
                                  provenance={'chunk_id':cid,'source_sha256':meta['source_sha256'],
                                              'page_no':meta.get('page_no'),'section':meta.get('section')},
                                  authority='retrieval_only'))
    write_rows(OUT / 'nodes.jsonl', nodes.values())
    write_rows(OUT / 'edges.jsonl', edges)


def load():
    import psycopg2
    from psycopg2.extras import Json, execute_batch
    ports = [json.loads(s) for s in (OUT / 'ports.jsonl').read_text(encoding='utf-8').splitlines()]
    with psycopg2.connect(os.environ['S101_DB_URL']) as conn, conn.cursor() as cur:
        cur.execute('CREATE SCHEMA IF NOT EXISTS serving')
        cur.execute('''CREATE TABLE IF NOT EXISTS serving.small_harbour_guide (
          source_id text PRIMARY KEY, name text NOT NULL, properties jsonb NOT NULL,
          provenance jsonb NOT NULL, geom geometry(Point,4326) NOT NULL)''')
        execute_batch(cur, '''INSERT INTO serving.small_harbour_guide VALUES
          (%s,%s,%s,%s,ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s),5179),4326))
          ON CONFLICT(source_id) DO UPDATE SET name=excluded.name, properties=excluded.properties,
          provenance=excluded.provenance,geom=excluded.geom''',
          [(p['source_id'],p['name'],Json(p['properties']),Json({k:v for k,v in p.items() if k not in ('properties','geometry')}),json.dumps(p['geometry'])) for p in ports])
        cur.execute('CREATE INDEX IF NOT EXISTS small_harbour_guide_geom ON serving.small_harbour_guide USING gist(geom)')
        cur.execute('''SELECT count(*),count(*) FILTER(WHERE NOT ST_IsValid(geom) OR
          ST_X(geom) NOT BETWEEN 120 AND 140 OR ST_Y(geom) NOT BETWEEN 30 AND 45)
          FROM serving.small_harbour_guide''')
        total, invalid = cur.fetchone()
        if invalid:
            raise ValueError(f'invalid harbour geometry: {invalid}')
        print(dict(spatial_rows=total, invalid=invalid))
        chunks = [json.loads(s) for s in (OUT / 'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
        execute_batch(cur, '''INSERT INTO knowledge.document_chunks
          (chunk_id,document_id,document_type,title,section,language,content,source_file,page_no,
           source_id,source_sha256,metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(chunk_id) DO NOTHING''',
          [(r['chunk_id'],r['metadata']['document_id'],r['metadata']['document_type'],r['metadata']['title'],
            r['metadata']['section'],r['metadata']['language'],r['text'],r['metadata']['source_file'],
            r['metadata'].get('page_no'),r['metadata']['source_id'],r['metadata']['source_sha256'],
            Json({**r['metadata'],'embedding_status':'PENDING'})) for r in chunks])
        print(dict(text_chunks=len(chunks),embedding_status='per-row; NULL means pending'))


def embed():
    """Resume real embeddings; commit each batch so progress is queryable and durable."""
    import time
    import urllib.request
    import psycopg2
    from psycopg2.extras import Json
    from scripts.generate_rag_embeddings import load_existing
    rows = [json.loads(s) for s in (OUT / 'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
    output = OUT / 'embeddings.jsonl'
    existing = load_existing(output)
    current_ids = {r['chunk_id'] for r in rows}
    existing = {key:value for key,value in existing.items() if key in current_ids}
    endpoint = os.environ.get('OLLAMA_EMBEDDING_URL','http://host.docker.internal:11434/api/embed')
    started = time.time()
    with psycopg2.connect(os.environ['S101_DB_URL']) as conn, output.open('a',encoding='utf-8') as stream:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_try_advisory_lock(202610018440)')
            if not cur.fetchone()[0]:
                raise RuntimeError('A coastal embedding worker is already running')
        def persist(batch):
            with conn.cursor() as cur:
                for row in batch:
                    vector = row['embedding']
                    if len(vector) != 1024 or not all(__import__('math').isfinite(x) for x in vector):
                        raise ValueError('Invalid bge-m3 embedding')
                    cur.execute('''UPDATE knowledge.document_chunks SET embedding=%s::vector,
                        metadata=metadata || %s::jsonb WHERE chunk_id=%s AND source_sha256=%s''',
                        (json.dumps(vector),Json({'embedding_status':'COMPLETED','embedding_model':'bge-m3','embedding_dimension':1024}),
                         row['chunk_id'],row['source_sha256']))
                    if cur.rowcount != 1:
                        raise RuntimeError('Embedding source row/hash changed; reload verified source first')
            conn.commit()
        persist(list(existing.values()))
        pending = [r for r in rows if r['chunk_id'] not in existing]
        # Prioritize Korean explanatory passages and harbour attributes for the UI.
        pending.sort(key=lambda r: (r['metadata'].get('language')!='ko',
                                   not any(t in r['text'] for t in ['부산항','다대포항','울릉','해운대']),
                                   r['metadata']['document_type']!='small_harbour_guide'))
        for offset in range(0,len(pending),2):
            batch = pending[offset:offset+2]
            req = urllib.request.Request(endpoint,data=json.dumps({'model':'bge-m3','input':[r['text'] for r in batch],
                  'options':{'num_thread':4}}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=600) as response:
                vectors = json.load(response)['embeddings']
            if len(vectors) != len(batch):
                raise ValueError('Embedding batch cardinality mismatch')
            generated = []
            for row,vector in zip(batch,vectors):
                record = dict(chunk_id=row['chunk_id'],content=row['text'],metadata=row['metadata'],embedding=vector,
                              source_sha256=row['metadata']['source_sha256'],model='bge-m3',dimension=len(vector))
                generated.append(record)
                stream.write(json.dumps(record,ensure_ascii=False)+'\n')
            stream.flush()
            persist(generated)
            count = len(existing)+offset+len(batch)
            progress = dict(total=len(rows),embedded=count,pending=len(rows)-count,elapsed_seconds=round(time.time()-started,2),
                            status='COMPLETED' if count==len(rows) else 'RUNNING')
            temp = OUT / 'embedding_progress.tmp'
            temp.write_text(json.dumps(progress),encoding='utf-8')
            temp.replace(OUT / 'embedding_progress.json')
            print(json.dumps(progress),flush=True)


def extract_hwp():
    import olefile
    chunks = [json.loads(s) for s in (OUT / 'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in chunks:
        if '\x00' in row['text']:
            row['text'] = row['text'].replace('\x00', '')
            row['chunk_id'] = digest((row['chunk_id'] + row['text']).encode())
            row['metadata']['removed_nul_characters'] = True
    inventory = json.loads((OUT / 'inventory.json').read_text(encoding='utf-8'))
    for item in inventory:
        path = ROOT / item['source_file']
        if path.suffix.lower() != '.hwp':
            continue
        sid = 'coastal_hwp:' + item['source_sha256']
        chunks = [c for c in chunks if c['metadata']['source_id'] != sid]
        count = 0
        with olefile.OleFileIO(path) as doc:
            header = doc.openstream('FileHeader').read()
            flags = struct.unpack_from('<I', header, 36)[0]
            if flags & 2:
                item['status'] = 'ENCRYPTED_NOT_EXTRACTED'
                continue
            sections = sorted(p for p in doc.listdir() if p[0] == 'BodyText' and p[-1].startswith('Section'))
            for section in sections:
                raw = doc.openstream(section).read()
                if flags & 1:
                    raw = zlib.decompress(raw, -15)
                offset, paragraphs = 0, []
                while offset + 4 <= len(raw):
                    record = struct.unpack_from('<I', raw, offset)[0]
                    offset += 4
                    tag, size = record & 0x3ff, record >> 20
                    if size == 0xfff:
                        size = struct.unpack_from('<I', raw, offset)[0]
                        offset += 4
                    payload = raw[offset:offset + size]
                    offset += size
                    if tag == 67:
                        # HWP inline/extended controls occupy 8 UTF-16 code units.
                        units = struct.unpack('<' + 'H' * (len(payload)//2), payload[:len(payload)//2*2])
                        cleaned, index = [], 0
                        extended = {1,2,3,4,5,6,7,8,9,11,12,14,15,16,17,18,19,20,21,22,23}
                        while index < len(units):
                            code = units[index]
                            if code in extended:
                                cleaned.append(' ')
                                index += 8
                            else:
                                cleaned.append(chr(code) if code >= 32 else '\n' if code in {10,13} else ' ')
                                index += 1
                        paragraphs.append(''.join(cleaned).encode('utf-16-le', errors='surrogatepass').decode('utf-16-le', errors='replace'))
                for start, value in parts('\n'.join(paragraphs)):
                    meta = dict(source_id=sid,document_id=sid,source_file=item['source_file'],source_sha256=item['source_sha256'],
                                title=path.stem,section='/'.join(section),char_offset=start,document_type='coastal_pilot',
                                language='ko' if '국문' in str(path) else 'en',version=None,edition_status='UNVERIFIED',
                                extraction_method='hwp5_bodytext',extraction_warning='HWP section locator; page and table layout not reconstructed',
                                clearance_level='PUBLIC')
                    chunks.append(dict(chunk_id=digest(f'{sid}:{section}:{start}:{value}'.encode()),text=value,metadata=meta))
                    count += 1
        item.update(status='EXTRACTED', chunks=count, locator='HWP BodyText section + character offset')
    # Deduplicate identical passages while retaining every source locator.
    unique = {}
    for row in chunks:
        key = digest(re.sub(r'\s+', '', row['text']).encode())
        if key in unique:
            unique[key]['metadata'].setdefault('alternate_source_locators', []).append(row['metadata'])
        else:
            unique[key] = row
    chunks = list(unique.values())
    write_rows(OUT / 'chunks.jsonl',chunks)
    (OUT / 'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    ports = [json.loads(s) for s in (OUT / 'ports.jsonl').read_text(encoding='utf-8').splitlines()]
    build_graph(chunks, ports)
    print(dict(chunks=len(chunks),hwp_files=sum(i['source_file'].endswith('.hwp') and i['status']=='EXTRACTED' for i in inventory)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', action='store_true')
    parser.add_argument('--hwp', action='store_true')
    parser.add_argument('--embed', action='store_true')
    args = parser.parse_args()
    load() if args.load else embed() if args.embed else extract_hwp() if args.hwp else extract()
