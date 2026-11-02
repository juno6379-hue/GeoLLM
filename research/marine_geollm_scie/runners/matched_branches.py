"""Paired B3/B4/P0/H orchestration; adapters must be validated separately.

This module does not supply a replacement validator, executor, or GOLD. It
freezes the common candidate and reviewer output, isolates branches, and keeps
failed branches. It never interprets callback invocation as GIS execution.
"""
import copy
import hashlib
import json
import time
from pathlib import Path


def plan_hash(plan):
    return hashlib.sha256(json.dumps(plan,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()


def save_new(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)


def freeze_initial(path, *, case_id, repeat, plan, generation):
    artifact={'case_id':case_id,'repeat':repeat,'plan':copy.deepcopy(plan),
              'plan_hash':plan_hash(plan),'generation':copy.deepcopy(generation)}
    save_new(Path(path),artifact)
    return artifact


def load_frozen(path):
    artifact=json.loads(Path(path).read_text(encoding='utf-8'))
    if plan_hash(artifact['plan'])!=artifact['plan_hash']:
        raise ValueError('Frozen initial plan was modified')
    return artifact


def run_branches(initial_path, output, *, reviewer, validator, executor, query=None, sql_events=None):
    """Reviewer returns {plan, call}; validator accepts and returns actual QEC.

    Caller must supply research-isolated, source-pinned adapters. No production
    HTTP/DB dispatch is selected here. Authorization uses the production gate.
    B4 and H also share one frozen review, to isolate the validator's effect.
    """
    from services.orchestrator.execution_validator import is_execution_authorized
    from research.marine_geollm_scie.baselines.lossless_qec import compile_plan,validate_without_repair
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    original=load_frozen(initial_path)
    root_hash=original['plan_hash']
    review=None;review_error=None;review_started=time.perf_counter()
    try:
        review=reviewer(copy.deepcopy(original['plan']))
        save_new(out/'reviewed_plan.json',{'initial_plan_hash':root_hash,
            'reviewed_plan_hash':plan_hash(review['plan']),**review})
    except Exception as exc:
        review_error=type(exc).__name__
        save_new(out/'review_failure.json',{'initial_plan_hash':root_hash,'error_type':review_error})
    review_latency_ms=(time.perf_counter()-review_started)*1000
    rows=[]
    for method in ('B3','B4','P0','H'):
        branch_started=time.perf_counter()
        sql_start=len(sql_events()) if sql_events is not None else None
        row={'method':method,'case_id':original['case_id'],'repeat':original['repeat'],
             'initial_plan_hash':root_hash,'execution_callback_invoked':False,
             'execution_observation':None,'status':'STARTED'}
        try:
            if method in ('B4','H') and review_error:
                row.update(status='REVIEW_ERROR',error_type=review_error)
            else:
                candidate=copy.deepcopy(review['plan'] if method in ('B4','H') else original['plan'])
                row['candidate_plan_hash']=plan_hash(candidate)
                row['candidate_plan']=copy.deepcopy(candidate)
                allowed=True
                if method in ('P0','H'):
                    compiled=compile_plan(copy.deepcopy(candidate),query=query,
                                          request_id=f"{original['case_id']}:{original['repeat']}:{method}")
                    row['compilation_traces']=[item['trace'] for item in compiled]
                    validated=[validate_without_repair(item,validator) for item in compiled]
                    row['validated_qecs']=[q.model_dump(mode='json') for q in validated]
                    allowed=bool(validated) and all(is_execution_authorized(q) for q in validated)
                    row['composite_gate_policy']='ALL_TASK_QECS_REQUIRED; no plan repair or partial plan rewriting'
                    row['validator_authorized']=allowed
                if allowed:
                    row['execution_callback_invoked']=True
                    row['execution']=executor(copy.deepcopy(candidate))
                    row['execution_observation']=row['execution'].get('execution_observation')
                    row['status']='EXECUTOR_RETURNED'
                else:
                    row['status']='VALIDATOR_BLOCKED'
        except Exception as exc:
            row.update(status='BRANCH_ERROR',error_type=type(exc).__name__)
        if load_frozen(initial_path)['plan_hash']!=root_hash:
            raise ValueError('Frozen initial artifact changed during branching')
        row['branch_latency_ms']=(time.perf_counter()-branch_started)*1000
        row['shared_review_latency_ms']=review_latency_ms
        row['all_sql_events']=copy.deepcopy(sql_events()[sql_start:]) if sql_events is not None else None
        row['sql_telemetry_complete']=sql_events is not None
        save_new(out/(method+'.json'),row)
        rows.append(row)
    save_new(out/'manifest.json',{'initial_plan_hash':root_hash,
        'methods':[r['method'] for r in rows],'shared_initial_generation':True,'shared_B4_H_review':True,
        'model_comparison_complete':False,'scope':'BRANCH_CONTROLLER_ONLY; adapters and actual execution traces require separate validation'})
    return rows
