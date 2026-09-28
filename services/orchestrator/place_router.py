"""Typed place resolution for query clients, using server-owned provenance."""

import asyncio
import hashlib
import json
import math
import os
import re
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scripts.run_external_evidence_gap_fill import run_gap_fill
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location

router = APIRouter(tags=["places"])


class PlaceResolveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    spatial_context: dict[str, Any] = Field(default_factory=dict)


def place_navigation_target(query: str) -> str:
    text = str(query or "").strip()
    text = re.sub(r"\s+", " ", text)
    patterns = [
        r"^(?P<place>.+?)(?:으로|로)?\s*이동(?:해줘|해|하기)?[.!?]?$",
        r"^(?P<place>.+?)(?:으로|로)?\s*가줘[.!?]?$",
        r"^(?P<place>.+?)(?:을|를)?\s*(?:찾아줘|보여줘|표시해줘)[.!?]?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return match.group("place").strip()
    compact_match = re.match(r"^(?P<place>.+?)(?:으로|로)?이동$", text)
    if compact_match:
        return compact_match.group("place").strip()
    return text


def _candidate_version(candidate: dict[str, Any]) -> str:
    raw = json.dumps(candidate, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _external_candidate_to_place(candidate: dict[str, Any]) -> dict[str, Any]:
    geometry = candidate.get("geometry") or {}
    evidence = candidate.get("evidence") if isinstance(candidate.get("evidence"), dict) else {}
    coordinates = geometry.get("coordinates")
    wkt = None
    if isinstance(coordinates, list) and len(coordinates) >= 2 and all(value is not None for value in coordinates[:2]):
        wkt = f"POINT({coordinates[0]} {coordinates[1]})"
    authority_level = candidate.get("authority_level")
    evidence_summary = evidence.get("description") or evidence.get("location_text") or candidate.get("category")
    result = {
        "place_id": candidate.get("candidate_id"),
        "place_version": _candidate_version(candidate),
        "label": candidate.get("name") or candidate.get("candidate_id"),
        "base_location": candidate.get("name") or candidate.get("candidate_id"),
        "geometry": wkt,
        "geometry_geojson": geometry.get("geojson"),
        "crs": "EPSG:4326",
        "status": "public_authoritative_candidate" if authority_level == "public_authoritative" else "supplemental_external_candidate",
        "source_ref": candidate.get("source_name") or candidate.get("source_tier"),
        "source_records": [{
            "source_ref": candidate.get("source_name") or candidate.get("source_tier"),
            "source_url": candidate.get("source_url"),
            "authority_level": candidate.get("authority_level"),
            "promotion_status": candidate.get("promotion_status"),
            "review_required": candidate.get("review_required", True),
            "evidence_summary": evidence_summary,
            "evidence": evidence,
        }],
        "source_url": candidate.get("source_url"),
        "category": candidate.get("category"),
        "evidence_summary": evidence_summary,
        "evidence_detail": evidence,
        "requires_confirmation": True,
        "authority_level": authority_level,
        "promotion_status": candidate.get("promotion_status"),
        "review_required": candidate.get("review_required", True),
    }
    if wkt:
        result["longitude"] = coordinates[0]
        result["latitude"] = coordinates[1]
    return result


def external_place_fallback(query: str) -> dict[str, Any] | None:
    place_query = place_navigation_target(query)
    report = run_gap_fill(
        place_query,
        fetch_osm=bool(os.getenv("GEOLLM_OSM_USER_AGENT")),
        ask_ollama=bool(os.getenv("GEOLLM_PLACE_FALLBACK_OLLAMA")),
    )
    raw_candidates = [
        candidate
        for candidate in report.get("candidates") or []
        if candidate.get("authority_level") in {"public_authoritative", "supplemental"}
    ]
    with_geometry = [
        candidate for candidate in raw_candidates
        if ((candidate.get("geometry") or {}).get("coordinates"))
    ]
    candidates = [
        _external_candidate_to_place(candidate)
        for candidate in (with_geometry or raw_candidates)
    ]
    if not candidates:
        return None
    has_public = any(candidate.get("authority_level") == "public_authoritative" for candidate in raw_candidates)
    first = candidates[0]
    evidence_text = first.get("evidence_summary") or first.get("category") or first.get("source_ref")
    source_text = first.get("source_ref")
    return {
        "status": "NEEDS_CLARIFICATION",
        "error_code": "EXTERNAL_PLACE_CANDIDATES",
        "summary": (
            "로컬 해양 지명사전에는 없지만 공공 근거 기반 후보를 찾았습니다. "
            f"대표 후보는 {first.get('label')}이며, 근거 요지는 '{evidence_text}'입니다. "
            f"출처는 {source_text}입니다. 정확한 feature geometry 승격 전이므로 후보를 확인해 주세요."
            if has_public
            else "로컬 해양 지명사전에는 없지만 외부 보조 후보를 찾았습니다. 요청한 위치와 일치하는 후보를 선택해 주세요. 후보 선택은 권위 지명 등록을 의미하지 않습니다."
        ),
        "location_candidates": candidates,
        "external_evidence_report": {
            "domain_id": report.get("domain_id"),
            "candidate_counts": report.get("candidate_counts"),
            "osm_fetch_diagnostics": report.get("osm_fetch_diagnostics"),
            "ollama_ambiguity_review": report.get("ollama_ambiguity_review"),
            "evidence_summary": evidence_text,
            "primary_source": source_text,
        },
    }


def allow_display_navigation(query, payload, spatial_context=None):
    """A unique exact administrative place may move the viewport, never ground analysis."""
    if payload.get("error_code") != "EXTERNAL_PLACE_CANDIDATES":
        return payload
    permission = {"allowed": False, "scope": "map_view_only", "analysis_authority": False,
                  "registry_promoted": False, "reason": "confirmation_required"}
    result = {**payload, "execution_permission": permission}
    # Narrow operation + slots + evidence contract, not a lone keyword trigger.
    command = re.fullmatch(r"([가-힣]{2,30}(?:구|시|군|동|읍|면))(?:으로|로)?\s*(?:이동(?:해줘|해|하기)?|가줘)[.!?]?", query.strip())
    context = spatial_context or {}
    if not command or any(context.get(k) for k in ("exclusions", "target_features", "selected_feature", "radius", "distance_m")):
        return result
    if (payload.get("external_evidence_report") or {}).get("domain_id") != "administrative_place_lookup":
        return result
    candidates = payload.get("location_candidates") or []
    if len(candidates) != 1:
        permission["reason"] = "ambiguous_candidates"
        return result
    candidate = candidates[0]
    if str(candidate.get("label", "")).split(",")[0].strip() != command.group(1):
        permission["reason"] = "name_not_exact"
        return result
    match = re.fullmatch(r"POINT\(([0-9.+-]+)\s+([0-9.+-]+)\)", candidate.get("geometry") or "")
    try:
        coords = [float(v) for v in match.groups()] if match else []
    except ValueError:
        coords = []
    if (len(coords) != 2 or not all(math.isfinite(v) for v in coords)
            or not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90)
            or candidate.get("crs") != "EPSG:4326"
            or not candidate.get("source_ref") or not candidate.get("source_url")
            or candidate.get("authority_level") not in {"supplemental", "public_authoritative"}):
        permission["reason"] = "invalid_geometry_or_provenance"
        return result
    permission.update(allowed=True, reason="unique_exact_administrative_place_for_explicit_navigation")
    return {**result, "status": "RESOLVED", "error_code": None,
            "geometry": candidate["geometry"], "crs": "EPSG:4326", "location_text": candidate["label"],
            "place_id": candidate.get("place_id"), "place_version": candidate.get("place_version"),
            "location_resolution": {**candidate, "status": "SUPPLEMENTAL_DISPLAY_ONLY", "use_as_authority": False,
                                    "requires_confirmation": False, "execution_permission": permission},
            "location_candidates": [],
            "summary": f"{candidate['label']} 위치로 지도를 이동합니다. 출처: {candidate['source_ref']}. 이 보조 위치는 분석의 권위 근거로 승인된 것이 아닙니다."}


def resolve_payload(query, spatial_context):
    place_query = place_navigation_target(query)
    try:
        geometry, label, crs, resolution = resolve_location(place_query, spatial_context)
        return {
            "status": "RESOLVED", "geometry": geometry, "location_text": label, "crs": crs,
            "place_id": resolution.get("place_id"), "place_version": resolution.get("place_version"),
            "location_resolution": resolution, "location_candidates": [],
            "summary": f"{label}의 기준 위치를 확인했습니다.",
        }
    except PlaceResolutionProblem as exc:
        if exc.code in {"GAZETTEER_UNAVAILABLE", "LOCATION_UNCONFIRMED"}:
            fallback = external_place_fallback(query)
            if fallback:
                return fallback
        return {
            "status": "NEEDS_CLARIFICATION" if exc.status == "NEEDS_USER_INPUT" else "BLOCKED",
            "error_code": exc.code, "summary": str(exc), "location_candidates": exc.candidates,
        }


@router.post("/places/resolve")
async def resolve_place(request: PlaceResolveRequest):
    return await asyncio.to_thread(resolve_payload, request.query, request.spatial_context)
