"""검증된 실행계약에 따라 사고-S101 relation을 조회한다."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

from shared.observability.logger import get_logger
from shared.schemas.agent import (
    AgentRequest,
    AgentResult,
    AgentStatus,
    EvidenceBundle,
    PlanStatus,
    QueryExecutionContext,
    ToolCallLog,
)
from services.orchestrator.evidence_builder import build_evidence_bundle
from services.orchestrator.execution_validator import validate_execution_context
from services.orchestrator.specialist_kg_context import build_specialist_kg_context

logger = get_logger("accident_risk_agent")


def _readiness_value(qec: QueryExecutionContext | None) -> str:
    if not qec:
        return ""
    return qec.readiness.value if hasattr(qec.readiness, "value") else str(qec.readiness)


def _contract_blocked_result(request: AgentRequest, qec: QueryExecutionContext | None, blockers: list[str]) -> AgentResult:
    status = AgentStatus.NEEDS_CLARIFICATION if any(str(b).startswith("NEEDS_USER_INPUT") for b in blockers) else AgentStatus.BLOCKED
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Accident/Risk Agent",
        agent_version="3.0.0-contract",
        status=status,
        error_code="EXECUTION_CONTRACT_NOT_READY",
        summary="사고 관계 조회 실행계약이 준비되지 않아 실행하지 않았습니다.",
        answer_text="사고 관계를 조회하려면 검증된 객체 식별자와 사고-객체 relation binding이 필요합니다.",
        structured_result={
            "blockers": blockers,
            "query_execution_context": qec.model_dump(mode="json") if qec else None,
        },
        warnings=blockers,
        provenance={"validator": "services.orchestrator.execution_validator.validate_execution_context"},
        created_at=datetime.utcnow(),
    )


def _feature_instance_id(qec: QueryExecutionContext) -> Any:
    slots = qec.slots
    if slots.feature_instance_id not in (None, ""):
        return slots.feature_instance_id
    if slots.feature_instance_ref:
        return (
            slots.feature_instance_ref.get("feature_instance_id")
            or slots.feature_instance_ref.get("id")
            or slots.feature_instance_ref.get("foid")
        )
    return slots.filters.get("feature_instance_id")


def _distance_limit(qec: QueryExecutionContext) -> float | None:
    raw = qec.slots.distance_m or qec.slots.filters.get("distance_m") or qec.slots.filters.get("max_distance_m")
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _limit(qec: QueryExecutionContext) -> int:
    raw = qec.slots.filters.get("limit") or qec.slots.filters.get("k") or 100
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 100
    return max(1, min(value, 500))


def _relation_binding(qec: QueryExecutionContext) -> tuple[str, str]:
    binding = next((item for item in qec.data_bindings if item.dataset_id == "accident_s101_relation"), None)
    if not binding:
        binding = qec.data_bindings[0] if qec.data_bindings else None
    relation = binding.relation if binding else "serving.accident_s101_relation_current"
    distance_column = binding.distance_column if binding and binding.distance_column else "distance_meters"
    if relation != "serving.accident_s101_relation_current":
        raise ValueError(f"Unsupported accident relation table: {relation}")
    return relation, distance_column


def _query_accident_relations(qec: QueryExecutionContext) -> tuple[list[dict[str, Any]], str]:
    feature_id = _feature_instance_id(qec)
    relation, distance_column = _relation_binding(qec)
    distance_limit = _distance_limit(qec)
    limit = _limit(qec)
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL or POSTGIS_URL is not configured")

    where = ["feature_instance_id = %s"]
    params: list[Any] = [feature_id]
    if distance_limit is not None:
        where.append(f"{distance_column} <= %s")
        params.append(distance_limit)
    params.append(limit)

    sql = f"""
        select
            event_id,
            occurred_at,
            authority,
            sea_area,
            accident_type,
            cause,
            vessel_type,
            tonnage,
            feature_instance_id,
            dataset_id,
            dataset_name,
            feature_type_code,
            feature_type_name,
            product_specification,
            anchor_rank,
            {distance_column} as distance_meters,
            relation_type,
            relation_rank,
            st_asgeojson(accident_geometry)::json as accident_geojson,
            st_asgeojson(anchor_geometry)::json as anchor_geojson
        from {relation}
        where {' and '.join(where)}
        order by {distance_column} asc nulls last, relation_rank asc nulls last
        limit %s
    """

    import psycopg2
    import psycopg2.extras

    with psycopg2.connect(url, connect_timeout=5) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
    return rows, sql


def _relations_to_geojson(relations: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for relation in relations:
        geometry = relation.get("accident_geojson")
        if isinstance(geometry, str):
            try:
                geometry = json.loads(geometry)
            except ValueError:
                geometry = None
        if not geometry:
            continue
        properties = {k: v for k, v in relation.items() if k not in {"accident_geojson", "anchor_geojson"}}
        properties["role"] = "accident_relation"
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return {"type": "FeatureCollection", "features": features}


def _relations_to_evidence(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = []
    for row in relations:
        distance = row.get("distance_meters")
        summary = f"{row.get('accident_type') or '사고'}: feature_instance_id={row.get('feature_instance_id')}, distance_m={distance}"
        evidence.append({
            "evidence_type": "accident_relation",
            "summary": summary,
            "source_ref": "serving.accident_s101_relation_current",
            "relation_table": "serving.accident_s101_relation_current",
            "event_id": row.get("event_id"),
            "feature_instance_id": row.get("feature_instance_id"),
            "feature_type_name": row.get("feature_type_name"),
            "accident_type": row.get("accident_type"),
            "cause": row.get("cause"),
            "occurred_at": str(row.get("occurred_at")) if row.get("occurred_at") else None,
            "distance_meters": float(distance) if distance is not None else None,
            "relation_type": row.get("relation_type"),
            "relation_rank": row.get("relation_rank"),
            "data": row,
        })
    return evidence


from services.orchestrator.agent_execution_gate import validated_agent


@validated_agent('Accident/Risk Agent')
async def execute_accident_risk(request: AgentRequest) -> AgentResult:
    qec = request.query_execution_context
    if not qec:
        return _contract_blocked_result(request, None, ["BLOCKED_CONFIG: query_execution_context is required"])

    # The entry decorator has revalidated the current request and bindings.
    if _readiness_value(qec) != PlanStatus.EXECUTION_READY.value:
        return _contract_blocked_result(request, qec, qec.blockers or ["Execution contract is not ready"])

    start = time.time()
    try:
        kg_context = build_specialist_kg_context("accident", request)
    except Exception as exc:
        logger.warning("전문 KG context를 사용할 수 없어 실행계약 정보로 계속 진행합니다.", error=str(exc))
        kg_context = qec.kg if isinstance(qec.kg, dict) else {}

    try:
        rows, sql = _query_accident_relations(qec)
    except Exception as exc:
        logger.error("사고 relation 조회에 실패했습니다.", error=str(exc), exc_info=True)
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="Accident/Risk Agent",
            agent_version="3.0.0-contract",
            status=AgentStatus.FAILED,
            error_code="ACCIDENT_RELATION_QUERY_FAILED",
            summary="사고 관계 조회 SQL 실행에 실패했습니다.",
            answer_text="사고 관계 테이블을 조회하지 못했습니다. DB 연결과 relation schema를 확인해야 합니다.",
            structured_result={
                "query_execution_context": qec.model_dump(mode="json"),
                "error": str(exc),
            },
            warnings=[str(exc)],
            created_at=datetime.utcnow(),
        )

    evidence = _relations_to_evidence(rows)
    structured = {
        "count": len(rows),
        "feature_instance_id": _feature_instance_id(qec),
        "distance_m": _distance_limit(qec),
        "relations": rows,
        "accident_relation_evidence": evidence,
        "accident_spatial_geojson": _relations_to_geojson(rows),
        "query_execution_context": qec.model_dump(mode="json"),
        "spatial_provenance": {
            "query_template": "accident_s101_relation_lookup",
            "executed_query": sql,
            "relation": "serving.accident_s101_relation_current",
        },
        "kg_context": kg_context,
    }
    evidence_bundle: EvidenceBundle = build_evidence_bundle(
        graph_context=kg_context,
        structured_result=structured,
        task_id=request.task_id,
    )
    answer = (
        f"해당 전자해도 객체와 연결된 사고 관계 {len(rows)}건을 확인했습니다. "
        "이 관계는 거리 기반 근접 근거이며 사고 원인을 단정하지는 않습니다."
        if rows
        else "해당 전자해도 객체와 연결된 사고 관계를 찾지 못했습니다."
    )
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Accident/Risk Agent",
        agent_version="3.0.0-contract",
        status=AgentStatus.COMPLETED,
        summary=answer,
        answer_text=answer,
        structured_result=structured,
        evidence_bundle=evidence_bundle,
        provenance={
            "spatial": structured["spatial_provenance"],
            "kg": kg_context,
        },
        tool_calls=[
            ToolCallLog(
                tool_name="accident.s101_relation_lookup",
                status="SUCCESS",
                execution_time_ms=(time.time() - start) * 1000,
            )
        ],
        validation_payload={"query_execution_context_readiness": qec.readiness.value, "row_count": len(rows)},
        created_at=datetime.utcnow(),
    )
