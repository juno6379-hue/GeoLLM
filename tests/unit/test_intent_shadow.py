import copy
import json

import pytest

from services.orchestrator import intent_shadow as shadow
from scripts.run_intent_shadow import fit_temperature, summarize, validate_dataset


@pytest.fixture
def candidates():
    return [{"candidate_id": "A", "rule_score": .8, "registry_readiness": 0., "context_completeness": 0., "signals": [], "capabilities": []},
            {"candidate_id": "B", "rule_score": .7, "registry_readiness": 1., "context_completeness": 1., "signals": [], "capabilities": []}]


def judgement():
    return {"assessments": [{"candidate_id": c, "score": score, "context_fit": .5,
                              "query_quote": "test", "capability_ids": [], "rationale": "No capability contract supplied", "unmet_requirements": [],
                              "required_evidence": [], "missing_slots": [], "reason_codes": ["INTENT_MATCH"]}
                             for c,score in [("A",.1),("B",.9)]],
            "selected_candidate": "B", "intent_description": "test", "analysis_type": "test",
            "requires_clarification": False, "out_of_candidates": False}


@pytest.mark.parametrize("mutation", ["unknown", "duplicate", "nan", "extra", "contradiction", "missing"])
def test_invalid_model_output_rejected(candidates, mutation):
    value = judgement()
    if mutation == "unknown": value["selected_candidate"] = "UNREGISTERED"
    if mutation == "duplicate": value["assessments"][1]["candidate_id"] = "A"
    if mutation == "nan": value["assessments"][0]["score"] = float("nan")
    if mutation == "extra": value["sql"] = "not allowed"
    if mutation == "contradiction": value["selected_candidate"] = "A"
    if mutation == "missing": value["assessments"].pop()
    with pytest.raises(ValueError): shadow.validate_judgement(json.dumps(value), candidates)


def test_inference_never_mutates_candidates_or_grants_execution(candidates, monkeypatch):
    before = copy.deepcopy(candidates)
    def request(url, payload, timeout):
        shown = json.loads(payload["prompt"])
        assert all("rule_score" not in c and "signals" not in c for c in shown["candidates"])
        assert "expected_route" not in shown and "split" not in shown
        return {"done": True, "response": json.dumps(judgement())}
    monkeypatch.setattr(shadow, "json_request", request)
    result = shadow.score_candidates("test", {}, candidates, base_url="http://test", model="test", prompt_text="test")
    assert result["accepted"] and result["used"] is False
    assert candidates == before


def test_timeout_cannot_replace_rule_ranking(candidates, monkeypatch):
    def request(*args): raise TimeoutError("test")
    monkeypatch.setattr(shadow, "json_request", request)
    result = shadow.score_candidates("test", {}, candidates, base_url="http://test", model="test", prompt_text="test")
    assert not result["accepted"] and not result["used"]
    assert list(shadow.rankings(candidates, result)) == ["rule"]


def test_fabricated_rationale_reference_rejected(candidates):
    value = judgement()
    value['assessments'][0]['capability_ids'] = ['invented.tool']
    with pytest.raises(ValueError, match='capability'):
        shadow.validate_judgement(json.dumps(value), candidates, query='test')
    value = judgement()
    with pytest.raises(ValueError, match='verbatim'):
        shadow.validate_judgement(json.dumps(value), candidates, query='different input')


def test_ties_preserve_original_rule_order(candidates):
    candidates[0]["candidate_id"] = "Z"
    candidates[1]["rule_score"] = candidates[0]["rule_score"]
    assert shadow.rankings(candidates, {})["rule"]["ranking"] == ["Z", "B"]


def test_model_selection_breaks_equal_model_scores(candidates):
    value = judgement()
    for item in value["assessments"]:
        item["score"] = .5
    result = shadow.rankings(candidates, {"accepted": True, "judgement": value})
    assert result["ollama"]["ranking"][0] == "B"
    assert result["ollama_calibrated"]["ranking"][0] == "B"
    assert result["rule"]["ranking"][0] == "A"


def test_calibration_never_reads_evaluation_labels(candidates):
    row = {"case": {"id":"c","split":"calibration","expected_route":"B"}, "candidates": candidates,
           "shadow": {"accepted": True,"judgement": judgement()}}
    heldout = {**row, "case": {"id":"e","split":"evaluation","expected_route":"A"}}
    assert fit_temperature([row,heldout]) == fit_temperature([row])


def test_candidate_miss_and_invalid_response_remain_in_denominator(candidates):
    row = {"case": {"id":"e","split":"evaluation","expected_route":"MISSING"}, "candidates": candidates,
           "shadow": {"accepted":False,"latency_ms":1.}}
    report = summarize([row], {"temperature":1.}, {"label_status":"REVIEW_REQUIRED"})
    assert report["reference_label_coverage"] == 0
    assert report["metrics_all_evaluation"]["rule"]["provisional_label_agreement"] == 0
    assert report["semantic_candidate_recall"] is None
    assert report["task_adequacy"]["status"] == "NOT_REVIEWED"
    assert report["metrics_all_evaluation"]["rule"]["label_disagreements"][0]["semantic_verdict"] == "NOT_REVIEWED"
    assert report["gold_label_accuracy"] is None
    assert report["qlora_decision"]["apply"] is False


def test_lineage_leakage_rejected():
    with pytest.raises(ValueError,match="Lineage"):
        validate_dataset({"cases":[{"id":"1","query":"a","group":"g","split":"calibration"},
                                   {"id":"2","query":"b","group":"g","split":"evaluation"}]})
