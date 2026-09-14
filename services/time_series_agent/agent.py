from __future__ import annotations

from typing import Any

from shared.observability.logger import get_logger
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, PlanStatus, ToolCallLog
from services.time_series_agent.tools import analyze_time_series


logger = get_logger("time_series_agent")


def _contract_blocked_result(request: AgentRequest, blockers: list[str]) -> AgentResult:
    status = AgentStatus.NEEDS_CLARIFICATION if any(item.startswith("NEEDS_USER_INPUT") for item in blockers) else AgentStatus.BLOCKED
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Time-Series Agent",
        agent_version="1.0.0-contract",
        status=status,
        error_code=PlanStatus.NEEDS_USER_INPUT.value if status == AgentStatus.NEEDS_CLARIFICATION else PlanStatus.BLOCKED_DATA.value,
        summary="Time-series analysis is blocked by the execution contract.",
        answer_text="Time-series analysis requires a registered or supplied source path, timestamp column, and value column.",
        structured_result={"blockers": blockers},
        warnings=blockers,
        provenance={"validator": "services.orchestrator.execution_validator.validate_execution_context"},
    )


def _slot_value(request: AgentRequest, key: str, default: Any = None) -> Any:
    qec = request.query_execution_context
    if qec:
        payload = qec.slots.model_dump()
        if payload.get(key) not in (None, "", [], {}):
            return payload.get(key)
        if qec.slots.filters.get(key) not in (None, "", [], {}):
            return qec.slots.filters.get(key)
    if request.task_plan and request.task_plan.slots:
        value = request.task_plan.slots.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


async def execute_time_series_analysis(request: AgentRequest) -> AgentResult:
    logger.info("Time-Series Agent started", task_id=request.task_id)
    qec = request.query_execution_context
    if not qec:
        return _contract_blocked_result(request, ["BLOCKED_CONFIG: query_execution_context is required"])
    if qec.readiness != PlanStatus.EXECUTION_READY:
        return _contract_blocked_result(request, qec.blockers or ["BLOCKED_DATA: time-series execution context is not ready"])

    time_range = qec.slots.time_range or {}
    result = analyze_time_series(
        dataset_id=_slot_value(request, "dataset_id") or (qec.data_bindings[0].dataset_id if qec.data_bindings else None),
        source_path=_slot_value(request, "source_path"),
        timestamp_column=_slot_value(request, "timestamp_column"),
        value_column=_slot_value(request, "value_column"),
        station_column=_slot_value(request, "station_column"),
        station_id=_slot_value(request, "station_id"),
        start_time=_slot_value(request, "start_time") or time_range.get("start") or time_range.get("start_time"),
        end_time=_slot_value(request, "end_time") or time_range.get("end") or time_range.get("end_time"),
        z_threshold=float(_slot_value(request, "z_threshold", 3.0)),
    )

    if result.get("status") in {"BLOCKED_DATA", "NO_DATA"}:
        blockers = result.get("blockers") or [f"{result.get('status')}: no executable time-series rows"]
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="Time-Series Agent",
            agent_version="1.0.0-contract",
            status=AgentStatus.BLOCKED,
            error_code=PlanStatus.BLOCKED_DATA.value,
            summary="No executable time-series values were available.",
            answer_text="The requested time-series source is missing or contains no rows for the requested filters.",
            structured_result=result,
            warnings=blockers,
            provenance={"tool": "services.time_series_agent.tools.analyze_time_series"},
            tool_calls=[ToolCallLog(tool_name="timeseries.observation_analyze", status="BLOCKED_DATA", execution_time_ms=0.0)],
        )

    metrics = result.get("metrics") or {}
    anomaly_count = metrics.get("anomaly_count", 0)
    summary = (
        f"Analyzed {metrics.get('filtered_count', 0)} time-series rows "
        f"with missing_rate={metrics.get('missing_rate', 0)} and anomalies={anomaly_count}."
    )
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Time-Series Agent",
        agent_version="1.0.0-contract",
        status=AgentStatus.COMPLETED,
        summary=summary,
        answer_text=summary,
        structured_result=result,
        metrics=metrics,
        evidence=[result.get("source_path")],
        provenance={
            "tool": "services.time_series_agent.tools.analyze_time_series",
            "source_path": result.get("source_path"),
            "query_execution_context": qec.model_dump(mode="json"),
        },
        validation_payload={
            "type": "time_series_metrics",
            "status": result.get("status"),
            "missing_rate": metrics.get("missing_rate"),
            "anomaly_count": anomaly_count,
        },
        tool_calls=[ToolCallLog(tool_name="timeseries.observation_analyze", status="SUCCESS", execution_time_ms=0.0)],
    )
