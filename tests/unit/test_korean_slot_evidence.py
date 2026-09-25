import pytest
from pydantic import ValidationError

from services.orchestrator.slot_evidence import extract_quantities, validate_slot
from services.orchestrator.korean_query_analysis import analyze_query, constraints, contract_problem


@pytest.mark.parametrize('raw,kind,value,unit', [
    ('1해리', 'distance', 1852.0, 'm'), ('1.5km', 'distance', 1500.0, 'm'),
    ('12개월', 'duration', 'P12M', 'iso8601_duration'), ('1년', 'duration', 'P1Y', 'iso8601_duration'),
    ('1,000m', 'distance', 1000.0, 'm'), ('.5km', 'distance', 500.0, 'm'),
])
def test_dimensions_and_deterministic_conversion(raw, kind, value, unit):
    row = validate_slot(raw, {'slot_type': kind, 'raw_text': raw, 'span': [0, len(raw)]})
    assert row['validation_status'] == 'GROUNDED'
    assert (row['normalized_value'], row['unit']) == (value, unit)


@pytest.mark.parametrize('raw,code', [('12개월','UNIT_DIMENSION_MISMATCH'), ('2.0','EXPLICIT_UNIT_REQUIRED'),
                                        ('-1km','NON_POSITIVE_QUANTITY'), ('0m','NON_POSITIVE_QUANTITY')])
def test_time_version_and_invalid_values_cannot_be_radius(raw, code):
    result = validate_slot(raw, {'slot_type': 'distance', 'raw_text': raw, 'span': [0,len(raw)]})
    assert code in result['reason_codes']


def test_model_cannot_invent_span_or_normalized_number():
    row = validate_slot('12개월', {'slot_type':'distance','raw_text':'1km','span':[0,3], 'normalized_value': 1000})
    assert 'SOURCE_SPAN_MISMATCH' in row['reason_codes']
    row = validate_slot('1해리', {'slot_type':'distance','raw_text':'1해리','span':[0,3], 'normalized_value': 1000})
    assert 'NORMALIZED_VALUE_MISMATCH' in row['reason_codes']


def test_unicode_offsets_are_original_codepoints():
    query = '🛟 부산항 반경1해리 이내'
    result = extract_quantities(query)
    assert len(result) == 1
    row = result[0]
    assert query[slice(*row['span'])] == '1해리'
    assert row['quantity_role'] == 'radius'


def test_depth_length_does_not_become_search_radius():
    slots = extract_quantities('수심 8m에서 반경 1km 이내 침선')
    assert [s['quantity_role'] for s in slots] == ['length_unspecified','radius']


def test_calendar_year_is_not_duration():
    assert extract_quantities('2023년 사고')[0]['slot_type'] == 'date'


def test_shared_executor_distance_matches_unit_contract():
    from services.orchestrator.slot_evidence import distance_m
    assert distance_m('반경1해리 이내') == 1852
    assert distance_m('수심 8m') is None
    assert distance_m('반경 1km와 반경 2km') is None
    from services.orchestrator.s101_radius_execution import parse_distance
    assert parse_distance('수심 8m에서 반경 1해리 이내 침선', {}) == 1852


def test_model_radius_without_source_is_removed_and_map_radius_is_attributed():
    from services.orchestrator.slot_evidence import ground_distance_payload
    result = ground_distance_payload('최근 12개월 통항량', {'distance_m':12000})
    assert 'distance_m' not in result
    assert result['rejected_distance_proposal']['value']==12000
    result = ground_distance_payload('주변 침선', {'distance_m':3000}, {'buffer_distance':1852})
    assert result['distance_m']==1852
    assert result['distance_evidence']['source_ref']=='request.spatial_context.buffer_distance'


def test_ambiguous_or_depth_quantity_does_not_fall_back_to_stale_map_radius():
    from services.orchestrator.slot_evidence import ground_distance_payload
    for query in ('반경1km와 반경2km','수심8m'):
        assert 'distance_m' not in ground_distance_payload(query, {'distance_m':3000}, {'buffer_distance':3000})


def test_requested_portrayal_mapping_cannot_complete_with_definition():
    from services.orchestrator.request_obligations import audit_outputs
    final = audit_outputs('S-101 portrayal symbol과 장애물 아이콘 매칭 근거를 보여줘',
                          {'status':'COMPLETED','structured_result':{'definition':'Obstruction'},'answer_text':'정의'})
    assert final['status'] == 'PARTIAL'
    assert final['error_code'] == 'OUTPUT_OBLIGATIONS_UNMET'


def test_map_object_without_identity_clarifies_even_if_word_evidence_present():
    query = '위험객체 지도 클릭 시 feature 정보와 근거를 같이 보여줘'
    assert contract_problem(query, {'constraints':[],'slots':[]})['code'] == 'SELECTED_FEATURE_REQUIRED'


def test_provenance_question_is_dataset_request_not_spatial_execution():
    from services.orchestrator.graph import _looks_like_dataset_evidence_query, check_intent_parsed
    query = '해양수산부 바다갈라짐 ZIP은 어떤 방식으로 좌표를 보완했어?'
    assert _looks_like_dataset_evidence_query(query)
    assert check_intent_parsed({'query':query,'status':'NEEDS_CLARIFICATION'}) == 'fast_dataset_evidence_answer'


def test_composite_traffic_accident_cannot_complete_one_obligation():
    from services.orchestrator.request_obligations import audit_outputs
    result = audit_outputs('통항량과 사고 이력을 분석해줘', {'status':'COMPLETED','structured_result':{'monthly_breakdown':[{'count':1}]}})
    assert result['status'] == 'PARTIAL'
    assert result['structured_result']['unmet_outputs'] == ['accident_evidence']


def test_context_identifier_alone_cannot_validate_slot():
    row = validate_slot('여기', {'slot_type':'location','raw_text':'부산항','source_kind':'map','source_ref':'fake'})
    assert row['validation_status'] == 'REJECTED'


def test_bool_offsets_are_not_accepted_as_integer_positions():
    with pytest.raises(ValidationError):
        validate_slot('1km', {'slot_type':'distance','raw_text':'1km','span':[False,3]})


@pytest.mark.parametrize('query,kind,target', [('사고 말고 침선만 찾아줘','exclusion','사고'),
    ('부산항은 제외하고 인천항 주변','exclusion','부산항'), ('사고가 없는 구역을 찾아줘','absence_predicate','사고')])
def test_negation_scopes(query,kind,target):
    assert any(c['kind']==kind and c['target']==target for c in constraints(query))


def test_quote_is_not_automatically_an_execution_exclusion():
    query = '"사고 말고"라는 표현을 찾아줘'
    analysis = {'constraints':constraints(query),'slots':[]}
    assert contract_problem(query,analysis) is None


def test_missing_location_is_not_an_accident_search_term():
    query = '위치 없이 부근 사고를 찾아줘'
    problem = contract_problem(query, {'constraints':constraints(query),'slots':[]})
    assert problem['code'] == 'LOCATION_REQUIRED'
    assert problem['status'] == 'NEEDS_CLARIFICATION'


def test_supplied_map_context_is_not_called_missing():
    query = '위치 없이 부근 사고를 찾아줘'
    problem = contract_problem(query, {'constraints':constraints(query),'slots':[]}, {'geometry':'POINT(129 35)'})
    assert problem['code'] != 'LOCATION_REQUIRED'


def test_kiwi_can_be_disabled_without_losing_unit_validation(monkeypatch):
    monkeypatch.setenv('GEOLLM_KIWI_ENABLED','false')
    result = analyze_query('반경1해리 이내')
    assert result['analyzer']['status'] == 'DISABLED'
    assert result['slots'][0]['normalized_value'] == 1852


def test_kiwi_real_tokens_preserve_original_and_dictionary():
    pytest.importorskip('kiwipiepy')
    result = analyze_query('부산항에서 침선을 찾아줘')
    assert result['analyzer']['status'] == 'AVAILABLE'
    assert result['analyzer']['dictionary_sha256']
    assert any(t['form']=='침선' for t in result['tokens'])
    assert all('부산항에서 침선을 찾아줘'[slice(*t['span'])] == t['raw_text'] for t in result['tokens'])


def test_ontology_capability_binding_does_not_claim_geometry_ready():
    from services.orchestrator.semantic_slot_binding import bind_semantic_slots
    query = '침선 반경1해리 이내 검색'
    analysis = {'constraints':[], 'slots':extract_quantities(query)}
    candidate = {'candidate_id':'tool.spatial_radius_search', 'input_slots':['anchor_geometry','radius_m','target_feature_group'],
                 'output_slots':['spatial_features']}
    binding = bind_semantic_slots(query, analysis, [candidate])
    assert 'Wreck' in binding['target_features']
    assert binding['term_bindings'][0]['canonical_id'] == 'Wreck'
    assert set(binding['source_sha256']) == {'terms','ontology','kg_nodes','kg_edges'}
    tool = binding['capability_bindings'][0]
    assert tool['bound_inputs']['radius_m']['evidence']['normalized_value'] == 1852
    assert tool['unresolved_inputs'] == ['anchor_geometry']
    assert tool['execution_authorized'] is False


def test_null_evidence_is_unmet_not_an_audit_exception():
    from services.orchestrator.request_obligations import audit_outputs
    result = audit_outputs('portrayal 심볼 매칭', {'status':'COMPLETED', 'structured_result':{'portrayal_binding':None}})
    assert result['status'] == 'PARTIAL'
    assert '지도 객체와 심볼의 연결 근거' in result['summary']


def test_excluded_term_alone_does_not_bind_feature_input():
    from services.orchestrator.semantic_slot_binding import bind_semantic_slots
    query = '침선 말고 찾아줘'
    binding = bind_semantic_slots(query, {'constraints':constraints(query),'slots':[]},
                                  [{'candidate_id':'term', 'input_slots':['feature_term']}])
    assert binding['capability_bindings'][0]['unresolved_inputs'] == ['feature_term']


def test_reference_verification_deduplicates_per_request(monkeypatch):
    from services.orchestrator import query_candidate_broker as broker
    calls=[]
    monkeypatch.setattr(broker, '_verify_reference', lambda ref: calls.append(ref) or {'status':'verified'})
    candidates=[{'candidate_id':str(i),'authority_ref':'same','registry_ref':'same'} for i in range(4)]
    assert len(broker._verify_candidates(candidates)) == 4
    assert calls == ['same']


@pytest.mark.asyncio
async def test_graph_guard_prevents_query_and_tool_execution(monkeypatch):
    from services.orchestrator import graph
    monkeypatch.setenv('GEOLLM_KIWI_ENABLED','false')
    def unexpected(*args, **kwargs):
        raise AssertionError('No candidate/DB lookup is needed for a missing reference location')
    monkeypatch.setattr(graph.query_candidate_broker,'build_trace',unexpected)
    state = await graph.parse_intent_node({'task_id':'guard-test', 'query':'위치 없이 부근 사고를 찾아줘', 'spatial_context':{}})
    assert graph.check_intent_parsed(state) == 'query_contract_stop'
    assert state['final_dict']['error_code'] == 'LOCATION_REQUIRED'
    assert state['query_execution_context']['execution_status'] == 'NOT_RUN'


@pytest.mark.asyncio
async def test_output_audit_writes_graph_state_for_legacy_agent_result():
    from services.orchestrator.graph import verify_output_obligations_node
    from shared.schemas.agent import AgentStatus
    result = await verify_output_obligations_node({'query':'심볼 매칭 근거', 'status':AgentStatus.COMPLETED,
                                                   'agent_result':{'status':'COMPLETED','structured_result':{}}})
    assert result['status'] == AgentStatus.PARTIAL
    assert result['final_dict']['error_code'] == 'OUTPUT_OBLIGATIONS_UNMET'
    result = await verify_output_obligations_node({'query':'설명', 'status':AgentStatus.COMPLETED})
    assert result == {'status':AgentStatus.COMPLETED}
