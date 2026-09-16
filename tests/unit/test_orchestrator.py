import pytest
import asyncio
from fastapi.testclient import TestClient

from services.orchestrator.main import app
from services.orchestrator.router import TASK_STORE
from shared.schemas.agent import AgentStatus

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_task_and_get_status():
    # 1. 태스크 생성
    payload = {
        "query": "부산항 입구 3km 이내 위험객체 분석",
        "organization_id": "test_org"
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 202
    
    data = response.json()
    task_id = data["task_id"]
    assert data["status"] == AgentStatus.RECEIVED

    # FastAPI TestClient의 BackgroundTasks는 동기적으로 실행되지 않기 때문에
    # 직접 state machine을 호출하거나, 비동기 테스트 환경이 필요합니다.
    # 여기서는 간단히 TASK_STORE에 잘 들어갔는지만 검증.
    
    assert task_id in TASK_STORE
    assert TASK_STORE[task_id]["query"] == payload["query"]
    assert TASK_STORE[task_id]["status"] == AgentStatus.RECEIVED

    # 2. 상태 조회 API 검증
    status_response = client.get(f"/api/v1/tasks/{task_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == AgentStatus.RECEIVED

def test_query_execution_context_contract_fields():
    from services.orchestrator.graph import _build_query_execution_context

    state = {
        "task_id": "task-contract-1",
        "query": "부산항 입구 3km 이내 위험객체",
        "user_id": "u1",
        "organization_id": "org1",
        "normalized_query": "부산항 입구 3000m 이내 위험객체",
        "spatial_context": {"base_location": "부산항 입구"},
        "graph_context": {"graph_paths": [{"id": "path1"}], "rag_filters": {"product_id": "S-101"}},
        "data_discovery_result": {"can_execute_spatial_query": True},
    }
    route_plan = {
        "task_id": "task-contract-1",
        "execution_ready": True,
        "warnings": ["check"],
    }

    qec = _build_query_execution_context(
        state,
        {"location_text": "부산항 입구", "distance_m": 3000, "target_features": ["Wreck"]},
        ctx_res={"selected_context": "항해안전", "analysis_type": "radius_feature_search", "status": "RESOLVED"},
        route_plan=route_plan,
    )

    assert qec.contract_version == "geollm.execution.v1"
    assert qec.request_id == "task-contract-1"
    assert qec.plan_hash
    assert qec.readiness == "EXECUTION_READY"
    assert qec.slots.resolved_target_set == ["Wreck"]
    assert qec.rag["filters"] == {"product_id": "S-101"}


def test_s101_hazard_radius_fast_path_is_registry_backed():
    from services.orchestrator.graph import (
        _resolve_known_marine_place_wkt,
        _s101_hazard_radius_registry_config,
    )

    config = _s101_hazard_radius_registry_config()

    assert config["template_id"] == "feature_search_by_radius"
    assert config["layer_id"] == "GBENC_S101_feature"
    assert set(config["feature_codes"]) >= {100, 101, 102}
    assert set(config["target_features"]) >= {"UnderwaterAwashRock", "Wreck", "Obstruction"}
    assert config["layer"]["physical_table"] == "projection.s101_feature_current"
    assert config["template"]["executor"] == "postgis.dwithin"

    wkt, name = _resolve_known_marine_place_wkt(
        "Busan Port Entrance 3km Wreck",
        {"spatial_context": {}},
    )
    assert wkt == "POINT(129.075 35.075)"
    assert name == "부산항 입구"

@pytest.mark.asyncio
async def test_state_machine_flow():
    from services.orchestrator.state_machine import run_orchestration_workflow
    
    task_id = "test-task-123"
    query = "부산항 위험객체 분석"
    TASK_STORE[task_id] = {
        "status": AgentStatus.RECEIVED,
        "query": query,
        "result": None
    }
    
    await run_orchestration_workflow(task_id, query, TASK_STORE)
    
    assert TASK_STORE[task_id]["status"] == AgentStatus.COMPLETED
    assert TASK_STORE[task_id]["result"] is not None
    assert TASK_STORE[task_id]["result"]["agent_name"] == "spatial-analysis-agent"
    assert TASK_STORE[task_id]["result"]["structured_result"]["count"] == 5
