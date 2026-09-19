"""Contract tests for the bounded U-Port S-101 map endpoint."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from data.database import get_s101_db
from services.uport.map_router import parse_bbox, router


@pytest.mark.parametrize("raw", [
    "129,35,129,36",       # Zero-width extent cannot represent a viewport.
    "129,35,132,36",       # Large requests bypass the intended query bound.
    "129,35,nan,36",       # Non-finite values must not reach PostGIS.
    "129,35,130",          # Missing coordinate is an invalid API contract.
])
def test_invalid_bbox_is_rejected(raw):
    with pytest.raises(HTTPException) as error:
        parse_bbox(raw)
    assert error.value.status_code == 422


def test_unconfigured_database_has_explicit_unavailable_response():
    # This isolated FastAPI app verifies the HTTP error contract without
    # importing the full Orchestrator or requiring an external PostGIS server.
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_s101_db] = lambda: None
    response = TestClient(app).get("/api/v1/uport/map/berths?bbox=129.3,35.4,129.5,35.6")
    assert response.status_code == 503
    assert response.json()["detail"] == "S-101 database is not configured"


def test_live_ais_is_unavailable_without_a_registered_provider():
    # A valid viewport must not silently fall back to historical CSV tracks.
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/uport/map/vessels?bbox=129.3,35.4,129.5,35.6")
    assert response.status_code == 503
    assert response.json()["detail"] == "Live AIS provider is not configured"
