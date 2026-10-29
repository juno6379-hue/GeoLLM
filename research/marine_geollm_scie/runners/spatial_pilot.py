"""Frozen real-data component pilot. Never imports research into production.

Source is read only. COPY preserves source rows/IDs; a separate disposable Docker
database serves the production radius executor. SQL consistency is NOT expert gold.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import quote, urlsplit

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
CONTAINER = 'marine-scie-pilot-db'
PORT = 55439
BBOX = [128.9, 34.9, 129.3, 35.3]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def snapshot(output):
    """Export a bounded subset with transaction identity; fail rather than overwrite."""
    output.mkdir(parents=True, exist_ok=True)
    if (output/'source_rows.csv').exists():
        raise FileExistsError('Snapshot already exists; use a new output directory')
    source = os.environ.get('SCIE_SOURCE_DSN')
    if not source:
        inspected=json.loads(subprocess.check_output(['docker','inspect','an_geollm_postgis'],text=True))[0]
        env=dict(item.split('=',1) for item in inspected['Config']['Env'] if '=' in item)
        source='postgresql://'+quote(env.get('POSTGRES_USER','postgres'),safe='')+':'+quote(env['POSTGRES_PASSWORD'],safe='')+'@127.0.0.1:5433/gbhd_s101'
    with psycopg2.connect(source, connect_timeout=5) as conn:
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute("SELECT a.attname, format_type(a.atttypid,a.atttypmod) FROM pg_attribute a WHERE a.attrelid='projection.s101_feature_current'::regclass AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum")
            columns = cur.fetchall()
            cur.execute('SELECT txid_current_snapshot()::text, transaction_timestamp()::text, version()')
            tx, timestamp, version = cur.fetchone()
            query = cur.mogrify('SELECT * FROM projection.s101_feature_current WHERE geometry && ST_MakeEnvelope(%s,%s,%s,%s,4326) AND ST_IsValid(geometry) ORDER BY feature_instance_id', BBOX).decode()
            with (output/'source_rows.csv').open('w',encoding='utf-8',newline='') as stream:
                cur.copy_expert('COPY ('+query+') TO STDOUT WITH CSV HEADER',stream)
    manifest = {'source_relation':'projection.s101_feature_current','source_database':'gbhd_s101',
                'source_transaction':tx,'captured_at':timestamp,'postgres_version':version,
                'bbox_epsg4326':BBOX,'selection_sql':query,'columns':columns,
                'source_sha256':hashlib.sha256((output/'source_rows.csv').read_bytes()).hexdigest(),
                'scope':'bounded valid-geometry source subset; not full production database',
                'gold_status':'DRAFT; no expert approval'}
    write(output/'snapshot_manifest.json',manifest)
    return manifest


def load_snapshot(output, manifest):
    # Fixed research-only identity: existing containers are never reused or removed.
    dsn=os.environ.get('SCIE_TARGET_DSN')
    if dsn and urlsplit(dsn).path != '/scie_pilot':
        raise ValueError('Target must be the isolated scie_pilot database')
    if not dsn:
        subprocess.run(['docker','run','-d','--name',CONTAINER,'--label','marine.scie.research=true',
                    '-p',f'127.0.0.1:{PORT}:5432','-e','POSTGRES_PASSWORD=scie_local_pilot',
                    '-e','POSTGRES_DB=scie_pilot','an-geollm-postgis:16-3.4-pgvector'],check=True,capture_output=True)
        dsn=f'postgresql://postgres:scie_local_pilot@127.0.0.1:{PORT}/scie_pilot'
    for attempt in range(30):
        try:
            conn=psycopg2.connect(dsn,connect_timeout=2)
            break
        except psycopg2.OperationalError:
            time.sleep(1)
    else:
        raise RuntimeError('Research PostGIS startup failed')
    with conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS postgis; CREATE SCHEMA projection')
            definitions=sql.SQL(',').join(sql.SQL('{} {}').format(sql.Identifier(name),sql.SQL(dtype)) for name,dtype in manifest['columns'])
            cur.execute(sql.SQL('CREATE TABLE projection.s101_feature_current ({})').format(definitions))
            with (output/'source_rows.csv').open(encoding='utf-8',newline='') as stream:
                cur.copy_expert('COPY projection.s101_feature_current FROM STDIN WITH CSV HEADER',stream)
            cur.execute('CREATE INDEX ON projection.s101_feature_current USING gist(geometry); CREATE VIEW projection.s101_feature_valid AS SELECT * FROM projection.s101_feature_current; ANALYZE projection.s101_feature_current')
            cur.execute('SELECT COUNT(*) FROM projection.s101_feature_current')
            manifest['subset_rows']=cur.fetchone()[0]
            cur.execute("SELECT feature_instance_id, ST_AsText(ST_PointOnSurface(geometry)) FROM projection.s101_feature_current WHERE feature_type_name='Wreck' AND ST_Within(geometry,ST_MakeEnvelope(129.0,35.0,129.2,35.2,4326)) ORDER BY feature_instance_id LIMIT 1")
            anchor=cur.fetchone()
            if not anchor: raise RuntimeError('No source-backed test anchor within inner bbox')
            manifest['test_anchor']={'feature_instance_id':anchor[0],'geometry':anchor[1],'meaning':'experimental point on actual source Wreck; not a named harbour reference'}
    conn.close()
    write(output/'snapshot_manifest.json',manifest)
    return dsn


def run(output, reuse_snapshot=False):
    if reuse_snapshot:
        manifest=json.loads((output/'snapshot_manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256((output/'source_rows.csv').read_bytes()).hexdigest()!=manifest['source_sha256']:
            raise ValueError('Frozen snapshot digest mismatch')
        dsn=os.environ['SCIE_TARGET_DSN']
        if urlsplit(dsn).path != '/scie_pilot':
            raise ValueError('Target must be the isolated scie_pilot database')
    else:
        manifest=snapshot(output)
        dsn=load_snapshot(output,manifest)
    # Process-local environment only. Explicit coordinates avoid gazetteer/network calls.
    os.environ['S101_DB_URL']=dsn+'?options=-c%20default_transaction_read_only%3Don'
    os.environ['POSTGIS_URL']=os.environ['S101_DB_URL']
    from services.orchestrator.s101_radius_execution import execute_radius_request
    from shapely import wkt
    from shapely.geometry import Point
    specs=[('500m','지정 위치 500m 이내 침선을 찾아줘',500),
           ('half_km','지정 위치 0.5km 이내 침선을 찾아줘',500),
           ('2km','지정 위치 2km 이내 위험객체를 찾아줘',2000),
           ('empty_probe','지정 위치 0.1m 이내 침선을 찾아줘',0.1),
           ('zero','지정 위치 0m 이내 침선을 찾아줘',0),
           ('over_limit','지정 위치 50001m 이내 침선을 찾아줘',50001)]
    cases=[{'case_id':'spatial_'+name,'query':query,'category':'Q4' if name!='2km' else 'Q3',
            'annotation_status':'DRAFT','expected_behavior':'EXECUTE' if 0<radius<=50000 else 'BLOCK',
            'scope':'real-data radius component; explicit experimental point, no end-to-end intent routing',
            'spatial_context':{'geometry':manifest['test_anchor']['geometry'],'crs':'EPSG:4326'}} for name,query,radius in specs]
    anchor=wkt.loads(manifest['test_anchor']['geometry'])
    for case in cases:
        if case['case_id']=='spatial_empty_probe':
            case['spatial_context']['geometry']=Point(anchor.x+0.0001,anchor.y+0.0001).wkt
            case['reference_provenance']='deterministic +0.0001 degree x/y offset from source anchor; experimental coordinate, not a place assertion'
    (output/'spatial_cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
    with (output/'spatial_rows.jsonl').open('x',encoding='utf-8') as stream:
        for case,(_,_,radius) in zip(cases,specs):
            for repeat in range(3):
                start=time.perf_counter()
                result=execute_radius_request({'task_id':f"{case['case_id']}_{repeat}",'query':case['query'],'user_id':'research_pilot','spatial_context':case['spatial_context']})
                elapsed=(time.perf_counter()-start)*1000
                qec=(result.get('orchestrator_v2') or {}).get('query_execution_context')
                row={'case_id':case['case_id'],'method':'P_radius_component','repeat':repeat,'status':result.get('status'),
                     'latency_ms':elapsed,'full_qec':qec,'final_result':result,'diagnostic_only':True,
                     'execution_success':result.get('status') in ('SUCCESS','COMPLETED'),'semantic_correct':None,'plan_valid':None,
                     'spatial_correct':None,'evidence_correct':None,'input_tokens':None,'output_tokens':None,
                     'review_status':'DRAFT','snapshot_sha256':manifest['source_sha256']}
                # Independent unindexed-distance SQL check, operational consistency only.
                if qec and 0<radius<=50000 and result.get('status') in ('SUCCESS','COMPLETED'):
                    with psycopg2.connect(os.environ['S101_DB_URL']) as conn:
                        with conn.cursor() as cur:
                            cur.execute('SELECT feature_instance_id FROM projection.s101_feature_current WHERE feature_type_name=ANY(%s) AND ST_Distance(geometry::geography,ST_GeomFromText(%s,4326)::geography)<=%s ORDER BY feature_instance_id',
                                        (qec['slots']['target_features'],case['spatial_context']['geometry'],radius))
                            row['independent_sql_ids']=[str(x[0]) for x in cur.fetchall()]
                    row['consistency_scope']='independent distance predicate on same frozen subset; NOT spatial gold'
                    returned=(result.get('structured_result') or {}).get('feature_ids')
                    row['returned_object_ids']=None if returned is None else [str(x) for x in returned]
                    row['sql_object_set_consistent']=None if returned is None else set(row['returned_object_ids'])==set(row['independent_sql_ids'])
                stream.write(json.dumps(row,ensure_ascii=False,default=str)+'\n'); stream.flush()
    rows=[json.loads(line) for line in (output/'spatial_rows.jsonl').read_text(encoding='utf-8').splitlines()]
    write(output/'spatial_summary.json',{'status':'COMPLETED','rows':len(rows),'gold_cases':0,
          'status_counts':{status:sum(r['status']==status for r in rows) for status in {r['status'] for r in rows}},
          'scope':'production radius component on frozen source subset, not full P and not expert spatial gold'})
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--reuse-snapshot',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(args.output_dir,args.reuse_snapshot),ensure_ascii=False,default=str))
