from services.orchestrator.query_candidate_broker import (
    execution_contract_ready,
    query_candidate_broker,
)
from shared.schemas.agent import ExecutionSlots


def test_accident_lookup_contract_is_registry_ready_without_pgvector(monkeypatch):
    monkeypatch.setenv("GEOLLM_CAPABILITY_PGVECTOR", "false")
    monkeypatch.delenv("S101_DB_URL", raising=False)
    monkeypatch.delenv("POSTGIS_URL", raising=False)

    trace = query_candidate_broker.build_trace("창원 정비불량 사건을 찾아줘")

    assert execution_contract_ready(
        trace,
        route="ACCIDENT_ANALYSIS",
        capability_id="tool.accident_event_lookup",
    )
    signals = {row["signal_id"] for row in trace["deterministic_signals"]}
    assert {"accident_cause", "accident_event", "structured_event_lookup"} <= signals
    verified = {
        row["candidate_id"]
        for row in trace["verified_candidates"]
        if row["status"] == "verified_ready"
    }
    assert {"tool.accident_event_lookup", "dataset.accident_events"} <= verified


def test_compacted_korean_query_uses_registry_lexical_signals(monkeypatch):
    monkeypatch.setenv("GEOLLM_CAPABILITY_PGVECTOR", "false")

    trace = query_candidate_broker.build_trace("독도부근해저지명")

    route_scores = {row["route"]: row["score"] for row in trace["route_candidates"]}
    assert route_scores["SPATIAL_ANALYSIS"] > 0
    signals = {row["signal_id"] for row in trace["deterministic_signals"]}
    assert {"nearby_search", "marine_gazetteer_target"} <= signals


def test_nearby_accident_history_prefers_spatial_history_tool(monkeypatch):
    monkeypatch.setenv("GEOLLM_CAPABILITY_PGVECTOR", "false")

    trace = query_candidate_broker.build_trace("독도 부근 사고 이력")

    signals = {row["signal_id"] for row in trace["deterministic_signals"]}
    assert {"accident_event", "accident_history", "nearby_search"} <= signals
    assert trace["capability_candidates"][0]["candidate_id"] == "tool.accident_spatial_history_lookup"
    assert execution_contract_ready(
        trace,
        route="ACCIDENT_ANALYSIS",
        capability_id="tool.accident_spatial_history_lookup",
    )


def test_place_accident_history_uses_spatial_history_tool_without_nearby_word(monkeypatch):
    monkeypatch.setenv("GEOLLM_CAPABILITY_PGVECTOR", "false")

    trace = query_candidate_broker.build_trace("독도 사고 이력")

    signals = {row["signal_id"] for row in trace["deterministic_signals"]}
    assert {"accident_event", "accident_history", "place_name"} <= signals
    assert trace["execution_contract"]["execution_route"] == "ACCIDENT_ANALYSIS"
    assert trace["capability_candidates"][0]["candidate_id"] == "tool.accident_spatial_history_lookup"
    assert execution_contract_ready(
        trace,
        route="ACCIDENT_ANALYSIS",
        capability_id="tool.accident_spatial_history_lookup",
    )


def test_spatial_relation_is_not_promoted_to_derived_concept():
    slots = ExecutionSlots.from_payload({"derived_concepts": ["부근"], "spatial_relation": "부근"})

    assert slots.spatial_relation == "부근"
    assert slots.derived_concept is None
