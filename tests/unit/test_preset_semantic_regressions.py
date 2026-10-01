import pytest
from services.orchestrator import graph
from services.orchestrator.query_normalizer import QueryNormalizer
from shared.schemas.agent import AgentStatus


def test_evidence_word_is_not_changed_to_spatial_relation():
    query = '수로 측량 데이터 품질 관리 관련 근거 문서를 검색해줘'
    normalized = QueryNormalizer().normalize_with_debug(query)['normalized_query']
    assert '근거' in normalized and '근처' not in normalized
    assert not graph._looks_like_dataset_evidence_query(query)
    assert not graph._looks_like_legal_rag_query(query)
    assert graph._looks_like_legal_rag_query('부산항 통항 법령 근거를 찾아줘')
    assert graph._legal_notice_documents_for_query(query) == []
    assert graph._looks_like_dataset_evidence_query('Dataset 항로표지.csv 적재 근거를 보여줘')


@pytest.mark.parametrize('query', ['무창포 바다갈라짐 시간을 알려줘', '제부도 바닷길 예측 정보를 알려줘'])
def test_prediction_or_planned_area_cannot_complete_as_place_navigation(query):
    assert graph.check_intent_parsed({'query': query, 'normalized_query': query,
                                     'status': AgentStatus.INTENT_PARSED}) == 'fast_spatial_or_traffic_block'


@pytest.mark.parametrize('query', ['신항만예정지역을 지도에 표시해줘', '부산 신항만예정지역을 찾아줘'])
def test_planned_area_uses_real_layer_instead_of_port_centroid(query):
    from services.orchestrator.fast_path_policy import instant_place_navigation_decision
    assert not instant_place_navigation_decision(query)['allowed']
    target = graph._requested_spatial_layer_targets(query)[0]
    assert target['relation'] == 'serving.planned_port_area_current'
    assert graph.check_intent_parsed({'query': query, 'status': AgentStatus.INTENT_PARSED}) == 'fast_requested_spatial_layer_execute'


@pytest.mark.parametrize('query,anchor', [('독도 주변 해저지명과 사고 이력을 같이 보여줘', '독도'),
    ('해운대구 주변 천연보호구역을 찾아줘', '해운대구'), ('부근 해저지명 찾아줘', '')])
def test_target_words_are_not_invented_as_place_names(query, anchor):
    assert graph._requested_layer_anchor_query(query, graph._requested_spatial_layer_targets(query)) == anchor


@pytest.mark.parametrize('query,title', [
    ('부산항 항법 고시 근거를 설명해줘', '부산항 항법 등에 관한 규칙'),
    ('인천항 육상항만구역 지형도면', '인천항 육상항만구역 및 지형도면 변경 고시')])
def test_legal_registry_retains_explicit_notice_matches(query, title):
    assert any(doc['title'] == title for doc in graph._legal_notice_documents_for_query(query))
