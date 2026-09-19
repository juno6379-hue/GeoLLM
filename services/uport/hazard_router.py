"""U-Port viewport access to GeoLLM's existing S-101 hazard pipeline."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.orchestrator.s101_radius_execution import execute_radius_request
from services.orchestrator.query_candidate_broker import query_candidate_broker
from services.uport.map_router import parse_bbox

router = APIRouter(prefix="/uport/s101", tags=["U-Port S-101"])


class HazardViewportRequest(BaseModel):
    """Bounded WGS84 viewport; vessel identity is not inferred from it."""

    bbox: str = Field(description="west,south,east,north in EPSG:4326")


class HazardQueryRequest(HazardViewportRequest):
    """Natural-language hazard query grounded to the current map viewport."""

    query: str = Field(min_length=1, max_length=2000)


class HazardViewportResponse(BaseModel):
    """A verified subset of the shared spatial pipeline's result contract."""

    status: str
    total_count: int = Field(ge=0)
    returned_count: int = Field(ge=0)
    truncated: bool
    geojson: dict
    evidence_bundle: dict
    source_layer: dict
    narrative: str


@router.post("/hazards/viewport", response_model=HazardViewportResponse)
def search_hazards_in_viewport(request: HazardViewportRequest) -> HazardViewportResponse:
    """Use GeoLLM's approved catalogue, QueryBuilder, PostGIS and validator.

    This adapter supplies only a validated map extent and an explicit
    navigation-safety purpose. The shared pipeline owns feature selection,
    SQL execution, result geometry validation, Evidence and provenance.
    """

    return _run_hazard_query("현재 지도 범위의 S-101 항행 위험객체를 찾아줘", request.bbox)


@router.post("/hazards/query", response_model=HazardViewportResponse)
def search_hazards_from_query(request: HazardQueryRequest) -> HazardViewportResponse:
    """Accept only Registry-routed viewport requests from the Agent panel."""

    selected = {row["candidate_id"] for row in
                query_candidate_broker.retrieve_domain_capabilities(request.query, "uport")}
    if "uport.s101.hazard.search" in selected or "uport.s101.hazard.viewport" not in selected:
        raise HTTPException(status_code=422, detail={
            "code": "VALIDATION_FAILED", "message": "Query is not a viewport hazard search",
        })
    return _run_hazard_query(request.query, request.bbox)


def _run_hazard_query(query: str, bbox: str) -> HazardViewportResponse:
    """Delegate both map control and natural language to one verified path."""

    west, south, east, north = parse_bbox(bbox)
    result = execute_radius_request({
        "task_id": str(uuid4()), "user_id": "uport-dashboard",
        "query": query,
        "spatial_context": {
            "map_bounds": [west, south, east, north], "crs": "EPSG:4326",
            "context": "navigation_safety",
        },
    })
    if result.get("status") != "COMPLETED":
        # A missing source or failed validation must never turn into a blank
        # but apparently successful hazard layer.
        raise HTTPException(status_code=503, detail={
            "code": result.get("error_code") or "DATASET_NOT_AVAILABLE",
            "message": result.get("summary") or "S-101 hazard search is unavailable",
        })
    summary = result.get("structured_result") or {}
    geojson = result.get("features") or {}
    bundle = result.get("evidence_bundle") or {}
    layer = summary.get("source_layer") or {}
    total = summary.get("total_count")
    returned = summary.get("returned_count")
    feature_evidence = bundle.get("spatial_feature_evidence") if isinstance(bundle, dict) else None
    if (not isinstance(total, int) or not isinstance(returned, int)
            or total < returned or not isinstance(feature_evidence, list)
            or not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection"
            or not isinstance(geojson.get("features"), list)
            or len(geojson["features"]) != returned
            or len(feature_evidence) != returned or not layer):
        raise HTTPException(status_code=502, detail={
            "code": "RESULT_CONTRACT_MISMATCH",
            "message": "S-101 hazard response failed U-Port contract validation",
        })
    return HazardViewportResponse(
        status="success", total_count=total, returned_count=returned,
        truncated=bool(summary.get("truncated")), geojson=geojson,
        evidence_bundle=bundle, source_layer=layer,
        narrative=result.get("summary") or "S-101 hazard search completed",
    )
