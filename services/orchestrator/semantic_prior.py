"""General semantic priors for candidate-first routing.

This module may use deterministic signals and, only when useful, Ollama. Its
output is always candidate/prior information. It must never be treated as
authoritative geometry, legal fact, row count, or execution permission.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

from shared.observability.logger import get_logger


logger = get_logger("orchestrator.semantic_prior")


PLACE_TYPE_PATTERNS: list[tuple[str, float, list[str]]] = [
    ("poi_beach", 0.94, ["해수욕장", "beach"]),
    ("tourism_poi", 0.86, ["관광지", "명소", "전망대", "공원", "해변", "beach"]),
    ("administrative_area", 0.88, ["구", "시", "군", "읍", "면", "동", "리", "district", "city"]),
    ("port", 0.9, ["항", "항만", "port", "harbour", "harbor"]),
    ("island", 0.9, ["도", "섬", "island"]),
    ("marine_gazetteer", 0.9, ["해양지명", "해저지명", "지명"]),
    ("address", 0.82, ["주소", "address", "road"]),
]

PLACE_ACTION_RE = re.compile(r"(찾아줘|보여줘|표시해줘|이동|가줘|위치|어디|좌표|find|show|move|where)", re.I)


def _ollama_endpoint() -> str:
    return os.getenv(
        "OLLAMA_GENERATE_URL",
        os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/generate",
    )


def semantic_prior_model() -> tuple[str, str]:
    """Use explicit prior settings, then the configured ambiguity/shadow model.

    LLM_MODEL belongs to the general parser and must not silently change the
    semantic-prior experiment. Explicit research worker settings retain priority.
    """
    for key in ('GEOLLM_OLLAMA_MODEL', 'OLLAMA_MODEL', 'GEOLLM_WEB_SHADOW_MODEL'):
        value = os.getenv(key, '').strip()
        if value:
            return value, key
    return 'llama3.1', 'legacy_default'


def _deterministic_place_type_candidates(query: str) -> list[dict[str, Any]]:
    text = query or ""
    compact = re.sub(r"\s+", "", text.lower())
    candidates: list[dict[str, Any]] = []
    for place_type, confidence, terms in PLACE_TYPE_PATTERNS:
        matched = []
        for term in terms:
            term_l = term.lower()
            if term_l in text.lower() or term_l in compact:
                matched.append(term)
        if matched:
            candidates.append({
                "type": place_type,
                "confidence": confidence,
                "evidence": matched,
                "source": "deterministic_semantic_prior",
            })
    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return candidates


def _place_name_guess(query: str) -> str:
    text = re.sub(r"\s+", " ", str(query or "").strip())
    text = re.sub(r"(으로|로)?\s*(이동|가줘)(해줘|해|하기)?[.!?]?$", "", text)
    text = re.sub(r"(을|를)?\s*(찾아줘|보여줘|표시해줘)[.!?]?$", "", text)
    return text.strip()


def _ollama_prior(query: str, deterministic_candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if os.getenv("GEOLLM_SEMANTIC_PRIOR_OLLAMA", "true").lower() not in {"1", "true", "yes", "on"}:
        return None
    if not os.getenv("OLLAMA_BASE_URL") and not os.getenv("OLLAMA_GENERATE_URL"):
        return None
    best = deterministic_candidates[0]["confidence"] if deterministic_candidates else 0.0
    if best >= 0.9:
        return None
    prompt = {
        "task": "Classify Korean maritime/geospatial query semantics. Return JSON only.",
        "query": query,
        "allowed_place_types": [
            "administrative_area",
            "poi_beach",
            "tourism_poi",
            "port",
            "island",
            "marine_gazetteer",
            "address",
            "unknown",
        ],
        "constraints": [
            "Do not provide coordinates.",
            "Do not assert authority.",
            "Return candidate semantics only.",
        ],
        "schema": {
            "is_place_like": "boolean",
            "normalized_place_name": "string|null",
            "operation": "map_navigation|place_lookup|spatial_analysis|unknown",
            "place_type_candidates": [{"type": "string", "confidence": "number"}],
        },
    }
    model, model_source = semantic_prior_model()
    body = json.dumps(
        {
            "model": model,
            "prompt": json.dumps(prompt, ensure_ascii=False),
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(_ollama_endpoint(), data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC", "2.5"))) as response:
            payload = json.load(response)
        raw = payload.get("response") or "{}"
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(parsed, dict):
            parsed["source"] = "ollama_semantic_prior"
            parsed["authority"] = "candidate_only"
            parsed['model'] = model
            parsed['model_selection_source'] = model_source
            return parsed
    except Exception as exc:
        logger.warning("Ollama semantic prior failed", error=str(exc), model=model, model_selection_source=model_source)
    return None


def build_semantic_prior(query: str, normalized_query: str | None = None, *, allow_ollama: bool = True) -> dict[str, Any]:
    model, model_source = semantic_prior_model()
    combined = " ".join(part for part in [query, normalized_query] if part)
    deterministic = _deterministic_place_type_candidates(combined)
    place_like = bool(deterministic) or bool(PLACE_ACTION_RE.search(combined or ""))
    operation = "map_navigation" if re.search(r"이동|가줘|move", combined or "", re.I) else (
        "place_lookup" if place_like else "unknown"
    )
    prior: dict[str, Any] = {
        "version": "semantic_prior.v1",
        "role": "candidate_only_not_authority",
        "is_place_like": place_like,
        "normalized_place_name": _place_name_guess(normalized_query or query) if place_like else None,
        "operation": operation,
        "place_type_candidates": deterministic,
        "ollama": {
            "enabled": os.getenv("GEOLLM_SEMANTIC_PRIOR_OLLAMA", "true").lower() in {"1", "true", "yes", "on"},
            "used": False,
            "role": "ambiguity_resolver_only",
            "model": model,
            "model_selection_source": model_source,
            "timeout_seconds": os.getenv('GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC', '2.5'),
        },
    }
    prior["ollama"]["enabled"] = prior["ollama"]["enabled"] and allow_ollama
    ollama = _ollama_prior(combined, deterministic) if allow_ollama else None
    if ollama:
        prior["ollama"]["used"] = True
        if isinstance(ollama.get("place_type_candidates"), list):
            merged = {item["type"]: dict(item) for item in deterministic if item.get("type")}
            for item in ollama.get("place_type_candidates") or []:
                if not isinstance(item, dict) or not item.get("type"):
                    continue
                existing = merged.get(str(item["type"]))
                confidence = float(item.get("confidence") or 0.0)
                if not existing or confidence > float(existing.get("confidence") or 0.0):
                    merged[str(item["type"])] = {
                        "type": str(item["type"]),
                        "confidence": max(0.0, min(confidence, 0.95)),
                        "source": "ollama_semantic_prior",
                    }
            prior["place_type_candidates"] = sorted(merged.values(), key=lambda row: row.get("confidence", 0), reverse=True)
        prior["is_place_like"] = bool(ollama.get("is_place_like", prior["is_place_like"]))
        prior["normalized_place_name"] = ollama.get("normalized_place_name") or prior["normalized_place_name"]
        prior["operation"] = ollama.get("operation") or prior["operation"]
    return prior


def semantic_prior_signals(prior: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if prior.get("is_place_like"):
        signals.append({"signal_id": "semantic_place_like", "routes": ["PLACE_LOOKUP"], "value": prior.get("normalized_place_name")})
    for item in prior.get("place_type_candidates") or []:
        place_type = str(item.get("type") or "")
        if place_type:
            signals.append({"signal_id": f"semantic_place_type:{place_type}", "routes": ["PLACE_LOOKUP"], "value": place_type})
    return signals
