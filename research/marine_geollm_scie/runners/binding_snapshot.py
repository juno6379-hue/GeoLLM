"""Freeze real source relations into a new research DB; never write source DBs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
TARGET_CONTAINER = 'marine-scie-pilot-db'
TARGET_DATABASE = 'scie_binding_v2'
ALLOWED_DATABASES = {'scie_binding_v2', 'scie_model_v3'}
RELATIONS = ('knowledge.document_chunks', 'serving.marine_gazetteer_current',
             'serving.navigation_aid_current', 'serving.island_gazetteer_current')
MODEL_RELATIONS = (*RELATIONS, 'knowledge.capability_embeddings')
OLD = 'research/marine_geollm_scie/runs/20261029_pilot/spatial'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def verify_files(manifest, output):
    for record in manifest['relations']:
        p = (output / record['csv_path']).resolve()
        if not p.is_relative_to(output.resolve()) or digest(p) != record['sha256']:
            raise ValueError('Snapshot file missing, escaped, or changed')
    for record in manifest.get('files', []):
        if digest(ROOT / record['path']) != record['sha256']:
            raise ValueError('Mounted source file changed: ' + record['path'])


def export(output):
    import psycopg2
    from psycopg2 import sql
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'status':'EXPORTING', 'db_identity':{'container':TARGET_CONTAINER, 'database':TARGET_DATABASE},
        'relations':[], 'files':[], 'source_readonly':True,
        'scientific_status':'DATA_BINDING_PREPARATION_NOT_MODEL_EVALUATION',
        'coverage_complete':False, 'embedding_profile_verified':False}
    source = os.environ['SCIE_SOURCE_DSN']
    with psycopg2.connect(source, connect_timeout=10) as conn:
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout='180s'")
            cur.execute('SELECT txid_current_snapshot()::text, transaction_timestamp()::text')
            manifest['source_transaction'], manifest['captured_at'] = cur.fetchone()
            for relation in (MODEL_RELATIONS if TARGET_DATABASE == 'scie_model_v3' else RELATIONS):
                cur.execute('SELECT attname, format_type(atttypid,atttypmod) FROM pg_attribute WHERE attrelid=%s::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum', (relation,))
                columns = cur.fetchall()
                identifier = sql.Identifier(*relation.split('.'))
                key = 'chunk_id' if relation == 'knowledge.document_chunks' else 'id' if relation == 'knowledge.capability_embeddings' else 'source_id'
                cur.execute(sql.SQL('SELECT count(*), count(DISTINCT {}) FROM {}').format(sql.Identifier(key), identifier))
                total, unique = cur.fetchone()
                if total != unique: raise ValueError('Snapshot order key is not unique: '+relation)
                query = sql.SQL('SELECT * FROM {} ORDER BY {}').format(identifier, sql.Identifier(key))
                name = relation.replace('.', '__') + '.csv'
                with (output/name).open('w', encoding='utf-8', newline='') as f:
                    cur.copy_expert(sql.SQL('COPY ({}) TO STDOUT WITH CSV HEADER').format(query), f)
                cur.execute(sql.SQL('SELECT count(*) FROM {}').format(identifier))
                record = {'relation':relation, 'columns':columns, 'rows':cur.fetchone()[0],
                    'csv_path':name, 'sha256':digest(output/name), 'selection_sql':query.as_string(conn),
                    'coverage':{'selection':'ALL_ROWS_IN_SOURCE_RELATION', 'national_completeness_verified':False}}
                if relation == 'knowledge.document_chunks':
                    cur.execute('SELECT count(*) FILTER(WHERE embedding IS NOT NULL), count(*) FILTER(WHERE source_sha256 IS NULL OR source_id IS NULL), count(*) FILTER(WHERE metadata @> %s::jsonb) FROM knowledge.document_chunks',
                        (json.dumps({'product_id':'S-101','version':'2.0.0','product_specification':'INT.IHO.S-101.2.0'}),))
                    record['embedding_rows'], record['missing_lineage_rows'], record['production_default_filter_rows'] = cur.fetchone()
                elif relation == 'knowledge.capability_embeddings':
                    cur.execute('SELECT count(embedding),min(vector_dims(embedding)),max(vector_dims(embedding)) FROM knowledge.capability_embeddings')
                    record['embedding_rows'],record['min_embedding_dimension'],record['max_embedding_dimension']=cur.fetchone()
                else:
                    cur.execute(sql.SQL('SELECT ST_Extent(geometry)::text, count(*) FILTER(WHERE geometry IS NULL OR NOT ST_IsValid(geometry)) FROM {}').format(identifier))
                    record['extent'], record['invalid_or_null_geometry_rows'] = cur.fetchone()
                manifest['relations'].append(record)
    old = json.loads((ROOT/OLD/'snapshot_manifest.json').read_text(encoding='utf-8'))
    old_file = ROOT/OLD/'source_rows.csv'
    if digest(old_file) != old['source_sha256']: raise ValueError('Prior spatial snapshot changed')
    name = 'projection__s101_feature_current.csv'
    shutil.copyfile(old_file, output/name)
    manifest['projection_snapshot'] = old
    manifest['relations'].append({'relation':'projection.s101_feature_current','columns':old['columns'],
        'rows':old['subset_rows'],'csv_path':name,'sha256':old['source_sha256'],
        'coverage':{'selection':'BOUNDED_SUBSET','bbox_epsg4326':old['bbox_epsg4326'],
                    'national_completeness_verified':False,'dokdo_coverage':False}})
    paths = ['data/s101_feature_catalogue_v2_parsed.json','data/public_place_anchors.json',
             'data/spatial_layer_registry.yaml','data/marine_term_dictionary.yaml',
             'data/s101_feature_dictionary.yaml']
    for folder, pattern in [('outputs/graph','kg_*_v2.jsonl'),('outputs/evidence','*candidates.jsonl')]:
        paths.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).glob(pattern))
    for folder in ('outputs/coastal_knowledge','outputs/dataset_pipeline'):
        paths.extend((Path(folder)/name).as_posix() for name in ('nodes.jsonl','edges.jsonl') if (ROOT/folder/name).exists())
    paths.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'outputs/dictionaries').glob('*.yaml'))
    paths.extend(['services/orchestrator/query_normalizer.py','services/orchestrator/graph_rag_retriever.py'])
    for path in sorted(set(paths)):
        manifest['files'].append({'path':path,'sha256':digest(ROOT/path)})
    manifest['status'] = 'EXPORTED'
    write(output/'snapshot_manifest.json',manifest)
    print(json.dumps({'status':'EXPORTED','relations':len(manifest['relations'])}))


def psql(query, database='postgres'):
    result = subprocess.run(['docker','exec','-i',TARGET_CONTAINER,'psql','-X','-q','-A','-t',
        '-v','ON_ERROR_STOP=1','-U','postgres','-d',database], input=query.encode('utf-8'), capture_output=True, check=True)
    return result.stdout.decode('utf-8').strip()


def load(output):
    manifest = json.loads((output/'snapshot_manifest.json').read_text(encoding='utf-8'))
    if manifest['db_identity'] != {'container':TARGET_CONTAINER,'database':TARGET_DATABASE}:
        raise ValueError('Unapproved research target')
    info = json.loads(subprocess.check_output(['docker','inspect',TARGET_CONTAINER]))[0]
    if info['Config'].get('Labels',{}).get('marine.scie.research') != 'true':
        raise ValueError('Research label missing')
    verify_files(manifest, output)
    # No replace/drop/truncate: an existing target must be inspected separately.
    psql('CREATE DATABASE '+TARGET_DATABASE+';')
    psql('CREATE EXTENSION postgis; CREATE EXTENSION vector; CREATE SCHEMA knowledge; CREATE SCHEMA serving; CREATE SCHEMA projection;', TARGET_DATABASE)
    verified = []
    for record in manifest['relations']:
        relation = record['relation']
        if relation not in (*MODEL_RELATIONS, 'projection.s101_feature_current'): raise ValueError('Unknown relation')
        # Column definitions came from format_type in the authenticated read-only snapshot.
        definitions = ','.join('"'+name.replace('"','""')+'" '+dtype for name,dtype in record['columns'])
        psql('CREATE TABLE '+relation+' ('+definitions+');', TARGET_DATABASE)
        with (output/record['csv_path']).open('rb') as stream:
            subprocess.run(['docker','exec','-i',TARGET_CONTAINER,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres','-d',TARGET_DATABASE,
                '-c','COPY '+relation+' FROM STDIN WITH CSV HEADER'],stdin=stream,stdout=subprocess.DEVNULL,check=True)
        count = int(psql('SELECT count(*) FROM '+relation+';',TARGET_DATABASE))
        if count != record['rows']: raise ValueError('Loaded row count mismatch')
        # COPY back in the exact export order to verify content as well as count.
        key = 'chunk_id' if relation == 'knowledge.document_chunks' else 'id' if relation == 'knowledge.capability_embeddings' else 'feature_instance_id' if relation.startswith('projection.') else 'source_id'
        target_copy = output/(record['csv_path']+'.loaded')
        with target_copy.open('wb') as stream:
            subprocess.run(['docker','exec',TARGET_CONTAINER,'psql','-X','-q','-U','postgres','-d',TARGET_DATABASE,
                '-c','COPY (SELECT * FROM '+relation+' ORDER BY '+key+') TO STDOUT WITH CSV HEADER'],stdout=stream,check=True)
        same = digest(target_copy) == record['sha256']
        if not same: raise ValueError('Loaded content digest mismatch: '+relation)
        verified.append({'relation':relation,'rows':count,'roundtrip_sha256':digest(target_copy),'content_match':same})
        if any(c[0]=='geometry' for c in record['columns']):
            psql('CREATE INDEX ON '+relation+' USING gist(geometry);',TARGET_DATABASE)
        psql('ANALYZE '+relation+';',TARGET_DATABASE)
    psql('CREATE VIEW projection.s101_feature_valid AS SELECT * FROM projection.s101_feature_current WHERE ST_IsValid(geometry);',TARGET_DATABASE)
    manifest.update(status='LOADED_VERIFIED',loaded_verification=verified)
    write(output/'snapshot_manifest.json',manifest)
    print(json.dumps({'status':manifest['status'],'database':TARGET_DATABASE,'relations':len(verified)}))


def launch(output):
    if output.exists(): raise FileExistsError('Use a new snapshot directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    backend = json.loads(subprocess.check_output(['docker','inspect','geollm_backend']))[0]
    env = dict(v.split('=',1) for v in backend['Config']['Env'] if '=' in v)
    source = env['S101_DB_URL']
    if urlsplit(source).path != '/gbhd_s101': raise ValueError('Unexpected source database')
    net = next(iter(backend['NetworkSettings']['Networks']))
    command = ['docker','run','--rm','--network',net,'--label','marine.scie.research=true',
        '--mount',f'type=bind,source={ROOT},target=/work,readonly',
        '--mount',f'type=bind,source={output.parent},target=/out',
        '--workdir','/work','--env','PYTHONDONTWRITEBYTECODE=1','--env','SCIE_SOURCE_DSN='+source,
        'docker-backend','python','-m','research.marine_geollm_scie.runners.binding_snapshot',
        '--worker-export','--output','/out/'+output.name,'--database',TARGET_DATABASE]
    proc = subprocess.run(command,capture_output=True,timeout=600)
    if proc.returncode:
        if output.exists():
            (output/'export_failure.log').write_bytes(proc.stderr.replace(source.encode(),b'[REDACTED_DSN]'))
        raise RuntimeError('Source export failed; see redacted local log')
    print(proc.stdout.decode('utf-8'))
    load(output)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker-export',action='store_true');p.add_argument('--load-only',action='store_true')
    p.add_argument('--database',choices=sorted(ALLOWED_DATABASES),default=TARGET_DATABASE)
    a=p.parse_args()
    TARGET_DATABASE=a.database
    if a.worker_export: export(a.output)
    elif a.load_only: load(a.output.resolve())
    else: launch(a.output.resolve())
