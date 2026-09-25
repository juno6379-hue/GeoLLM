import pytest
from services.orchestrator.request_semantics import permits_document_answer
from services.orchestrator.definition_router import is_definition_query, resolve_definition


@pytest.mark.parametrize("query", [
    "최근 1년간 AIS/V-PASS 통항량을 분석해줘",
    "부산항 최근 12개월 AIS 통항량을 구역별로 요약해줘",
    "인천항 주변 통항분리구역을 표시해줘",
    "부산항 입구 1km 이내 침선을 찾아줘",
    "AIS 법령과 최근 12개월 통항량을 분석해줘",
])
def test_execution_outputs_cannot_be_satisfied_by_topical_documents(query):
    assert not permits_document_answer(query)


@pytest.mark.parametrize("query", ["인천항 선박통항규칙을 찾아줘", "Wreck 정의와 S-101 근거를 알려줘", "AIS 관련 법령을 요약해줘"])
def test_explicit_document_requests_stay_document_requests(query):
    assert permits_document_answer(query)


def test_feature_mapping_uses_dictionary_and_catalogue_not_legal_notice():
    query = "정박지는 S-101에서 어떤 Feature야?"
    assert is_definition_query(query)
    result = resolve_definition(query)
    assert result["term_id"] == "AnchorageArea"
    assert result["source_kind"] == "s101_feature_catalogue"


def test_multifeature_alias_is_not_arbitrarily_resolved():
    assert resolve_definition("선석은 S-101에서 어떤 Feature야?") is None


def test_traffic_separation_geometry_is_not_traffic_volume():
    from services.orchestrator.graph import _looks_like_traffic_query, _requested_spatial_layer_targets, _requested_layer_distance_m
    query = "인천항 주변 통항분리구역을 표시해줘"
    assert not _looks_like_traffic_query(query)
    assert _requested_spatial_layer_targets(query)[0]['layer_id'] == 'traffic_separation_boundary'
    assert _requested_layer_distance_m(query, {}) is None


def test_reselecting_existing_verified_route_does_not_promote_unverified_tools():
    from services.orchestrator.query_candidate_broker import select_execution_route, execution_contract_ready
    trace = {'route_candidates': [{'route': 'PLACE_LOOKUP', 'score': 1}, {'route': 'TRAFFIC_ANALYSIS', 'score': 1}],
        'execution_contract': {'execution_route': 'PLACE_LOOKUP'},
        'capability_candidates': [{'candidate_id': 'traffic', 'kind': 'tool_description', 'routes': ['TRAFFIC_ANALYSIS']}],
        'verified_candidates': []}
    blocked = select_execution_route(trace, 'TRAFFIC_ANALYSIS', 'aggregate output requested')
    assert not execution_contract_ready(blocked, route='TRAFFIC_ANALYSIS', capability_id='traffic')
    trace['verified_candidates'] = [{'candidate_id': 'traffic', 'status': 'verified_ready'}]
    selected = select_execution_route(trace, 'TRAFFIC_ANALYSIS', 'aggregate output requested')
    assert execution_contract_ready(selected, route='TRAFFIC_ANALYSIS', capability_id='traffic')
    assert selected['execution_selection']['ranked_route'] == 'PLACE_LOOKUP'
    assert select_execution_route(trace, 'ABSENT', 'unsupported') is trace


def test_system_trace_question_requires_actual_task_context():
    from services.orchestrator.pipeline_diagnostics import diagnostic_response, diagnostic_request
    query = 'Ontology/KG validator가 후보를 제거한 이유를 설명해줘'
    assert diagnostic_request(query) == 'execution_trace'
    result = diagnostic_response({'task_id': 'diagnostic', 'query': query})
    assert result['status'] == 'NEEDS_CLARIFICATION'
    assert result['orchestrator_v2']['query_execution_context']['tool_bindings'][0]['status'] == 'BLOCKED'
    assert not result['evidence_bundle']['diagnostic_evidence']


def test_loaded_period_is_execution_modifier_not_ingestion_question():
    from services.orchestrator.pipeline_diagnostics import diagnostic_request
    from services.orchestrator.graph import _looks_like_dataset_evidence_query
    query = '부산항 최신 적재 월 AIS 통항량을 분석해줘'
    assert diagnostic_request(query) is None
    assert not _looks_like_dataset_evidence_query(query)


def test_ingestion_and_registry_questions_have_runtime_diagnostic_targets():
    from services.orchestrator.pipeline_diagnostics import diagnostic_request, diagnostic_response
    assert diagnostic_request('Dataset 폴더 안의 embedding 완료 현황을 요약해줘') == 'document_coverage'
    query = 'Resolver Registry에서 사용 가능한 해양 resolver 목록을 보여줘'
    assert diagnostic_request(query) == 'resolver_registry'
    final = diagnostic_response({'task_id': 'registry-probe', 'query': query})
    assert final['status'] == 'PARTIAL'
    assert final['structured_result']['rows']


def test_find_action_alone_does_not_supply_accident_semantics():
    from services.orchestrator.query_candidate_broker import _signal_scan
    assert 'structured_event_lookup' not in {s.signal_id for s in _signal_scan('정박지를 찾아줘')}
    assert 'structured_event_lookup' in {s.signal_id for s in _signal_scan('기관손상 사고를 찾아줘')}
    assert 'nearby_search' in {s.signal_id for s in _signal_scan('가장 가까운 정박지')}


@pytest.mark.parametrize('query', ['최근 사고 이력', '사고 찾아줘'])
def test_accident_requests_without_filters_clarify_without_querying_db(query, monkeypatch):
    import asyncio
    from services.orchestrator import graph
    assert graph._looks_like_accident_event_lookup_query(query)
    monkeypatch.setattr(graph, '_query_accident_events', lambda *_: pytest.fail('Unbounded accident query must not execute'))
    result = asyncio.run(graph.fast_accident_event_lookup_node({'task_id': 'missing-filters', 'query': query}))
    assert result['final_dict']['error_code'] == 'ACCIDENT_FILTERS_REQUIRED'
    assert result['query_execution_context']['tool_bindings'][0]['status'] == 'NOT_RUN'
def test_registry_diagnostic_cannot_be_intercepted_as_map_navigation():
    from services.orchestrator.fast_path_policy import instant_place_navigation_decision
    decision = instant_place_navigation_decision('Resolver Registry에서 사용 가능한 해양 resolver 목록을 보여줘')
    assert decision['allowed'] is False
    assert decision['diagnostic_target'] == 'resolver_registry'
