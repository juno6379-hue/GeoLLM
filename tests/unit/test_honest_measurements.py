import pytest


def test_las_metadata_is_measured_from_file(tmp_path):
    import laspy
    import numpy as np
    from services.drone_analysis_agent.data_ingestion import parse_las_header

    points = laspy.LasData(laspy.LasHeader(point_format=0, version="1.2"))
    points.x = np.array([0., 1., 2.])
    points.y = np.array([0., 1., 2.])
    points.z = np.array([1., 2., 3.])
    path = tmp_path / "measured.las"
    points.write(path)
    metadata = parse_las_header(str(path))
    assert metadata["point_count"] == 3
    assert metadata["has_rgb"] is False
    assert metadata["has_intensity"] is True
    assert metadata["crs"] is None
    assert metadata["average_density"] is None


@pytest.mark.asyncio
async def test_missing_risk_evidence_cannot_create_grade(monkeypatch):
    from services.spatial_analysis_agent.risk_evaluator import RiskEvaluator

    monkeypatch.setenv("OPENAI_API_KEY", "test-never-used")
    result = await RiskEvaluator().aevaluate(
        {"properties": {"name": "Wreck", "depth": 5, "distance_m": 0}}
    )
    assert result["risk_level"] == "UNKNOWN"
    assert result["evaluation_status"] == "NOT_EVALUATED"


@pytest.mark.asyncio
async def test_document_packaging_preserves_blocked_status(monkeypatch):
    from services.orchestrator import graph
    from shared.schemas.agent import AgentResult, AgentStatus

    monkeypatch.setattr(graph, "_record_query_quality_issues", lambda *args: None)
    result = AgentResult(task_id="blocked-test", trace_id="blocked-test", agent_name="Standard RAG Agent",
                         agent_version="test", status=AgentStatus.BLOCKED, error_code="RAG_SOURCE_UNAVAILABLE")
    state = await graph.map_report_node({"task_id": "blocked-test", "query": "definition",
                                         "agent_result": result, "task_plan": {"analysis_type": "document_search"}})
    assert state["status"] == state["final_dict"]["status"] == AgentStatus.BLOCKED
    assert state["final_dict"]["error_code"] == "RAG_SOURCE_UNAVAILABLE"


def test_registration_commits_file_metadata_and_reuses_dataset_id(tmp_path):
    import laspy
    import numpy as np
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from services.orchestrator.lidar_router import FolderRegisterRequest, register_local_folder
    from data.models.lidar_dataset import LiDARDataset

    points = laspy.LasData(laspy.LasHeader(point_format=0, version="1.2"))
    points.x = np.array([0., 1., 2.])
    points.y = np.array([0., 1., 2.])
    points.z = np.array([1., 2., 3.])
    points.write(tmp_path / "registered.las")
    engine = create_engine("sqlite://")
    LiDARDataset.__table__.create(engine)
    try:
        with Session(engine) as db:
            req = FolderRegisterRequest(folder_path=str(tmp_path))
            first = register_local_folder(req, db)
            second = register_local_folder(req, db)
            assert first["status"] == second["status"] == "COMPLETED"
            assert first["datasets"][0]["dataset_id"] == second["datasets"][0]["dataset_id"]
            stored = db.query(LiDARDataset).one()
            assert stored.point_count == 3
            assert stored.file_size_bytes == (tmp_path / "registered.las").stat().st_size
            assert stored.crs is None and stored.has_rgb is False
    finally:
        engine.dispose()
