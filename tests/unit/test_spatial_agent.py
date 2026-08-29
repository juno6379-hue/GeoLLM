import pytest

from shared.schemas.agent import AgentRequest, Intent, SecurityContext, SpatialContext
from shared.schemas.tool import ToolResult
from services.spatial_analysis_agent import agent as spatial_agent


def _request() -> AgentRequest:
    return AgentRequest(
        task_id="sp-1",
        trace_id="tr1",
        user_id="u1",
        organization_id="org1",
        agent_name="spatial-analysis-agent",
        original_query="Find navigation hazards",
        parsed_intent=Intent(intent_type="SPATIAL", target_objects=["hazard"]),
        spatial_context=SpatialContext(
            base_location="Busan Port",
            geometry="POINT(129.07 35.09)",
            buffer_distance=3000,
        ),
        security_context=SecurityContext(clearance_level="PUBLIC"),
    )


@pytest.mark.asyncio
async def test_spatial_analysis_aggregates_real_tool_result(monkeypatch):
    def fake_execute(**kwargs):
        return ToolResult(
            task_id=kwargs["task_id"],
            trace_id=kwargs["trace_id"],
            tool_name="postgis.dwithin",
            tool_version="2.0",
            status="SUCCESS",
            structured_result={"count": 1, "inline_geojson": {"type": "FeatureCollection", "features": []}},
            execution_time=1,
        )

    monkeypatch.setattr(spatial_agent, "execute_spatial_tool", fake_execute)
    result = await spatial_agent.execute_spatial_analysis(_request())

    assert result.status == "COMPLETED"
    assert result.tool_calls[0].tool_name == "postgis.dwithin"
    assert result.tool_calls[0].status == "SUCCESS"
    assert result.structured_result["count"] == 1


@pytest.mark.asyncio
async def test_spatial_analysis_propagates_tool_failure_without_synthetic_features(monkeypatch):
    def fake_execute(**kwargs):
        return ToolResult(
            task_id=kwargs["task_id"],
            trace_id=kwargs["trace_id"],
            tool_name="postgis.dwithin",
            tool_version="2.0",
            status="FAILED",
            error_code="SQL_EXECUTION_FAILED",
            errors=["database unavailable"],
            execution_time=1,
        )

    monkeypatch.setattr(spatial_agent, "execute_spatial_tool", fake_execute)
    result = await spatial_agent.execute_spatial_analysis(_request())

    assert result.status == "FAILED"
    assert result.structured_result.get("features") in (None, [])
