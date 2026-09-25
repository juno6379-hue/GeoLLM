from __future__ import annotations

import math
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from shared.observability.logger import get_logger
from services.orchestrator.semantic_prior import build_semantic_prior, semantic_prior_signals

logger = get_logger("orchestrator.query_candidate_broker")

ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_REGISTRY = ROOT / "data" / "capability_registry.yaml"


def _db_url() -> str | None:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")


def _embedding_endpoint() -> str:
    return os.getenv("OLLAMA_EMBEDDING_URL", os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/embed")


ROUTE_HINTS: dict[str, list[str]] = {
    "PLACE_LOOKUP": [
        "찾아", "찾아줘", "위치", "어디", "좌표", "place", "lookup", "섬", "도서",
        "항", "항만", "입구", "해역", "독도", "부산항",
    ],
    "SPATIAL_ANALYSIS": [
        "이내", "반경", "근처", "주변", "거리", "km", "m", "위험객체", "장애물",
        "obstruction", "wreck", "침선", "간출암", "노출암", "부표",
    ],
    "DATASET_PROVENANCE": [
        "근거", "출처", "적재", "파싱", "표준화", "임베딩", "embedding",
        "dataset", "gazetteer", "serving", "row", "coverage",
    ],
    "STANDARD_RAG": [
        "정의", "법령", "고시", "표준", "근거", "조항", "S-101", "S-100",
        "DCEG", "Feature Catalogue", "catalogue",
    ],
    "TRAFFIC_ANALYSIS": [
        "통항량", "AIS", "V-PASS", "vpass", "traffic", "최근 1년", "월별",
        "latest_available_12_months",
    ],
    "LAYER_INSPECTION": [
        "폴리곤", "레이어", "지도", "표시", "클릭", "상세정보", "범례", "portrayal",
        "symbol", "아이콘",
    ],
    "QUALITY_REVIEW": [
        "이상", "오류", "왜", "다른", "정확도", "유사도", "품질", "검증",
    ],
}

ROUTE_HINTS["PLACE_LOOKUP"].extend([
    "찾아",
    "찾아줘",
    "위치",
    "어디",
    "좌표",
    "독도",
    "부산항",
    "입구",
    "해역",
])
ROUTE_HINTS["SPATIAL_ANALYSIS"].extend([
    "이내",
    "반경",
    "근처",
    "주변",
    "부근",
    "거리",
    "해저지명",
    "해저 지명",
    "해양지명",
    "해양 지명",
    "지명",
])
ROUTE_HINTS["DATASET_PROVENANCE"].extend([
    "근거",
    "출처",
    "적재",
    "파싱",
    "표준화",
    "임베딩",
])
ROUTE_HINTS["TRAFFIC_ANALYSIS"].extend([
    "통항량",
    "최근 1년",
    "월별",
])

ROUTE_HINTS.setdefault("ACCIDENT_ANALYSIS", []).extend([
    "accident",
    "incident",
    "case",
    "사고",
    "사건",
    "해상조난",
    "조난사고",
    "해양사고",
    "선박사고",
    "정비불량",
    "관리소홀",
    "운항부주의",
    "안전부주의",
    "기관손상",
    "추진기손상",
    "침몰",
    "침수",
    "좌초",
    "충돌",
    "화재",
    "전복",
    "표류",
])

DETERMINISTIC_PATTERNS: list[tuple[str, re.Pattern[str], list[str]]] = [
    ("radius_slot", re.compile(r"(\d+(?:\.\d+)?)\s*(km|m|킬로|미터)", re.I), ["SPATIAL_ANALYSIS"]),
    ("temporal_window", re.compile(r"최근\s*\d+\s*(년|개월|달)|latest_available_12_months", re.I), ["TRAFFIC_ANALYSIS"]),
    ("provenance_request", re.compile(r"근거|출처|적재|파싱|표준화|임베딩|embedding", re.I), ["DATASET_PROVENANCE", "STANDARD_RAG"]),
    (
        "definition_request",
        re.compile(r"정의|뜻|의미|표준|DCEG|Feature Catalogue|catalogue|(?:이란|란)\??\s*$", re.I),
        ["STANDARD_RAG"],
    ),
    ("traffic_term", re.compile(r"통항량|AIS|V-PASS|vpass|traffic", re.I), ["TRAFFIC_ANALYSIS"]),
    ("nearby_search", re.compile(r"이내|반경|근처|주변|거리|가까운|nearest|closest", re.I), ["SPATIAL_ANALYSIS"]),
    ("hazard_target", re.compile(r"위험객체|장애물|obstruction|wreck|침선|간출암|노출암|부표", re.I), ["SPATIAL_ANALYSIS", "LAYER_INSPECTION"]),
    ("find_intent", re.compile(r"찾아줘|찾아|위치|어디|좌표", re.I), ["PLACE_LOOKUP"]),
    ("place_name", re.compile(r"독도|[가-힣A-Za-z]+항\s*입구|[가-힣A-Za-z]+항|[가-힣]+해역|도서지명", re.I), ["PLACE_LOOKUP"]),
    ("layer_inspection", re.compile(r"폴리곤|레이어|지도|클릭|상세정보|범례|symbol|아이콘|portrayal", re.I), ["LAYER_INSPECTION"]),
]

DETERMINISTIC_PATTERNS.extend([
    ("accident_event", re.compile(r"accident|incident|사고|사건|해상조난|조난사고|해양사고|선박사고", re.I), ["ACCIDENT_ANALYSIS"]),
    ("accident_history", re.compile(r"사고\s*이력|사고\s*내역|이력|history", re.I), ["ACCIDENT_ANALYSIS"]),
    ("accident_cause", re.compile(r"정비불량|관리소홀|운항부주의|안전부주의|원인미상|발생원인", re.I), ["ACCIDENT_ANALYSIS"]),
    ("accident_type", re.compile(r"기관손상|추진기손상|키손상|침몰|침수|좌초|충돌|화재|전복|표류|발생유형", re.I), ["ACCIDENT_ANALYSIS"]),
    ("structured_event_lookup", re.compile(r"찾아줘|찾아|검색|조회|목록|event|case", re.I), ["ACCIDENT_ANALYSIS"]),
    ("nearby_search_utf8", re.compile(r"이내|반경|근처|주변|부근|거리", re.I), ["SPATIAL_ANALYSIS"]),
    ("marine_gazetteer_target", re.compile(r"해저지명|해저\s*지명|해양지명|해양\s*지명|부근\s*지명|주변\s*지명", re.I), ["SPATIAL_ANALYSIS"]),
    ("place_name_utf8", re.compile(r"독도|[가-힣A-Za-z]+항\s*입구|[가-힣A-Za-z]+항|[가-힣]+해역|도서지명", re.I), ["PLACE_LOOKUP"]),
    ("find_intent_utf8", re.compile(r"찾아줘|찾아|위치|어디|좌표", re.I), ["PLACE_LOOKUP"]),
    ("traffic_term_utf8", re.compile(r"통항량|AIS|V-PASS|vpass|traffic", re.I), ["TRAFFIC_ANALYSIS"]),
])


@dataclass(frozen=True)
class Signal:
    signal_id: str
    routes: list[str]
    value: str | None = None


def _load_registry() -> dict[str, Any]:
    try:
        return yaml.safe_load(CAPABILITY_REGISTRY.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        logger.warning("Capability registry not found", path=str(CAPABILITY_REGISTRY))
        return {}
    except Exception as exc:
        logger.warning("Failed to load capability registry", path=str(CAPABILITY_REGISTRY), error=str(exc))
        return {}


@lru_cache(maxsize=1)
def _registry_lexical_signals() -> tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]:
    registry = _load_registry()
    rows = []
    for item in registry.get("lexical_signals") or []:
        signal_id = str(item.get("signal_id") or "").strip()
        routes = tuple(str(route) for route in item.get("routes") or [] if route)
        terms = tuple(str(term).lower() for term in item.get("terms") or [] if str(term).strip())
        if signal_id and routes and terms:
            rows.append((signal_id, routes, terms))
    return tuple(rows)


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_\-]+|[가-힣]{2,}", text or "")
        if token.strip()
    }


def _signal_scan(query: str) -> list[Signal]:
    signals: list[Signal] = []
    for signal_id, pattern, routes in DETERMINISTIC_PATTERNS:
        match = pattern.search(query or "")
        if match:
            signals.append(Signal(signal_id=signal_id, routes=routes, value=match.group(0)))
    if not any(signal.signal_id.startswith('accident_') for signal in signals):
        signals = [signal for signal in signals if signal.signal_id != 'structured_event_lookup']
    return signals


def _registry_signal_scan(query: str) -> list[Signal]:
    lowered = (query or "").lower()
    compacted = _compact_text(query)
    signals: list[Signal] = []
    for signal_id, routes, terms in _registry_lexical_signals():
        for term in terms:
            if term in lowered or _compact_text(term) in compacted:
                signals.append(Signal(signal_id=signal_id, routes=list(routes), value=term))
                break
    return signals


def _semantic_prior_signal_scan(prior: dict[str, Any]) -> list[Signal]:
    signals: list[Signal] = []
    for item in semantic_prior_signals(prior):
        signal_id = str(item.get("signal_id") or "")
        routes = [str(route) for route in item.get("routes") or [] if route]
        if signal_id and routes:
            signals.append(Signal(signal_id=signal_id, routes=routes, value=item.get("value")))
    return signals


def _dedupe_signals(signals: list[Signal]) -> list[Signal]:
    deduped: list[Signal] = []
    seen: set[tuple[str, str | None]] = set()
    for signal in signals:
        key = (signal.signal_id, signal.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    return deduped


def _route_candidates(query: str, signals: list[Signal], *, top_k: int = 5) -> list[dict[str, Any]]:
    query_lower = (query or "").lower()
    scores: dict[str, float] = {route: 0.0 for route in ROUTE_HINTS}
    route_signals: dict[str, list[str]] = {route: [] for route in ROUTE_HINTS}
    for route, hints in ROUTE_HINTS.items():
        for hint in hints:
            if hint.lower() in query_lower:
                scores[route] += 0.16
                route_signals[route].append(hint)
    for signal in signals:
        for route in signal.routes:
            scores[route] = scores.get(route, 0.0) + 0.32
            route_signals.setdefault(route, []).append(signal.signal_id)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    result = []
    for index, (route, score) in enumerate(ranked[:top_k]):
        if score <= 0 and index > 2:
            continue
        role = "primary" if index == 0 and score > 0 else "supporting" if score > 0 else "fallback"
        result.append({
            "route": route,
            "score": round(min(score, 1.0), 3),
            "role": role,
            "signals": list(dict.fromkeys(route_signals.get(route, []))),
            "verification_status": "pending",
        })
    return result


def _capability_text(capability: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("capability_id", "object_type", "label", "description"):
        value = capability.get(key)
        if value:
            parts.append(str(value))
    for key in ("routes", "input_slots", "output_slots", "deterministic_hints"):
        values = capability.get(key) or []
        if isinstance(values, list):
            parts.extend(str(item) for item in values)
    return " ".join(parts)


def _registry_capability_candidates(
    query: str,
    route_candidates: list[dict[str, Any]],
    signals: list[Signal],
    *,
    top_k: int = 8,
    require_signal_match: bool = False,
) -> list[dict[str, Any]]:
    registry = _load_registry()
    capabilities = registry.get("capabilities") or []
    query_tokens = _tokens(query)
    route_scores = {row["route"]: float(row.get("score") or 0.0) for row in route_candidates}
    signal_ids = {signal.signal_id for signal in signals}
    scored: list[tuple[float, dict[str, Any]]] = []
    for capability in capabilities:
        # Domain entries use the dedicated domain retrieval call. Keeping them
        # out of the existing GeoLLM top-k preserves current routing behavior.
        if capability.get("domain") not in (None, "geollm"):
            continue
        hint_overlap = signal_ids & set(capability.get("deterministic_hints") or [])
        if require_signal_match and not hint_overlap:
            continue
        text_tokens = _tokens(_capability_text(capability))
        overlap = query_tokens & text_tokens
        token_score = len(overlap) / math.sqrt(max(len(query_tokens), 1) * max(len(text_tokens), 1))
        routes = capability.get("routes") or []
        route_score = max((route_scores.get(route, 0.0) for route in routes), default=0.0)
        hint_score = min(len(hint_overlap) * 0.16, 0.48)
        score = token_score + (route_score * 0.55) + hint_score
        if score <= 0:
            continue
        item = {
            "candidate_id": capability.get("capability_id"),
            "kind": capability.get("object_type"),
            "label": capability.get("label"),
            "routes": routes,
            "role": capability.get("role"),
            "score": round(min(score, 1.0), 3),
            "matched_tokens": sorted(overlap)[:10],
            "matched_signals": sorted(hint_overlap),
            "input_slots": capability.get("input_slots") or [],
            "output_slots": capability.get("output_slots") or [],
            "authority_ref": capability.get("authority_ref"),
            "registry_ref": capability.get("registry_ref"),
            "verification_status": "pending",
            "retrieval_source": "registry_signal" if hint_overlap else "registry_fallback",
        }
        scored.append((score, item))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def _embed_query(text: str) -> list[float]:
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    body = json.dumps({"model": model, "input": [text]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(_embedding_endpoint(), data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=float(os.getenv("CAPABILITY_EMBEDDING_TIMEOUT_SEC", "5"))) as response:
        payload = json.load(response)
    embeddings = payload.get("embeddings") or []
    if not embeddings:
        raise RuntimeError("empty embedding response")
    return embeddings[0]


def _primary_execution_route(route_candidates: list[dict[str, Any]]) -> str | None:
    top = next((row for row in route_candidates if row.get("role") == "primary"), None)
    top_route = top.get("route") if top else None
    if top_route in {"DATASET_PROVENANCE", "TRAFFIC_ANALYSIS", "STANDARD_RAG"}:
        return str(top_route)
    accident = next((row for row in route_candidates if row.get("route") == "ACCIDENT_ANALYSIS"), None)
    accident_signals = set(accident.get("signals") or []) if accident else set()
    accident_execution_signals = {
        "accident_event",
        "accident_history",
        "accident_cause",
        "accident_type",
        "structured_event_lookup",
    }
    if accident and float(accident.get("score") or 0.0) > 0 and accident_signals & accident_execution_signals:
        return "ACCIDENT_ANALYSIS"
    spatial = next((row for row in route_candidates if row.get("route") == "SPATIAL_ANALYSIS"), None)
    spatial_signals = set(spatial.get("signals") or []) if spatial else set()
    spatial_execution_signals = {
        "radius_slot",
        "nearby_search",
        "nearby_search_utf8",
        "hazard_target",
        "marine_gazetteer_target",
    }
    if spatial and float(spatial.get("score") or 0.0) > 0 and spatial_signals & spatial_execution_signals:
        return "SPATIAL_ANALYSIS"
    return str(top_route) if top_route else None


def _pgvector_capability_candidates(
    query: str,
    route_candidates: list[dict[str, Any]],
    *,
    top_k: int = 8,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if os.getenv("GEOLLM_CAPABILITY_PGVECTOR", "true").lower() not in {"1", "true", "yes", "on"}:
        return [], {"status": "disabled"}
    url = _db_url()
    if not url:
        return [], {"status": "unavailable", "reason": "database_url_missing"}
    try:
        vector = _embed_query(query)
    except Exception as exc:
        logger.warning("pgvector capability query embedding failed", error=str(exc))
        return [], {"status": "fallback", "reason": f"query_embedding_failed: {exc}"}
    route_scores = {row["route"]: float(row.get("score") or 0.0) for row in route_candidates}
    route_tags = [row["route"] for row in route_candidates if float(row.get("score") or 0.0) > 0]
    try:
        import psycopg2
        import psycopg2.extras

        with psycopg2.connect(url, connect_timeout=3) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT to_regclass('knowledge.capability_embeddings')")
                if not cur.fetchone()["to_regclass"]:
                    return [], {"status": "unavailable", "reason": "table_missing"}
                cur.execute(
                    """
                    SELECT id, object_type, object_id, label, route_tags, input_slots, output_slots,
                           authority_ref, registry_ref, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM knowledge.capability_embeddings
                    WHERE embedding IS NOT NULL
                      AND (%s::text[] = '{}'::text[] OR route_tags && %s::text[])
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (json.dumps(vector), route_tags, route_tags, json.dumps(vector), max(top_k * 2, top_k)),
                )
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("pgvector capability retrieval failed", error=str(exc))
        return [], {"status": "fallback", "reason": str(exc)}

    candidates = []
    primary_route = _primary_execution_route(route_candidates)
    for row in rows:
        routes = list(row.get("route_tags") or [])
        route_score = max((route_scores.get(route, 0.0) for route in routes), default=0.0)
        matched_routes = [route for route in routes if route in route_scores and route_scores.get(route, 0.0) > 0]
        primary_route_bonus = 0.15 if primary_route and primary_route in routes else 0.0
        similarity = float(row.get("similarity") or 0.0)
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        score = min((similarity * 0.60) + (route_score * 0.25) + primary_route_bonus, 1.0)
        candidates.append({
            "candidate_id": row.get("id"),
            "kind": row.get("object_type"),
            "label": row.get("label"),
            "routes": routes,
            "role": metadata.get("role"),
            "score": round(score, 3),
            "semantic_similarity": round(similarity, 4),
            "matched_routes": matched_routes,
            "matched_tokens": [],
            "matched_signals": [],
            "input_slots": row.get("input_slots") or [],
            "output_slots": row.get("output_slots") or [],
            "authority_ref": row.get("authority_ref"),
            "registry_ref": row.get("registry_ref"),
            "verification_status": "pending",
            "retrieval_source": "pgvector",
        })
    candidates.sort(key=lambda item: item.get("score") or 0.0, reverse=True)
    return candidates[:top_k], {
        "status": "pgvector_top_k",
        "target_table": "knowledge.capability_embeddings",
        "role": "top_k_candidate_retrieval_only",
        "route_filter": route_tags,
        "returned": len(candidates[:top_k]),
    }


def _capability_candidates(
    query: str,
    route_candidates: list[dict[str, Any]],
    signals: list[Signal],
    *,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    signal_ids = {signal.signal_id for signal in signals}
    execution_route = _primary_execution_route(route_candidates)
    if (
        execution_route == "ACCIDENT_ANALYSIS"
        and signal_ids & {"accident_history"}
        and signal_ids & {"place_name", "place_name_utf8"}
    ):
        deterministic_candidates = _registry_capability_candidates(
            query,
            route_candidates,
            signals,
            top_k=top_k,
            require_signal_match=True,
        )
        if any(
            candidate.get("candidate_id") == "tool.accident_spatial_history_lookup"
            for candidate in deterministic_candidates
        ):
            return deterministic_candidates

    pgvector_candidates, _policy = _pgvector_capability_candidates(query, route_candidates, top_k=top_k)
    if pgvector_candidates:
        supplement = _registry_capability_candidates(
            query,
            route_candidates,
            signals,
            top_k=top_k,
            require_signal_match=True,
        )
        merged = {str(item.get("candidate_id")): item for item in pgvector_candidates}
        for item in supplement:
            candidate_id = str(item.get("candidate_id"))
            if candidate_id not in merged:
                merged[candidate_id] = item
                continue
            existing = merged[candidate_id]
            existing["score"] = max(float(existing.get("score") or 0.0), float(item.get("score") or 0.0))
            existing["matched_signals"] = sorted(
                set(existing.get("matched_signals") or []) | set(item.get("matched_signals") or [])
            )
            existing["matched_tokens"] = sorted(
                set(existing.get("matched_tokens") or []) | set(item.get("matched_tokens") or [])
            )[:10]
            existing["retrieval_source"] = "pgvector+registry_signal"
        result = list(merged.values())
        result.sort(
            key=lambda item: (
                float(item.get("score") or 0.0),
                len(item.get("matched_signals") or []),
                1 if "registry_signal" in str(item.get("retrieval_source") or "") else 0,
            ),
            reverse=True,
        )
        return result[: max(top_k, len(pgvector_candidates))]
    return _registry_capability_candidates(query, route_candidates, signals, top_k=top_k)


def _verify_candidates(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verified = []
    reference_checks = {}
    for candidate in capabilities:
        authority = candidate.get("authority_ref")
        registry = candidate.get("registry_ref")
        for ref in (authority, registry):
            if ref not in reference_checks:
                reference_checks[ref] = _verify_reference(ref)
        authority_check = reference_checks[authority]
        registry_check = reference_checks[registry]
        has_declared_refs = bool(authority and registry)
        has_registry_or_authority = authority_check["status"] in {"verified", "declared"} and registry_check["status"] in {"verified", "declared"}
        status = "verified_ready" if has_declared_refs and has_registry_or_authority else "candidate_needs_authority"
        reason = "authority_ref and registry_ref verified or declared" if status == "verified_ready" else "missing or unverifiable authority_ref/registry_ref"
        verified.append({
            "candidate_id": candidate.get("candidate_id"),
            "status": status,
            "reason": reason,
            "authority_ref": authority,
            "registry_ref": registry,
            "authority_check": authority_check,
            "registry_check": registry_check,
        })
    return verified


def _verify_reference(ref: Any) -> dict[str, Any]:
    if not ref:
        return {"status": "missing", "ref": ref}
    ref_text = str(ref)
    db_relation_prefixes = ("serving.", "projection.", "knowledge.", "public.", "canonical.")
    if ref_text.startswith(db_relation_prefixes):
        try:
            import psycopg2

            url = _db_url()
            if not url:
                return {"status": "declared", "type": "db_relation", "ref": ref_text, "reason": "database_url_missing"}
            with psycopg2.connect(url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass(%s)", (ref_text,))
                    exists = bool(cur.fetchone()[0])
            return {"status": "verified" if exists else "declared", "type": "db_relation", "ref": ref_text}
        except Exception as exc:
            return {"status": "declared", "type": "db_relation", "ref": ref_text, "reason": str(exc)}
    path_like = any(token in ref_text for token in ("/", "\\")) or Path(ref_text).suffix
    if path_like:
        path = ROOT / ref_text
        if path.exists():
            return {"status": "verified", "type": "file", "ref": ref_text}
        # Some authority files are external source names. They are allowed as
        # declared authority, but they are not used as geometry truth directly.
        if ref_text.startswith(("Dataset/", "outputs/", "data/")):
            return {"status": "declared", "type": "source_ref", "ref": ref_text}
        return {"status": "unverified", "type": "file", "ref": ref_text}
    if "." in ref_text:
        try:
            import psycopg2

            url = _db_url()
            if not url:
                return {"status": "declared", "type": "db_relation", "ref": ref_text, "reason": "database_url_missing"}
            with psycopg2.connect(url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass(%s)", (ref_text,))
                    exists = bool(cur.fetchone()[0])
            return {"status": "verified" if exists else "declared", "type": "db_relation", "ref": ref_text}
        except Exception as exc:
            return {"status": "declared", "type": "db_relation", "ref": ref_text, "reason": str(exc)}
    return {"status": "declared", "type": "registry_symbol", "ref": ref_text}


def _tool_graph_candidates(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = []
    for candidate in capabilities:
        kind = str(candidate.get("kind") or "")
        if kind not in {"resolver_description", "tool_description", "agent_description", "dataset_metadata", "feature_class_description", "ontology_class_description", "marine_term"}:
            continue
        nodes.append({
            "node_id": candidate.get("candidate_id"),
            "kind": kind,
            "requires": candidate.get("input_slots") or [],
            "produces": candidate.get("output_slots") or [],
            "verification_status": "pending",
        })
    return nodes[:10]


def _execution_route_row(routes: list[dict[str, Any]], execution_route: str | None) -> dict[str, Any] | None:
    if not execution_route:
        return next((row for row in routes if row.get("role") == "primary"), None)
    for row in routes:
        if row.get("route") == execution_route:
            selected = dict(row)
            selected["role"] = "selected_execution"
            return selected
    return {"route": execution_route, "score": 0.0, "role": "selected_execution", "signals": []}


def _tool_readiness(
    capabilities: list[dict[str, Any]],
    verified: list[dict[str, Any]],
    *,
    execution_route: str | None = None,
) -> list[dict[str, Any]]:
    verified_ids = {row.get("candidate_id") for row in verified if row.get("status") == "verified_ready"}
    readiness = []
    for candidate in capabilities:
        candidate_id = candidate.get("candidate_id")
        kind = str(candidate.get("kind") or "")
        is_executable_kind = kind in {"tool_description", "agent_description", "resolver_description", "dataset_metadata"}
        candidate_routes = set(candidate.get("routes") or [])
        route_selected = not execution_route or execution_route in candidate_routes
        ready = is_executable_kind and candidate_id in verified_ids and route_selected
        readiness.append({
            "candidate_id": candidate_id,
            "kind": kind,
            "status": "ready" if ready else "candidate_only",
            "execution_route": execution_route,
            "reason": "verified executable registry/authority candidate for selected route" if ready else (
                "verified alternative-route candidate; kept as candidate only"
                if candidate_id in verified_ids and not route_selected
                else
                "verified supporting candidate, not executable by itself"
                if candidate_id in verified_ids
                else "not selected for execution until verified"
            ),
        })
    return readiness


def _execution_contract(
    routes: list[dict[str, Any]],
    capabilities: list[dict[str, Any]],
    verified: list[dict[str, Any]],
    tool_readiness: list[dict[str, Any]],
    *,
    execution_route: str | None = None,
) -> dict[str, Any]:
    primary_route = _execution_route_row(routes, execution_route)
    verified_ids = {row.get("candidate_id") for row in verified if row.get("status") == "verified_ready"}
    ready_tools = [row for row in tool_readiness if row.get("status") == "ready"]
    ontology_candidates = [
        row for row in capabilities
        if row.get("kind") in {"ontology_class_description", "marine_term", "feature_class_description"}
        and row.get("candidate_id") in verified_ids
    ]
    steps = [
        {
            "step": 1,
            "name": "route_classification",
            "status": "ready" if primary_route else "blocked",
            "authority": "deterministic_signals_and_route_scores",
            "selected": primary_route,
        },
        {
            "step": 2,
            "name": "resolver_dictionary_tool_candidate_retrieval",
            "status": "ready" if capabilities else "blocked",
            "authority": "pgvector_top_k_then_registry_fallback",
            "candidate_ids": [row.get("candidate_id") for row in capabilities[:8]],
        },
        {
            "step": 3,
            "name": "ontology_kg_verification",
            "status": "ready" if ontology_candidates else "not_required_or_deferred",
            "authority": "ontology_kg_registry",
            "candidate_ids": [row.get("candidate_id") for row in ontology_candidates[:5]],
        },
        {
            "step": 4,
            "name": "registry_authority_verification",
            "status": "ready" if verified_ids else "blocked",
            "authority": "registry_ref_and_authority_ref",
            "candidate_ids": list(verified_ids)[:8],
        },
        {
            "step": 5,
            "name": "tool_readiness",
            "status": "ready" if ready_tools else "blocked",
            "authority": "verified_executable_capability_for_selected_route",
            "candidate_ids": [row.get("candidate_id") for row in ready_tools[:8]],
        },
        {
            "step": 6,
            "name": "verified_execution_only",
            "status": "ready" if primary_route and verified_ids and ready_tools else "blocked",
            "authority": "execute_only_after_steps_1_to_5",
            "policy": "pgvector_never_authority_for_geometry_or_facts",
        },
    ]
    return {
        "contract": "candidate_first_execution_contract.v1",
        "status": "ready" if steps[-1]["status"] == "ready" else "blocked",
        "execution_route": execution_route,
        "steps": steps,
    }


def select_execution_route(trace: dict[str, Any], route: str, reason: str) -> dict[str, Any]:
    """Revalidate an existing candidate route after resolving requested outputs.

    Ranking remains recorded; this cannot introduce capabilities or turn an
    unverified candidate into an executable tool. Runtime slot/data gates remain.
    """
    routes = trace.get("route_candidates") or []
    if not any(row.get("route") == route and row.get("score", 0) > 0 for row in routes):
        return trace
    previous = (trace.get("execution_contract") or {}).get("execution_route")
    capabilities, verified = trace.get("capability_candidates") or [], trace.get("verified_candidates") or []
    readiness = _tool_readiness(capabilities, verified, execution_route=route)
    contract = _execution_contract(routes, capabilities, verified, readiness, execution_route=route)
    return {**trace, "tool_readiness": readiness, "execution_contract": contract,
            "execution_selection": {"ranked_route": previous, "selected_route": route, "reason": reason,
                                    "runtime_validation_required": True, "ollama_used": False}}


def execution_contract_ready(trace: dict[str, Any] | None, *, route: str | None = None, capability_id: str | None = None) -> bool:
    if not isinstance(trace, dict):
        return False
    contract = trace.get("execution_contract") if isinstance(trace.get("execution_contract"), dict) else {}
    if contract.get("status") != "ready":
        return False
    if route:
        routes = trace.get("route_candidates") if isinstance(trace.get("route_candidates"), list) else []
        if not any(row.get("route") == route and row.get("score", 0) > 0 for row in routes if isinstance(row, dict)):
            return False
    if capability_id:
        readiness = trace.get("tool_readiness") if isinstance(trace.get("tool_readiness"), list) else []
        if not any(row.get("candidate_id") == capability_id and row.get("status") == "ready" for row in readiness if isinstance(row, dict)):
            return False
    return True


class QueryCandidateBroker:
    def domain_capability_definitions(self, domain: str) -> dict[str, dict[str, Any]]:
        """Expose one domain's Registry metadata to its dependency planner."""
        return {
            entry["capability_id"]: entry
            for entry in _load_registry().get("capabilities") or []
            if entry.get("domain") == domain and entry.get("capability_id")
        }

    def retrieve_domain_capabilities(self, query: str, domain: str, *, top_k: int = 8) -> list[dict[str, Any]]:
        """Rank Registry entries in one domain without granting execution authority.

        Domain cue terms are metadata, not a query-specific if/else router.
        The existing Registry remains the only candidate source; dataset and
        entity checks are performed later by ExecutionValidator.
        """
        registry = _load_registry()
        normalized = query.casefold()
        candidates = []
        for entry in registry.get("capabilities") or []:
            if entry.get("domain") != domain:
                continue
            matched = [term for term in entry.get("cue_terms") or [] if str(term).casefold() in normalized]
            if not matched:
                continue
            candidates.append({
                "candidate_id": entry["capability_id"],
                "score": round(min(len(matched) / max(len(entry.get("cue_terms") or []), 1), 1.0), 3),
                "matched_terms": matched,
                "verification_status": "pending",
                "retrieval_source": "registry_domain_cues",
            })
        candidates.sort(key=lambda row: (-row["score"], row["candidate_id"]))
        return candidates[:top_k]

    def build_trace(self, query: str, normalized_query: str | None = None, norm_result: dict[str, Any] | None = None) -> dict[str, Any]:
        combined = " ".join(part for part in [query, normalized_query] if part)
        semantic_prior = build_semantic_prior(query, normalized_query)
        signals = _dedupe_signals(
            _signal_scan(combined)
            + _registry_signal_scan(combined)
            + _semantic_prior_signal_scan(semantic_prior)
        )
        routes = _route_candidates(combined, signals)
        capabilities = _capability_candidates(combined, routes, signals)
        pgvector_used = bool(capabilities and capabilities[0].get("retrieval_source") == "pgvector")
        verified = _verify_candidates(capabilities)
        execution_route = _primary_execution_route(routes)
        readiness = _tool_readiness(capabilities, verified, execution_route=execution_route)
        execution_contract = _execution_contract(routes, capabilities, verified, readiness, execution_route=execution_route)
        needs_ollama = self._needs_ollama(routes, verified)
        trace = {
            "contract": "candidate_first_orchestration.v0.dry_run",
            "mode": "dry_run_no_execution_change",
            "query": query,
            "normalized_query": normalized_query,
            "deterministic_signals": [
                {"signal_id": signal.signal_id, "value": signal.value, "routes": signal.routes}
                for signal in signals
            ],
            "semantic_prior": semantic_prior,
            "route_candidates": routes,
            "capability_candidates": capabilities,
            "verified_candidates": verified,
            "tool_graph_candidates": _tool_graph_candidates(capabilities),
            "tool_readiness": readiness,
            "execution_contract": execution_contract,
            "ollama_policy": {
                "role": "ambiguity_resolver_only",
                "needed": needs_ollama,
                "reason": self._ollama_reason(routes, verified) if needs_ollama else "unique_or_sufficient_verified_candidate",
            },
            "pgvector_policy": {
                "target_table": "knowledge.capability_embeddings",
                "status": "pgvector_top_k" if pgvector_used else "registry_fallback",
                "role": "top_k_candidate_retrieval_only",
            },
        }
        if norm_result:
            trace["normalizer"] = {
                "canonical_terms": norm_result.get("canonical_terms") or [],
                "candidate_contexts": norm_result.get("candidate_contexts") or [],
            }
        return trace

    @staticmethod
    def _needs_ollama(routes: list[dict[str, Any]], verified: list[dict[str, Any]]) -> bool:
        positive = [route for route in routes if float(route.get("score") or 0.0) > 0]
        if len(positive) >= 2:
            first = float(positive[0].get("score") or 0.0)
            second = float(positive[1].get("score") or 0.0)
            if first - second < 0.18:
                pair = (positive[0].get("route"), positive[1].get("route"))
                if pair in {
                    ("SPATIAL_ANALYSIS", "PLACE_LOOKUP"),
                    ("TRAFFIC_ANALYSIS", "PLACE_LOOKUP"),
                    ("DATASET_PROVENANCE", "STANDARD_RAG"),
                    ("STANDARD_RAG", "DATASET_PROVENANCE"),
                }:
                    return False
                return True
        ready = [row for row in verified if row.get("status") == "verified_ready"]
        return len(ready) == 0 and bool(positive)

    @staticmethod
    def _ollama_reason(routes: list[dict[str, Any]], verified: list[dict[str, Any]]) -> str:
        positive = [route for route in routes if float(route.get("score") or 0.0) > 0]
        ready = [row for row in verified if row.get("status") == "verified_ready"]
        if not ready and positive:
            return "route_candidates_exist_but_no_verified_candidate"
        if len(positive) >= 2:
            return "top_route_scores_are_close"
        return "ambiguous_candidate_state"


query_candidate_broker = QueryCandidateBroker()
