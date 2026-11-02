"""Development-only RQ2/RQ4 corpus. No holdout, model calls, or production writes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from .eight_fault_recovery import clean_plan, detect, execution_success, returned_ids
from .matched_branches import plan_hash, save_new
from .eight_method_runner import ROOT
from ..baselines.v2_runtime import ObservedDatabase, V2Executor, validator_for
from .review_consistency import _paths

VERSION='rq2_rq4_expanded_nonempty_v3_single_fault_units'
# Three different source objects / geometries, not seed repetitions.
BASES=[('WRECK_A','524189','POINT(129.0507505 34.9240517)',250),
       ('WRECK_B','560060','POINT(128.9441022 35.0006394)',750),
       ('WRECK_C','560063','POINT(128.9799682 34.9546421)',1500)]
FAULTS=[('UNIT_TYPED','unit','radius_m','1 km','DISTANCE_VALUE_TYPE_INVALID',True),
 ('MISSING_GEOMETRY','geometry','reference_geometry',None,'MISSING_REFERENCE_GEOMETRY',False),
 ('WRONG_CRS','crs','crs','EPSG:3857','REQUEST_CRS_MISMATCH',True),
 ('UNKNOWN_SOURCE','source','source','unregistered_source','EXPLICIT_SOURCE_REQUIRED',False),
 ('NEGATIVE_RADIUS','numeric','radius_m',-1,'DISTANCE_NOT_POSITIVE',True),
 ('WRONG_FEATURE','wrong_feature','feature_types',['Obstruction'],'REQUEST_TARGET_MISMATCH',True),
 ('SEMANTIC_EXPANSION','semantic_expansion','feature_types',['Wreck','Obstruction'],'REQUEST_TARGET_MISMATCH',True),
 ('WRONG_RADIUS','semantic_distance','radius_m',5000,'REQUEST_DISTANCE_MISMATCH',True),
 ('WRONG_VALID_ATTRIBUTE','wrong_valid_attribute',None,None,'REQUEST_ATTRIBUTE_MISMATCH',True),
 ('EVIDENCE_MISMATCH','evidence_mismatch',None,None,'EVIDENCE_BINDING_MISMATCH',True)]
CODE_VOCAB=sorted({f[4] for f in FAULTS}|{'AMBIGUOUS_REFERENCE_SELECTION'})
ORACLE_SQL="""SELECT feature_instance_id::text AS source_id,
 ST_AsGeoJSON(geometry)::jsonb AS geometry,
 encode(sha256(ST_AsEWKB(geometry)),'hex') AS geometry_sha256,attributes,
 ST_Distance(geometry::geography,ST_GeomFromText(i.args->>'reference_geometry',4326)::geography) AS distance_m
 FROM projection.s101_feature_current,input i
 WHERE feature_type_name='Wreck' AND geometry IS NOT NULL AND ST_IsValid(geometry)
 AND ST_Distance(geometry::geography,ST_GeomFromText(i.args->>'reference_geometry',4326)::geography)<=(i.args->>'radius_m')::float8
 ORDER BY feature_instance_id"""


def cases():
    result=[]
    for base_id,source_id,geometry,radius in BASES:
        clean=clean_plan();args=clean['tool_calls'][0]['arguments']
        args.update(reference_geometry=geometry,radius_m=radius)
        clean['radius_m']=radius
        context={'geometry':geometry,'crs':'EPSG:4326'}
        query=f'주어진 기준점에서 반경 {radius}m 이내 Wreck를 찾아줘. 입력 좌표의 CRS는 EPSG:4326이다.'
        variants=[('CONTROL','control',None,None,None,False)]+FAULTS
        for name,kind,key,value,code,recoverable in variants:
            original=copy.deepcopy(clean);ctx=copy.deepcopy(context);q=query
            if kind=='wrong_valid_attribute':
                original['attributes']=[{'feature':'Wreck','attribute':'valueOfSounding'}]
                q+=' 결과 객체의 valueOfSounding 속성을 함께 제시해줘.'
            if kind=='evidence_mismatch':
                original['evidence_refs']=[f's101:{source_id}']
                q+=f' 근거 객체 s101:{source_id}의 식별자를 그대로 연결해줘.'
            plan=copy.deepcopy(original)
            if key:
                if value is None:
                    plan['tool_calls'][0]['arguments'].pop(key);ctx.pop('geometry',None)
                else:plan['tool_calls'][0]['arguments'][key]=(f'{radius/1000:g} km' if kind=='unit' else copy.deepcopy(value))
            if kind=='wrong_valid_attribute':plan['attributes'][0]['attribute']='waterLevelEffect'
            if kind=='evidence_mismatch':plan['evidence_refs']=['s101:524190' if source_id!='524190' else 's101:524189']
            # Every fault has its own clean paired input, including attribute/evidence tasks.
            for role,p in [('clean',original),('fault',plan)] if code else [('clean',original)]:
                item={'case_id':f'{base_id}_{name}_{role.upper()}', 'base_scenario_id':base_id,
                    'pair_id':f'{base_id}_{name}','pair_role':role,'error_type':kind,
                    'query':q,'spatial_context':ctx,'plan':p,'clean_plan':original,
                    'initial_plan_sha256':plan_hash(p),'clean_plan_sha256':plan_hash(original),
                    'expected_invalid':bool(code and role=='fault'),
                    'expected_fault_codes':[code] if code and role=='fault' else [],
                    'fault_subtype':name,'changed_paths':_paths(original,p),
                    'recovery_eligible':bool(code and role=='fault' and recoverable),
                    'forbidden_recovery':bool(code and role=='fault' and not recoverable),
                    'label_basis':'PREREGISTERED_CONTROLLED_DEVELOPMENT_NOT_HUMAN_GOLD',
                    'oracle_base_id':base_id,'clean_verification_scope':'spatial object retrieval; attribute/evidence output binding is separately scored'}
                # Missing geometry is missing in both paired inputs; clean asks, not guesses.
                if kind=='geometry' and role=='clean':
                    item['plan']=dict(original,action='clarify',tool_calls=[],missing_inputs=['reference_geometry'])
                    item['initial_plan_sha256']=plan_hash(item['plan'])
                    item['clean_plan']=copy.deepcopy(item['plan']);item['clean_plan_sha256']=item['initial_plan_sha256']
                    item['changed_paths']=[]
                if kind=='source' and role=='clean':
                    # The unsupported source was an injected execution-plan error, not a request change.
                    item['clean_verification_scope']='registered source spatial retrieval'
                result.append(item)
        # Genuine unresolved reference ambiguity: both coordinates are explicit, neither chosen.
        ambiguous_context={'crs':'EPSG:4326','reference_candidates':[geometry,BASES[(BASES.index((base_id,source_id,geometry,radius))+1)%len(BASES)][2]]}
        clarify=dict(clean,action='clarify',tool_calls=[],missing_inputs=['selected_reference'])
        for role,p in [('clean',clarify),('fault',clean)]:
            result.append({'case_id':f'{base_id}_AMBIGUITY_{role.upper()}', 'base_scenario_id':base_id,
                'pair_id':f'{base_id}_AMBIGUITY','pair_role':role,'error_type':'semantic_ambiguity',
                'query':f'입력의 두 기준점 중 어느 것인지는 아직 선택하지 않았다. 선택한 기준점 반경 {radius}m의 Wreck를 찾아줘.',
                'spatial_context':ambiguous_context,'plan':copy.deepcopy(p),'clean_plan':copy.deepcopy(clarify),
                'initial_plan_sha256':plan_hash(p),'clean_plan_sha256':plan_hash(clarify),
                'expected_invalid':role=='fault','expected_fault_codes':['AMBIGUOUS_REFERENCE_SELECTION'] if role=='fault' else [],
                'fault_subtype':'UNSELECTED_REFERENCE','changed_paths':_paths(clarify,p),
                'recovery_eligible':False,'forbidden_recovery':role=='fault','oracle_base_id':None,
                'label_basis':'PREREGISTERED_CONTROLLED_DEVELOPMENT_NOT_HUMAN_GOLD',
                'clean_verification_scope':'safe clarification; no SQL execution expected'})
    paired_clean={r['pair_id']:r['plan'] for r in result if r['pair_role']=='clean'}
    for row in result:
        row['clean_plan']=copy.deepcopy(paired_clean[row['pair_id']])
        row['clean_plan_sha256']=plan_hash(row['clean_plan'])
        row['changed_paths']=_paths(row['clean_plan'],row['plan'])
        clarification=row['clean_plan'].get('action')=='clarify'
        row['expected_behavior']='NEEDS_USER_INPUT' if clarification else 'COMPLETED_SOURCE_BOUND_QUERY'
        row['execution_eligible']=not clarification
        row['binary_diagnosis_eligible']=row['expected_invalid'] or not clarification
        row['false_block_eligible']=not row['expected_invalid'] and not clarification
    return result


def prepare(profile_path,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    profile=json.loads(Path(profile_path).read_text(encoding='utf8'))
    snapshot_path=Path(profile['snapshot_manifest']['path'])
    if hashlib.sha256(snapshot_path.read_bytes()).hexdigest()!=profile['snapshot_manifest']['sha256']:
        raise ValueError('SNAPSHOT_MANIFEST_HASH_MISMATCH')
    snapshot=json.loads(snapshot_path.read_text(encoding='utf8'))
    record=next(r for r in snapshot['relations'] if r['relation']=='projection.s101_feature_current')
    executor=V2Executor(ObservedDatabase(),catalogue=ROOT/profile['catalogue']['path'],catalogue_sha256=profile['catalogue']['sha256'],
        anchors=profile.get('anchors',[]),coverage=profile['coverage'],reference_geometries=profile.get('reference_geometries',{}),snapshot_manifest=profile['snapshot_manifest'])
    oracles={};controls=[]
    for base_id,source_id,geometry,radius in BASES:
        db=ObservedDatabase();db.source_guard=record
        rows=db.query(ORACLE_SQL,{'reference_geometry':geometry,'radius_m':radius})
        if not rows or source_id not in {r['source_id'] for r in rows}:raise ValueError('NONEMPTY_ORACLE_REQUIRED:'+base_id)
        clean=next(c for c in cases() if c['case_id']==base_id+'_CONTROL_CLEAN')
        initial=detect(clean['plan'],validator_for(executor,query=clean['query'],spatial_context=clean['spatial_context']),query=clean['query'])
        execution=executor.execute(clean['plan']) if initial['invalid'] is False else None
        ids=sorted(r['source_id'] for r in rows)
        passed=bool(execution and execution_success(execution) is True and returned_ids(execution)==ids)
        oracles[base_id]={'object_ids':ids,'rows':rows,'sql':ORACLE_SQL,'parameters':{'reference_geometry':geometry,'radius_m':radius},
            'source_snapshot':profile['snapshot_manifest'],'source_sha256':record['sha256'],'db_events':db.events}
        injected=next(c for c in cases() if c['case_id']==base_id+'_UNIT_TYPED_FAULT')
        invalid=detect(injected['plan'],validator_for(executor,query=injected['query'],spatial_context=injected['spatial_context']),query=injected['query'])
        controls.append({'base_scenario_id':base_id,'native_detection':initial,'execution':execution,'passed':passed,
            'injected_fault':injected['plan'],'injected_detection':invalid,
            'repair_contract_check':{'mode':'EXPLICIT_CLEAN_FIXTURE_NOT_MODEL_RECOVERY',
                'initial_fault_rejected':invalid['invalid'] is True,'repaired_plan':clean['plan'],
                'restored_object_ids':returned_ids(execution) if execution else None,
                'object_set_restored':passed,'semantic_signature_preserved':True,
                'model_recovery_success_measured':False}})
    contract={'version':VERSION,'cases':cases(),'code_vocabulary':CODE_VOCAB,'snapshot_manifest':profile['snapshot_manifest'],
        'oracle_file':'oracles.json','prepared_before_model':True,'model_calls':0,'holdout_used':False,
        'independent_base_scenarios':len(BASES),'independence_warning':'Fault mutations and paired controls share a base scenario; cluster by base, not independent row count',
        'attribute_evidence_limit':'Native compiler may not preserve/check these fields; missed detections must remain failures, never synthesized from expected codes'}
    save_new(output/'contract.json',contract);save_new(output/'oracles.json',oracles);save_new(output/'clean_verification.json',controls)
    manifest={'version':VERSION,'status':'READY_FOR_FROZEN_MODEL_RUN' if all(c['passed'] for c in controls) else 'BLOCKED_CLEAN_SOURCE_CONTROL',
        'model_calls':0,'database_writes':False,'holdout_used':False,'cases':len(contract['cases']),
        'expected_observations':3*len(contract['cases']),'nonempty_bases':len(oracles),
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    save_new(output/'manifest.json',manifest)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(prepare(a.profile,a.output),ensure_ascii=False))
