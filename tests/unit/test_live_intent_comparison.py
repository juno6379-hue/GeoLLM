import json

import pytest

from services.orchestrator import live_intent_comparison as live
from services.orchestrator.place_router import allow_display_navigation


def candidate():
    return {"label": "해운대구, 부산광역시, 대한민국", "geometry": "POINT(129.1638 35.1629)",
            "crs": "EPSG:4326", "source_ref": "OpenStreetMap Nominatim", "source_url": "https://www.openstreetmap.org/relation/1",
            "authority_level": "supplemental", "requires_confirmation": True}


def test_review_history_survives_reopen_and_keeps_request_order(tmp_path):
    path = tmp_path / "review.sqlite3"
    db = live.ComparisonStore(path, worker=False)
    db.update("old", comparison_id="old", created_at=1, query="원문", human_gold=None)
    db.update("new", comparison_id="new", created_at=2, query="새 질의", human_gold=None, status="COMPLETED")
    db.update("old", status="COMPLETED")
    reopened = live.ComparisonStore(path, worker=False)
    assert [row["comparison_id"] for row in reopened.recent(2)] == ["new", "old"]
    assert reopened.recent(1)[0]["human_gold"] is None


def test_review_observation_preserves_actual_normalization(monkeypatch, tmp_path):
    db = live.ComparisonStore(tmp_path / "review.sqlite3", worker=False)
    monkeypatch.setattr(live, "store", lambda: db)
    live.observe("request", {"status": "BLOCKED", "orchestrator_v2": {
        "candidate_trace": {"normalized_query": "부산항 반경 1km"},
        "query_execution_context": {"readiness": "BLOCKED_DATA", "blockers": ["source missing"]}}})
    row = db.get("request")
    assert row["execution"]["normalized_query"] == "부산항 반경 1km"
    assert row["execution"]["query_execution_context"]["blockers"] == ["source missing"]


def payload():
    return {"status": "NEEDS_CLARIFICATION", "error_code": "EXTERNAL_PLACE_CANDIDATES",
            "external_evidence_report": {"domain_id": "administrative_place_lookup"}, "location_candidates": [candidate()]}


def test_exact_navigation_is_display_only_without_mutating_evidence():
    source = payload()
    result = allow_display_navigation("해운대구로 이동", source, {"map_bounds": [1, 2, 3, 4]})
    assert result["status"] == "RESOLVED"
    assert result["execution_permission"]["allowed"]
    assert not result["location_resolution"]["use_as_authority"]
    assert not result["execution_permission"]["registry_promoted"]
    assert source["location_candidates"][0]["requires_confirmation"]


@pytest.mark.parametrize("query", ["해운대구", "해운대구 분석", "해운대구 위험객체로 이동", "해운대구로 이동하고 사고 분석", "해운대구 제외 이동", "해운대구 예측 이동"])
def test_analysis_compound_and_lookup_do_not_receive_navigation_permission(query):
    assert allow_display_navigation(query, payload())["status"] == "NEEDS_CLARIFICATION"


@pytest.mark.parametrize("field,value", [("geometry", "POINT(999 35)"), ("geometry", "POINT(nan 35)"),
                                       ("source_ref", None), ("source_url", None), ("label", "해운대구청, 부산"), ("crs", "EPSG:5179")])
def test_invalid_or_nonexact_source_is_not_auto_resolved(field, value):
    p = payload()
    p["location_candidates"][0][field] = value
    assert not allow_display_navigation("해운대구로 이동", p)["execution_permission"]["allowed"]


def test_ambiguity_and_constraints_require_confirmation():
    p = payload()
    p["location_candidates"].append(candidate())
    assert not allow_display_navigation("해운대구로 이동", p)["execution_permission"]["allowed"]
    assert not allow_display_navigation("해운대구로 이동", payload(), {"exclusions": ["육상"]})["execution_permission"]["allowed"]


def judgement():
    return {"scores": [{"candidate_id": "PLACE_LOOKUP", "score": .9}, {"candidate_id": "OTHER", "score": .1}],
            "selected": "PLACE_LOOKUP", "quote": "해운대구로 이동", "location": "해운대구", "radius": None,
            "time": None, "capabilities": ["place"], "reason": "지도 이동", "needs_clarification": False}


CANDIDATES = [{"candidate_id": "PLACE_LOOKUP", "capabilities": [{"id": "place"}]}, {"candidate_id": "OTHER", "capabilities": []}]


@pytest.mark.parametrize("change", [{"location": "부산"}, {"radius": "3km"}, {"selected": "OTHER"}, {"capabilities": ["invented"]},
                                    {"scores": [{"candidate_id": "OTHER", "score": .1}]}, {"quote": ""}])
def test_model_output_validation_rejects_ungrounded_or_inconsistent_output(change):
    data = {**judgement(), **change}
    with pytest.raises(ValueError):
        live.validate(json.dumps(data), CANDIDATES, "해운대구로 이동")


def test_valid_model_output_does_not_claim_semantic_accuracy():
    assert live.validate(json.dumps(judgement()), CANDIDATES, "해운대구로 이동").selected == "PLACE_LOOKUP"


def test_attempt_ids_queue_overload_and_restart_are_explicit(tmp_path):
    path = tmp_path / "compare.db"
    store = live.ComparisonStore(path, capacity=1, worker=False)
    first = store.submit("same-task", "해운대구로 이동", {})
    second = store.submit("same-task", "부산으로 이동", {})
    assert first != second
    assert store.get(second)["status"] == "QUEUE_FULL"
    assert not store.get(first)["execution_authority"]
    store.update(first, execution={"status": "COMPLETED"})
    store.update(first, status="RUNNING", called=True)
    assert store.get(first)["execution"]["status"] == "COMPLETED"
    reopened = live.ComparisonStore(path, worker=False)
    assert reopened.get(first)["status"] == "INTERRUPTED"
    assert reopened.get(second)["status"] == "QUEUE_FULL"


@pytest.mark.parametrize("failure", [False, True])
def test_actual_transport_contract_keeps_rule_model_mix_separate(monkeypatch, failure):
    monkeypatch.setenv("GEOLLM_WEB_SHADOW_MODEL", "qwen3.5:4b")
    from services.orchestrator import query_candidate_broker as broker
    calls = []
    monkeypatch.setattr(broker.QueryCandidateBroker, "build_trace", lambda self, query, **kw: {"allow_ollama": kw["allow_ollama"]})
    monkeypatch.setattr(broker, "_load_registry", lambda: {})
    candidates = [{**r, "rule_score": .8 if r["candidate_id"] == "PLACE_LOOKUP" else .2,
                   "registry_readiness": 0, "context_completeness": 0} for r in CANDIDATES]
    monkeypatch.setattr(live, "prepare_candidates", lambda *args: candidates)
    monkeypatch.setattr(live, "registry_snapshot", lambda: {"test": "hash"})

    def transport(url, payload=None, timeout=None):
        calls.append((url, payload))
        if url.endswith("/api/tags"):
            return {"models": [{"name": "qwen3.5:4b", "digest": "actual-digest"}]}
        if failure:
            raise TimeoutError("model timed out")
        answer = judgement()
        answer.pop("selected")
        answer["abstain"] = False
        answer["scores"] = {row["candidate_id"]: row["score"] for row in answer["scores"]}
        return {"done": True, "response": json.dumps(answer)}

    monkeypatch.setattr(live, "json_request", transport)
    record = live.compare("해운대구로 이동", {})
    assert record["called"]
    assert record["candidate_trace"]["allow_ollama"] is False
    assert record["model_digest"] == "actual-digest"
    shown = json.loads(calls[-1][1]["prompt"])["candidates"]
    assert {r["candidate_id"] for r in shown} == {r["candidate_id"] for r in candidates}
    assert all("rule_score" not in r for r in shown)
    assert record["calibration"] == "UNFITTED" and record["human_gold"] is None
    if failure:
        assert record["status"] == "FAILED" and set(record["rankings"]) == {"rule"}
        assert not record["accepted"]
    else:
        assert record["status"] == "COMPLETED"
        assert set(record["rankings"]) == {"rule", "ollama", "simple_mix"}


def test_schema_constrains_null_and_candidate_coverage():
    schema = live.grounded_schema("해운대구로 이동", CANDIDATES)
    assert "해운대구" in schema["properties"]["location"]["enum"]
    assert "null" not in schema["properties"]["location"]["enum"]
    assert schema["properties"]["radius"]["enum"] == [None]
    assert set(schema["properties"]["scores"]["required"]) == {"PLACE_LOOKUP", "OTHER"}
    schema = live.grounded_schema("해운대구 1km 주변 최근 3개월 사고", CANDIDATES)
    assert "1km" in schema["properties"]["radius"]["enum"]
    assert "3개월" not in schema["properties"]["radius"]["enum"]
