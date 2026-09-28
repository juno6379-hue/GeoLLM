import pytest

from shared.schemas.agent import AgentRequest, ExecutionSlots, Intent, PlanStatus, QueryExecutionContext, SecurityContext, SpatialContext
from shared.schemas.tool import ToolResult
from services.spatial_analysis_agent import agent as spatial_agent


def _request() -> AgentRequest:
    qec = QueryExecutionContext(
        task_id="sp-1",
        request_id="sp-1",
        original_query="Find navigation hazards",
        normalized_query="Find navigation hazards",
        readiness=PlanStatus.EXECUTION_READY,
        route_plan={"analysis_type": "feature_search_by_radius", "intent": "spatial_feature_proximity_search"},
        slots=ExecutionSlots(
            location_text="Busan Port",
            reference_geometry="POINT(129.07 35.09)",
            distance_m=3000,
            target_features=["Wreck"],
            resolved_target_set=["Wreck"],
        ),
        spatial={"spatial_context": {"base_location": "Busan Port", "geometry": "POINT(129.07 35.09)"}},
        data_bindings=[{"dataset_id": "GBENC_S101_feature", "relation": "projection.s101_feature_current", "geometry_column": "geometry", "srid": 4326}],
        tool_bindings=[{"tool_id": "postgis.dwithin", "operation": "ST_DWithin", "query_template_id": "feature_search_by_radius"}],
    )
    from types import SimpleNamespace
    from services.orchestrator.execution_validator import validate_execution_context
    adapter = SimpleNamespace(build_bindings=lambda *_: SimpleNamespace(
        data_bindings=qec.data_bindings, tool_bindings=qec.tool_bindings,
        blockers=[], warnings=[], inspected_relations={}))
    qec = validate_execution_context(qec, binding_adapter=adapter)
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
        query_execution_context=qec,
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


@pytest.mark.asyncio
async def test_spatial_analysis_requires_execution_contract():
    req = _request()
    req.query_execution_context = None

    result = await spatial_agent.execute_spatial_analysis(req)

    assert result.status == "BLOCKED"
    assert result.error_code == "BLOCKED_CONFIG"


@pytest.mark.asyncio
async def test_spatial_analysis_blocks_unready_contract():
    req = _request()
    req.query_execution_context.readiness = PlanStatus.NEEDS_USER_INPUT
    req.query_execution_context.blockers = ["NEEDS_USER_INPUT: reference geometry is unresolved"]

    result = await spatial_agent.execute_spatial_analysis(req)

    assert result.status == "NEEDS_CLARIFICATION"
    assert result.error_code == "NEEDS_USER_INPUT"
