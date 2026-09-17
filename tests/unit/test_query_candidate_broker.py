from services.orchestrator.query_candidate_broker import (
    execution_contract_ready,
    query_candidate_broker,
)


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
