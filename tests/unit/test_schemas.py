import pytest
from datetime import datetime
from shared.schemas.agent import AgentRequest, SecurityContext, OrchestratorContext
from shared.security.context import check_clearance, ClearanceLevel
from services.registry.mock import get_tools, get_tool_by_name

def test_agent_request_creation():
    req = AgentRequest(
        task_id="t1",
        trace_id="tr1",
        user_id="u1",
        organization_id="org1",
        agent_name="spatial",
        original_query="hello",
        security_context=SecurityContext(clearance_level="PUBLIC")
    )
    assert req.task_id == "t1"
    assert req.orchestrator_context.priority == "NORMAL"

def test_clearance_level():
    assert check_clearance(ClearanceLevel.SECRET, ClearanceLevel.CONFIDENTIAL) is True
    assert check_clearance(ClearanceLevel.PUBLIC, ClearanceLevel.SECRET) is False

def test_mock_registry():
    tools = get_tools()
    assert len(tools) == 1
    tool = get_tool_by_name("postgis.dwithin")
    assert tool is not None
    assert tool.tool_name == "postgis.dwithin"
    
    missing = get_tool_by_name("not.exist")
    assert missing is None
