"""Execution gate tests using a deterministic DB boundary, not fake UI data."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from data.database import get_s101_db
from services.uport.planning_router import router
from services.uport.agent_registry import get_executable_agent


class _Result:
    """Represent only the SQLAlchemy result methods exercised by the Agent."""
    def __init__(self, row):
        self.row = row

    def first(self):
        return self.row

    def mappings(self):
        return self


class _Database:
    """Record bound SQL parameters so ID/version validation can be asserted."""
    def __init__(self, matched=True):
        self.matched = matched
        self.parameters = []

    def execute(self, statement, params=None):
        sql = str(statement)
        if params:
            self.parameters.append(params)
        if sql.startswith("SET LOCAL"):
            return _Result(None)
        if sql.lstrip().startswith("SELECT 1"):
            return _Result((1,) if self.matched else None)
        return _Result({
            "feature_instance_id": 936480,
            "dataset_id": 12,
            "dataset_version_id": 34,
            "geometry_type": "POINT",
            "geometry": {"type": "Point", "coordinates": [129.38, 35.51]},
            "rebuilt_at": None,
        })


def _client(db):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_s101_db] = lambda: db
    return TestClient(app)


def _request(query="이 선석을 지도에 보여줘"):
    return {
        "query": query,
        "map_selection": {
            "entity_type": "s101_berth", "feature_id": 936480,
            "dataset_id": 12, "dataset_version_id": 34,
        },
    }


def test_selected_berth_requires_exact_dataset_and_returns_evidence():
    database = _Database()
    response = _client(database).post("/api/v1/uport/query/execute", json=_request())
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["query_execution_context"]["readiness"] == "EXECUTION_READY"
    assert result["features"][0]["id"] == "936480"
    assert result["map_layers"][0]["inline_geojson"]["features"][0]["id"] == "936480"
    assert result["evidence"][0]["data"]["product_specification"] == "INT.IHO.S-101.2.0"
    assert all(params["feature_id"] == 936480 and params["dataset_version_id"] == 34
               for params in database.parameters)


def test_nonexistent_or_wrong_version_berth_never_executes_tool():
    database = _Database(matched=False)
    response = _client(database).post("/api/v1/uport/query/execute", json=_request())
    result = response.json()
    assert result["error_code"] == "ENTITY_NOT_FOUND"
    assert result["features"] == []
    assert len(database.parameters) == 1  # Only the preflight lookup ran.


def test_live_ais_query_is_blocked_before_database_access():
    database = _Database()
    response = _client(database).post("/api/v1/uport/query/execute", json=_request("AIS 선박 ETA를 보여줘"))
    result = response.json()
    assert result["status"] == "blocked"
    assert result["error_code"] == "DATASET_NOT_AVAILABLE"
    assert database.parameters == []


def test_only_implemented_specialist_is_executable():
    # Registry names alone cannot cause unavailable models or providers to run.
    assert get_executable_agent("uport.s101.berth.search") is not None
    assert get_executable_agent("uport.ais.search") is None
    assert get_executable_agent("uport.eta.predict") is None
    assert get_executable_agent("uport.berth.optimize") is None
    assert get_executable_agent("uport.port_knowledge.search") is None
