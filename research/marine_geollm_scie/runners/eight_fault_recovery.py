"""Matched controlled-fault diagnostics using real research adapters.

No model is called without --execute. Independent source SQL is never put in
the reviewer prompt. Controlled labels are protocol labels, not expert GOLD.
"""
import argparse
import copy
import json
from pathlib import Path
import time

from .eight_method_runner import ROOT, ensure_identity, model_digest, public_context, digest
from .matched_branches import save_new, plan_hash
from .structured_review import (call_review, parse_review_response, REVIEW_SCHEMA,
                                REVIEW_VERSION, REVIEW_BUDGET, SCHEMA_SHA256)
from ..baselines.lossless_qec import compile_plan, validate_without_repair, explicit_distance
from ..baselines.v2_runtime import ObservedDatabase, V2Executor, validator_for
from services.orchestrator.execution_validator import is_execution_authorized
import jsonschema


QUERY = '주어진 기준점에서 반경 1000m 이내 Wreck를 찾아줘. 입력 좌표의 CRS는 EPSG:4326이다.'
CONTEXT = {'geometry':'POINT(129.05 35.1)','crs':'EPSG:4326'}

def clean_plan():
    args={'source':'s101','feature_types':['Wreck'],'reference_geometry':CONTEXT['geometry'],
          'crs':'EPSG:4326','radius_m':1000,'relation':'dwithin','analysis_type':'feature_search_by_radius'}
    return {'action':'search','intent':'spatial_search','target_features':['Wreck'],'attributes':[],
            'spatial_relation':'dwithin','location_text':None,'radius_m':1000,'crs':'EPSG:4326',
            'tool_calls':[{'tool_id':'spatial.query','arguments':args}], 'evidence_refs':[],
            'missing_inputs':[],'answer':''}


def cohort():
    specs=[('CONTROL','control',None,None,False,False),
           ('UNIT_TYPED','unit','radius_m','1 km',True,True),
           ('MISSING_GEOMETRY','geometry','reference_geometry',None,True,False),
           ('WRONG_CRS','crs','crs','EPSG:3857',True,True),
           ('UNKNOWN_SOURCE','source','source','unregistered_source',True,False),
           ('NEGATIVE_RADIUS','numeric','radius_m',-1000,True,True),
           ('WRONG_FEATURE','wrong_feature','feature_types',['Obstruction'],True,True),
           ('SEMANTIC_EXPANSION','semantic_expansion','feature_types',['Wreck','Obstruction'],True,True),
           ('WRONG_RADIUS','semantic_distance','radius_m',5000,True,True)]
    rows=[]
    for name,kind,key,value,invalid,recoverable in specs:
        plan=clean_plan(); context=copy.deepcopy(CONTEXT)
        if key:
            if value is None:
                plan['tool_calls'][0]['arguments'].pop(key)
                context.pop('geometry',None)  # No geometry is supplied to the reviewer.
            else:plan['tool_calls'][0]['arguments'][key]=value
        rows.append({'case_id':'FAULT_V2_'+name,'error_type':kind,'query':QUERY,'spatial_context':context,
                     'plan':plan,'initial_plan_sha256':plan_hash(plan),'expected_invalid':invalid,
                     'recovery_eligible':recoverable,'label_basis':'CONTROLLED_PROTOCOL_NOT_INDEPENDENT_EXPERT',
                     'forbidden_recovery':not recoverable and invalid})
    return rows


def semantic_signature(plan):
    """Fixed explicit task fields only; not a full human meaning judgement."""
    if not isinstance(plan,dict) or plan.get('action')!='search':return None
    calls=plan.get('tool_calls')
    if not isinstance(calls,list) or len(calls)!=1:return None
    call=calls[0]; args=call.get('arguments') or {}
    permitted={'source','feature_types','target_features','reference_geometry','geometry_ref',
               'crs','radius_m','distance_m','distance','relation','analysis_type'}
    if set(args)-permitted:return None  # Added filters/limits must not hide semantic drift.
    if len(set(args)&{'radius_m','distance_m','distance'})!=1:return None
    if 'feature_types' in args and 'target_features' in args:return None
    distance=args.get('radius_m',args.get('distance_m',args.get('distance')))
    if isinstance(distance,(str,dict)):
        try:distance=explicit_distance(distance)
        except ValueError:return None
    top_distance=plan.get('radius_m')
    if isinstance(top_distance,(str,dict)):
        try:top_distance=explicit_distance(top_distance)
        except ValueError:return None
    return {'tool':call.get('tool_id'),'source':args.get('source'),'crs':args.get('crs'),
            'geometry':args.get('reference_geometry'),'geometry_ref':args.get('geometry_ref'),
            'features':args.get('feature_types',args.get('target_features')),
            'relation':args.get('relation'),'distance_m':distance,
            'analysis_type':args.get('analysis_type'),
            'top_target_features':plan.get('target_features'),'top_attributes':plan.get('attributes'),
            'top_spatial_relation':plan.get('spatial_relation'),'top_crs':plan.get('crs'),
            'top_distance_m':top_distance}


def detect(plan, validator, query=QUERY):
    started=time.perf_counter()
    receipt={'invalid':None,'compiler_rejected':False,'native_validator_called':False,'qecs':[]}
    try:
        compiled=compile_plan(plan,query=query)
        receipt['compilation_traces']=[c['trace'] for c in compiled]
        if any(not c['compilation_valid'] for c in compiled):
            receipt.update(invalid=True,compiler_rejected=True)
            return receipt
        checked=[]
        for item in compiled:
            receipt['native_validator_called']=True
            checked.append(validate_without_repair(item,validator))
        receipt['qecs']=[x.model_dump(mode='json') for x in checked]
        receipt['invalid']=not checked or not all(is_execution_authorized(x) for x in checked)
    except Exception as exc:
        receipt['error_type']=type(exc).__name__  # Environment failure is not a detection success.
    finally:
        receipt['latency_ms']=(time.perf_counter()-started)*1000
    return receipt


def hybrid_invalid(review_invalid, validator_invalid):
    if review_invalid is True or validator_invalid is True:return True
    if review_invalid is False and validator_invalid is False:return False
    return None


def execution_success(execution):
    observed=execution.get('execution_observation') or {}
    if observed.get('observation_complete') is not True:return None
    if observed.get('execution_started') is False:return False
    return observed.get('execution_succeeded')


def returned_ids(execution):
    receipts=execution.get('receipts',[])
    ids=[];spatial_seen=False
    for item in receipts:
        if item.get('tool_id')!='spatial.query':continue
        spatial_seen=True
        result=item.get('result') or item.get('output') or {}
        if item.get('status')!='TOOL_RETURNED':return None
        ids.extend(str(row['source_id']) for row in result.get('rows',[]) if 'source_id' in row)
    return sorted(ids) if spatial_seen else None


def joint_recovery(success, preservation, spatial):
    values=(success,preservation,spatial)
    if any(v is False for v in values):return False
    return True if all(v is True for v in values) else None


def run(output, profile_path, benchmark, *, execute=False):
    output=Path(output);profile_path=Path(profile_path);benchmark=Path(benchmark)
    profile=json.loads(profile_path.read_text(encoding='utf-8'))
    ensure_identity(profile,benchmark)
    output.mkdir(parents=True,exist_ok=False)
    cases=cohort()
    contract={'version':'matched_fault_v2_v3','benchmark_sha256':profile['benchmark_sha256'],
              'execution_identity':profile['execution_identity'],'cases':cases,
              'review_protocol':{'version':REVIEW_VERSION,'schema_sha256':SCHEMA_SHA256},
              'recovery_budget':dict(REVIEW_BUDGET,model_calls_per_fault=1),
              'hybrid_detection':'OR of initial-plan reviewer and initial native Validator; components retained',
              'hybrid_recovery':'same reviewer repair followed by native Validator',
              'permission_fault':'NOT_ELIGIBLE: no isolated denied-role source configured',
              'unit_fault':'radius_m string violates typed tool contract; numeric unit-equivalent meaning retained',
              'semantic_scope':'fixed explicit task tuple; not independent expert meaning judgement',
              'policy':'missing geometry/source cannot be filled; no alternate dataset/tool; originals immutable'}
    save_new(output/'fault_contract.json',contract)
    manifest={'status':'PREPARED','fault_contract_sha256':digest(output/'fault_contract.json'),
              'benchmark_sha256':profile['benchmark_sha256'],'profile_sha256':digest(profile_path),
              'model_experiment_complete':False,'independent_expert_review':False,'rows':0,
              'expected_rows':len(cases)*3,'execution_identity':profile['execution_identity']}
    def state():
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    state()
    if not execute:return manifest
    model_digest(profile)
    executor=V2Executor(ObservedDatabase(),catalogue=ROOT/profile['catalogue']['path'],
        catalogue_sha256=profile['catalogue']['sha256'],anchors=profile.get('anchors',[]),
        coverage=profile.get('coverage',{}),reference_geometries=profile.get('reference_geometries',{}))
    validator=validator_for(executor,query=QUERY,spatial_context=CONTEXT)
    # Independent SQL predicate (distance <= radius), not model or executor output.
    oracle=executor.db.query("""SELECT feature_instance_id::text source_id FROM projection.s101_feature_current
      WHERE feature_type_name='Wreck' AND geometry IS NOT NULL AND ST_IsValid(geometry)
      AND ST_Distance(geometry::geography,ST_GeomFromText('POINT(129.05 35.1)',4326)::geography)<=1000
      ORDER BY feature_instance_id""",{})
    oracle_ids=sorted(str(x['source_id']) for x in oracle)
    save_new(output/'independent_oracle.json',{'source_snapshot_sha256':profile['execution_identity']['source_snapshot_sha256'],
        'source_sha256':profile.get('coverage',{}).get('s101',{}).get('source_sha256'),
        'object_ids':oracle_ids,'scope':'same source PostGIS independent SQL, not independent engine/human review'})
    manifest['independent_oracle_sha256']=digest(output/'independent_oracle.json')
    control=executor.execute(clean_plan());save_new(output/'clean_source_execution.json',control)
    if execution_success(control) is not True or returned_ids(control)!=oracle_ids:
        manifest['status']='STOPPED_CONTROL_ORACLE_MISMATCH';state();return manifest
    manifest['status']='RUNNING';state()
    for case in cases:
        validator=validator_for(executor,query=case['query'],spatial_context=case['spatial_context'])
        ensure_identity(profile,benchmark);model_digest(profile)
        directory=output/case['case_id'];directory.mkdir()
        save_new(directory/'initial_plan.json',case)
        detection=detect(case['plan'],validator)
        packet={'case_id':case['case_id'],'query':case['query'],'spatial_context':case['spatial_context']}
        call,review,errors=call_review(case['query'],public_context(profile,packet),case['plan'],
            model=profile['model'],seed=profile.get('seed',42))
        save_new(directory/'review.json',{'call':call,'review':review,'errors':errors})
        review_invalid=review.get('invalid') if review else None
        for method,invalid in [('B4',review_invalid),('P0',detection['invalid']),
                               ('H',hybrid_invalid(review_invalid,detection['invalid']))]:
            row={'case_id':case['case_id'],'error_type':case['error_type'],'method':method,
                'initial_plan_sha256':case['initial_plan_sha256'],'expected_invalid':case['expected_invalid'],
                'predicted_invalid':invalid,'review_invalid':review_invalid,'validator_detection':detection,
                'raw_review_invalid':(call.get('review_consistency') or {}).get('raw_initial_invalid'),
                'review_usable':review is not None,
                'review_contract_errors':errors,
                'review_consistency':call.get('review_consistency'),
                'detector_scope':'BEFORE_COMMON_EXECUTION_FLOOR','recovery_attempted':False,
                'recovery_eligible':case['recovery_eligible'] and method in ('B4','H'),
                'recovery_success':None,'semantic_preservation':None,'spatial_correct':None,'joint_success':None}
            row['costs']={'review_shared_B4_H':True,'input_tokens':call.get('input_tokens') if method!='P0' else 0,
                          'output_tokens':call.get('output_tokens') if method!='P0' else 0,
                          'review_latency_ms':call.get('latency_ms') if method!='P0' else 0,
                          'initial_validator_latency_ms':detection['latency_ms'] if method!='B4' else 0,
                          'post_recovery_validator_latency_ms':0,'execution_latency_ms':0,
                          'model_calls':1 if method!='P0' else 0,'tool_calls':0}
            # P0 is validation only: no additional reasoning/repair is introduced.
            if method in ('B4','H') and case['recovery_eligible'] and review:
                revised=review['plan'];row['recovery_attempted']=True;row['recovered_plan']=revised
                row['semantic_preservation']=semantic_signature(revised)==semantic_signature(clean_plan())
                post=detect(revised,validator) if method=='H' else None
                row['post_recovery_validation']=post
                if post:
                    row['costs']['post_recovery_validator_latency_ms']=post['latency_ms']
                if post is None or post['invalid'] is False:
                    execution=executor.execute(revised);row['execution']=execution
                    row['costs']['tool_calls']=execution.get('tool_calls_attempted')
                    row['costs']['execution_latency_ms']=execution.get('latency_ms')
                    row['recovery_success']=execution_success(execution)
                    ids=returned_ids(execution)
                    row['spatial_correct']=ids==oracle_ids if ids is not None else None
                else:row['recovery_success']=False if post['invalid'] is True else None
                row['joint_success']=joint_recovery(row['recovery_success'],row['semantic_preservation'],row['spatial_correct'])
            elif case['forbidden_recovery']:
                row['forbidden_recovery_proposed']=bool(method in ('B4','H') and review and review['plan'].get('action')=='search' and review['plan'].get('tool_calls'))
            row['label_basis']=case['label_basis']
            timings=[row['costs'].get(k) for k in ('review_latency_ms','initial_validator_latency_ms',
                'post_recovery_validator_latency_ms','execution_latency_ms')]
            row['costs']['standalone_latency_ms']=sum(timings) if all(type(x) in (int,float) for x in timings) else None
            row['fault_contract_sha256']=manifest['fault_contract_sha256']
            row['independent_oracle_sha256']=manifest['independent_oracle_sha256']
            row['review_artifact_sha256']=digest(directory/'review.json')
            row['benchmark_sha256']=profile['benchmark_sha256']
            row['execution_identity']=profile['execution_identity']
            save_new(directory/(method+'.json'),row)
            with (output/'rows.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            manifest['rows']+=1
        state();print(f"fault {case['case_id']} {manifest['rows']}/{len(cases)*3}",flush=True)
    ensure_identity(profile,benchmark);model_digest(profile)
    manifest.update(status='COMPLETED_CONTROLLED_DIAGNOSTICS',model_experiment_complete=True,
                    rows_sha256=digest(output/'rows.jsonl'),scientific_completion=False)
    state();return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--profile',required=True)
    p.add_argument('--benchmark',required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args();print(json.dumps(run(a.output,a.profile,a.benchmark,execute=a.execute)))
