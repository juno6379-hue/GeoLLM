import asyncio
import pytest
from services.orchestrator.graph import _looks_like_navigation_risk_analysis, fast_document_answer_node
from services.orchestrator.port_context import request_geometry, PortContextError

def test_navigation_risk_explanation_is_analysis_intent():
    assert _looks_like_navigation_risk_analysis("이 해역의 통항위험이 높은 이유를 설명해줘")
    assert not _looks_like_navigation_risk_analysis("인천항 선박통항규칙을 찾아줘")

def test_selected_geometry_takes_priority_over_viewport():
    geometry, method = request_geometry({"selected_feature": {"geometry": {"type": "Point", "coordinates": [126, 37]}},
                                         "map_bounds": [129,35,130,36]})
    assert geometry == "POINT (126 37)"
    assert method == "selected_feature"

@pytest.mark.parametrize("bounds", [[0,0,100,80], [129,35,128,36], [0,float('nan'),1,1]])
def test_invalid_analysis_extent_is_rejected(bounds):
    with pytest.raises(PortContextError):
        request_geometry({"map_bounds": bounds})

def test_missing_context_requests_location_without_db(monkeypatch):
    monkeypatch.delenv("S101_DB_URL", raising=False)
    final = asyncio.run(fast_document_answer_node({"task_id": "no-context", "query": "이 해역의 통항위험 원인을 설명해줘"}))["final_dict"]
    assert final["status"] == "NEEDS_CLARIFICATION"
    assert final["error_code"] == "LOCATION_REQUIRED"
    assert final["structured_result"]["traffic_analysis"] is None
    assert final["clarification_questions"]

def test_unavailable_port_source_does_not_fall_back_to_seed(monkeypatch):
    monkeypatch.delenv("S101_DB_URL", raising=False)
    final = asyncio.run(fast_document_answer_node({"task_id": "no-db", "query": "부산항 통항위험 원인을 설명해줘"}))["final_dict"]
    assert final["status"] == "BLOCKED"
    assert final["error_code"] == "PORT_SOURCE_UNAVAILABLE"
    assert final["structured_result"]["nearest_port_resolution"] is None

def test_missing_traffic_is_partial_not_zero(monkeypatch):
    from services.orchestrator import navigation_risk
    monkeypatch.setattr(navigation_risk, "resolve_port_context", lambda *_: {
        "port": "인천항", "geometry": "POLYGON((126.5 37.3,126.7 37.3,126.7 37.5,126.5 37.5,126.5 37.3))",
        "source_ref": "projection.s101_feature_valid", "source_id": "test-fixture"})
    def unavailable(_):
        raise RuntimeError("traffic relation is unavailable")
    monkeypatch.setattr("services.orchestrator.traffic_execution.execute_traffic_request", unavailable)
    final = asyncio.run(fast_document_answer_node({"task_id": "no-traffic", "query": "인천항 통항위험 원인을 설명해줘"}))["final_dict"]
    assert final["status"] == "PARTIAL"
    assert final["structured_result"]["traffic_analysis"] is None
    assert final["structured_result"]["traffic_error"] == "traffic relation is unavailable"
    assert final["quality_metrics"]["estimated_accuracy"] is None
    assert "0건" not in final["answer_text"]
    assert "종합 위험도는 확정하지 않았습니다" in final["answer_text"]
    bindings = final["orchestrator_v2"]["query_execution_context"]["tool_bindings"]
    assert bindings[-1]["status"] == "FAILED"
