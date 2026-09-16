"""The dispatch boundary must preserve the execution gate's final decision."""

from unittest.mock import Mock

import pytest

from services.orchestrator import execution_validator, graph
from services.orchestrator.schema_binding_adapter import BindingResult
from shared.schemas.agent import (
    AgentRequest,
    AgentStatus,
    DataBinding,
    ExecutionSlots,
    PlanStatus,
    QueryExecutionContext,
    SecurityContext,
    ToolBinding,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("blockers", "expected_readiness", "expected_status"),
    [
        (["BLOCKED_POLICY: access denied"], PlanStatus.BLOCKED_POLICY, AgentStatus.BLOCKED),
        (["BLOCKED_DATA: dataset unavailable"], PlanStatus.BLOCKED_DATA, AgentStatus.BLOCKED),
        (["BLOCKED_CONFIG: missing tool"], PlanStatus.BLOCKED_CONFIG, AgentStatus.BLOCKED),
        ([], PlanStatus.NEEDS_USER_INPUT, AgentStatus.NEEDS_CLARIFICATION),
    ],
)
async def test_dispatch_preserves_gate_status_with_unresolved_geometry(
    monkeypatch, blockers, expected_readiness, expected_status
):
    binding_result = BindingResult(
        data_bindings=[DataBinding(dataset_id="fixture", relation="fixture.features", srid=4326)],
        tool_bindings=[ToolBinding(tool_id="fixture.tool", operation="ST_DWithin")],
    )
    monkeypatch.setattr(
        execution_validator.schema_binding_adapter,
        "build_bindings",
        lambda *_: binding_result,
    )
    dispatch = Mock(side_effect=AssertionError("Blocked plans must not dispatch an agent"))
    monkeypatch.setattr(graph.registry, "get_execute_function", dispatch)
    request = AgentRequest(
        task_id="fixture-gate-dispatch",
        trace_id="fixture-trace",
        user_id="fixture-user",
        organization_id="fixture-org",
        agent_name="Spatial Analysis Agent",
        original_query="Find Wreck features within 3000 meters",
        security_context=SecurityContext(clearance_level="PUBLIC"),
        query_execution_context=QueryExecutionContext(
            route_plan={"analysis_type": "feature_search_by_radius"},
            slots=ExecutionSlots(distance_m=3000, target_features=["Wreck"]),
            blockers=blockers,
        ),
    )

    result = await graph.execute_agent_node({"task_id": request.task_id, "agent_request": request})

    dispatch.assert_not_called()
    assert result["status"] == expected_status
    assert result["agent_result"].status == expected_status
    assert result["agent_result"].error_code == expected_readiness.value
    context = QueryExecutionContext.model_validate(result["query_execution_context"])
    assert context.readiness == expected_readiness
    assert any(item.startswith("NEEDS_USER_INPUT") for item in context.blockers)
