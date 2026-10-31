"""Common post-run checks. No GOLD is passed to model/tool generation.

Accept only adapter-normalized emitted answers and independently recorded
execution observations. Missing execution logs never become false.
"""
import math


def distances_match(observed, expected, tolerance):
    if not isinstance(observed,dict) or set(observed)!=set(expected):
        return False
    for target,values in expected.items():
        if not isinstance(observed[target],dict): return False
        for key,value in values.items():
            actual=observed[target].get(key)
            if value is None:
                if actual is not None: return False
            elif type(actual) not in (float,int) or not math.isfinite(actual) or abs(actual-value)>tolerance:
                return False
    return True


def all_known(checks):
    values=list(checks.values())
    if any(v is False for v in values):
        return False
    return True if values and all(v is True for v in values) else None


def score(contract, answer, trace):
    stratum=contract['evaluation_stratum']; checks={}
    result={'case_id':contract['case_id'],'stratum':stratum,'checks':checks,
            'spatial_correctness':None,'safe_abstention_correct':None,
            'execution_correctness_gap_applicable':False,'semantic_human_accuracy':None}
    complete=trace.get('observation_complete') is True
    attempted=trace.get('execution_attempted')
    no_attempt=False if attempted is True else True if complete and attempted is False else None
    source_hashes=set(contract.get('coverage_reference',{}).get('source_relation_sha256',{}).values())
    if stratum=='OUT_OF_COVERAGE_SAFE_ABSTENTION':
        expected=contract['expected_spatial_behavior']
        tasks=answer.get('spatial_tasks',{})
        for target in expected['per_target']:
            task=tasks.get(target,{})
            checks[target+'_blocked']=task.get('status') in expected['accepted_states']
            checks[target+'_no_result_claim']=task.get('object_ids') is None and task.get('count') is None
        # Explicit source identity + scope statement, not merely the word BLOCKED.
        disclosure=answer.get('source_coverage',{})
        checks['coverage_disclosed']=bool(disclosure.get('source_snapshot_sha256') in source_hashes and
            disclosure.get('requested_extent_covered') is False and disclosure.get('explanation'))
        checks['no_spatial_execution']=no_attempt
        result['safe_abstention_correct']=all_known(checks)
        result['full_spatial_success']=False
    elif stratum=='MISSING_REQUIRED_INPUT':
        checks['needs_user_input']=answer.get('status')=='NEEDS_USER_INPUT'
        checks['missing_reference_geometry']=answer.get('blocker')=='MISSING_REFERENCE_GEOMETRY'
        checks['clarification_present']=bool(answer.get('clarification_request'))
        checks['no_spatial_execution']=no_attempt
    elif stratum=='IN_SNAPSHOT_SPATIAL':
        tasks=answer.get('spatial_tasks',{}); spatial_checks={}
        for target,gold in contract['spatial_gold'].items():
            task=tasks.get(target,{})
            ids=task.get('object_ids')
            spatial_checks[target+'_object_set']=isinstance(ids,list) and set(map(str,ids))==set(gold['object_ids'])
            spatial_checks[target+'_source']=task.get('source_snapshot_sha256')==gold['source_snapshot_sha256']
            checks.update(spatial_checks)
            evidence=task.get('object_evidence',{})
            checks[target+'_evidence']=all(
                isinstance(evidence.get(identifier),dict) and
                evidence[identifier].get('source_snapshot_sha256')==gold['source_snapshot_sha256'] and
                evidence[identifier].get('object_id')==identifier
                for identifier in gold['object_ids'])
            if not gold['object_ids']:
                checks[target+'_empty_scope_evidence']=task.get('source_snapshot_sha256')==gold['source_snapshot_sha256'] and bool(task.get('query_evidence'))
        result['spatial_correctness']=all_known(spatial_checks)
        result['execution_correctness_gap_applicable']=True
        result['execution_succeeded']=trace.get('execution_succeeded') if complete else None
        disclosure=answer.get('source_coverage',{})
        checks['coverage_disclosed']=bool(disclosure.get('source_snapshot_sha256') in source_hashes and disclosure.get('explanation'))
        if 'comparison_gold' in contract:
            gold=contract['comparison_gold']; comparison=answer.get('comparison',{})
            checks['comparison_counts']=comparison.get('counts')==gold['counts']
            checks['comparison_distances']=distances_match(comparison.get('distance_ranges_m'),gold['distance_ranges_m'],gold['distance_tolerance_m'])
            checks['comparison_definitions']=all(bool(comparison.get('feature_definition_evidence',{}).get(t)) for t in gold['counts'])
    else:
        result['status']='USE_INHERITED_FROZEN_V5_COMPONENT_EVALUATOR'
        return result
    result['all_applicable_checks_pass']=all_known(checks)
    return result
