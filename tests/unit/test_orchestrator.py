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
