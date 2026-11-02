import json
import pytest
from tools.scie_results_ui.paper_tables import build_paper_tables,detector_metrics,recovery_metrics,summary_rate,conditional_correctness

RID='20261102_gold_v2_eight_k1_v6'


def fixture(tmp_path):
    base=tmp_path/'research/marine_geollm_scie/runs'/RID
    for folder in ['report_with_faults','faults','comparison']:(base/folder).mkdir(parents=True)
    m={'observations':18,'execution_success_all_eligible':{'value':0,'denominator':5,'measured':5,'missing':0},'spatial_correctness':{'value':None,'denominator':5,'measured':2,'missing':3},'execution_correctness_gap':0,'silent_spatial_failure_given_success':{'value':None,'denominator':0,'measured':0,'missing':0},'costs':{'latency_seconds':{'p50':10,'p95':30,'mean':14,'measured':18,'missing':0}}}
    (base/'report_with_faults/summary.json').write_text(json.dumps({'overall_by_method':{'P1':m}}))
    rows=[dict(case_id='invalid',error_type='unit',method='B4',expected_invalid=True,predicted_invalid=False,recovery_eligible=True,recovery_attempted=True,recovery_success=True,semantic_preservation=False,spatial_correct=False,joint_success=False),dict(case_id='control',error_type='control',method='B4',expected_invalid=False,predicted_invalid=False,recovery_eligible=False,recovery_attempted=False)]
    (base/'faults/rows.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
    (base/'comparison/manifest.json').write_text('{}')
    return base


def test_recall_false_ready_and_control_denominators_are_separate():
    rows=[dict(expected_invalid=True,predicted_invalid=True),dict(expected_invalid=True,predicted_invalid=False),dict(expected_invalid=False,predicted_invalid=True)]
    r=detector_metrics(rows)
    assert (r['recall']['numerator'],r['recall']['denominator'],r['recall']['value'])==(1,2,.5)
    assert (r['false_block']['numerator'],r['false_block']['denominator'])==(1,1)
    assert detector_metrics(rows[:2])['false_block']['value'] is None
    assert detector_metrics(rows[:2])['false_block']['status']=='UNDEFINED'


def test_missing_prediction_is_not_dropped():
    r=detector_metrics([dict(expected_invalid=True,predicted_invalid=True),dict(expected_invalid=True)])['recall']
    assert r['value'] is None and r['denominator']==2 and r['missing']==1


def test_recovery_joint_success_not_execution_alone():
    r=recovery_metrics([dict(recovery_eligible=True,recovery_attempted=True,recovery_success=True,semantic_preservation=False,spatial_correct=False,joint_success=False)])
    assert r['recovery_success']['value']==1 and r['joint_recovery']['value']==0
    assert r['semantic_drift']['value']==1 and r['first_repair']['value'] is None


def test_missing_spatial_observation_remains_unknown():
    r=recovery_metrics([dict(recovery_eligible=True,recovery_attempted=True,spatial_correct=True),dict(recovery_eligible=True,recovery_attempted=True,spatial_correct=None)])
    assert r['recovered_spatial_correctness']['value'] is None
    assert r['recovered_spatial_correctness']['denominator']==2


def test_tables_preserve_metric_non_equivalence_and_unrun_ablation(tmp_path):
    base=fixture(tmp_path);before={p:p.read_bytes() for p in base.rglob('*') if p.is_file()}
    result=build_paper_tables(tmp_path,RID)
    p1=result['tables']['table11']['rows'][-1]
    assert p1['esr']['value']==0 and p1['esr']['denominator']==5
    assert p1['spatial_correctness']['value'] is None and p1['ssfr']['status']=='UNDEFINED'
    assert p1['cge']['value'] is None and p1['evqsr']['value'] is None and p1['execution_correctness_gap']['value']==0
    assert p1['paired_delta_ci']['value'] is None
    for row in result['tables']['table13']['rows']:
        assert row['ablation_delta']['value'] is None
        assert row['semantic_errors']['value'] is None
    assert all(p.read_bytes()==raw for p,raw in before.items())
    assert all(s['sha256'] for s in result['sources'] if s['status']=='AVAILABLE')


def test_cost_population_is_not_fault_population(tmp_path):
    fixture(tmp_path);result=build_paper_tables(tmp_path,RID)
    p1=result['tables']['table14']['rows'][-1]
    assert p1['latency_p50']['value']==10 and p1['latency_p50']['unit']=='seconds'
    assert p1['false_ready']['value'] is None and p1['tool_calls']['value'] is None
    assert p1['evidence_completeness']['value'] is None


def test_absent_files_do_not_become_zero_performance(tmp_path):
    result=build_paper_tables(tmp_path,RID)
    assert all(r['esr']['value'] is None for r in result['tables']['table11']['rows'])
    assert all(r['recall']['value'] is None for r in result['tables']['table10']['rows'])


def test_rejects_run_traversal_and_duplicate_observation(tmp_path):
    unsafe=build_paper_tables(tmp_path,'../holdout')
    assert unsafe['errors']==['INVALID_SELECTED_RUN'] and unsafe['sources']==[]
    base=fixture(tmp_path);p=base/'faults/rows.jsonl';line=p.read_text().splitlines()[0];p.write_text(line+'\n'+line)
    result=build_paper_tables(tmp_path,RID)
    assert 'DUPLICATE_CONTROLLED_OBSERVATION' in result['errors']
    assert all(r['recall']['value'] is None for r in result['tables']['table10']['rows'])


def test_absent_selection_preserves_empty_dashboard_state(tmp_path):
    result=build_paper_tables(tmp_path,None)
    assert result['status']=='UNAVAILABLE_SELECTED_RUN'
    assert result['tables']=={} and result['sources']==[]


def test_partial_summary_denominator_is_not_shrunk():
    r=summary_rate({'value':None,'denominator':5,'measured':2,'missing':3},'spatial')
    assert r['value'] is None and r['denominator']==5 and r['measured']==2


def test_cge_is_conditional_correctness_not_execution_gap():
    m={'execution_success_all_eligible':dict(value=.6,denominator=10,measured=10,missing=0),
       'silent_spatial_failure_given_success':dict(value=1/6,denominator=6,measured=6,missing=0)}
    result=conditional_correctness(m)
    assert result['value']==pytest.approx(5/6)
    assert (result['numerator'],result['denominator'])==(5,6)
    m['execution_success_all_eligible']['missing']=1
    assert conditional_correctness(m)['value'] is None
