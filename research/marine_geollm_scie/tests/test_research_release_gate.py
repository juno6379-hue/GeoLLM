from copy import deepcopy

from research.marine_geollm_scie.reliability.research_release_gate import report_gate
from research.marine_geollm_scie.runners.gold_v2_gate import METHODS


IDENTITY = {k: k+'-hash' for k in (
    'system_source_sha256', 'adapter_sha256', 'model_profile_sha256',
    'source_snapshot_sha256', 'benchmark_inputs_sha256', 'method_definitions_sha256')}


def rows():
    return [dict(case_id='case', method=m, repeat=0, benchmark_sha256='gold',
                 execution_identity=deepcopy(IDENTITY), raw_artifact_sha256='rawhash',
                 raw_artifact_path='raw.json', initial_plan_sha256='plan',
                 review_artifact_sha256='review', lossless_compilation_verified=True,
                 domain_tools_enabled=False) for m in METHODS]


def gate(observations, **kwargs):
    return report_gate(case_ids=['case'], repeats=[0], observations=observations,
                       execution_identity=IDENTITY, benchmark_sha256='gold',
                       raw_integrity_verified=True, **kwargs)


def test_full_observations_do_not_claim_rq_completion_or_production_release():
    result = gate(rows(), independent_gold_review_complete=True)
    assert result['observation_comparison_complete']
    assert not result['rq1_to_rq5_complete']
    assert not result['production_release_approved']
    assert not result['human_semantic_accuracy_claim_allowed']


def test_frozen_benchmark_alone_is_not_completed_comparison():
    assert not gate([])['observation_comparison_complete']


def test_changed_production_requires_full_rerun():
    observations = rows()
    observations[0]['execution_identity']['system_source_sha256'] = 'old-source'
    assert any(x.startswith('FULL_RERUN_REQUIRED') for x in gate(observations)['errors'])


def test_paired_plans_and_reviews_must_match():
    observations = rows()
    next(r for r in observations if r['method'] == 'H')['review_artifact_sha256'] = 'newreview'
    next(r for r in observations if r['method'] == 'P0')['initial_plan_sha256'] = 'newplan'
    result = gate(observations)
    assert any(x.startswith('SHARED_REVIEW_MISMATCH') for x in result['errors'])
    assert any(x.startswith('PAIRED_INITIAL_PLAN_MISMATCH') for x in result['errors'])


def test_same_count_duplicate_cannot_replace_missing_method():
    observations = rows()
    observations[-1] = deepcopy(observations[0])
    result = gate(observations)
    assert 'OBSERVATION_SET_INCOMPLETE_OR_EXTRA' in result['errors']
    assert any(x.startswith('DUPLICATE_OBSERVATION') for x in result['errors'])


def test_lossless_and_direct_baseline_required():
    observations = rows()
    next(r for r in observations if r['method'] == 'P0')['lossless_compilation_verified'] = False
    observations[0]['domain_tools_enabled'] = True
    errors = gate(observations)['errors']
    assert any(x.startswith('LOSSLESS_COMPILATION_UNVERIFIED') for x in errors)
    assert any(x.startswith('B0_NOT_DIRECT_LLM') for x in errors)


def test_observed_rejected_compilation_is_valid_failure_data():
    observations=rows()
    branch=next(r for r in observations if r['method']=='P0')
    branch.update(lossless_compilation_verified=False, compilation_status='REJECTED',
        compilation_failure_reason='Unsupported literal unit', execution_callback_invoked=False,
        execution_observation={'observation_complete':True,'execution_attempted':False,
            'execution_started':False,'tool_called':False,'sql_executed':False})
    assert gate(observations)['observation_comparison_complete']
    branch['execution_observation']['tool_called']=True
    assert not gate(observations)['observation_comparison_complete']


def test_unobserved_rejected_compilation_is_not_certified_nonexecution():
    observations=rows()
    branch=next(r for r in observations if r['method']=='H')
    branch.update(lossless_compilation_verified=False, compilation_status='NOT_ATTEMPTED_REVIEW_ERROR',
        compilation_failure_reason='TimeoutError', execution_callback_invoked=False)
    assert not gate(observations)['observation_comparison_complete']
