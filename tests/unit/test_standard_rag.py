import pytest
from shared.schemas.agent import AgentRequest, Intent, SecurityContext, OrchestratorContext
from services.standard_rag_agent.agent import execute_rag_search

@pytest.mark.asyncio
async def test_rag_search_with_match():
    request = AgentRequest(
        task_id="test-rag-1",
        trace_id="tr1",
        user_id="u1",
        organization_id="org1",
        agent_name="standard-rag-agent",
        original_query="해상풍력 단지 개발 시 보호구역 기준이 어떻게 되나요?",
        parsed_intent=Intent(intent_type="SEARCH", target_objects=["해상풍력", "보호구역"]),
        security_context=SecurityContext(clearance_level="PUBLIC")
    )
    
    result = await execute_rag_search(request)
    
    assert result.status == "COMPLETED"
    assert result.structured_result["retrieved_count"] >= 1
    assert len(result.evidence) >= 1
    assert "해양환경관리법" in result.evidence[0]

@pytest.mark.asyncio
async def test_rag_search_no_match():
    request = AgentRequest(
        task_id="test-rag-2",
        trace_id="tr2",
        user_id="u1",
        organization_id="org1",
        agent_name="standard-rag-agent",
        original_query="우주 정거장 설계 기준",
        security_context=SecurityContext(clearance_level="PUBLIC")
    )
    
    result = await execute_rag_search(request)
    
    assert result.status == "COMPLETED"
    assert result.structured_result["retrieved_count"] == 0
    assert len(result.evidence) == 0
