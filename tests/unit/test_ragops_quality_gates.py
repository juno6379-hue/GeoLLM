from services.orchestrator import graph
from shared.schemas.agent import AgentStatus


def test_blocked_no_evidence_fast_path_has_quality_metrics():
    metrics = graph._quality_metrics_from_state(
        {"graph_context": {}},
        fast_path="document_no_evidence",
        blocked_no_evidence=True,
    )

    assert metrics["method"] == "deterministic_authoritative_no_evidence_gate"
    assert metrics["estimated_accuracy"] >= 0.8
    assert metrics["kg_similarity"] > 0
    assert metrics["evidence_similarity"] > 0


def test_default_fast_path_quality_is_not_unavailable():
    metrics = graph._quality_metrics_from_state({"graph_context": {}}, fast_path="dataset_place_resolver")

    assert metrics["method"] == "deterministic_fast_path_default_quality_v1"
    assert metrics["estimated_accuracy"] >= 0.55
    assert metrics["confidence_band"] == "medium"


def test_blocked_data_is_not_logged_as_execution_not_ready(monkeypatch):
    recorded = []

    def fake_record_quality_issue(**kwargs):
        recorded.append(kwargs)

    monkeypatch.setattr(graph.collector, "record_quality_issue", fake_record_quality_issue)

    graph._record_query_quality_issues(
        {"query": "imaginaryfeature abc-999", "task_id": "task-1", "status": AgentStatus.BLOCKED},
        {
            "task_id": "task-1",
            "status": "BLOCKED",
            "error_code": "NO_AUTHORITATIVE_EVIDENCE",
            "quality_metrics": graph._quality_metrics_from_state(
                {"graph_context": {}},
                fast_path="document_no_evidence",
                blocked_no_evidence=True,
            ),
            "orchestrator_v2": {
                "route_plan": {
                    "analysis_type": "document_search",
                    "execution_ready": False,
                    "route_plan_status": "BLOCKED_DATA",
                    "tools": ["rag.graph_scoped_retrieve"],
                    "data": ["s101_feature_catalogue"],
                    "slots": {"target_term": "no_authoritative_evidence"},
                }
            },
        },
    )

    issue_types = {item["issue_type"] for item in recorded}
    assert "blocked_or_no_evidence_response" in issue_types
    assert "quality_metrics_unavailable" not in issue_types
    assert "execution_not_ready_without_clarification" not in issue_types


def test_unsafe_execution_ready_without_bindings_is_logged(monkeypatch):
    recorded = []

    def fake_record_quality_issue(**kwargs):
        recorded.append(kwargs)

    monkeypatch.setattr(graph.collector, "record_quality_issue", fake_record_quality_issue)

    graph._record_query_quality_issues(
        {"query": "bad ready", "task_id": "task-2", "status": AgentStatus.COMPLETED},
        {
            "task_id": "task-2",
            "status": "COMPLETED",
            "quality_metrics": graph._quality_metrics_from_state({"graph_context": {}}, fast_path="test"),
            "orchestrator_v2": {
                "route_plan": {
                    "analysis_type": "feature_search_by_radius",
                    "execution_ready": True,
                    "route_plan_status": "EXECUTION_READY",
                    "tools": [],
                    "data": [],
                    "slots": {},
                }
            },
        },
    )

    assert any(item["issue_type"] == "unsafe_execution_ready_without_bindings" for item in recorded)


def test_dataset_evidence_domain_blocks_legal_and_standard_overmatch():
    query = "해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘"

    assert graph._looks_like_dataset_evidence_query(query)
    assert not graph._looks_like_legal_rag_query(query)
    assert not graph._looks_like_standard_rag_query(query)

