"""U-Port delegates viewport hazards to the existing validated S-101 path."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import services.uport.hazard_router as hazard_router
from services.orchestrator.s101_radius_execution import prepare_bounds_request
from services.uport.planning_router import route_dashboard_query
from services.uport.planning_router import router as planning_router
from services.uport.planning import UportPlanRequest


def _client():
    app = FastAPI()
    app.include_router(hazard_router.router, prefix="/api/v1")
    return TestClient(app)


def test_shared_catalogue_preflight_accepts_uport_viewport_without_db():
    """The reused Agent must bind approved hazard classes before SQL runs."""

    context, _layer, _params = prepare_bounds_request({
        "task_id": "uport-preflight", "user_id": "uport-dashboard",
        "query": "현재 지도 범위의 S-101 항행 위험객체를 찾아줘",
        "spatial_context": {"map_bounds": [129.25, 35.35, 129.55, 35.65],
                            "crs": "EPSG:4326", "context": "navigation_safety"},
    })
    assert context.slots.analysis_type == "feature_search_by_area"
    assert {"Wreck", "Obstruction", "UnderwaterAwashRock"} <= set(context.slots.target_features)
    assert context.provenance["location_resolution"]["status"] == "MAP_BOUNDS"


def test_registry_routes_map_hazards_without_turning_vessel_search_into_viewport():
    """Missing AIS must remain a blocked vessel-centered capability."""

    assert route_dashboard_query(UportPlanRequest(
        query="지도 범위 위험객체를 보여줘",
    )).mode == "s101_hazard_viewport"
    assert route_dashboard_query(UportPlanRequest(
        query="이 선박 주변의 S-101 항행 위험 객체를 찾아줘",
    )).mode == "unavailable"
    assert route_dashboard_query(UportPlanRequest(
        query="선석을 보여줘",
    )).mode == "s101_berth"
    app = FastAPI()
    app.include_router(planning_router, prefix="/api/v1")
    routed = TestClient(app).post("/api/v1/uport/query/route", json={
        "query": "지도 범위 위험객체를 보여줘",
    })
    assert routed.status_code == 200
    assert routed.json()["mode"] == "s101_hazard_viewport"


def test_viewport_uses_shared_pipeline_and_preserves_evidence(monkeypatch):
    calls = []
    feature = {"type": "Feature", "id": "101", "geometry": {
        "type": "Point", "coordinates": [129.4, 35.5],
    }, "properties": {"feature_name": "Wreck"}}

    def shared_pipeline(state):
        calls.append(state)
        return {
            "status": "COMPLETED", "summary": "검증된 위험객체 1건",
            "structured_result": {"total_count": 1, "returned_count": 1,
                                  "truncated": False, "source_layer": {"physical_table": "projection.s101_feature_valid"}},
            "features": {"type": "FeatureCollection", "features": [feature]},
            "evidence_bundle": {"spatial_feature_evidence": [{"evidence_id": "source-101"}]},
        }

    monkeypatch.setattr(hazard_router, "execute_radius_request", shared_pipeline)
    response = _client().post("/api/v1/uport/s101/hazards/viewport", json={
        "bbox": "129.25,35.35,129.55,35.65",
    })
    assert response.status_code == 200
    assert calls[0]["spatial_context"]["map_bounds"] == [129.25, 35.35, 129.55, 35.65]
    assert calls[0]["spatial_context"]["context"] == "navigation_safety"
    assert response.json()["geojson"]["features"][0]["id"] == "101"
    assert response.json()["evidence_bundle"]["spatial_feature_evidence"][0]["evidence_id"] == "source-101"

    natural = _client().post("/api/v1/uport/s101/hazards/query", json={
        "query": "지도 범위 위험객체를 보여줘", "bbox": "129.25,35.35,129.55,35.65",
    })
    assert natural.status_code == 200
    assert calls[1]["query"] == "지도 범위 위험객체를 보여줘"


def test_vessel_centered_hazard_query_cannot_use_viewport_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(hazard_router, "execute_radius_request", lambda state: calls.append(state))
    response = _client().post("/api/v1/uport/s101/hazards/query", json={
        "query": "이 선박 주변의 S-101 항행 위험 객체를 찾아줘",
        "bbox": "129.25,35.35,129.55,35.65",
    })
    assert response.status_code == 422
    assert calls == []


def test_invalid_bounds_and_blocked_search_do_not_return_features(monkeypatch):
    calls = []
    monkeypatch.setattr(hazard_router, "execute_radius_request", lambda state: calls.append(state) or {
        "status": "BLOCKED", "error_code": "DATASET_NOT_AVAILABLE", "summary": "S-101 source unavailable",
    })
    invalid = _client().post("/api/v1/uport/s101/hazards/viewport", json={"bbox": "0,0,5,5"})
    assert invalid.status_code == 422
    assert calls == []
    blocked = _client().post("/api/v1/uport/s101/hazards/viewport", json={
        "bbox": "129.25,35.35,129.55,35.65",
    })
    assert blocked.status_code == 503
    assert blocked.json()["detail"]["code"] == "DATASET_NOT_AVAILABLE"


def test_mismatched_shared_result_is_rejected(monkeypatch):
    monkeypatch.setattr(hazard_router, "execute_radius_request", lambda _state: {
        "status": "COMPLETED", "structured_result": {"total_count": 3, "returned_count": 2,
        "source_layer": {"physical_table": "projection.s101_feature_valid"}},
        "features": {"type": "FeatureCollection", "features": []},
    })
    response = _client().post("/api/v1/uport/s101/hazards/viewport", json={
        "bbox": "129.25,35.35,129.55,35.65",
    })
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "RESULT_CONTRACT_MISMATCH"
