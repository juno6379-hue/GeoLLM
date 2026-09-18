"""Registry-backed gates for router fast paths.

Fast paths are latency optimizations, not authority decisions. This module keeps
the router from accumulating one-off if/else rules by loading suppress/allow
signals from the capability registry.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from services.orchestrator.place_router import place_navigation_target
from services.orchestrator.semantic_prior import build_semantic_prior


ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_REGISTRY = ROOT / "data" / "capability_registry.yaml"


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    if not CAPABILITY_REGISTRY.exists():
        return {}
    return yaml.safe_load(CAPABILITY_REGISTRY.read_text(encoding="utf-8")) or {}


def _instant_policy() -> dict[str, Any]:
    policies = _registry().get("router_policies") or {}
    policy = policies.get("instant_place_navigation") or {}
    return policy if isinstance(policy, dict) else {}


def _contains_term(text: str, lowered: str, term: str) -> bool:
    item = str(term or "").strip()
    if not item:
        return False
    item_l = item.lower()
    return item_l in lowered or item in text


def instant_place_navigation_decision(query: str) -> dict[str, Any]:
    text = str(query or "").strip()
    if not text:
        return {"allowed": False, "reason": "empty_query"}

    policy = _instant_policy()
    lowered = text.lower()
    prior = build_semantic_prior(text, text)
    place_types = {
        str(item.get("type") or "")
        for item in prior.get("place_type_candidates") or []
        if isinstance(item, dict)
    }

    for place_type in policy.get("suppress_when_semantic_place_types") or []:
        if str(place_type) in place_types:
            return {
                "allowed": False,
                "reason": "semantic_place_type_suppressed",
                "matched_signal": f"semantic_place_type:{place_type}",
                "semantic_prior": prior,
            }

    for signal in policy.get("suppress_when_signals") or []:
        if not isinstance(signal, dict):
            continue
        matched = [
            str(term)
            for term in signal.get("terms") or []
            if _contains_term(text, lowered, str(term))
        ]
        if matched:
            return {
                "allowed": False,
                "reason": signal.get("reason") or "policy_suppressed",
                "matched_signal": signal.get("signal_id"),
                "matched_terms": matched,
                "semantic_prior": prior,
            }

    target = place_navigation_target(text)
    if target and target != text:
        return {
            "allowed": True,
            "reason": "place_navigation_action",
            "target": target,
            "semantic_prior": prior,
        }

    pattern = str(policy.get("standalone_place_suffix_pattern") or "")
    if pattern and re.match(pattern, text):
        return {
            "allowed": True,
            "reason": "standalone_place_suffix",
            "target": target,
            "semantic_prior": prior,
        }

    return {
        "allowed": False,
        "reason": "not_simple_place_navigation",
        "target": target,
        "semantic_prior": prior,
    }


def is_instant_place_navigation_allowed(query: str) -> bool:
    return bool(instant_place_navigation_decision(query).get("allowed"))
