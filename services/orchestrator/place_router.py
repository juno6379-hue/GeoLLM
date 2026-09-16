"""Typed place resolution for query clients, using server-owned provenance."""

import asyncio
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location

router = APIRouter(tags=["places"])


class PlaceResolveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    spatial_context: dict[str, Any] = Field(default_factory=dict)


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
        return {
            "status": "NEEDS_CLARIFICATION" if exc.status == "NEEDS_USER_INPUT" else "BLOCKED",
            "error_code": exc.code, "summary": str(exc), "location_candidates": exc.candidates,
        }


@router.post("/places/resolve")
async def resolve_place(request: PlaceResolveRequest):
    return await asyncio.to_thread(resolve_payload, request.query, request.spatial_context)
