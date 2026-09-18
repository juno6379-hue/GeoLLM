"""Typed place resolution for query clients, using server-owned provenance."""

import asyncio
import hashlib
import json
import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scripts.run_external_evidence_gap_fill import run_gap_fill
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location

router = APIRouter(tags=["places"])


class PlaceResolveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    spatial_context: dict[str, Any] = Field(default_factory=dict)


def _candidate_version(candidate: dict[str, Any]) -> str:
    raw = json.dumps(candidate, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _external_candidate_to_place(candidate: dict[str, Any]) -> dict[str, Any]:
    geometry = candidate.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    wkt = None
    if isinstance(coordinates, list) and len(coordinates) >= 2 and all(value is not None for value in coordinates[:2]):
        wkt = f"POINT({coordinates[0]} {coordinates[1]})"
    result = {
        "place_id": candidate.get("candidate_id"),
        "place_version": _candidate_version(candidate),
        "label": candidate.get("name") or candidate.get("candidate_id"),
        "base_location": candidate.get("name") or candidate.get("candidate_id"),
        "geometry": wkt,
        "geometry_geojson": geometry.get("geojson"),
        "crs": "EPSG:4326",
        "status": "supplemental_external_candidate",
        "source_ref": candidate.get("source_name") or candidate.get("source_tier"),
        "source_records": [{
            "source_ref": candidate.get("source_name") or candidate.get("source_tier"),
            "source_url": candidate.get("source_url"),
            "authority_level": candidate.get("authority_level"),
            "promotion_status": candidate.get("promotion_status"),
            "review_required": candidate.get("review_required", True),
        }],
        "requires_confirmation": True,
        "authority_level": candidate.get("authority_level"),
        "promotion_status": candidate.get("promotion_status"),
        "review_required": candidate.get("review_required", True),
    }
    if wkt:
        result["longitude"] = coordinates[0]
        result["latitude"] = coordinates[1]
    return result


def external_place_fallback(query: str) -> dict[str, Any] | None:
    report = run_gap_fill(
        query,
        fetch_osm=bool(os.getenv("GEOLLM_OSM_USER_AGENT")),
        ask_ollama=bool(os.getenv("GEOLLM_PLACE_FALLBACK_OLLAMA")),
    )
    raw_candidates = [
        candidate
        for candidate in report.get("candidates") or []
        if candidate.get("authority_level") == "supplemental"
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
    return {
        "status": "NEEDS_CLARIFICATION",
        "error_code": "EXTERNAL_PLACE_CANDIDATES",
        "summary": "로컬 해양 지명사전에는 없지만 외부 보조 후보를 찾았습니다. authoritative 승격 전이므로 후보를 확인해 주세요.",
        "location_candidates": candidates,
        "external_evidence_report": {
            "domain_id": report.get("domain_id"),
            "candidate_counts": report.get("candidate_counts"),
            "osm_fetch_diagnostics": report.get("osm_fetch_diagnostics"),
            "ollama_ambiguity_review": report.get("ollama_ambiguity_review"),
        },
    }


def resolve_payload(query, spatial_context):
    try:
        geometry, label, crs, resolution = resolve_location(query, spatial_context)
        return {
            "status": "RESOLVED", "geometry": geometry, "location_text": label, "crs": crs,
            "place_id": resolution.get("place_id"), "place_version": resolution.get("place_version"),
            "location_resolution": resolution, "location_candidates": [],
            "summary": f"{label}의 기준 위치를 확인했습니다.",
        }
    except PlaceResolutionProblem as exc:
        if exc.code == "GAZETTEER_UNAVAILABLE":
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
