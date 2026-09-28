from services.orchestrator.execution_validator import (
    is_execution_authorized, project_execution_decision, validate_place_resolution,
)
from shared.schemas.agent import QueryExecutionContext, PlanStatus


def test_readiness_flag_alone_cannot_authorize_execution():
    qec = QueryExecutionContext(original_query="이동", readiness=PlanStatus.EXECUTION_READY)
    assert not is_execution_authorized(qec)
    assert project_execution_decision(qec, {})["execution_ready"] is False


def test_validator_receipt_is_invalidated_by_slot_changes():
    qec = validate_place_resolution("부산항 이동", {
        "status": "RESOLVED", "geometry": "POINT(129 35)", "crs": "EPSG:4326",
        "location_text": "부산항", "location_resolution": {"source_ref": "test:place"},
    })
    assert is_execution_authorized(qec)
    qec.slots.reference_geometry = "POINT(130 36)"
    assert not is_execution_authorized(qec)


def test_unconfirmed_place_remains_clarification_not_source_failure():
    qec = validate_place_resolution("해운대구 분석", {"status": "NEEDS_CLARIFICATION"})
    assert qec.readiness == PlanStatus.NEEDS_USER_INPUT
    assert not is_execution_authorized(qec)
