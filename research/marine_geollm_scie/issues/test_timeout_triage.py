"""Isolated contract probes, not live performance or production API evidence."""
import json
import pytest
from services.orchestrator import live_intent_comparison as live
from services.orchestrator import query_candidate_broker as broker


@pytest.mark.parametrize("metadata_timeout", [False, True])
def test_web_timeout_scope(monkeypatch, metadata_timeout):
    monkeypatch.delenv("GEOLLM_WEB_SHADOW_TIMEOUT", raising=False)
    monkeypatch.setattr(broker.QueryCandidateBroker, "build_trace", lambda *a, **kw: {})
    monkeypatch.setattr(broker, "_load_registry", lambda: {})
    candidates = [{"candidate_id": key, "capabilities": [], "rule_score": score,
                   "registry_readiness": 0, "context_completeness": 0}
                  for key, score in [("PLACE_LOOKUP", .8), ("OTHER", .2)]]
    monkeypatch.setattr(live, "prepare_candidates", lambda *a: candidates)
    monkeypatch.setattr(live, "registry_snapshot", lambda: {})
    calls = []
    def transport(url, payload=None, timeout=None):
        calls.append((url.rsplit("/", 1)[-1], timeout))
        if url.endswith("/tags"):
            if metadata_timeout: raise TimeoutError("isolated injected metadata timeout")
            return {"models": []}
        return {"done": True, "response": json.dumps({
            "scores": {"PLACE_LOOKUP": .8, "OTHER": .2}, "selected": "PLACE_LOOKUP",
            "quote": "독도", "location": "독도", "radius": None, "time": None,
            "capabilities": [], "reason": "지명 확인", "needs_clarification": False})}
    monkeypatch.setattr(live, "json_request", transport)
    result = live.compare("독도", {})
    assert calls[0] == ("tags", 10)
    if metadata_timeout:
        assert result["status"] == "FAILED" and result["called"] is False
        assert len(calls) == 1
        assert set(result["rankings"]) == {"rule"}
    else:
        assert calls[1] == ("generate", 180.0)
        assert result["status"] == "COMPLETED", result.get("error")
    assert result["human_gold"] is None
