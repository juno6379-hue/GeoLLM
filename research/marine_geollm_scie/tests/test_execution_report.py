import json
from pathlib import Path
import pytest
from research.marine_geollm_scie.runners.execution_report import normalized_baseline, check_contract, score, common_output_observations
from research.marine_geollm_scie.runners.compare_execution import completed_keys


def test_spatial_mapping_requires_actual_lineage_not_gold_ids():
    row = {'tool_execution': {'receipts': [{'tool_id': 'spatial.query', 'status': 'TOOL_RETURNED', 'result': {
        'source': 'marine_places', 'rows': [{'properties': {'공간정보일련번호': '44'}, 'provenance': {'source_sha256': 'source'}}]}}]}}
    output = normalized_baseline(row)
    assert output['returned_object_ids'] == ['mof_marine_names_20221231:44']
    check = {'kind': 'source_bound_set_equality', 'field': 'returned_object_ids', 'expected': ['mof_marine_names_20221231:44'], 'dataset_snapshot_sha256': 'source'}
    assert check_contract(output, check) is True
    check['dataset_snapshot_sha256'] = 'other'
    assert check_contract(output, check) is None
    assert check_contract(normalized_baseline({}), check) is None


def test_retrieved_snippet_not_promoted_to_p_answer():
    row = {'case_id': 'x', 'method': 'P', 'final_state': {'evidence': 'correct looking source'}}
    result = score(row, {'machine_checks': []}, 'P_PRODUCTION_GRAPH')
    assert result['status'] == 'OUTPUT_MAPPING_NOT_AVAILABLE'
    assert result['all_applicable_checks_pass'] is None


def test_missing_document_is_failed_applicable_component_not_semantic_accuracy():
    result = score({'case_id': 'x', 'method': 'B0_EXECUTION_ADAPTER'}, {'machine_checks': [
        {'id': 'features', 'kind': 'set_inclusion', 'expected': ['Wreck'], 'field': 'document_answer.features[].code'}]}, 'BASELINE_EXECUTION_ADAPTER')
    assert result['all_applicable_checks_pass'] is False
    assert result['full_semantic_accuracy'] is None


def test_resume_rejects_duplicate_and_truncated_rows(tmp_path):
    p = tmp_path/'rows.jsonl'; row={'case_id':'x','method':'B0_EXECUTION_ADAPTER','repeat':0}
    p.write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n')
    with pytest.raises(ValueError): completed_keys(p)
    p.write_text(json.dumps(row)+'\n{"broken":')
    with pytest.raises(ValueError): completed_keys(p)


def test_source_locator_without_claim_link_fails():
    check = {'kind': 'edition_hash_locator_match', 'field': 'document_answer.evidence',
        'expected': {'edition': '2', 'source_sha256': 'hash', 'locators': ['loc']}}
    output = {'document_answer': {'evidence': {'edition':'2','source_sha256':'hash','locators':['loc']}}}
    assert check_contract(output, check) is False
    output['document_answer']['evidence']['claim_source_links'] = [{'definition_locator':'loc','source_sha256':'hash'}]
    assert check_contract(output, check) is True


def test_common_answer_observation_excludes_retrieval_snippet():
    contract={'document_scope':{'features':[{'code':'Wreck','definition':'A verified fixture.'}]}}
    row={'case_id':'x','method':'P','final_state':{'final_dict':{'answer_text':'Wreck information',
        'structured_result':{'documents':[{'excerpt_reference':'A verified fixture.'}], 'citations':[{'path':'source'}]}}}}
    result=common_output_observations(row,contract,'P_PRODUCTION_GRAPH')
    assert result['definition_verbatim_in_emitted_answer']['Wreck'] is False
    assert result['feature_code_literal_in_emitted_answer']['Wreck'] is True
    assert result['returned_citation_count']==1
    assert result['semantic_accuracy'] is None
