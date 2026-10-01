"""HTTP contract checks without importing the orchestrator graph or databases."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.orchestrator import place_router
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(place_router.router, prefix="/api/v1")
    with TestClient(app) as client:
        yield client


def test_resolved_response_carries_server_owned_identity_and_sources(client, monkeypatch):
    calls = []
    resolution = {"status": "CONFIRMED_SELECTION", "place_id": "island:7", "place_version": "a" * 64, "source_ref": "serving.island_gazetteer_current", "source_records": [{"source_id": "7", "revision": "current"}]}

    def resolve(query, spatial):
        calls.append((query, spatial))
        return "POINT(129 35)", "Island A", "EPSG:4326", resolution

    monkeypatch.setattr(place_router, "resolve_location", resolve)
    spatial = {"place_id": "island:7", "place_version": "a" * 64, "geometry": "POINT(129 35)", "crs": "EPSG:4326", "target_features": ["Wreck"], "location_resolution": {"source_ref": "client supplied"}}
    response = client.post("/api/v1/places/resolve", json={"query": "Island A", "spatial_context": spatial})
    assert response.status_code == 200
    body = response.json()
    assert calls == [("Island A", spatial)]
    assert body["status"] == "RESOLVED"
    assert body["geometry"] == "POINT(129 35)"
    assert body["crs"] == "EPSG:4326"
    assert body["location_text"] == "Island A"
    assert body["place_id"] == resolution["place_id"]
    assert body["place_version"] == resolution["place_version"]
    assert body["location_resolution"] == resolution
    assert body["location_candidates"] == []


def test_explicit_coordinate_response_does_not_invent_place_identity(client, monkeypatch):
    monkeypatch.setattr(place_router, "resolve_location", lambda query, spatial: ("POINT(129 35)", "Explicit point", "EPSG:4326", {"status": "CONFIRMED_INPUT", "source_ref": "request.spatial_context.geometry"}))
    response = client.post("/api/v1/places/resolve", json={"query": "Explicit point"})
    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"
    assert response.json()["place_id"] is None
    assert response.json()["place_version"] is None


@pytest.mark.parametrize("code", ["LOCATION_UNCONFIRMED", "STALE_PLACE_SELECTION", "CONFLICTING_LOCATION"])
def test_clarification_preserves_candidate_version_and_provenance(client, monkeypatch, code):
    candidates = [{"place_id": "khoa:2", "place_version": "b" * 64, "geometry": "POINT(129 35)", "crs": "EPSG:4326", "label": "Candidate", "source_ref": "public.maritime_gazetteer_khoa", "source_records": [{"source_id": "2", "revision": "2026"}], "requires_confirmation": True}]

    def resolve(query, spatial):
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", code, "Choose a location", candidates=candidates)

    monkeypatch.setattr(place_router, "resolve_location", resolve)
    response = client.post("/api/v1/places/resolve", json={"query": "Candidate"})
    assert response.status_code == 200
    payload = response.json()
    assert {key: payload[key] for key in ('status', 'error_code', 'summary', 'location_candidates')} == {"status": "NEEDS_CLARIFICATION", "error_code": code, "summary": "Choose a location", "location_candidates": candidates}
    assert payload['query_interpretation']['location_text'] == 'Candidate'
    assert payload['search_execution']['status'] == 'NOT_RUN'


@pytest.mark.parametrize("status,code", [("BLOCKED_DATA", "GAZETTEER_UNAVAILABLE"), ("BLOCKED_CONFIG", "INVALID_REGISTRY")])
def test_source_failure_is_blocked_not_empty_resolution(client, monkeypatch, status, code):
    def resolve(query, spatial):
        raise PlaceResolutionProblem(status, code, "Source unavailable")

    monkeypatch.setattr(place_router, "resolve_location", resolve)
    monkeypatch.setattr(place_router, "external_place_fallback", lambda query: None)
    response = client.post("/api/v1/places/resolve", json={"query": "A place"})
    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"
    assert response.json()["error_code"] == code
    assert response.json()["location_candidates"] == []
    assert not response.json().get("geometry")


def test_gazetteer_unavailable_returns_external_place_candidates(client, monkeypatch):
    def resolve(query, spatial):
        raise PlaceResolutionProblem("BLOCKED_DATA", "GAZETTEER_UNAVAILABLE", "Source unavailable")

    fallback = {
        "status": "NEEDS_CLARIFICATION",
        "error_code": "EXTERNAL_PLACE_CANDIDATES",
        "summary": "external candidates",
        "location_candidates": [{
            "place_id": "extgap.osm_nominatim:1",
            "place_version": "a" * 64,
            "label": "Haeundae-gu",
            "geometry": "POINT(129.1638 35.1629)",
            "crs": "EPSG:4326",
            "requires_confirmation": True,
            "authority_level": "supplemental",
        }],
        "external_evidence_report": {"domain_id": "administrative_place_lookup"},
    }

    monkeypatch.setattr(place_router, "resolve_location", resolve)
    monkeypatch.setattr(place_router, "external_place_fallback", lambda query: fallback)
    response = client.post("/api/v1/places/resolve", json={"query": "해운대구"})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "NEEDS_CLARIFICATION"
    assert body["error_code"] == "EXTERNAL_PLACE_CANDIDATES"
    assert body["location_candidates"][0]["geometry"] == "POINT(129.1638 35.1629)"
    assert body["external_evidence_report"]["domain_id"] == "administrative_place_lookup"


@pytest.mark.parametrize("payload", [{}, {"query": ""}, {"query": "x" * 1001}, {"query": "A", "spatial_context": []}, {"query": "A", "spatial_context": None}])
def test_invalid_request_is_rejected_before_resolution(client, monkeypatch, payload):
    def unexpected_call(query, spatial):
        pytest.fail("Invalid request reached the resolver")

    monkeypatch.setattr(place_router, "resolve_location", unexpected_call)
    response = client.post("/api/v1/places/resolve", json=payload)
    assert response.status_code == 422
