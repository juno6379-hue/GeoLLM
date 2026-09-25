import pytest
from datetime import datetime
from shared.schemas.agent import (
    AgentRequest,
    AgentResult,
    AgentStatus,
    EvidenceBundle,
    ExecutionSlots,
    PlanStatus,
    QueryExecutionContext,
    SecurityContext,
)
from shared.security.context import check_clearance, ClearanceLevel
from services.spatial_analysis_agent.tool_registry import QueryTemplateRegistry

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

def test_execution_slots_normalize_legacy_payload():
    slots = ExecutionSlots.from_payload({
        "location": "부산항 입구",
        "distance_m": "3000",
        "target_feature_candidates": ["Wreck", "Obstruction"],
        "derived_concepts": ["hazard_object"],
    })

    assert slots.location_text == "부산항 입구"
    assert slots.distance_m == 3000
    assert slots.target_features == ["Wreck", "Obstruction"]
    assert slots.derived_concept == "hazard_object"

def test_query_execution_context_patch_does_not_clear_explicit_slots():
    ctx = QueryExecutionContext(
        request_id="r1",
        task_id="t1",
        original_query="부산항 입구 3km 이내 위험객체",
        slots=ExecutionSlots(location_text="부산항 입구", distance_m=3000, target_features=["Wreck"]),
        readiness=PlanStatus.PLAN_READY,
    )

    patched = ctx.merge_slot_patch(
        {"location_text": None, "distance_m": "", "target_features": [], "exclusions": ["Buoy"]},
        producer="unit-test",
        reason_code="USER_PATCH",
    )

    assert patched.slots.location_text == "부산항 입구"
    assert patched.slots.distance_m == 3000
    assert patched.slots.target_features == ["Wreck"]
    assert patched.slots.exclusions == ["Buoy"]
    assert patched.revision == 2
    assert patched.provenance["patches"][0]["field_path"] == "slots.exclusions"

def test_agent_result_has_answer_and_evidence_contract():
    result = AgentResult(
        task_id="t1",
        trace_id="tr1",
        agent_name="spatial-analysis-agent",
        agent_version="test",
        status=AgentStatus.COMPLETED,
        summary="요약",
        answer_text="사용자에게 보여줄 자연어 답변",
        evidence_bundle=EvidenceBundle(),
    )

    dumped = result.model_dump()
    assert dumped["answer_text"] == "사용자에게 보여줄 자연어 답변"
    assert dumped["evidence_bundle"]["spatial_feature_evidence"] == []

def test_clearance_level():
    assert check_clearance(ClearanceLevel.SECRET, ClearanceLevel.CONFIDENTIAL) is True
    assert check_clearance(ClearanceLevel.PUBLIC, ClearanceLevel.SECRET) is False

def test_registered_spatial_query_template():
    registry = QueryTemplateRegistry()
    assert registry.get_template_sql("feature_search_by_radius")
    with pytest.raises(ValueError):
        registry.get_template_sql("not.exist")
