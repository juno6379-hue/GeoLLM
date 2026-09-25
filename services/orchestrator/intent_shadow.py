"""Offline shadow reranking. This module cannot execute or select service tools."""
from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.request
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "configs/evaluation/intent_shadow_prompt.txt"


class CandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    score: float = Field(ge=0, le=1, allow_inf_nan=False)
    context_fit: float = Field(ge=0, le=1, allow_inf_nan=False)
    query_quote: str = Field(min_length=1, max_length=100)
    capability_ids: list[str] = Field(max_length=3)
    rationale: str = Field(min_length=1, max_length=240)
    unmet_requirements: list[str] = Field(max_length=3)
    required_evidence: list[str] = Field(max_length=8)
    missing_slots: list[str] = Field(max_length=8)
    reason_codes: list[Literal["INTENT_MATCH", "INTENT_MISMATCH", "CONTEXT_MATCH", "MISSING_CONTEXT",
                              "COMPOSITE_REQUEST", "MISSING_EVIDENCE", "DEFINITION_ONLY", "EXECUTION_REQUEST"]] = Field(max_length=8)


class IntentAmbiguityJudgement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assessments: list[CandidateAssessment] = Field(min_length=2, max_length=4)
    selected_candidate: str | None
    intent_description: str = Field(max_length=300)
    analysis_type: str = Field(max_length=100)
    requires_clarification: bool
    out_of_candidates: bool


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def registry_snapshot() -> dict:
    names = ["capability_registry.yaml", "marine_term_dictionary.yaml", "derived_concept_registry_v2.yaml",
             "spatial_layer_registry.yaml", "query_template_registry.yaml", "definition_term_registry.yaml"]
    return {name: hashlib.sha256((ROOT / "data" / name).read_bytes()).hexdigest() for name in names}


def prepare_candidates(trace: dict, context: dict, registry: dict) -> list[dict]:
    """Same candidates for every ranking; never inject the expected label."""
    descriptions = {row["capability_id"]: row for row in registry.get("capabilities", [])}
    checks = {row["candidate_id"]: row for row in trace.get("verified_candidates", [])}
    supplied = {"query_text", "query"} | {key for key, value in context.items() if value not in (None, {}, [], "")}
    supplied |= {key for key, value in (context.get("spatial_context") or {}).items() if value not in (None, {}, [], "")}
    candidates = []
    for row in trace.get("route_candidates", [])[:4]:
        capabilities = [c for c in trace.get("capability_candidates", []) if row["route"] in c.get("routes", [])]
        support = []
        readiness = []
        completeness = []
        for capability in capabilities[:3]:
            identifier = capability["candidate_id"]
            entry = descriptions.get(identifier, {})
            check = checks.get(identifier, {})
            # A declaration or a file's existence does not prove tool readiness.
            verified = all(check.get(k, {}).get("status") == "verified" for k in ("authority_check", "registry_check"))
            readiness.append(float(verified))
            required = set(capability.get("input_slots") or [])
            completeness.append(len(required & supplied) / len(required) if required else 1.)
            support.append({"id": identifier, "description": entry.get("description") or capability.get("label"),
                            "input_slots": sorted(required), "output_slots": capability.get("output_slots", []),
                            "references_verified": verified})
        candidates.append({"candidate_id": row["route"], "rule_score": float(row.get("score", 0)),
                           "registry_readiness": max(readiness, default=0.),
                           "context_completeness": max(completeness, default=0.),
                           "capabilities": support, "signals": row.get("signals", [])})
    if not 2 <= len(candidates) <= 4:
        raise ValueError("Shadow experiment requires 2–4 existing candidates")
    return candidates


def validate_judgement(raw: str, candidates: list[dict], query: str | None = None) -> IntentAmbiguityJudgement:
    result = IntentAmbiguityJudgement.model_validate_json(raw)
    expected = {c["candidate_id"] for c in candidates}
    actual = [c.candidate_id for c in result.assessments]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError("Model must score every supplied candidate exactly once")
    for assessment in result.assessments:
        candidate = next(c for c in candidates if c['candidate_id'] == assessment.candidate_id)
        available = {c['id'] for c in candidate.get('capabilities', [])}
        if set(assessment.capability_ids) - available:
            raise ValueError('Rationale cites a capability not supplied for this candidate')
        if query is not None and assessment.query_quote not in query:
            raise ValueError('Rationale quote must occur verbatim in the query')
    if result.selected_candidate is not None and result.selected_candidate not in expected:
        raise ValueError("Model selected an unknown candidate")
    if result.out_of_candidates and result.selected_candidate is not None:
        raise ValueError("Out-of-candidates judgement must abstain")
    if not result.out_of_candidates and result.selected_candidate is None:
        raise ValueError("A supported judgement must select a candidate")
    if result.selected_candidate:
        chosen = next(row.score for row in result.assessments if row.candidate_id == result.selected_candidate)
        if chosen < max(row.score for row in result.assessments):
            raise ValueError("Selected candidate contradicts model scores")
    return result


def json_request(url: str, payload=None, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def score_candidates(query: str, context: dict, candidates: list[dict], *, base_url: str,
                     model: str, timeout=120, prompt_text=None) -> dict:
    prompt = prompt_text if prompt_text is not None else PROMPT.read_text(encoding="utf-8")
    # No rule scores, label, split, or review metadata are sent to the model.
    shown = [{"candidate_id": row["candidate_id"], "capabilities": [
        {"id": c["id"], "description": (c.get("description") or "")[:160],
         "input_slots": c["input_slots"], "output_slots": c["output_slots"]}
        for c in row.get("capabilities", [])]} for row in candidates]
    # Stable shuffle reduces first-position bias without changing candidate identity.
    shown.sort(key=lambda row: fingerprint([query, row["candidate_id"]]))
    inputs = {"query": query, "context": context, "candidates": shown}
    schema = IntentAmbiguityJudgement.model_json_schema()
    identifiers = [c['candidate_id'] for c in candidates]
    schema['$defs']['CandidateAssessment']['properties']['candidate_id']['enum'] = identifiers
    schema['properties']['assessments'].update(minItems=len(identifiers), maxItems=len(identifiers))
    schema['properties']['selected_candidate']['anyOf'][0]['enum'] = identifiers
    request = {"model": model, "system": prompt, "prompt": json.dumps(inputs, ensure_ascii=False, separators=(',', ':')),
               "format": schema, "stream": False,
               "options": {"temperature": 0, "seed": 20260925, "num_predict": 1800, "num_ctx": 4096}}
    record = {"called": True, "used": False, "accepted": False, "mode": "shadow_no_execution_change",
              "acceptance_scope": "structure_and_reference_integrity_only", "semantic_review_required": True,
              "prompt_hash": fingerprint(prompt), "request_hash": fingerprint(request), "request": request}
    start = time.monotonic()
    try:
        response = json_request(base_url.rstrip("/") + "/api/generate", request, timeout)
        record["raw_response"] = response
        if not response.get("done") or response.get("done_reason") == "length":
            raise ValueError("Model response did not finish normally")
        judgement = validate_judgement(response.get("response", ""), candidates, query=query)
        record.update(accepted=True, judgement=judgement.model_dump(), rejected_reason=None)
    except Exception as exc:
        record["rejected_reason"] = f"{type(exc).__name__}: {exc}"
    record["latency_ms"] = round((time.monotonic() - start) * 1000, 2)
    return record


def distribution(values: list[float], temperature=1.) -> list[float]:
    if not math.isfinite(temperature) or temperature <= 0 or not all(math.isfinite(v) for v in values):
        raise ValueError("Finite scores and positive temperature required")
    maximum = max(values)
    exp = [math.exp((value - maximum) / temperature) for value in values]
    return [value / sum(exp) for value in exp]


def rankings(candidates: list[dict], shadow: dict, temperature=1.) -> dict:
    ids = [row["candidate_id"] for row in candidates]
    rule = distribution([row["rule_score"] for row in candidates])
    def ordered(scores):
        return sorted(ids, key=lambda identifier: -scores[ids.index(identifier)])
    result = {"rule": {"ranking": ordered(rule), "probabilities": dict(zip(ids, rule))}}
    if not shadow.get("accepted"):
        return result
    scores = {row["candidate_id"]: row["score"] for row in shadow["judgement"]["assessments"]}
    raw = distribution([scores[i] for i in ids])
    calibrated = distribution([scores[i] for i in ids], temperature)
    readiness = [row["registry_readiness"] for row in candidates]
    completeness = [row["context_completeness"] for row in candidates]
    methods = {"ollama": raw, "ollama_calibrated": calibrated,
               "simple_mix": [(a + b) / 2 for a, b in zip(rule, raw)],
               "calibrated_mix": [.75 * a + .25 * b for a, b in zip(rule, calibrated)],
               "registry_context_mix": [.55*a + .25*b + .1*c + .1*d for a,b,c,d in zip(rule, calibrated, readiness, completeness)]}
    for name, values in methods.items():
        normalized = [value / sum(values) for value in values]
        order = ordered(normalized)
        if name.startswith("ollama"):
            selected = shadow["judgement"]["selected_candidate"]
            order = sorted(ids, key=lambda identifier: (-normalized[ids.index(identifier)], identifier != selected))
        result[name] = {"ranking": order, "probabilities": dict(zip(ids, normalized))}
    result["ollama"]["abstained"] = shadow["judgement"]["out_of_candidates"]
    result["registry_context_mix"]["advisory_blocked"] = shadow["judgement"]["requires_clarification"] or shadow["judgement"]["out_of_candidates"]
    return result
