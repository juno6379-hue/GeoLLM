import copy
import pytest
from research.marine_geollm_scie.evaluation.execution_semantics import canonical_trace
from research.marine_geollm_scie.evaluation.v2_results import score_row, summarize
from research.marine_geollm_scie.tests.test_v2_results import contract, row


def trace(**changes):
    return dict(observation_complete=True, execution_attempted=False, execution_started=False,
                tool_called=False, sql_executed=False, execution_succeeded=None, **{}) | changes


@pytest.mark.parametrize('attempted', [False, True])
def test_complete_no_sql_is_measured_false_even_pre_sql_block(attempted):
    actual=canonical_trace(trace(execution_attempted=attempted, tool_called=attempted))
    assert actual['execution_succeeded'] is False


@pytest.mark.parametrize('raw', [trace(observation_complete=False), {},
    {'observation_complete':True}, trace(observation_complete=False, execution_succeeded=True)])
def test_missing_or_incomplete_does_not_certify_success(raw):
    assert canonical_trace(raw)['execution_succeeded'] is None


@pytest.mark.parametrize('changes', [{'execution_succeeded':True}, {'tool_called':True},
    {'sql_executed':True}, {'execution_started':True}, {'execution_attempted':'false'}])
def test_contradictions_are_rejected_not_repaired(changes):
    actual=canonical_trace(trace(**changes))
    assert actual['execution_succeeded'] is None
    assert actual['observation_complete'] is False
    assert actual['telemetry_errors']
    assert actual['raw_observation']==trace(**changes)


@pytest.mark.parametrize('execution', [trace(), trace(execution_attempted=True,tool_called=True),
    trace(execution_attempted=True,tool_called=True,execution_started=True,sql_executed=True,execution_succeeded=True),
    {}, trace(observation_complete=False)])
def test_identical_traces_have_identical_scores_for_all_eight_methods(execution):
    scores=[]
    for method in ('B0','B1','B2','B3','B4','P0','H','P1'):
        item=row() | {'method':method,'execution_observation':copy.deepcopy(execution)}
        scores.append(score_row(item,contract()))
    measured=[(s['execution_succeeded'],s['spatial_correctness'],s['silent_spatial_failure']) for s in scores]
    assert len(set(measured))==1


def test_output_absence_and_malformed_structure_do_not_remove_esr_denominator():
    first=row() | {'emitted_answer':None,'execution_observation':trace()}
    second=row() | {'emitted_answer':{'spatial_tasks':[]},'execution_observation':trace()}
    summary=summarize([score_row(first,contract()),score_row(second,contract())])['overall_by_method']['B3']
    assert summary['execution_success_all_eligible']=={'value':0,'denominator':2,'measured':2,'missing':0}
    assert summary['execution_success_given_attempt']['denominator']==0
    assert summary['execution_success_given_attempt']['value'] is None


def test_expected_abstention_can_pass_with_execution_success_false():
    c={'case_id':'C','category':'Q3','evaluation_stratum':'MISSING_REQUIRED_INPUT'}
    item=row() | {'execution_observation':trace(), 'emitted_answer':{'status':'NEEDS_USER_INPUT',
        'blocker':'MISSING_REFERENCE_GEOMETRY','clarification_request':['Select area']}}
    scored=score_row(item,c)
    assert scored['execution_succeeded'] is False
    assert scored['all_applicable_checks_pass'] is True
    assert summarize([scored])['overall_by_method']['B3']['execution_success']['denominator']==0


def test_conditional_esr_retains_unknown_membership():
    item=row() | {'execution_observation':{}}
    summary=summarize([score_row(item,contract())])['overall_by_method']['B3']
    assert summary['execution_success_given_attempt']['unknown_attempt_membership']==1
    assert summary['execution_success_given_attempt']['value'] is None


def test_observer_sql_without_completion_stays_unknown():
    from research.marine_geollm_scie.runners.spatial_execution_observer import SpatialExecutionObserver
    observer=SpatialExecutionObserver('fixture')
    observer.submission('SELECT ST_Intersects(a,b)',None,'fixture')
    observer.complete=True
    actual=observer.result()
    assert actual['sql_executed'] is True
    assert actual['observation_complete'] is False
    assert actual['execution_succeeded'] is None


def test_observer_document_success_is_not_spatial_success():
    from research.marine_geollm_scie.runners.spatial_execution_observer import SpatialExecutionObserver
    observer=SpatialExecutionObserver('fixture')
    kind,digest=observer.submission('SELECT content FROM documents',None,'fixture')
    observer.finished(kind,digest,'fixture',True)
    observer.complete=True
    assert observer.result()['execution_succeeded'] is False


def test_baseline_pre_sql_tool_error_is_measured_failure_not_unknown(tmp_path):
    from research.marine_geollm_scie.baselines.v2_runtime import V2Executor
    import hashlib
    class DB:
        events=[]
    path=tmp_path/'fc.json'
    path.write_text('{"features": []}')
    executor=V2Executor(DB(),catalogue=path,catalogue_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),anchors=[],coverage={})
    result=executor.execute({'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':{}}]})
    actual=result['execution_observation']
    assert actual['tool_called'] is True
    assert actual['execution_attempted'] is True
    assert actual['sql_executed'] is False
    assert actual['execution_succeeded'] is False
