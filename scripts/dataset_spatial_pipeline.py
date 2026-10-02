"""Lossless source-record staging for missing static SHP archives.

No registry promotion, inferred coordinates, geometry repair or scale deduplication.
Host extracts raw attributes/geometry; container transforms and validates in PostGIS.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from scripts.dataset_pipeline import ROOT, OUT, dump, sha, connect


def strict_srid(wkt):
    value=wkt.lower()
    params={k:float(v) for k,v in re.findall(r'parameter\["([a-z_]+)",\s*([-\d.]+)\]',value)}
    expected={'false_easting':1000000,'false_northing':2000000,'central_meridian':127.5,'latitude_of_origin':38,'scale_factor':0.9996}
    if ('korea' in value or 'kgd2002' in value) and 'transverse_mercator' in value and all(params.get(k)==v for k,v in expected.items()) and '298.257222101' in value:
        return 5179
    if value.startswith('geogcs[') and ('wgs_1984' in value or 'wgs 84' in value):
        return 4326
    raise ValueError('Unverified CRS; spatial ingest blocked')


def extract(retry=False):
    import shapefile
    manifest=json.loads((OUT/'raw_manifest/raw_source_manifest.json').read_text(encoding='utf-8'))['sources']
    live=json.loads((OUT/'live_snapshot.json').read_text(encoding='utf-8'))
    existing={r['source_sha256'] for r in live['spatial']}
    seen=set(); reports=[]
    if retry:
        previous=json.loads((OUT/'spatial_extraction.json').read_text(encoding='utf-8'))
        failed={r['source_sha256'] for r in previous if r['status']!='EXTRACTED'}
        manifest=[s for s in manifest if s['sha256'] in failed]
        reports=[r for r in previous if r['source_sha256'] not in failed]
    with (OUT/'spatial_records.jsonl').open('a' if retry else 'w',encoding='utf-8') as stream:
        for source in manifest:
            path=ROOT/'Dataset'/source['relative_path']
            if path.parent!=ROOT/'Dataset' or path.suffix.lower()!='.zip' or path.name.startswith(('AIS','V-PASS','download','소형선항만')):
                continue
            h=source['sha256']
            if h in seen or h in existing:
                continue
            seen.add(h)
            with path.open('rb') as original:
                if hashlib.file_digest(original,'sha256').hexdigest()!=h:
                    raise ValueError('Archive changed after inventory')
            with zipfile.ZipFile(path) as archive:
                lookup={n.lower():n for n in archive.namelist()}
                for member in sorted(n for n in archive.namelist() if n.lower().endswith('.shp')):
                    report=dict(source_file='Dataset/'+source['relative_path'],source_sha256=h,member=member,rows=0,errors=[])
                    reports.append(report)
                    stem=member[:-4]
                    def read(ext):
                        return archive.read(lookup[(stem+ext).lower()])
                    try:
                        srid=strict_srid(read('.prj').decode('utf-8-sig'))
                        cpg=read('.cpg').decode().strip() if (stem+'.cpg').lower() in lookup else None
                        encoding={'UTF-8':'utf-8','UTF_8':'utf-8','949':'cp949','65001':'utf-8'}.get(cpg,cpg)
                        raw_dbf=read('.dbf')
                        if not encoding:
                            # Decode all DBF bytes strictly; preserve failure rather than replace text.
                            for candidate in ('utf-8','cp949'):
                                try:
                                    reader=shapefile.Reader(shp=io.BytesIO(read('.shp')),shx=io.BytesIO(read('.shx')),dbf=io.BytesIO(raw_dbf),encoding=candidate)
                                    list(reader.iterRecords())
                                    encoding=candidate
                                    break
                                except (UnicodeError,shapefile.ShapefileException):
                                    continue
                        if not encoding:
                            raise ValueError('DBF encoding unresolved')
                        reader=shapefile.Reader(shp=io.BytesIO(read('.shp')),shx=io.BytesIO(read('.shx')),dbf=io.BytesIO(raw_dbf),encoding=encoding)
                        report.update(expected_rows=len(reader),source_srid=srid,encoding=encoding,fields=reader.fields[1:])
                        for i,record in enumerate(reader.iterShapeRecords()):
                            sid='dataset_record:'+sha(f'{h}:{member}:{i}'.encode())
                            props=record.record.as_dict()
                            geometry=record.shape.__geo_interface__ if record.shape.shapeType else None
                            item=dict(source_id=sid,source_file=report['source_file'],source_sha256=h,member=member,row_index=i,
                                      source_srid=srid,properties=props,geometry=geometry,encoding=encoding)
                            stream.write(json.dumps(item,ensure_ascii=False,default=str)+'\n')
                            report['rows']+=1
                        report['status']='EXTRACTED'
                    except Exception as exc:
                        report.update(status='PARTIAL_OR_FAILED',error=str(exc))
                    print(json.dumps(report,ensure_ascii=False),flush=True)
    dump('spatial_extraction.json',reports)


def load(records_file=None):
    from psycopg2.extras import Json, execute_values
    reports=json.loads((OUT/'spatial_extraction.json').read_text(encoding='utf-8'))
    complete={(r['source_sha256'],r['member']) for r in reports if r['status']=='EXTRACTED' and r['rows']==r['expected_rows']}
    with connect() as conn, conn.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS serving.dataset_source_records(
            source_id text PRIMARY KEY, source_sha256 text NOT NULL, source_file text NOT NULL,
            source_member text NOT NULL, row_index integer NOT NULL, properties jsonb NOT NULL,
            provenance jsonb NOT NULL, geom geometry(Geometry,4326), geometry_valid boolean NOT NULL DEFAULT false)''')
        cur.execute('SELECT source_id FROM serving.dataset_source_records')
        existing={row[0] for row in cur.fetchall()}
        def persist(batch):
            if not batch:return
            execute_values(cur,'''INSERT INTO serving.dataset_source_records
              (source_id,source_sha256,source_file,source_member,row_index,properties,provenance,geom)
              VALUES %s ON CONFLICT(source_id) DO NOTHING''',batch,
              template='(%s,%s,%s,%s,%s,%s,%s,ST_Force2D(ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s),%s),4326)))')
            conn.commit()
        batch=[]
        for line in Path(records_file or OUT/'spatial_records.jsonl').open(encoding='utf-8'):
            r=json.loads(line)
            if r['source_id'] in existing:continue
            if (r['source_sha256'],r['member']) not in complete:continue
            batch.append((r['source_id'],r['source_sha256'],r['source_file'],r['member'],r['row_index'],Json(r['properties']),
                          Json({k:v for k,v in r.items() if k not in {'geometry','properties'}}),json.dumps(r['geometry']) if r['geometry'] else None,r['source_srid']))
            if len(batch)>=500:persist(batch);batch=[]
        persist(batch)
        cur.execute('''UPDATE serving.dataset_source_records SET geometry_valid=coalesce(
          NOT ST_IsEmpty(geom) AND ST_IsValid(geom) AND ST_CoveredBy(geom,ST_MakeEnvelope(120,30,140,45,4326)),false)''')
        cur.execute('CREATE INDEX IF NOT EXISTS dataset_source_records_geom ON serving.dataset_source_records USING gist(geom) WHERE geometry_valid')
        cur.execute('CREATE INDEX IF NOT EXISTS dataset_source_records_hash ON serving.dataset_source_records(source_sha256)')
        cur.execute('SELECT source_file,count(*),count(*) FILTER(WHERE geometry_valid) FROM serving.dataset_source_records GROUP BY 1 ORDER BY 1')
        dump('spatial_loaded.json',[dict(source_file=r[0],rows=r[1],valid=r[2]) for r in cur.fetchall()])
    print('Loaded source records; geometry_valid=false records excluded from spatial use')


def csv_records():
    """Preserve all CSV rows; never infer a coordinate system from column names."""
    from scripts.build_dataset_embedding_coverage import decode_best
    manifest=json.loads((OUT/'raw_manifest/raw_source_manifest.json').read_text(encoding='utf-8'))['sources']
    seen=set(); reports=[]
    with (OUT/'csv_records.jsonl').open('w',encoding='utf-8') as stream:
        for source in manifest:
            path=ROOT/'Dataset'/source['relative_path'];h=source['sha256']
            if path.suffix.lower()!='.csv' or h in seen:continue
            seen.add(h)
            raw=path.read_bytes()
            if sha(raw)!=h:raise ValueError('CSV changed after inventory')
            content,encoding=decode_best(raw)
            if 'replace' in encoding:
                reports.append(dict(source_file=source['relative_path'],status='ENCODING_UNRESOLVED'));continue
            reader=csv.reader(io.StringIO(content));header=next(reader,[]);count=0
            for i,values in enumerate(reader):
                record=dict(source_id='dataset_csv:'+sha(f'{h}:{i}'.encode()),source_sha256=h,source_file='Dataset/'+source['relative_path'],
                    source_member='CSV',row_index=i,properties={'header':header,'values':values},provenance={'source_sha256':h,
                    'source_file':'Dataset/'+source['relative_path'],'row_number':i+2,'encoding':encoding,'geometry_status':'NOT_INFERRED'})
                stream.write(json.dumps(record,ensure_ascii=False)+'\n');count+=1
            reports.append(dict(source_file='Dataset/'+source['relative_path'],source_sha256=h,status='EXTRACTED',rows=count,encoding=encoding))
    dump('csv_extraction.json',reports)


def load_csv(records_file=None):
    from psycopg2.extras import Json,execute_values
    with connect() as conn,conn.cursor() as cur:
        cur.execute("SELECT source_sha256,min(row_index),max(row_index),count(*) FROM serving.dataset_source_records WHERE source_member='CSV' GROUP BY 1")
        resume={h:maximum for h,minimum,maximum,count in cur.fetchall() if minimum==0 and maximum+1==count}
        batch=[]
        def persist():
            execute_values(cur,'''INSERT INTO serving.dataset_source_records
                (source_id,source_sha256,source_file,source_member,row_index,properties,provenance)
                VALUES %s ON CONFLICT(source_id) DO NOTHING''',batch)
            conn.commit();batch.clear()
        for line in Path(records_file or OUT/'csv_records.jsonl').open(encoding='utf-8'):
            r=json.loads(line)
            if r['row_index']<=resume.get(r['source_sha256'],-1):continue
            batch.append((r['source_id'],r['source_sha256'],r['source_file'],r['source_member'],r['row_index'],Json(r['properties']),Json(r['provenance'])))
            if len(batch)>=1000:persist()
        if batch:persist()
    print('CSV source rows loaded; coordinates not inferred')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['extract','load','csv_records','load_csv'])
    parser.add_argument('--retry',action='store_true')
    parser.add_argument('--records-file')
    args=parser.parse_args()
    if args.action=='extract':extract(args.retry)
    elif args.action=='load':load(args.records_file)
    elif args.action=='load_csv':load_csv(args.records_file)
    else:globals()[args.action]()
