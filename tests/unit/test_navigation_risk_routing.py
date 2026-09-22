from services.orchestrator.graph import (
    _legal_query_with_spatial_context,
    _looks_like_navigation_risk_analysis,
    _nearest_port_from_map_context,
)


def test_navigation_risk_explanation_is_analysis_intent():
    assert _looks_like_navigation_risk_analysis("이 해역의 통항위험이 높은 이유를 설명해줘")
    assert _looks_like_navigation_risk_analysis("현재 항행 위험 원인을 분석해줘")
    assert not _looks_like_navigation_risk_analysis("인천항 선박통항규칙을 찾아줘")


def test_map_center_resolves_nearest_port():
    spatial = {"map_bounds": [128.98, 35.02, 129.18, 35.18]}
    label, geometry, distance_m = _nearest_port_from_map_context(spatial)
    assert label == "부산항"
    assert geometry == "POINT(129.0756 35.1028)"
    assert distance_m is not None and distance_m < 1000


def test_deictic_sea_area_is_grounded_with_nearest_port():
    state = {"spatial_context": {"map_bounds": [128.98, 35.02, 129.18, 35.18]}}
    query, location = _legal_query_with_spatial_context(state, "이 해역의 통항위험이 높은 이유를 설명해줘")
    assert location == "부산항"
    assert query.endswith("부산항")
