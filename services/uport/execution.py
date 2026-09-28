"""Validated U-Port execution over registered specialist Agent adapters."""

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.uport.planning import UportPlanRequest, plan_query
from services.uport.agent_registry import get_executable_agent
from services.uport.s101_agent import S101AgentError
from shared.schemas.agent import DataBinding, EvidenceItem, PlanStatus, QueryExecutionContext, ToolBinding
from shared.schemas.map_layer import MapLayerSpecification, MapLayerStyle
from services.orchestrator.execution_validator import validate_uport_execution_context, is_execution_authorized


class UportExecutionResult(BaseModel):
    """Separate factual Tool output from the short deterministic narrative."""
    status: str
    error_code: str | None = None
    narrative: str | None = None
    query_execution_context: QueryExecutionContext
    features: list[dict] = Field(default_factory=list)
    map_layers: list[MapLayerSpecification] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def execute_query(request: UportPlanRequest, db: Session | None) -> UportExecutionResult:
    """Execute only verified read-only S-101 steps in dependency order.

    The Registry plan may contain AIS, prediction or optimization candidates,
    but those cannot run until their datasets and Agent adapters are available.
    No generated narrative is allowed to substitute a missing Tool result.
    """
    qec = plan_query(request)
    if qec.readiness != PlanStatus.PLAN_READY:
        code = "DATASET_NOT_AVAILABLE" if qec.readiness == PlanStatus.BLOCKED_DATA else "VALIDATION_FAILED"
        return UportExecutionResult(status="blocked", error_code=code,
                                    query_execution_context=qec, warnings=qec.blockers)
    if request.map_selection is None:
        qec.blockers.append("NEEDS_USER_INPUT: select a charted berth on the map")
        qec.readiness = PlanStatus.NEEDS_USER_INPUT
        return UportExecutionResult(status="needs_clarification", error_code="VALIDATION_FAILED",
                                    query_execution_context=qec, warnings=qec.blockers)
    agent = get_executable_agent("uport.s101.berth.search")
    if agent is None or any(
        step["capability_id"] not in {"uport.s101.berth.search", "uport.map.visualize"}
        for step in qec.route_plan["steps"]
    ):
        qec.blockers.append("BLOCKED_CONFIG: specialist Agent is not registered")
        qec.readiness = PlanStatus.BLOCKED_CONFIG
        return UportExecutionResult(status="blocked", error_code="MODEL_NOT_AVAILABLE",
                                    query_execution_context=qec, warnings=qec.blockers)
    if db is None:
        qec.blockers.append("BLOCKED_DATA: S-101 database is not configured")
        qec.readiness = PlanStatus.BLOCKED_DATA
        return UportExecutionResult(status="blocked", error_code="DATASET_NOT_AVAILABLE",
                                    query_execution_context=qec, warnings=qec.blockers)

    try:
        # This is the execution gate: the candidate map ID becomes authoritative
        # only after a read from the current dataset and version succeeds.
        qec = validate_uport_execution_context(qec, agent, db, request.map_selection)
        if not is_execution_authorized(qec):
            return UportExecutionResult(status="blocked", error_code="VALIDATION_FAILED", query_execution_context=qec, warnings=qec.blockers)
        feature, evidence = agent.execute(qec, db)
    except S101AgentError as exc:
        qec.blockers.append(f"{exc.code}: {exc}")
        qec.readiness = PlanStatus.BLOCKED_DATA if exc.code == "DATASET_NOT_AVAILABLE" else PlanStatus.BLOCKED_CONFIG
        return UportExecutionResult(status="failed", error_code=exc.code,
                                    query_execution_context=qec, warnings=qec.blockers)

    # GeoLLM's existing map layer schema carries the exact Tool geometry and
    # version. Narrative states only the verified identity and known limits.
    layer = MapLayerSpecification(
        layer_id=f"uport-berth-{feature['id']}", task_id=qec.request_id,
        title="S-101 선석 피처", description="검증된 전자해도 선석 객체",
        geometry_type=feature["geometry"]["type"].upper(), source_type="GEOJSON",
        inline_geojson={"type": "FeatureCollection", "features": [feature]},
        source_crs="EPSG:4326", display_crs="EPSG:3857",
        style=MapLayerStyle(stroke_color="#075fac", fill_color="#48c5f2"),
        popup_fields=["feature_type", "dataset_id", "dataset_version_id"],
        dataset_version=str(request.map_selection.dataset_version_id),
        provenance="projection.s101_feature_valid",
    )
    qec.provenance["s101_feature_evidence_id"] = evidence.evidence_id
    return UportExecutionResult(
        status="success", query_execution_context=qec, features=[feature],
        map_layers=[layer], evidence=[evidence],
        narrative=f"S-101 선석 피처 {feature['id']}를 확인했습니다. 점유·배정 상태는 제공되지 않습니다.",
    )
