from copy import deepcopy

from research.marine_geollm_scie.runners.execution_report import normalized_production, score, check_contract


def row(structured, **final):
    return {'case_id': 'arbitrary', 'method': 'P', 'final_state': {
        'final_dict': {'status': 'COMPLETED', 'structured_result': structured, **final}}}


def test_maps_only_emitted_document_not_retrieved_or_top_level_evaluation_override():
    r = row({'documents': [{'excerpt_reference': 'Gold-looking Wreck definition'}],
             'citations': [{'detail_text': 'Gold-looking Wreck definition'}]}, answer_text='Wreck prose')
    r['evaluation_output'] = {'document_answer': {'features': [{'code': 'Wreck'}]}}
    output = normalized_production(r)
    assert output['document_answer']['features'] == []
    assert output['search_executed'] is None
    result = score(r, {'machine_checks': [{'id': 'feature', 'kind': 'set_inclusion',
        'field': 'document_answer.features[].code', 'expected': ['Wreck']}]}, 'P_PRODUCTION_GRAPH')
    assert result['all_applicable_checks_pass'] is False
    assert result['full_semantic_accuracy'] is None


def test_actual_document_answer_is_mapped_without_reference_or_mutation():
    document = {'features': [{'code': 'ArbitraryFeature', 'definition': 'Source definition',
        'permitted_primitives': ['point']}], 'attribute_bindings': [],
        'evidence': {'edition': '2', 'source_sha256': 'hash', 'locators': ['x']}}
    r = row({'document_answer': document}); original = deepcopy(r)
    output = normalized_production(r)
    assert output['document_answer'] == document
    assert r == original
    assert output['mapping_provenance']['reference_used_for_mapping'] is False


def test_spatial_original_ids_require_recorded_execution_and_row_lineage():
    s = {'search_execution': {'status': 'COMPLETED'}, 'features': [
        {'layer_id': 'marine_gazetteer_mof', '공간정보일련번호': '999', 'provenance': {'source_sha256': 'hash'}}]}
    assert normalized_production(row(s))['returned_object_ids'] == ['mof_marine_names_20221231:999']
    s['search_execution']['status'] = 'NOT_RUN'
    output = normalized_production(row(s))
    assert output['search_executed'] is False
    assert 'returned_object_ids' not in output
    s['search_execution']['status'] = 'COMPLETED'
    s['features'][0]['provenance'] = {}
    assert 'dataset_snapshot_sha256' not in normalized_production(row(s))


def test_clarification_mapping_and_unknown_execution_stays_unmeasured():
    contract = {'machine_checks': [
        {'id': 'status', 'kind': 'exact_value', 'field': 'execution_status', 'expected': 'NEEDS_USER_INPUT'},
        {'id': 'execution', 'kind': 'exact_value', 'field': 'search_executed', 'expected': False}]}
    r = row({}, status='NEEDS_CLARIFICATION', clarification_questions=['Select area'])
    result = score(r, contract, 'P_PRODUCTION_GRAPH')
    assert [c['pass'] for c in result['checks']] == [True, None]
    r['final_state']['final_dict']['structured_result']['search_execution'] = {'status': 'NOT_RUN'}
    assert score(r, contract, 'P_PRODUCTION_GRAPH')['all_applicable_checks_pass'] is True


def test_legacy_attribute_does_not_invent_geometry_or_xml_claim_links():
    output = normalized_production(row({'analysis_type': 'public_catalogue_attribute_lookup',
        'feature_code': 'RestrictedArea', 'feature_definition': 'Source text', 'attribute_code': 'restriction',
        'binding': {'lower': '1'}, 'locators': ['/features/1'], 'xml_source_sha256': 'xml'}))
    assert output['document_answer']['features'][0]['code'] == 'RestrictedArea'
    assert 'permitted_primitives' not in output['document_answer']['features'][0]
    assert 'evidence' not in output['document_answer']


def test_executed_empty_needs_explicit_source_hash_not_zero_count():
    s = {'search_execution': {'status': 'COMPLETED'}, 'features': [], 'count': 0}
    check = {'kind': 'source_bound_set_equality', 'field': 'returned_object_ids',
        'expected': [], 'dataset_snapshot_sha256': 'hash'}
    assert check_contract(normalized_production(row(s)), check) is None
    s.update(source='marine_places', dataset_snapshot_sha256='hash')
    assert check_contract(normalized_production(row(s)), check) is True
    s['search_execution']['status'] = 'NOT_RUN'
    assert check_contract(normalized_production(row(s)), check) is None


def test_research_oracle_disclosure_not_invented_from_runtime_coverage():
    output = normalized_production(row({'source_coverage': {'unverified_conditions': ['source incomplete']}}))
    check = {'kind': 'required_structured_disclosure', 'field': 'source_coverage'}
    assert check_contract(output, check) is None
    assert 'benchmark_oracle_available' not in output['source_coverage']


def test_source_claim_can_bind_actual_definition_child_of_feature_locator():
    locator = "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"
    evidence = {'edition': '2', 'source_sha256': 'hash', 'locators': [locator],
        'claim_source_links': [{'source_sha256': 'hash', 'definition_locator': locator+"/*[local-name()='definition']"}]}
    check = {'kind': 'edition_hash_locator_match', 'field': 'document_answer.evidence',
        'expected': {'edition': '2', 'source_sha256': 'hash', 'locators': [locator]}}
    assert check_contract({'document_answer': {'evidence': evidence}}, check) is True
    evidence['claim_source_links'][0]['definition_locator'] = locator+'/invented'
    assert check_contract({'document_answer': {'evidence': evidence}}, check) is False
