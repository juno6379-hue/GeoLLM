"""Read-only SQL development counterexample, not an eight-method benchmark.

Fixed mutation: replace BOTH target and reference geometries with ST_Centroid
before geography distance. The correct operator remains minimum geometry-to-
geometry spheroidal distance. The mutation is selected before DB observations.
No production authority, model invocation, recovery, or GOLD modification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time

from .binding_snapshot import TARGET_CONTAINER, ALLOWED_DATABASES

ROOT=Path(__file__).resolve().parents[3]
DATABASE='scie_model_v3'
SNAPSHOT=Path('outputs/scie_gold_v2_eight_snapshot_20261102_v6')
GOLD=Path('research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1')
FROZEN={
 'answer_contracts.jsonl':'550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4',
 'canonical_busan_boundary.json':'a0f4408850683c987840531e436ff5698af3b9e39bab700098a453727ff5f63b',
 'oracle_checks.json':'0b7f30e293b2464cebedc2805b9522f95efca178a05e8c0409d59a0f2338fe7c',
}
RELATIONS={
 'projection.s101_feature_current':('feature_instance_id','1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85'),
 'serving.marine_gazetteer_current':('source_id','3f931edd30279f561a129afbaa597db33c985bc59d211b9b64bd33942e4e6d7a'),
}
MUTATION='CENTROID_TARGET_AND_REFERENCE_THEN_GEOGRAPHY_DWITHIN_2000M'
GAZETTEER_SOURCE=Path('data/source_inventory/marine_gazetteer_20221231.csv')
GAZETTEER_SHA='bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464'

SPATIAL_SQL="""WITH h AS MATERIALIZED (
 SELECT geometry g FROM projection.s101_feature_current
 WHERE feature_instance_id=1137770 AND feature_type_name='HarbourAreaAdministrative'
), candidates AS MATERIALIZED (
 SELECT p.feature_instance_id::text id,p.feature_type_name feature,
 encode(ST_AsEWKB(p.geometry),'hex') geometry_ewkb,
 ST_Distance(p.geometry::geography,h.g::geography,true) minimum_distance_m,
 ST_Distance(ST_Centroid(p.geometry)::geography,ST_Centroid(h.g)::geography,true) centroid_distance_m,
 ST_DWithin(p.geometry::geography,h.g::geography,2000,true) normal_included,
 ST_DWithin(ST_Centroid(p.geometry)::geography,ST_Centroid(h.g)::geography,2000,true) wrong_included
 FROM projection.s101_feature_current p CROSS JOIN h
 WHERE p.feature_type_name IN ('AnchorageArea','RestrictedArea') AND p.geometry IS NOT NULL AND ST_IsValid(p.geometry)
), gazetteer AS MATERIALIZED (
 SELECT p.source_id::text id,p.name,p.properties,p.provenance,
 ST_Distance(p.geometry::geography,a.g::geography,true) distance_m,
 encode(ST_AsEWKB(p.geometry),'hex') geometry_ewkb
 FROM serving.marine_gazetteer_current p CROSS JOIN
 (SELECT ST_SetSRID(ST_MakePoint(131.86955555555556,37.24077777777778),4326) g) a
 WHERE p.geometry IS NOT NULL AND ST_IsValid(p.geometry)
 AND ST_DWithin(p.geometry::geography,a.g::geography,5000,true)
)
SELECT jsonb_build_object(
 'transaction',txid_current_snapshot()::text,
 'read_only',current_setting('transaction_read_only'),
 'isolation',current_setting('transaction_isolation'),
 'database',current_database(),
 'postgis_version',PostGIS_Full_Version(),
 'reference_rows',(SELECT count(*) FROM h),
 'reference_geometry_ewkb',(SELECT encode(ST_AsEWKB(g),'hex') FROM h),
 'reference_valid',(SELECT ST_IsValid(g) FROM h),
 'reference_srid',(SELECT ST_SRID(g) FROM h),
 'candidate_rows',(SELECT coalesce(jsonb_agg(c ORDER BY feature,id),'[]'::jsonb) FROM candidates c),
 'q4_rows',(SELECT coalesce(jsonb_agg(g ORDER BY id),'[]'::jsonb) FROM gazetteer g));"""


def sha(data): return hashlib.sha256(data).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def write(p,data): p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def build_sql():
    sections=["\\encoding UTF8",'BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;',
              "SET LOCAL statement_timeout='180s';",'\\echo __RQ3_METADATA_BEGIN__',
              "SELECT jsonb_build_object('transaction',txid_current_snapshot()::text,'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'database',current_database());",
              '\\echo __RQ3_METADATA_END__']
    for i,(relation,(key,_)) in enumerate(RELATIONS.items()):
        sections.extend([f'\\echo __RQ3_SOURCE_{i}_BEGIN__',
                         f'COPY (SELECT * FROM {relation} ORDER BY {key}) TO STDOUT WITH CSV HEADER;',
                         f'\\echo __RQ3_SOURCE_{i}_END__'])
    sections+=['\\echo __RQ3_RESULT_BEGIN__',SPATIAL_SQL,'\\echo __RQ3_RESULT_END__','ROLLBACK;']
    return '\n'.join(sections)+'\n'


def section(raw,name):
    begin=('__RQ3_'+name+'_BEGIN__\n').encode();end=('__RQ3_'+name+'_END__\n').encode()
    if raw.count(begin)!=1 or raw.count(end)!=1:raise ValueError('Missing or repeated SQL output marker: '+name)
    body=raw.split(begin,1)[1].split(end,1)[0]
    return body


def source_object_ids(rows, source_bytes):
    """Join DB identities to original CSV IDs, never match by proximity/name alone."""
    if sha(source_bytes)!=GAZETTEER_SHA:
        raise ValueError('Gazetteer original CSV changed')
    source={}
    for row in csv.DictReader(io.StringIO(source_bytes.decode('cp949'))):
        if not row.get('공간정보') or not row.get('지명명'):
            continue
        key=sha(f"marine_gazetteer_mof|{row.get('공간정보일련번호')}|{row['지명명']}".encode())[:24]
        if key in source: raise ValueError('Duplicate source identity')
        source[key]=row
    ids=[]
    for row in rows:
        original=source.get(row['id'])
        if original is None or row.get('properties')!=original or row['name']!=original['지명명'] or row.get('provenance',{}).get('source_sha256')!=GAZETTEER_SHA:
            raise ValueError('Gazetteer original identity link failed')
        row['source_object_id']=original['공간정보일련번호']
        ids.append(row['source_object_id'])
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate original object ID')
    return sorted(ids)


def assess(result,gold_case,q4_case, *, q4_source_ids=None):
    groups={}
    for field in ('normal_included','wrong_included'):
        groups[field]={feature:sorted(r['id'] for r in result['candidate_rows'] if r['feature']==feature and r[field])
                       for feature in ('AnchorageArea','RestrictedArea')}
    expected={k:sorted(v['object_ids']) for k,v in gold_case['spatial_gold'].items()}
    q4_expected=sorted(o['source_id'] for o in q4_case['spatial_reference']['objects'])
    diffs={feature:{'missing':sorted(set(expected[feature])-set(groups['wrong_included'][feature])),
                    'extra':sorted(set(groups['wrong_included'][feature])-set(expected[feature]))} for feature in expected}
    normal_ok=groups['normal_included']==expected
    wrong_ok=groups['wrong_included']==expected
    return dict(normal_object_ids=groups['normal_included'],wrong_object_ids=groups['wrong_included'],
                expected_object_ids=expected,difference=diffs,
                normal={'E':True,'S':normal_ok},wrong={'E':True,'S':wrong_ok},
                counterexample_found=normal_ok and not wrong_ok,
                q4={'object_ids':q4_source_ids,
                    'db_source_ids':sorted(r['id'] for r in result['q4_rows']),
                    'id_namespace':'ORIGINAL_CSV_SPATIAL_SERIAL_NUMBER',
                    'expected_object_ids':q4_expected,'E':True,
                    'S':q4_source_ids==q4_expected if q4_source_ids is not None else None})


def run(output,root=ROOT):
    root=Path(root).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    flags=dict(execution_attempted=False,execution_started=False,tool_called=False,sql_executed=False)
    summary=dict(status='PREPARING',scope='DEVELOPMENT_SQL_MUTATION_NOT_METHOD_BENCHMARK',
                 mutation=MUTATION,reference_feature_id='1137770',radius_m=2000,
                 sql_trace=flags,evidence_verified=False,normal={'E':None,'S':None},wrong={'E':None,'S':None},
                 production_authority_granted=False,models_called=0,holdout_used=False)
    try:
        if DATABASE not in ALLOWED_DATABASES or TARGET_CONTAINER!='marine-scie-pilot-db':raise ValueError('Research target restriction changed')
        info=json.loads(subprocess.check_output(['docker','inspect',TARGET_CONTAINER],timeout=20))[0]
        if info['Config'].get('Labels',{}).get('marine.scie.research')!='true':raise ValueError('Missing research container label')
        if not info['State']['Running']:raise ValueError('Existing research container is stopped')
        write(output/'container_identity.json',{'container':TARGET_CONTAINER,'id':info['Id'],
              'database':DATABASE,'research_label':True,'mounts':info['Mounts']})
        files={}
        if digest(root/GAZETTEER_SOURCE)!=GAZETTEER_SHA:raise ValueError('Gazetteer source CSV changed')
        files[GAZETTEER_SOURCE.as_posix()]=GAZETTEER_SHA
        for name,expected in FROZEN.items():
            p=root/GOLD/name
            if digest(p)!=expected:raise ValueError('Frozen GOLD artifact changed: '+name)
            files[p.relative_to(root).as_posix()]=expected
        boundary=json.loads((root/GOLD/'canonical_busan_boundary.json').read_text(encoding='utf-8'))
        cases={d['case_id']:d for d in [json.loads(x) for x in (root/GOLD/'answer_contracts.jsonl').read_text(encoding='utf-8').splitlines()]}
        snapshot=json.loads((root/SNAPSHOT/'snapshot_manifest.json').read_text(encoding='utf-8'))
        if snapshot['db_identity']!={'container':TARGET_CONTAINER,'database':DATABASE}:raise ValueError('Snapshot DB identity differs')
        for relation,(_,expected) in RELATIONS.items():
            entry=next(r for r in snapshot['relations'] if r['relation']==relation)
            if entry['sha256']!=expected:raise ValueError('Frozen relation identity differs')
            p=(root/SNAPSHOT/entry['csv_path']).resolve()
            if not p.is_relative_to((root/SNAPSHOT).resolve()) or digest(p)!=expected:raise ValueError('Frozen relation file changed')
            files[p.relative_to(root).as_posix()]=expected
        write(output/'protocol_before_execution.json',{'mutation':MUTATION,'reference_id':1137770,
              'normal_predicate':'ST_DWithin(target::geography,reference::geography,2000,true)',
              'wrong_predicate':'ST_DWithin(ST_Centroid(target)::geography,ST_Centroid(reference)::geography,2000,true)',
              'frozen_files':files,'query_scope':'SOURCE_BOUND_RESEARCH_SNAPSHOT_ONLY',
              'real_world_completeness':'UNKNOWN','benchmark_method_result':False})
        sql=build_sql();(output/'transaction.sql').write_text(sql,encoding='utf-8')
        summary['sql_sha256']=sha(sql.encode());summary['oracle_sha256']=FROZEN['answer_contracts.jsonl']
        summary['sql_trace']=dict(execution_attempted=True,execution_started=None,tool_called=True,sql_executed=None)
        command=['docker','exec','-i',TARGET_CONTAINER,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','postgres','-d',DATABASE]
        start=time.monotonic()
        with (output/'transaction.stdout').open('wb') as out,(output/'transaction.stderr').open('wb') as err:
            process=subprocess.run(command,input=sql.encode(),stdout=out,stderr=err,timeout=240)
        summary['latency_seconds']=time.monotonic()-start;summary['process_returncode']=process.returncode
        if process.returncode:raise RuntimeError('RESEARCH_READ_ONLY_SQL_FAILED_SEE_STDERR')
        raw=(output/'transaction.stdout').read_bytes()
        metadata=json.loads(section(raw,'METADATA'))
        result=json.loads(section(raw,'RESULT'))
        summary['sql_trace']=dict(execution_attempted=True,execution_started=True,tool_called=True,sql_executed=True)
        summary['normal']['E']=True;summary['wrong']['E']=True
        summary['source_hashes']={}
        for i,(relation,(_,expected)) in enumerate(RELATIONS.items()):
            source=section(raw,f'SOURCE_{i}');actual=sha(source)
            summary['source_hashes'][relation]={'expected':expected,'actual':actual,'match':actual==expected}
            if actual!=expected:raise ValueError('Live relation changed: '+relation)
        if metadata['transaction']!=result['transaction'] or metadata['read_only']!='on' or result['read_only']!='on' or result['isolation']!='repeatable read' or result['database']!=DATABASE:
            raise ValueError('Transaction identity/read-only/isolation mismatch')
        geometry_hash=sha(bytes.fromhex(result['reference_geometry_ewkb']))
        if result['reference_rows']!=1 or result['reference_valid'] is not True or result['reference_srid']!=4326 or geometry_hash!=boundary['geometry_sha256']:
            raise ValueError('Canonical boundary geometry mismatch')
        q4_ids=source_object_ids(result['q4_rows'],(root/GAZETTEER_SOURCE).read_bytes())
        summary.update(assess(result,cases['PILOT_Q5_02'],cases['PILOT_Q4_01'],q4_source_ids=q4_ids))
        if not summary['normal']['S']:raise ValueError('Normal SQL differs from independent frozen GOLD')
        summary.update(evidence_verified=True,status='VERIFIED_SQL_COUNTEREXAMPLE' if summary['counterexample_found'] else 'VERIFIED_NO_COUNTEREXAMPLE',
                       transaction=metadata,reference_geometry_sha256=geometry_hash,
                       frozen_files=files,source_snapshot_manifest_sha256=digest(root/SNAPSHOT/'snapshot_manifest.json'))
        for row in result['candidate_rows']+result['q4_rows']:
            row['geometry_sha256']=sha(bytes.fromhex(row.pop('geometry_ewkb')))
        result.pop('reference_geometry_ewkb')
        write(output/'spatial_rows.json',result)
        if any(digest(root/p)!=h for p,h in files.items()):raise ValueError('Frozen local file changed during execution')
    except Exception as exc:
        summary.update(status='FAILED_PRESERVED',evidence_verified=False,error_type=type(exc).__name__,error=str(exc))
        summary['normal']['S']=None;summary['wrong']['S']=None
        summary['counterexample_found']=None
    summary['object_identity_policy']='FROZEN_SNAPSHOT_FEATURE_ROWS_NOT_DEDUPLICATED_PHYSICAL_FACILITIES'
    summary['spatial_cases']=[]
    if summary['evidence_verified']:
        expected=sorted(x for values in summary['expected_object_ids'].values() for x in values)
        for variant,key in [('normal','normal_object_ids'),('wrong','wrong_object_ids')]:
            actual=sorted(x for values in summary[key].values() for x in values)
            summary['spatial_cases'].append(dict(case_id='PILOT_Q5_02',variant=variant,
                execution_success=summary[variant]['E'],spatial_correct=summary[variant]['S'],
                returned_count=len(actual),gold_count=len(expected),object_ids=actual,
                missing_ids=sorted(set(expected)-set(actual)),extra_ids=sorted(set(actual)-set(expected)),
                scope='DEVELOPMENT_SQL_MUTATION_NOT_METHOD_BENCHMARK',
                reason='minimum full geometry distance' if variant=='normal' else MUTATION))
        q4=summary['q4']
        summary['spatial_cases'].append(dict(case_id='PILOT_Q4_01',variant='normal_source_bound',
            execution_success=q4['E'],spatial_correct=q4['S'],returned_count=len(q4['object_ids']),
            gold_count=len(q4['expected_object_ids']),object_ids=q4['object_ids'],
            missing_ids=sorted(set(q4['expected_object_ids'])-set(q4['object_ids'])),
            extra_ids=sorted(set(q4['object_ids'])-set(q4['expected_object_ids'])),
            scope='RESEARCH_DB_ORACLE_CHECK_NOT_PRODUCTION_P1_RESULT',id_namespace='ORIGINAL_CSV_SPATIAL_SERIAL_NUMBER',
            reason='explicit 5000m source-bound gazetteer SQL; object-set comparison only; DB projected geometry and GOLD DMS distance policy remain distinct'))
    write(output/'summary.json',summary)
    write(output/'manifest.json',{'status':summary['status'],'files':{
        p.name:digest(p) for p in output.iterdir() if p.is_file() and p.name!='manifest.json'},
        'runner_sha256':digest(Path(__file__)),'evidence_verified':summary['evidence_verified'],
        'scope':summary['scope'],'benchmark_method_result':False})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.output)
    print(json.dumps({k:result.get(k) for k in ['status','evidence_verified','normal','wrong','counterexample_found','error']},ensure_ascii=False))
    raise SystemExit(1 if result['status']=='FAILED_PRESERVED' else 0)
