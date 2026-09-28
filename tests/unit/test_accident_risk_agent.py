import pytest

from shared.schemas.agent import AgentRequest, ExecutionSlots, PlanStatus, QueryExecutionContext, SecurityContext
from services.accident_risk_agent import agent as accident_agent


def _request() -> AgentRequest:
    qec = QueryExecutionContext(
        task_id="acc-1",
        request_id="acc-1",
        original_query="feature 702036 근처 사고",
        normalized_query="feature 702036 근처 사고",
        readiness=PlanStatus.EXECUTION_READY,
        route_plan={"analysis_type": "accident_relation_lookup", "primary_agent": "Accident/Risk Agent"},
        slots=ExecutionSlots(feature_instance_id=702036, distance_m=5000),
        data_bindings=[
            {
                "dataset_id": "accident_s101_relation",
                "relation": "serving.accident_s101_relation_current",
                "geometry_column": "accident_geometry",
                "distance_column": "distance_meters",
                "srid": 4326,
                "layer_type": "accident_relation",
            }
        ],
        tool_bindings=[
            {
                "tool_id": "accident.s101_relation_lookup",
                "operation": "accident_relation_lookup",
                "query_template_id": "accident_s101_relation_lookup",
            }
        ],
    )
    return AgentRequest(
        task_id="acc-1",
        trace_id="trace-1",
        user_id="u1",
        organization_id="org1",
        agent_name="Accident/Risk Agent",
        original_query="feature 702036 근처 사고",
        security_context=SecurityContext(clearance_level="PUBLIC"),
        query_execution_context=qec,
    )


@pytest.mark.asyncio
async def test_accident_agent_returns_relation_evidence(monkeypatch):
    from services.orchestrator import execution_validator

    from services.orchestrator.schema_binding_adapter import BindingResult
    fixture = _request().query_execution_context
    monkeypatch.setattr(execution_validator.schema_binding_adapter, "build_bindings", lambda *_: BindingResult(
        data_bindings=fixture.data_bindings, tool_bindings=fixture.tool_bindings))

    def fake_query(qec):
        return [
            {
                "event_id": "acc-001",
                "accident_type": "충돌",
                "cause": "운항부주의",
                "feature_instance_id": 702036,
                "feature_type_name": "QualityOfBathymetricData",
                "distance_meters": 3827.399,
                "relation_type": "NEAREST_OVER_1000M",
                "relation_rank": 1,
                "accident_geojson": {"type": "Point", "coordinates": [129.1, 35.0]},
            }
        ], "select * from serving.accident_s101_relation_current"

    monkeypatch.setattr(accident_agent, "_query_accident_relations", fake_query)
    monkeypatch.setattr(accident_agent, "build_specialist_kg_context", lambda *_args, **_kwargs: {})

    result = await accident_agent.execute_accident_risk(_request())

    assert result.status == "COMPLETED"
    assert result.structured_result["count"] == 1
    assert len(result.evidence_bundle.accident_relation_evidence) == 1
    assert result.structured_result["accident_spatial_geojson"]["features"][0]["properties"]["role"] == "accident_relation"


@pytest.mark.asyncio
async def test_accident_agent_blocks_without_contract():
    req = _request()
    req.query_execution_context = None

    result = await accident_agent.execute_accident_risk(req)

    assert result.status == "BLOCKED"
    assert result.error_code == "BLOCKED_CONFIG"
