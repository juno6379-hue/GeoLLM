import pytest
from shared.schemas.agent import AgentRequest, Intent, SecurityContext, OrchestratorContext
from services.standard_rag_agent.agent import execute_rag_search
from shared.schemas.agent import QueryExecutionContext, DataBinding, ToolBinding
from services.orchestrator.schema_binding_adapter import BindingResult
from services.orchestrator import execution_validator

@pytest.fixture(autouse=True)
def document_contract(monkeypatch):
    monkeypatch.setenv("OLLAMA_EMBEDDING_URL", "http://fixture.invalid/api/embed")
    monkeypatch.setattr(execution_validator.schema_binding_adapter, "build_bindings", lambda *_: BindingResult(
        data_bindings=[DataBinding(dataset_id="docs", relation="knowledge.document_chunks")],
        tool_bindings=[ToolBinding(tool_id="rag.graph_scoped_retrieve", operation="document_search")]))

def attach_contract(request):
    request.query_execution_context = QueryExecutionContext(request_id=request.task_id,
        original_query=request.original_query, route_plan={"analysis_type": "document_search"})

@pytest.mark.asyncio
async def test_rag_search_with_match(monkeypatch):
    monkeypatch.setattr("services.standard_rag_agent.agent.search_vdb", lambda *a, **kw: [
        {"doc_id": "fixture-evidence", "title": "Source fixture", "version": "test", "section": "source",
         "content": "Source excerpt for retrieval contract testing.", "similarity": 0.73}])
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
    
    attach_contract(request)
    result = await execute_rag_search(request)
    
    assert result.status == "COMPLETED"
    assert result.structured_result["retrieved_count"] >= 1
    assert len(result.evidence) >= 1
    assert "Source fixture" in result.evidence[0]

@pytest.mark.asyncio
async def test_rag_search_no_match(monkeypatch):
    monkeypatch.setattr("services.standard_rag_agent.agent.search_vdb", lambda *a, **kw: [])
    request = AgentRequest(
        task_id="test-rag-2",
        trace_id="tr2",
        user_id="u1",
        organization_id="org1",
        agent_name="standard-rag-agent",
        original_query="우주 정거장 설계 기준",
        security_context=SecurityContext(clearance_level="PUBLIC")
    )
    
    attach_contract(request)
    result = await execute_rag_search(request)
    
    assert result.status == "COMPLETED"
    assert result.structured_result["retrieved_count"] == 0
    assert len(result.evidence) == 0
