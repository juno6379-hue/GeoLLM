from pathlib import Path
import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.drone_analysis_agent.module02_preprocessing import run_preprocessing
from services.drone_analysis_agent.tools import DroneToolRegistry
from services.orchestrator.lidar_router import router
from data.database import get_postgis_db

def test_missing_lidar_file_never_creates_fake_output(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_preprocessing("no-file", str(tmp_path / "absent.las"))
    assert not list(tmp_path.iterdir())

def test_missing_engine_never_copies_input(tmp_path, monkeypatch):
    source = tmp_path / "input.las"
    source.write_bytes(b"test input")
    monkeypatch.setattr("services.drone_analysis_agent.module02_preprocessing.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="PDAL"):
        run_preprocessing("no-engine", str(source))
    assert list(tmp_path.iterdir()) == [source]

@pytest.mark.parametrize("name", ["point_cloud_registration", "ground_classification", "terrain_model_generation", "object_extraction", "change_detection", "generate_visualization"])
def test_unimplemented_tools_never_claim_success(name):
    with pytest.raises(NotImplementedError):
        getattr(DroneToolRegistry(), name)("unregistered-input")

def test_lidar_api_missing_db_is_explicit():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_postgis_db] = lambda: None
    client = TestClient(app)
    for endpoint in ("preprocess", "classify"):
        response = client.post("/lidar/" + endpoint, json={"dataset_id": "demo_dataset_001"})
        assert response.status_code == 503
        assert "job_id" not in response.json()

def test_rag_never_uses_fake_documents_even_under_test_flags(monkeypatch):
    from services.standard_rag_agent import vdb
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")
    monkeypatch.delenv("S101_DB_URL", raising=False)
    monkeypatch.setattr(vdb.db_module, "init_engines", lambda: None)
    monkeypatch.setattr(vdb.db_module, "PostgisSessionLocal", None)
    with pytest.raises(vdb.RetrievalUnavailable):
        vdb.search_vdb("해상풍력 보호구역 거리")

def test_s111_cannot_return_handwritten_embedding_results():
    from services.spatial_analysis_agent.s111_semantic_tool import search_s111_semantic
    result = search_s111_semantic.invoke({"query": "위험한 조류"})
    assert result["status"] == "BLOCKED"
    assert "map_spec" not in result["structured_result"]
