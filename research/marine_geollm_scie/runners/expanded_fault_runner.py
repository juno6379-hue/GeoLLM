"""New frozen RQ2/RQ4 run; existing 27-row cohort and raw artifacts untouched."""
import argparse
import copy
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from jsonschema import Draft202012Validator
from . import eight_fault_recovery as old
from .expanded_fault_contract import VERSION,CODE_VOCAB
from .structured_review import REVIEW_SCHEMA,REVIEW_BUDGET,review_prompt,parse_review_response
from .review_consistency import inspect_review
from .matched_branches import save_new,plan_hash
from .eight_method_runner import ROOT,ensure_identity,model_digest,public_context
from ..baselines.v2_runtime import ObservedDatabase,V2Executor,validator_for

SCHEMA=copy.deepcopy(REVIEW_SCHEMA)
SCHEMA['required'].append('detected_fault_codes')
SCHEMA['properties']['detected_fault_codes']={'type':'array','uniqueItems':True,'items':{'enum':CODE_VOCAB}}
REVIEW_VERSION='expanded_fault_review_v1'
CODE_NORMALIZATION_VERSION='native_fault_message_alias_v1'
NATIVE_MESSAGE_ALIASES={
    'reference geometry is unresolved':'MISSING_REFERENCE_GEOMETRY',
    'distance_m must be positive':'DISTANCE_NOT_POSITIVE',
    'explicit research source required':'EXPLICIT_SOURCE_REQUIRED',
}


def call_review(query,context,plan,*,model,seed):
    prompt=review_prompt(query,context,plan)+'\nUse this extended schema instead of the earlier envelope: '+json.dumps(SCHEMA)+(
        '\nInclude detected_fault_codes for INITIAL input faults only; use [] when no listed code is justified. '
        'REQUEST_ATTRIBUTE_MISMATCH means a requested valid attribute was replaced; EVIDENCE_BINDING_MISMATCH means '
        'the explicit requested source object is not the linked evidence; AMBIGUOUS_REFERENCE_SELECTION means executing '
        'one reference despite unresolved multiple candidates. Never infer an expected label from case identity. '
        'The other codes denote literal initial input contract failures. This is diagnosis, not execution approval.')
    options={'temperature':REVIEW_BUDGET['temperature'],'seed':seed,'num_predict':REVIEW_BUDGET['max_output_tokens'],'num_ctx':8192}
    payload={'model':model,'prompt':prompt,'format':SCHEMA,'stream':False,'options':options,'keep_alive':'5m'}
    start=time.perf_counter();call={'prompt':prompt,'schema':SCHEMA,'review_version':REVIEW_VERSION,'budget':REVIEW_BUDGET,
        'raw_response':None,'input_tokens':None,'output_tokens':None,'model_calls':1}
    review=None;errors=[]
    try:
        req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=REVIEW_BUDGET['timeout_seconds']) as response:raw=json.load(response)
        call.update(status='completed',raw_response=raw.get('response'),input_tokens=raw.get('prompt_eval_count'),output_tokens=raw.get('eval_count'))
        value=json.loads(raw.get('response'));Draft202012Validator(SCHEMA).validate(value)
        codes=value.pop('detected_fault_codes');review,errors=parse_review_response(json.dumps(value))
        consistency=inspect_review(plan,json.dumps(value));call['review_consistency']=consistency
        if consistency['undeclared_plan_change'] is True:review=None;errors.append('REVIEW_UNDECLARED_PLAN_CHANGE')
        if raw.get('done') is not True or raw.get('done_reason')!='stop':review=None;errors.append('GENERATION_NOT_COMPLETED')
        if review is not None:review['detected_fault_codes']=codes
    except Exception as exc:
        call.update(status='failed',error_type=type(exc).__name__);errors.append(type(exc).__name__)
    call['latency_ms']=(time.perf_counter()-start)*1000
    return call,review,errors


def raw_native_codes(detection):
    if detection.get('invalid') is None:return None
    codes=set()
    for trace in detection.get('compilation_traces',[]):codes.update(trace.get('errors',[]))
    for qec in detection.get('qecs',[]):
        for blocker in qec.get('blockers',[]):
            code=blocker.get('code') if isinstance(blocker,dict) else blocker
            if isinstance(code,str):codes.add(code)
    return sorted(codes)


def native_codes(detection):
    raw=raw_native_codes(detection)
    if raw is None:return None
    stripped=[s.split(':',1)[-1].strip() for s in raw]
    return sorted({NATIVE_MESSAGE_ALIASES.get(s,s) for s in stripped})


def target_diagnosis(invalid,codes,expected):
    if not expected:return None
    if invalid is False:return False
    if invalid is None or codes is None:return None
    return set(expected).issubset(codes)


def load_contract(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    if manifest['status']!='READY_FOR_FROZEN_MODEL_RUN':raise ValueError('CLEAN_CONTROL_GATE_FAILED')
    for name,expected in manifest['files'].items():
        if Path(name).name!=name or hashlib.sha256((folder/name).read_bytes()).hexdigest()!=expected:raise ValueError('CONTRACT_HASH_MISMATCH')
    contract=json.loads((folder/'contract.json').read_text(encoding='utf8'))
    oracles=json.loads((folder/'oracles.json').read_text(encoding='utf8'))
    if contract['version']!=VERSION:raise ValueError('CONTRACT_VERSION_MISMATCH')
    for case in contract['cases']:
        if plan_hash(case['plan'])!=case['initial_plan_sha256'] or plan_hash(case['clean_plan'])!=case['clean_plan_sha256']:raise ValueError('PLAN_HASH_MISMATCH')
    return contract,oracles,manifest


def snapshot_bridge(old_pin,new_pin):
    """New code freeze may have a new manifest; all six data identities must agree."""
    inventories=[]
    for pin in (old_pin,new_pin):
        path=Path(pin['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=pin['sha256']:raise ValueError('SNAPSHOT_MANIFEST_CHANGED')
        value=json.loads(path.read_text(encoding='utf8'))
        inventories.append({r['relation']:{k:r[k] for k in ('sha256','rows','columns')} for r in value['relations']})
    if len(inventories[0])!=6 or inventories[0]!=inventories[1]:raise ValueError('SNAPSHOT_DATA_LINEAGE_MISMATCH')
    return {'contract_snapshot':old_pin,'execution_snapshot':new_pin,'six_data_relations_identical':True,
            'scope':'data-only lineage bridge; code/model identity still checked by ensure_identity'}


def run(contract_dir,profile_path,benchmark,output,*,execute=False):
    contract,oracles,pin=load_contract(contract_dir)
    profile=json.loads(Path(profile_path).read_text(encoding='utf8'));ensure_identity(profile,Path(benchmark))
    bridge=snapshot_bridge(contract['snapshot_manifest'],profile['snapshot_manifest'])
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    manifest={'version':VERSION,'status':'PREPARED','rows':0,'expected_rows':len(contract['cases'])*3,
        'contract_manifest_sha256':hashlib.sha256((Path(contract_dir)/'manifest.json').read_bytes()).hexdigest(),
        'execution_identity':profile['execution_identity'],'snapshot_bridge':bridge,'scientific_completion':False,'holdout_used':False}
    def state():(output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    state()
    if not execute:return manifest
    model_digest(profile)
    executor=V2Executor(ObservedDatabase(),catalogue=ROOT/profile['catalogue']['path'],catalogue_sha256=profile['catalogue']['sha256'],
        anchors=profile.get('anchors',[]),coverage=profile['coverage'],reference_geometries=profile.get('reference_geometries',{}),snapshot_manifest=profile['snapshot_manifest'])
    for case in contract['cases']:
        ensure_identity(profile,Path(benchmark));model_digest(profile)
        directory=output/case['case_id'];directory.mkdir();save_new(directory/'input.json',case)
        validator=validator_for(executor,query=case['query'],spatial_context=case['spatial_context'])
        detection=old.detect(case['plan'],validator,query=case['query'])
        context=public_context(profile,{'query':case['query'],'spatial_context':case['spatial_context']})
        call,review,errors=call_review(case['query'],context,case['plan'],model=profile['model'],seed=profile.get('seed',42))
        save_new(directory/'review.json',{'call':call,'review':review,'errors':errors})
        llm_invalid=review.get('invalid') if review else None
        llm_codes=review.get('detected_fault_codes') if review else None;det_codes=native_codes(detection)
        ids=(oracles.get(case.get('oracle_base_id')) or {}).get('object_ids')
        scope=old.recovery_oracle_scope(ids)
        for method,invalid,codes in [('B4',llm_invalid,llm_codes),('P0',detection['invalid'],det_codes),
            ('H',old.hybrid_invalid(llm_invalid,detection['invalid']),sorted(set(llm_codes or [])|set(det_codes or [])) if llm_codes is not None and det_codes is not None else None)]:
            row={k:case[k] for k in ('case_id','base_scenario_id','pair_id','pair_role','error_type','expected_invalid','expected_fault_codes','fault_subtype','initial_plan_sha256',
                                    'expected_behavior','execution_eligible','binary_diagnosis_eligible','false_block_eligible')}
            row.update(method=method,predicted_invalid=invalid,detected_fault_codes=codes,
                target_fault_code_detected=target_diagnosis(invalid,codes,case['expected_fault_codes']),
                detector_stage='INITIAL_BEFORE_REPAIR',validator_detection=detection if method!='B4' else None,
                raw_native_invalid=detection['invalid'] if method!='B4' else None,
                raw_native_fault_codes=raw_native_codes(detection) if method!='B4' else None,
                fault_code_normalization_version=CODE_NORMALIZATION_VERSION,
                safe_abstention_observed=None,
                safe_abstention_measurement_reason='INITIAL_VERDICT_IS_NOT_END_TO_END_BEHAVIOR' if not case['binary_diagnosis_eligible'] else None,
                review_artifact_sha256=hashlib.sha256((directory/'review.json').read_bytes()).hexdigest(),
                recovery_attempted=False,recovery_success=None,semantic_preservation=None,spatial_correct=None,joint_success=None,
                **old.recovery_eligibility(case,method,scope))
            forbidden=bool(case.get('forbidden_recovery') and method in ('B4','H'))
            proposal=(review or {}).get('plan')
            row.update(forbidden_recovery_eligible=forbidden,
                forbidden_recovery_proposed=(bool(proposal.get('tool_calls')) or proposal.get('action')=='search')
                    if forbidden and isinstance(proposal,dict) else None,
                proposed_action=proposal.get('action') if isinstance(proposal,dict) else None,
                human_escalation_observed=None,
                human_escalation_reason='NO_HUMAN_REVIEW_DISPATCH_EVENT_IN_THIS_RUNNER')
            if row['recovery_eligible'] and review:
                revised=review['plan'];row.update(recovery_attempted=True,recovered_plan=revised,
                    semantic_preservation=old.semantic_signature(revised)==old.semantic_signature(case['clean_plan']) and revised.get('evidence_refs')==case['clean_plan'].get('evidence_refs'))
                post=old.detect(revised,validator,query=case['query']) if method=='H' else None
                row['post_recovery_validation']=post
                if post is None or post['invalid'] is False:
                    execution=executor.execute(revised);row['execution']=execution
                    row['recovery_success']=old.execution_success(execution)
                    actual=old.returned_ids(execution);row['spatial_correct']=actual==ids if actual is not None else None
                else:row['recovery_success']=False if post['invalid'] is True else None
                row['joint_success']=old.joint_recovery(row['recovery_success'],row['semantic_preservation'],row['spatial_correct'])
            row['recovery_attempt_count']=1 if row['recovery_attempted'] else 0
            row['first_repair_joint_success']=row['joint_success'] if row['recovery_attempted'] else None
            row['semantic_drift']=(not row['semantic_preservation']) if type(row['semantic_preservation']) is bool else None
            row['costs']={'model_calls':0 if method=='P0' else 1,'review_shared_B4_H':True,
                'input_tokens':0 if method=='P0' else call.get('input_tokens'),'output_tokens':0 if method=='P0' else call.get('output_tokens'),
                'review_latency_ms':0 if method=='P0' else call.get('latency_ms'),
                'tool_calls':(row.get('execution') or {}).get('tool_calls_attempted',0)}
            save_new(directory/(method+'.json'),row)
            with (output/'rows.jsonl').open('a',encoding='utf8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            manifest['rows']+=1
        manifest['status']='RUNNING';state()
    ensure_identity(profile,Path(benchmark));model_digest(profile)
    manifest.update(status='COMPLETED_CONTROLLED_DIAGNOSTICS',rows_sha256=hashlib.sha256((output/'rows.jsonl').read_bytes()).hexdigest());state()
    return manifest


def report(run_dir,contract_dir,output):
    """Verify raw rows and expose binary/code recall with fixed denominators."""
    from ..evaluation.v2_fault_results import summarize_faults
    from ..evaluation.rq_metrics import rate
    from .report_eight_faults import recovery_measurement_summary
    from ..evaluation.expanded_fault_metrics import recovery_metrics,summarize_paired
    contract,_,_=load_contract(contract_dir);run_dir=Path(run_dir);output=Path(output)
    manifest=json.loads((run_dir/'manifest.json').read_text(encoding='utf8'))
    rows_path=run_dir/'rows.jsonl'
    if manifest['status']!='COMPLETED_CONTROLLED_DIAGNOSTICS' or hashlib.sha256(rows_path.read_bytes()).hexdigest()!=manifest['rows_sha256']:
        raise ValueError('INCOMPLETE_OR_CHANGED_RUN')
    if hashlib.sha256((Path(contract_dir)/'manifest.json').read_bytes()).hexdigest()!=manifest['contract_manifest_sha256']:
        raise ValueError('CONTRACT_PIN_MISMATCH')
    rows=[json.loads(line) for line in rows_path.read_text(encoding='utf8').splitlines() if line.strip()]
    expected={(c['case_id'],m) for c in contract['cases'] for m in ('B4','P0','H')}
    if len(rows)!=len(expected) or {(r['case_id'],r['method']) for r in rows}!=expected:raise ValueError('MISSING_OR_DUPLICATE_ROWS')
    cases={c['case_id']:c for c in contract['cases']}
    for row in rows:
        case=cases[row['case_id']];directory=run_dir/row['case_id']
        if json.loads((directory/(row['method']+'.json')).read_text(encoding='utf8'))!=row:raise ValueError('ROW_CHANGED')
        if json.loads((directory/'input.json').read_text(encoding='utf8'))!=case:raise ValueError('INPUT_CHANGED')
        if hashlib.sha256((directory/'review.json').read_bytes()).hexdigest()!=row['review_artifact_sha256']:raise ValueError('REVIEW_CHANGED')
        if row['expected_fault_codes']!=case['expected_fault_codes'] or row['expected_invalid']!=case['expected_invalid']:raise ValueError('LABEL_CHANGED')
        if any(row.get(k)!=case[k] for k in ('expected_behavior','execution_eligible','binary_diagnosis_eligible','false_block_eligible')):raise ValueError('BEHAVIOR_DENOMINATOR_CHANGED')
        if row['target_fault_code_detected']!=target_diagnosis(row['predicted_invalid'],row['detected_fault_codes'],case['expected_fault_codes']):raise ValueError('TARGET_CODE_SCORE_CHANGED')
    diagnostic_rows=[r for r in rows if r['binary_diagnosis_eligible']]
    summary=summarize_faults(diagnostic_rows);summary['rq4_recovery']=recovery_measurement_summary(rows)
    summary['raw_observation_rows']=len(rows)
    summary['binary_diagnostic_rows']=len(diagnostic_rows)
    summary['safe_abstention']={'status':'UNMEASURED_END_TO_END_BEHAVIOR',
        'expected_cases':sorted({r['case_id'] for r in rows if not r['binary_diagnosis_eligible']}),
        'rows_excluded_from_binary_and_false_block':len(rows)-len(diagnostic_rows),
        'value':None,'reason':'A native not-ready verdict alone is not invalid intent or proof of correct clarification; raw native verdict retained'}
    summary['rq2_target_codes']={}
    summary['rq2_paired_cluster_comparison']=summarize_paired(rows)
    summary['rq4_detailed_metrics']={}
    for method in ('B4','P0','H'):
        group=[r for r in rows if r['method']==method]
        details=recovery_metrics(group)
        summary['rq4_detailed_metrics'][method]=details
        summary['overall_by_method'][method]['forbidden_recovery_proposals']=details['forbidden_recovery']['complete_positive_count']
        for error_type in {r['error_type'] for r in group}:
            key=method+'|'+error_type
            if key in summary['by_method_error_type']:
                detail=recovery_metrics([r for r in group if r['error_type']==error_type])
                summary['by_method_error_type'][key]['forbidden_recovery_proposals']=detail['forbidden_recovery']['complete_positive_count']
                summary['by_method_error_type'][key]['explicit_recovery_measurement']=detail
        invalid=[r for r in group if r['expected_invalid']]
        clean=[r for r in group if r['false_block_eligible']]
        # Exact repeated clean inputs count once in the overall availability metric.
        unique_clean={}
        for row in clean:
            key=plan_hash({'query':cases[row['case_id']]['query'],'context':cases[row['case_id']]['spatial_context'],'plan':cases[row['case_id']]['plan']})
            unique_clean.setdefault(key,[]).append(row['predicted_invalid'])
        unique_verdicts=[v[0] if all(x is v[0] for x in v) else None for v in unique_clean.values()]
        bytype={}
        for kind in sorted({r['error_type'] for r in invalid}):
            subset=[r for r in invalid if r['error_type']==kind]
            bytype[kind]={'binary_recall':rate([r['predicted_invalid'] for r in subset]),
                'target_fault_code_recall':rate([r['target_fault_code_detected'] for r in subset]),
                'independent_bases':len({r['base_scenario_id'] for r in subset})}
        summary['rq2_target_codes'][method]={'binary_recall':rate([r['predicted_invalid'] for r in invalid]),
            'target_fault_code_recall':rate([r['target_fault_code_detected'] for r in invalid]),
            'paired_control_false_block':rate([r['predicted_invalid'] for r in clean]),
            'unique_clean_false_block':rate(unique_verdicts),
            'duplicate_clean_disagreements':sum(any(x is not v[0] for x in v) for v in unique_clean.values()),
            'by_error_type':bytype,'independent_bases':len({r['base_scenario_id'] for r in group})}
    summary['scope']='Development controlled faults; duplicated controls retained for pairing, clustered by 3 independent source bases; no general taxonomy or human accuracy claim'
    output.mkdir(parents=True,exist_ok=False);save_new(output/'summary.json',summary)
    lines=['# RQ2·RQ4 확장 오류 대조','',summary['scope'],'',
        '|방법|오류 수|이진 검출|목표 코드 검출|정상 오차단(중복제거)|','|---|---:|---|---|---|']
    for method,values in summary['rq2_target_codes'].items():
        lines.append(f"|{method}|{values['binary_recall']['denominator']}|{values['binary_recall']['value']}|{values['target_fault_code_recall']['value']}|{values['unique_clean_false_block']['value']}|")
    from .report_eight_faults import recovery_measurement_lines
    lines+=recovery_measurement_lines(summary['rq4_recovery'])
    lines+=['','## Paired source-base cluster 비교','',
        '|비교|측정|관측 pair/전체|cluster|차이|95% CI|','|---|---|---:|---:|---|---|']
    for method,metrics in summary['rq2_paired_cluster_comparison'].items():
        for name,value in metrics.items():
            lines.append(f"|{method}−B4|{name}|{value['measured_pairs']}/{value['paired_cases']}|{value['independent_base_clusters']}|{value['paired_delta']}|{value['ci95']}|")
    lines+=['','3개 source base의 개발용 기술통계 CI이며 오류유형 전체로 일반화하지 않습니다. 누락 pair가 하나라도 있으면 전체 차이와 CI는 null입니다.',
        '', '## 최초 복구·의미 변형·추가 검토','',
        '|방법|복구시도|최초 공동성공|의미 변형|금지된 복구 제안 측정/분모|금지 제안 관측 수|인간 escalation|',
        '|---|---:|---|---|---:|---:|---|']
    for method,value in summary['rq4_detailed_metrics'].items():
        denied=value['forbidden_recovery']
        lines.append(f"|{method}|{value['attempted']}|{value['first_repair_joint_success_given_attempt']['value']}|{value['semantic_drift_given_attempt']['value']}|{denied['measured']}/{denied['denominator']}|{denied['complete_positive_count']}|{value['human_escalation']['value']}|")
    lines+=['','복구는 1회 bounded 조건이며 최초 공동성공은 실행·object 복원·명시 task 의미 보존을 모두 요구합니다. 모델 검토 실패의 금지 제안 여부는 미측정이고, 인간 검토 dispatch 이벤트가 없으므로 escalation은 null입니다. clarification 제안을 인간 검토로 세지 않습니다.']
    lines+=['','정상 clarification 6사례×3방법은 실행 가능한 정상 요청의 False Block 분모에서 제외합니다. 초기 native not-ready 판정은 원문에 보존하지만 올바른 추가입력 행동을 입증하지 않으므로 Safe Abstention은 미측정(null)입니다.']
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    save_new(output/'manifest.json',{'run_manifest_sha256':hashlib.sha256((run_dir/'manifest.json').read_bytes()).hexdigest(),
        'rows_sha256':manifest['rows_sha256'],'contract_manifest_sha256':manifest['contract_manifest_sha256'],
        'source_files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),Path(__file__).parents[1]/'evaluation/expanded_fault_metrics.py')},'scientific_completion':False})
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract-dir',required=True);p.add_argument('--profile')
    p.add_argument('--benchmark');p.add_argument('--output',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--report-run')
    a=p.parse_args()
    if a.report_run:result=report(a.report_run,a.contract_dir,a.output)
    else:
        if not a.profile or not a.benchmark:p.error('--profile and --benchmark required for run')
        result=run(a.contract_dir,a.profile,a.benchmark,a.output,execute=a.execute)
    print(json.dumps({'status':result.get('status'),'rows':result.get('rows')},ensure_ascii=False))
