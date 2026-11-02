"""Frozen nonempty source Oracles and explicit post-plan SQL mutation diagnostics.

No model, production mutation, GOLD/holdout import, or fabricated method result.
Fault injection leaves source identity guard and the original plan untouched.
"""
import argparse,copy,csv,hashlib,json
import platform,importlib.metadata
from pathlib import Path
from shapely import wkb,wkt
from shapely.geometry import shape
from pyproj import Geod
from ..baselines.v2_runtime import ObservedDatabase,V2Executor,ToolBlocked
from ..evaluation.rq3_contract import summarize,method_table

ROOT=Path(__file__).resolve().parents[3]
VERSION='rq3_postplan_sql_faults.v3'
CODE_FILES=['research/marine_geollm_scie/runners/rq3_execution_faults.py','research/marine_geollm_scie/evaluation/rq3_contract.py',
            'research/marine_geollm_scie/baselines/v2_runtime.py','research/marine_geollm_scie/baselines/execution_dsl.py',
            'research/marine_geollm_scie/evaluation/execution_reliability_v1.py','research/marine_geollm_scie/evaluation/execution_semantics.py']
REF="ST_GeomFromText(i.args->>'reference_geometry',4326)"
FAULTS={'clean':None,'wrong_reference':('reference','ST_Translate('+REF+',1,0)'),
        'wrong_polygon':('reference','ST_Translate('+REF+',1,0)'),
        'wrong_predicate':('predicate','ST_Touches(p.geometry,r.geom)'),
        'wrong_distance_method':('distance',"(i.args->>'radius_m')::float8/1000.0"),
        'wrong_crs':('reference','ST_Transform(ST_SetSRID(ST_GeomFromText(i.args->>\'reference_geometry\'),3857),4326)'),
        'truncation':('limit','LIMIT 1')}


def sha(value):return hashlib.sha256(value).hexdigest()
def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def dependencies():return {'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ('shapely','pyproj')}}


def mutate_sql(body,fault):
    if fault not in FAULTS:raise ToolBlocked('UNKNOWN_RQ3_FAULT')
    if fault=='clean':return body
    kind,replacement=FAULTS[fault]
    old={'reference':REF,'predicate':'ST_Intersects(p.geometry,r.geom)',
         'distance':"(i.args->>'radius_m')::float8",'limit':'LIMIT 1001'}[kind]
    if body.count(old)!=1:raise ToolBlocked('RQ3_FAULT_INJECTION_TARGET_MISMATCH')
    return body.replace(old,replacement)


class FaultDatabase(ObservedDatabase):
    def __init__(self,fault='clean',**kwargs):
        super().__init__(**kwargs);self.fault=fault;self.injections=[]
    def query(self,body,arguments):
        if self.scope=='spatial':
            changed=mutate_sql(body,self.fault)
            # GeoJSON is rounded for display; collect actual stored geometry independently.
            projection='ST_AsGeoJSON(p.geometry)::jsonb geometry'
            if changed.count(projection)!=1:raise ToolBlocked('RQ3_GEOMETRY_TELEMETRY_TARGET_MISMATCH')
            changed=changed.replace(projection,projection+",encode(ST_AsEWKB(p.geometry),'hex') geometry_ewkb")
            self.injections.append({'fault':self.fault,'stage':'AFTER_PLAN_VALIDATION_BEFORE_SPATIAL_SQL',
                'original_sql':body,'executed_sql':changed,'original_sql_sha256':sha(body.encode()),
                'executed_sql_sha256':sha(changed.encode()),'arguments_sha256':sha(json.dumps(arguments,sort_keys=True).encode()),
                'arguments':copy.deepcopy(arguments),'geometry_telemetry':'ACTUAL_STORED_EWKB',
                'source_guard_retained':self.source_guard is not None})
            body=changed
        return super().query(body,arguments)


def profile_load(path):
    path=Path(path).resolve();raw=path.read_bytes();profile=json.loads(raw)
    pin=profile['snapshot_manifest'];manifest_path=Path(pin['path']).resolve()
    if sha(manifest_path.read_bytes())!=pin['sha256']:raise ValueError('Snapshot manifest changed')
    manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    rec=next(r for r in manifest['relations'] if r['relation']=='serving.marine_gazetteer_current')
    source=(manifest_path.parent/rec['csv_path']).resolve()
    if not source.is_relative_to(manifest_path.parent) or sha(source.read_bytes())!=rec['sha256']:
        raise ValueError('Frozen source CSV changed')
    return profile,{'profile_path':str(path),'profile_sha256':sha(raw),'snapshot_pin':pin,
                    'source_path':str(source),'source_sha256':rec['sha256']},source


def source_oracle(source,args):
    ref=wkt.loads(args['reference_geometry']);geod=Geod(ellps='WGS84');objects=[]
    with source.open(encoding='utf8',newline='') as stream:
        for row in csv.DictReader(stream):
            geom=wkb.loads(bytes.fromhex(row['geometry']))
            if not geom.is_valid or geom.is_empty:raise ValueError('Invalid Oracle geometry')
            if geom.geom_type not in ('Point','MultiPoint'):raise ValueError('Point-source Oracle required')
            points=[geom] if geom.geom_type=='Point' else list(geom.geoms)
            distance=min(geod.inv(ref.x,ref.y,p.x,p.y)[2] for p in points) if ref.geom_type=='Point' else None
            included=(distance<=args['radius_m']) if args['relation']=='dwithin' else geom.intersects(ref)
            if included:objects.append({'source_id':row['source_id'],'geometry_ewkb':row['geometry'],
                'geometry_sha256':sha(bytes.fromhex(row['geometry'])),'distance_m':distance})
    if not objects:raise ValueError('Nonempty Oracle required')
    return sorted(objects,key=lambda x:x['source_id'])


def prepare(profile_path,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    profile,pins,source=profile_load(profile_path)
    definitions=[('dokdo_radius','DOKDO_SOURCE_SELECTION','독도 동도 기준점 5km 이내 원천 해양지명',
       {'source':'marine_places','feature_types':[],'reference_geometry':'POINT(131.86955555555556 37.24077777777778)',
        'crs':'EPSG:4326','radius_m':5000,'relation':'dwithin','analysis_type':'feature_search_by_radius'},
       ['clean','wrong_reference','wrong_distance_method','wrong_crs','truncation']),
      ('busan_polygon','BUSAN_SOURCE_SELECTION','제공된 부산 선택 영역과 교차하는 원천 해양지명',
       {'source':'marine_places','feature_types':[],'reference_geometry':'POLYGON((129 35,129.2 35,129.2 35.2,129 35.2,129 35))',
        'crs':'EPSG:4326','relation':'intersects','analysis_type':'feature_search_by_area'},
       ['clean','wrong_polygon','wrong_predicate'])]
    cases=[]
    for base,group,query,args,faults in definitions:
        oracle={'method':'INDEPENDENT_FROZEN_CSV_SHAPELY_TOPOLOGY_PYPROJ_GEOD_WGS84',
                'source_sha256':pins['source_sha256'],'reference_geometry':args['reference_geometry'],
                'reference_sha256':sha(args['reference_geometry'].encode()),'relation':args['relation'],
                'distance_m':args.get('radius_m'),'objects':source_oracle(source,args),
                'identity_policy':'FROZEN_SOURCE_ROWS_NO_PHYSICAL_FACILITY_DEDUPLICATION',
                'real_world_completeness':'UNKNOWN','absence_certified':False}
        oracle_file=base+'_oracle.json';write(out/oracle_file,oracle)
        for fault in faults:
            cases.append({'case_id':base+'__'+fault,'base_case':base,'equivalence_group':group,'eligible':True,
              'query':query,'query_sha256':sha(query.encode()),'plan':{'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':args}]},
              'fault':fault,'oracle_file':oracle_file,'oracle_sha256':sha((out/oracle_file).read_bytes()),
              'expected_execution_success':True,'expected_spatial_correct':fault=='clean',
              'mutation_stage':'AFTER_PLAN_VALIDATION_BEFORE_SPATIAL_SQL','independent_human_approved':False})
    contract={'version':VERSION,'scope':'DEVELOPMENT_POSTPLAN_EXECUTOR_FAULT_DIAGNOSTIC','pins':pins,'cases':cases,
              'frozen_code':{p:sha((ROOT/p).read_bytes()) for p in CODE_FILES},
              'dependencies':dependencies(),
              'mutation_definitions':FAULTS,'model_calls':0,'holdout_used':False,
              'excluded_fault_families':[{'name':'centroid_vs_minimum_full_polygon_distance',
                'reason':'Prior independent SQL counterexample retained separately; full canonical polygon may fail shared executor coverage. Not counted as method-ready without new adapter execution.'}],
              'limitations':['Only 2 independent source-selection groups; 6 mutations are not 6 independent geographic tasks.',
                'Wrong distance method here means metre/kilometre application in SQL, not centroid/minimum-geometry equivalence.',
                'Model methods must supply their actual plans/raw outputs for comparisons; diagnostic rows are never relabelled B0-P1.']}
    write(out/'contract.json',contract)
    write(out/'manifest.json',{'status':'FROZEN_DEVELOPMENT_CONTRACT','contract_sha256':sha((out/'contract.json').read_bytes()),
          'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()},'human_gold':False})
    return contract


def verify_contract(path):
    path=Path(path);manifest=json.loads((path/'manifest.json').read_text(encoding='utf8'))
    for name,digest in manifest['files'].items():
        file=(path/name).resolve()
        if not file.is_relative_to(path.resolve()) or sha(file.read_bytes())!=digest:raise ValueError('Contract artifact changed')
    raw=(path/'contract.json').read_bytes()
    if sha(raw)!=manifest['contract_sha256']:raise ValueError('Contract hash mismatch')
    return json.loads(raw),manifest['contract_sha256']


def score_execution(case,oracle,result,injections):
    trace=result.get('execution_observation') or {};e=trace.get('execution_succeeded')
    rows=[row for r in result.get('receipts',[]) for row in r.get('result',{}).get('rows',[])]
    actual={r['source_id']:r for r in rows};expected={r['source_id']:r for r in oracle['objects']}
    measured=e is True
    ids_match=set(actual)==set(expected) and len(rows)==len(actual) if measured else None
    shared=set(actual)&set(expected)
    geometry_match=(all(actual[k]['geometry_ewkb'].lower()==expected[k]['geometry_ewkb'].lower() for k in shared)
                    if all(actual[k].get('geometry_ewkb') for k in shared) else None) if measured else None
    # Check executed SQL and arguments, never infer correctness from the fault label.
    relation_match=None
    if measured and injections:
        checks=[]
        for injection in injections:
            sql=injection['executed_sql'];args=injection.get('arguments',{})
            reference=REF+' geom) r'
            predicate=('ST_DWithin(p.geometry::geography,r.geom::geography,(i.args->>\'radius_m\')::float8)'
                       if oracle.get('relation')=='dwithin' else 'ST_Intersects(p.geometry,r.geom)')
            checks.append(reference in sql and predicate in sql and
                args.get('reference_geometry')==oracle.get('reference_geometry') and args.get('relation')==oracle.get('relation') and
                args.get('radius_m')==oracle.get('distance_m'))
        relation_match=all(checks)
    components=[ids_match,geometry_match,relation_match]
    spatial=(False if False in components else True if all(v is True for v in components) else None) if measured else None
    return {'execution_success':e,'spatial_correct':spatial,'object_set_match':ids_match,'geometry_match':geometry_match,
            'relation_match':relation_match,'expected_ids':sorted(expected),'actual_ids':sorted(actual),
            'missing_ids':sorted(set(expected)-set(actual)) if measured else None,
            'extra_ids':sorted(set(actual)-set(expected)) if measured else None,
            'semantic_correct':None,'evidence_correct':None}


def run(contract_path,output):
    contract,contract_sha=verify_contract(contract_path);folder=Path(contract_path);out=Path(output);out.mkdir(parents=True,exist_ok=False)
    pins=contract['pins'];profile,newpins,_=profile_load(pins['profile_path'])
    if pins!=newpins:raise ValueError('Pinned profile/source changed')
    codefiles=CODE_FILES
    before={p:sha((ROOT/p).read_bytes()) for p in codefiles};write(out/'protocol_before.json',{'source_hashes':before,'contract_sha256':contract_sha,'pins':pins})
    if before!=contract['frozen_code']:raise ValueError('Frozen executor/evaluator code changed; prepare new contract')
    if dependencies()!=contract['dependencies']:raise ValueError('Frozen GIS dependency changed')
    jobs=[{'method':'COMMON_EXECUTOR_DIAGNOSTIC','case_id':c['case_id'],'repeat_id':1,'plan':c['plan']} for c in contract['cases']]
    bycase={c['case_id']:c for c in contract['cases']};observations=[];seen=set()
    for job in jobs:
        key=(job['method'],job['case_id'],job['repeat_id'])
        if key in seen:raise ValueError('Duplicate submitted job')
        seen.add(key);case=bycase[job['case_id']];db=FaultDatabase(case['fault'])
        executor=V2Executor(db,catalogue=ROOT/profile['catalogue']['path'],catalogue_sha256=profile['catalogue']['sha256'],
            anchors=profile.get('anchors',[]),coverage=profile['coverage'],reference_geometries=profile.get('reference_geometries',{}),snapshot_manifest=profile['snapshot_manifest'])
        plan=copy.deepcopy(job['plan']);plan_sha=sha(json.dumps(plan,sort_keys=True).encode());result=executor.execute(plan)
        assert sha(json.dumps(plan,sort_keys=True).encode())==plan_sha
        oracle=json.loads((folder/case['oracle_file']).read_text(encoding='utf8'))
        row={k:case[k] for k in ('case_id','equivalence_group','eligible','query_sha256','oracle_sha256')}
        row.update(method=job['method'],repeat_id=job['repeat_id'],fault=case['fault'],contract_sha256=contract_sha,
            plan_sha256=plan_sha,execution=result,injections=db.injections,**score_execution(case,oracle,result,db.injections))
        rawfile=f'{len(observations):03d}.json';write(out/rawfile,{'job':job,'observation':row});row['raw_file']=rawfile;row['raw_sha256']=sha((out/rawfile).read_bytes())
        observations.append(row);print(json.dumps({'method':job['method'],'case':case['case_id'],'E':row['execution_success'],'S':row['spatial_correct']}),flush=True)
    after={p:sha((ROOT/p).read_bytes()) for p in codefiles}
    verify_contract(contract_path)
    passed=before==after and all(r['execution_success'] is True and r['spatial_correct']==(r['fault']=='clean') for r in observations)
    summary={'status':'COMPLETED' if passed else 'VALIDATION_FAILED','diagnostic_only':True,'sources_unchanged':before==after,
       'observations':len(observations),'contract_sha256':contract_sha,'source_before':before,'source_after':after,
       'metrics':summarize(observations),'eight_method_measurement_status':method_table([],contract['cases']),
       'model_calls':0,'semantic_evidence_metrics_unmeasured':True,'method_comparison_claim':False,
       'limitations':contract['limitations']}
    write(out/'observations.json',observations);write(out/'summary.json',summary)
    if not passed:raise RuntimeError('RQ3_EXPECTATIONS_OR_SOURCE_FREEZE_FAILED')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare-profile');p.add_argument('--contract',required=True);p.add_argument('--output');a=p.parse_args()
    if a.prepare_profile:prepare(a.prepare_profile,a.contract)
    else:
        if not a.output:p.error('--output required')
        run(a.contract,a.output)
