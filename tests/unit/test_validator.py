import pytest
from shared.schemas.agent import AgentResult, AgentStatus
from services.orchestrator.validator import validate_agent_result

def test_validator_pass():
    result = AgentResult(
        task_id="t1",
        trace_id="tr1",
        agent_name="standard-rag-agent",
        agent_version="1.0",
        status=AgentStatus.EXECUTING,
        summary="ok",
        structured_result={"retrieved_count": 2}
    )
    validated = validate_agent_result(result)
    assert validated.status != AgentStatus.NEEDS_HITL
    assert not validated.warnings

def test_validator_rag_hallucination():
    result = AgentResult(
        task_id="t2",
        trace_id="tr2",
        agent_name="standard-rag-agent",
        agent_version="1.0",
        status=AgentStatus.EXECUTING,
        summary="ok",
        structured_result={"retrieved_count": 0}
    )
    validated = validate_agent_result(result)
    assert validated.status == AgentStatus.NEEDS_HITL
    assert len(validated.warnings) > 0
    assert "환각" in validated.warnings[0]

def test_validator_spatial_overflow():
    result = AgentResult(
        task_id="t3",
        trace_id="tr3",
        agent_name="spatial-analysis-agent",
        agent_version="1.0",
        status=AgentStatus.EXECUTING,
        summary="ok",
        structured_result={"count": 50000}
    )
    validated = validate_agent_result(result)
    assert validated.status == AgentStatus.NEEDS_HITL
    assert "너무 많습니다" in validated.warnings[0]
