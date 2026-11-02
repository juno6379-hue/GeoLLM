"""Dashboard operation obligations and source-backed explanation regressions."""
import asyncio
import pytest
from shared.schemas.agent import AgentStatus
from services.orchestrator import graph
from services.orchestrator import query_candidate_broker as broker
from services.orchestrator.definition_router import resolve_definition, is_definition_query
from services.orchestrator.definition_response import build_definition_response


@pytest.mark.parametrize('query', ['부산항입구위험객체','부산항 입구 위험 객체 알려줘','부산항 입구 5km 이내 위험물','근처 위험물'])
def test_hazard_request_reaches_slot_validator_without_candidate_permission(query):
    state={'query':query,'candidate_trace':{},'spatial_context':{}}
    assert graph._should_fast_execute_s101_hazard_radius(state)
    assert any(signal.signal_id == 'hazard_target' for signal in broker._signal_scan(query))


def test_registered_concept_comparison_is_not_spatial():
    query='침선과 장애물의 차이'
    entry=resolve_definition(query)
    assert entry and len(entry['comparison_entries']) == 2
    assert {item['term_id'] for item in entry['comparison_entries']} == {'Wreck','Obstruction'}
    assert all(item['alias_binding_ref'].startswith('data/s101_feature_dictionary.yaml#') for item in entry['comparison_entries'])
    assert is_definition_query(query)
    assert not graph._should_fast_execute_s101_hazard_radius({'query':query})
    result=build_definition_response({'task_id':'comparison-fixture','query':query,'user_id':'fixture'})
    assert result
    final=result['final_dict']
    assert len(final['evidence_bundle']['rag_evidence'])==2
    assert len(result['query_execution_context']['data_bindings'])==2
    assert all(item['definition_ko'] in final['answer_text'] for item in entry['comparison_entries'])
    assert '특정 위치' in final['answer_text']


def test_spatial_composite_not_reduced_to_definition():
    assert not is_definition_query('부산항 5km 침선과 장애물의 차이')
    assert resolve_definition('위험 객체') is None


def test_product_explanation_is_bound_to_exact_registry_product():
    entry=resolve_definition('S-101이 뭐야')
    assert entry and entry['term_id']=='S-101'
    assert 'Electronic Navigational Chart' in entry['definition_ko']
    assert entry['verification_status']=='LOCAL_PRODUCT_REGISTRY'
    assert entry['source_ref'].endswith('/S-101')
    assert is_definition_query('S-101이 뭐야')


@pytest.mark.parametrize('query,code,status',[
    ('항로 안전성 분석','MISSING_ROUTE_GEOMETRY','NEEDS_CLARIFICATION'),
    ('부산 가장 가까운 항만','NEAREST_HARBOUR_CAPABILITY_UNAVAILABLE','BLOCKED'),
    ('전국 모든 침선을 빠짐없이 알려줘','REAL_WORLD_COMPLETENESS_UNVERIFIED','BLOCKED'),
])
def test_unfulfilled_obligations_are_not_place_or_radius_queries(query,code,status):
    result=graph._incomplete_operation_response({'task_id':'obligation-fixture','query':query})
    final=result['final_dict']
    assert final['error_code']==code and final['status']==status
    assert final['structured_result']['count'] is None
    assert all(v is False for v in final['structured_result']['search_execution'].values())
    assert 'DISTANCE_REQUIRED' not in final['answer_text']


def test_normal_source_bound_query_not_blocked_by_preflight():
    assert graph._incomplete_operation_response({'query':'독도 5km 해양지명','task_id':'normal'}) is None


def test_ambiguous_hazard_requests_input_instead_of_data_failure(monkeypatch):
    monkeypatch.setattr(graph,'_record_query_quality_issues',lambda *a:None)
    result=asyncio.run(graph.fast_spatial_or_traffic_block_node({'task_id':'ambiguous','query':'위험한 곳 알려줘'}))
    final=result['final_dict']
    assert result['status']==AgentStatus.NEEDS_CLARIFICATION
    assert final['status']=='NEEDS_CLARIFICATION'
    assert final['clarification_questions']
    assert final['orchestrator_v2']['route_plan']['clarification_required']
    assert final['orchestrator_v2']['query_execution_context']['readiness']=='NEEDS_USER_INPUT'
    assert 'BLOCKED_DATA' not in final['answer_text']
    assert all(v is False for v in final['structured_result']['search_execution'].values())
