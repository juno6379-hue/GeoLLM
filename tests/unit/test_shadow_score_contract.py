"""Scores-only model contract has one explicit, non-executing selection source."""
import json
import pytest
from jsonschema import ValidationError
from services.orchestrator import live_intent_comparison as live

CANDIDATES = [{"candidate_id": "SPATIAL", "capabilities": []},
              {"candidate_id": "PLACE", "capabilities": []}]
QUERY = "항구 주변 검색"

def response(**changes):
    return {"scores": {"SPATIAL": 0.9, "PLACE": 0.2}, "abstain": False,
            "quote": QUERY, "location": None, "radius": None, "time": None,
            "capabilities": [], "reason": "공간 검색", "needs_clarification": False,
            **changes}

def test_single_rank_source_is_explicit_and_raw_is_unchanged():
    raw = json.dumps(response())
    value, receipt = live.validate_ranked_response(raw, CANDIDATES, QUERY)
    assert value.selected == "SPATIAL"
    assert receipt["origin"] == "unique_score_argmax"
    assert not receipt["used_for_execution"]
    assert not receipt["semantic_accuracy_verified"]
    assert "selected" not in json.loads(raw)

@pytest.mark.parametrize("change,tied", [({"abstain": True}, False),
    ({"scores": {"SPATIAL": 0.7, "PLACE": 0.7}}, True)])
def test_abstention_and_ties_never_pick_arbitrary_candidate(change, tied):
    value, receipt = live.validate_ranked_response(json.dumps(response(**change)), CANDIDATES, QUERY)
    assert value.selected is None
    assert receipt["tie_abstention"] == tied

@pytest.mark.parametrize("change", [
    {"scores": {"SPATIAL": 0.9}},
    {"scores": {"SPATIAL": 0.9, "PLACE": 0.2, "OTHER": 0.1}},
    {"scores": {"SPATIAL": float("nan"), "PLACE": 0.2}},
    {"scores": {"SPATIAL": float("inf"), "PLACE": 0.2}},
    {"scores": [{"candidate_id": "SPATIAL", "score": 0.9}] * 2},
    {"selected": "PLACE"}, {"abstain": "false"}, {"location": "부산"},
    {"scores": {"SPATIAL": 2, "PLACE": 0.2}},
    {"scores": {"SPATIAL": 0.95, "PLACE": 0.2}},
])
def test_invalid_scores_or_legacy_selection_are_not_repaired(change):
    with pytest.raises((ValueError, ValidationError)):
        live.validate_ranked_response(json.dumps(response(**change)), CANDIDATES, QUERY)

def test_duplicate_json_score_key_is_not_silently_overwritten():
    raw = json.dumps(response()).replace('"SPATIAL": 0.9', '"SPATIAL": 0.1, "SPATIAL": 0.9')
    with pytest.raises(ValueError, match="duplicate"):
        live.validate_ranked_response(raw, CANDIDATES, QUERY)
