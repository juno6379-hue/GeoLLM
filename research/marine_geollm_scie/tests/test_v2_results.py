import json
import hashlib
import pytest
from research.marine_geollm_scie.evaluation.v2_observations import normalize
from research.marine_geollm_scie.evaluation.v2_results import score_row, summarize
from research.marine_geollm_scie.runners.report_eight import verify_raw
from research.marine_geollm_scie.runners.report_eight import run_report
from pathlib import Path


def contract():
    return {'case_id':'C','category':'Q3','evaluation_stratum':'IN_SNAPSHOT_SPATIAL',
            'coverage_reference':{'source_relation_sha256':{'features':'hash'}},
            'spatial_gold':{'Wreck':{'object_ids':['1'],'source_snapshot_sha256':'hash'}}}


def row():
    return {'case_id':'C','method':'B3','repeat':0,'status':'RETURNED',
            'emitted_answer':{'spatial_tasks':{'Wreck':{'object_ids':['2'],'source_snapshot_sha256':'hash'}}},
            'execution_observation':{'observation_complete':True,'execution_attempted':True,
                                     'execution_succeeded':True},'costs':{'latency_seconds':2}}


def test_silent_failure_requires_actual_success_and_wrong_spatial_answer():
    score=score_row(row(),contract())
    assert score['spatial_correctness'] is False
    assert score['execution_succeeded'] is True
    assert score['silent_spatial_failure'] is True
    summary=summarize([score])['overall_by_method']['B3']
    assert summary['execution_correctness_gap']==1
    assert summary['silent_spatial_failure_given_success']['value']==1


def test_absent_trace_never_becomes_false_or_success():
    item=row();item.pop('execution_observation')
    score=score_row(item,contract())
    assert score['execution_succeeded'] is None
    assert score['silent_spatial_failure'] is None
    assert summarize([score])['overall_by_method']['B3']['execution_success']['value'] is None


def test_absent_output_is_unmeasured_not_wrong_spatial_set():
    item=row();item.pop('emitted_answer')
    score=score_row(item,contract())
    assert score['spatial_correctness'] is None
    assert score['all_applicable_checks_pass'] is None


def test_fetched_gold_like_text_is_not_emitted_answer():
    assert normalize({'retrieved_documents':[{'document_answer':{'features':['Wreck']}}]})['output_available'] is False


def test_legacy_all_sql_observer_does_not_certify_gis_nonexecution():
    result=normalize({'emitted_answer':{},'execution_observation':{'version':'research_execution_observer_v1',
        'observation_complete':True,'execution_attempted':False,'sql_executed':False}})
    assert result['trace']['execution_attempted'] is None
    assert result['trace']['observation_complete'] is False


def test_report_does_not_claim_unrun_fault_or_recovery_results():
    result=summarize([score_row(row(),contract())])
    assert result['rq2_fault_comparison']['status']=='NOT_MEASURED'
    assert result['rq4_recovery']['status']=='NOT_MEASURED'
    assert result['rq5_false_ready_false_block']['status']=='NOT_MEASURED'


@pytest.mark.parametrize('answer',[
    {'spatial_tasks':['Wreck']}, {'spatial_tasks':{'Wreck':['wrong']}},
    {'source_coverage':['wrong']}, {'document_answer':['wrong']},
    {'document_answer':{'features':[{'code':['Wreck']}]}},
    {'comparison':{'feature_definition_evidence':['wrong']}},
])
def test_malformed_emitted_containers_are_failures_not_report_crashes(answer):
    item=row();item['emitted_answer']=answer
    result=score_row(item,contract())
    assert result['scoring_status']=='MALFORMED_EMITTED_STRUCTURE'
    assert result['all_applicable_checks_pass'] is False
    assert result['spatial_correctness'] is None
    assert result['observation']['answer']==answer or result['observation']['answer'].items()>=answer.items()


def test_malformed_trace_is_unknown_not_nonexecution():
    item=row();item['execution_observation']=['wrong']
    result=score_row(item,contract())
    assert result['execution_succeeded'] is None
    assert result['observation']['trace']['observation_complete'] is False
    assert result['observation']['trace']['raw_observation']==['wrong']


def test_unexpected_projection_error_retains_raw_error_and_unknown_answer():
    item=row();item.update(status='ANSWER_PROJECTION_ERROR',emitted_answer=None,
        answer_projection_error={'error_type':'TypeError','answer_repaired':False})
    result=score_row(item,contract())
    assert result['scoring_status']=='OUTPUT_UNAVAILABLE'
    assert result['all_applicable_checks_pass'] is None
    assert result['answer_projection_error']['answer_repaired'] is False


def test_raw_verification_rejects_changed_normalized_observation(tmp_path):
    raw=row();p=tmp_path/'raw.json';p.write_text(json.dumps(raw),encoding='utf-8')
    receipt={**raw,'raw_artifact_path':'raw.json','raw_artifact_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    assert verify_raw(tmp_path,receipt)==p
    receipt['emitted_answer']={}
    with pytest.raises(ValueError,match='differs from raw'):
        verify_raw(tmp_path,receipt)


def test_raw_verification_rejects_path_escape(tmp_path):
    outside=tmp_path.parent/'outside.json';outside.write_text('{}')
    with pytest.raises(ValueError,match='path/hash'):
        verify_raw(tmp_path,{'raw_artifact_path':'../outside.json','raw_artifact_sha256':hashlib.sha256(outside.read_bytes()).hexdigest()})


def test_actual_frozen_contract_partial_report_is_not_complete(tmp_path):
    benchmark=Path(__file__).resolve().parents[1]/'benchmark/gold_v2_immutable_20261101_v1'
    digest=hashlib.sha256((benchmark/'manifest.json').read_bytes()).hexdigest()
    identity={k:'fixture' for k in ('system_source_sha256','adapter_sha256','model_profile_sha256',
        'source_snapshot_sha256','benchmark_inputs_sha256','method_definitions_sha256')}
    run=tmp_path/'run';run.mkdir()
    (run/'manifest.json').write_text(json.dumps({'benchmark_sha256':digest,'repeats':[0],'execution_identity':identity}))
    raw={'case_id':'PILOT_Q1_01','method':'B0','repeat':0,'emitted_answer':{'answer_text':'fixture'},
         'domain_tools_enabled':False,'benchmark_sha256':digest,'execution_identity':identity}
    path=run/'raw.json';path.write_text(json.dumps(raw))
    receipt={**raw,'raw_artifact_path':'raw.json','raw_artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (run/'observations.jsonl').write_text(json.dumps(receipt)+'\n')
    result=run_report(run,benchmark,tmp_path/'report')
    assert result['observed_rows']==1
    assert result['expected_observations']==144
    assert result['completion_gate']['observation_comparison_complete'] is False
    assert result['scientific_completion'] is False
    with pytest.raises(FileExistsError):run_report(run,benchmark,tmp_path/'report')
