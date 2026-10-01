import asyncio
import pytest
from services.orchestrator import graph, place_router


@pytest.mark.parametrize('query', ['울릉도 주변 지명을 찾아줘', '울릉도 반경 5km 지명을 찾아줘'])
def test_missing_anchor_keeps_understood_location_and_not_run(monkeypatch, query):
    seen = []
    def resolve(anchor, context):
        seen.append(anchor)
        return {'status': 'NEEDS_CLARIFICATION', 'error_code': 'LOCATION_UNCONFIRMED',
                'summary': 'missing', 'location_candidates': []}
    monkeypatch.setattr(place_router, 'resolve_payload', resolve)
    monkeypatch.setattr(graph, '_record_query_quality_issues', lambda *args: None)
    result = asyncio.run(graph.fast_requested_spatial_layer_execute_node({'query': query, 'task_id': 'test'}))['final_dict']
    assert seen == ['울릉도']
    assert result['status'] == 'NEEDS_CLARIFICATION'
    assert '울릉도' in result['answer_text'] and '0건이라는 뜻은 아닙니다' in result['answer_text']
    structured = result['structured_result']
    assert structured['query_interpretation']['location_text'] == '울릉도'
    assert structured['search_execution']['status'] == 'NOT_RUN'
    assert ('검색 반경도' in result['answer_text']) == ('5km' not in query)
    assert result['orchestrator_v2']['route_plan']['execution_ready'] is False
    assert result['orchestrator_v2']['query_execution_context']['slots']['location_text'] == '울릉도'


def test_missing_radius_retains_verified_location_without_granting_execution(monkeypatch):
    monkeypatch.setattr(place_router, 'resolve_payload', lambda *args: {
        'status': 'RESOLVED', 'geometry': 'POINT(130.9 37.5)', 'location_text': '확인된 위치',
        'crs': 'EPSG:4326', 'location_resolution': {'source_ref': 'fixture.place'}, 'summary': 'resolved'})
    monkeypatch.setattr(graph, '_record_query_quality_issues', lambda *args: None)
    result = asyncio.run(graph.fast_requested_spatial_layer_execute_node(
        {'query': '확인된 위치 주변 지명을 찾아줘', 'task_id': 'test'}))['final_dict']
    assert result['error_code'] == 'DISTANCE_REQUIRED'
    assert '기준 위치는 확인했습니다' in result['answer_text']
    assert result['structured_result']['location_resolution']['source_ref'] == 'fixture.place'
    assert result['orchestrator_v2']['query_execution_context']['slots']['reference_geometry'] == 'POINT(130.9 37.5)'
    assert result['orchestrator_v2']['route_plan']['execution_ready'] is False
    assert result['features']['features'] == []


def test_gazetteer_radius_uses_registry_identity_and_distance_tool(monkeypatch):
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
    adapter = SchemaBindingAdapter()
    target = graph._requested_spatial_layer_targets('울릉항 반경 5km 지명을 찾아줘')[0]
    assert target['layer_id'] == 'marine_gazetteer_mof'
    monkeypatch.setattr(adapter, '_inspect_relation', lambda relation: {
        'exists': True, 'has_select': True, 'columns': [{'name': 'geometry'}]})
    result = adapter.build_bindings({'analysis_type': 'feature_search_by_radius'},
                                    {'target_layers': [target['registry_id']]})
    assert not result.blockers
    assert result.data_bindings[0].relation == target['relation']
    assert result.tool_bindings[0].tool_id == 'postgis.dwithin'
    assert result.tool_bindings[0].operation == 'feature_search_by_radius'
    rejected = adapter.build_bindings({'analysis_type': 'feature_search_by_radius'},
                                      {'target_layers': ['unregistered_layer']})
    assert rejected.blockers and not rejected.data_bindings
