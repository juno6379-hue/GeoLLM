import asyncio

from services.orchestrator.graph import (
    _legal_query_with_spatial_context,
    _looks_like_navigation_risk_analysis,
    _nearest_port_from_map_context,
    fast_document_answer_node,
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


def test_incheon_map_center_resolves_incheon_port():
    label, geometry, distance_m = _nearest_port_from_map_context(
        {"map_bounds": [126.50, 37.35, 126.70, 37.55]}
    )
    assert label == "인천항"
    assert geometry == "POINT(126.604 37.456)"
    assert distance_m is not None and distance_m < 1000


def _without_traffic(monkeypatch):
    def unavailable(_state):
        raise RuntimeError("traffic relation is unavailable")

    monkeypatch.setattr("services.orchestrator.traffic_execution.execute_traffic_request", unavailable)
    monkeypatch.setattr("services.orchestrator.graph._record_query_quality_issues", lambda *_: None)


def test_explicit_port_is_grounded_without_map(monkeypatch):
    _without_traffic(monkeypatch)
    final = asyncio.run(fast_document_answer_node({
        "task_id": "explicit-port-test", "query": "인천항 통항위험 원인을 설명해줘",
        "spatial_context": {},
    }))["final_dict"]
    assert final["agent_name"] == "Navigation Risk Analysis Agent"
    assert final["structured_result"]["documents"]
    assert all("인천항" in doc["ports"] for doc in final["structured_result"]["documents"])


def test_missing_context_does_not_choose_a_port(monkeypatch):
    _without_traffic(monkeypatch)
    final = asyncio.run(fast_document_answer_node({
        "task_id": "no-map-test", "query": "이 해역의 통항위험 원인을 설명해줘",
        "spatial_context": {},
    }))["final_dict"]
    assert final["status"] == "BLOCKED"
    assert final["structured_result"]["nearest_port_resolution"]["port"] is None
    assert final["structured_result"]["traffic_analysis"] is None
    assert not final["structured_result"]["documents"]


def test_unavailable_traffic_is_partial_evidence_not_zero_traffic(monkeypatch):
    _without_traffic(monkeypatch)
    final = asyncio.run(fast_document_answer_node({
        "task_id": "missing-traffic-test", "query": "이 해역의 통항위험 원인을 설명해줘",
        "spatial_context": {"map_bounds": [128.98, 35.02, 129.18, 35.18]},
    }))["final_dict"]
    structured = final["structured_result"]
    assert structured["traffic_analysis"] is None
    assert structured["traffic_error"] == "traffic relation is unavailable"
    assert structured["documents"]
    assert structured["quality_metrics"]["estimated_accuracy"] < 1
    assert "종합 위험도는 확정하지 않았습니다" in final["answer_text"]
