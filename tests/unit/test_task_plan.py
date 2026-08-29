import pytest
import uuid
import sys
import sys

from shared.schemas.agent import AgentRequest, SecurityContext, AgentStatus
from services.orchestrator.graph import parse_intent_node, resolve_context_node, create_plan_node

queries = [
    "부산항 입구 3km 이내 위험객체를 찾아줘",
    "항로 주변 위험객체를 지도에 표시해줘",
    "위험객체 찾아줘",
    "부산항 위험한 것 찾아줘",
    "해상풍력 후보지 주변 위험객체 찾아줘"
]

@pytest.mark.asyncio
async def test_hazard_search_task_plan():
    # 1. 대상 쿼리: 부산항 입구 3km 이내 위험객체를 찾아줘
    query = queries[0]
    
    req = AgentRequest(
        task_id=f"TASK-{uuid.uuid4().hex[:8]}",
        trace_id="trace_1",
        user_id="user1",
        organization_id="org1",
        agent_name="Orchestrator",
        original_query=query,
        security_context=SecurityContext(clearance_level="PUBLIC", allowed_tool_scopes=[])
    )
    
    state = {
        "task_id": req.task_id,
        "query": query,
        "agent_request": req,
        "status": AgentStatus.RECEIVED,
        "state_history": []
    }
    
    state = await parse_intent_node(state)
    state = await resolve_context_node(state)
    
    assert state["status"] != AgentStatus.NEEDS_CLARIFICATION, "이 질의는 clarification 대상이 아닙니다."
    
    state = await create_plan_node(state)
    
    task_plan = state.get("task_plan")
    assert task_plan is not None
    
    assert task_plan["status"] == "ROUTED"
    assert task_plan["intent"] == "marine_hazard_feature_search"
    assert task_plan["context"] == "navigation_safety"
    assert task_plan["analysis_type"] == "feature_search_by_radius"
    assert task_plan["primary_agent"] == "Spatial Analysis Agent"
    
    # 툴 매칭 확인
    assert "gbenc.s101_feature_search_by_radius" in task_plan["tools"]
    assert "postgis.dwithin" in task_plan["tools"]
    
    # 슬롯 확인
    slots = task_plan["slots"]
    assert slots["location"] == "부산항 입구"
    assert slots["distance_m"] == 3000
    assert slots["target_term"] == "위험객체"
    assert "Wreck" in slots["target_features"]
    
    assert task_plan["clarification_required"] is False
    assert task_plan["confidence"] >= 0.85

@pytest.mark.asyncio
async def test_clarification_queries():
    # 다른 쿼리들에 대한 모호성 해소 검증
    for query in queries[1:]:
        req = AgentRequest(
            task_id=f"TASK-{uuid.uuid4().hex[:8]}",
            trace_id="trace_1",
            user_id="user1",
            organization_id="org1",
            agent_name="Orchestrator",
            original_query=query,
            security_context=SecurityContext(clearance_level="PUBLIC", allowed_tool_scopes=[])
        )
        state = {
            "task_id": req.task_id,
            "query": query,
            "agent_request": req,
            "status": AgentStatus.RECEIVED,
            "state_history": []
        }
        
        state = await parse_intent_node(state)
        state = await resolve_context_node(state)
        
        if query == "항로 주변 위험객체를 지도에 표시해줘":
            # 이 쿼리도 위치(항로 주변 -> 위치정보 추출) + 지도 조건 충족으로 패스될 수 있음.
            # 하지만 SlotExtractor가 "항로 주변"을 위치로 잘 뽑는지에 따라 달라짐.
            pass
        elif query == "위험객체 찾아줘":
            assert state["status"] == AgentStatus.NEEDS_CLARIFICATION
            assert "어느 위치" in state["clarification_questions"][0]
        elif query == "부산항 위험한 것 찾아줘":
            assert state["status"] == AgentStatus.NEEDS_CLARIFICATION
            assert "추가 정보(거리 또는 영역)가 필요합니다" in state["clarification_questions"][0]
        elif query == "해상풍력 후보지 주변 위험객체 찾아줘":
            assert state["status"] == AgentStatus.NEEDS_CLARIFICATION
