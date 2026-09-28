from __future__ import annotations

from typing import Any

from shared.observability.logger import get_logger
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, PlanStatus, ToolCallLog
from services.time_series_agent.tools import forecast_time_series


logger = get_logger("time_series_forecast_agent")


def _slot_value(request: AgentRequest, key: str, default: Any = None) -> Any:
    qec = request.query_execution_context
    if qec:
        payload = qec.slots.model_dump()
        if payload.get(key) not in (None, "", [], {}):
            return payload.get(key)
        if qec.slots.filters.get(key) not in (None, "", [], {}):
            return qec.slots.filters.get(key)
    return default


def _blocked(request: AgentRequest, blockers: list[str]) -> AgentResult:
    status = AgentStatus.NEEDS_CLARIFICATION if any(item.startswith("NEEDS_USER_INPUT") for item in blockers) else AgentStatus.BLOCKED
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Time-Series Forecast Agent",
        agent_version="1.0.0-contract",
        status=status,
        error_code=PlanStatus.NEEDS_USER_INPUT.value if status == AgentStatus.NEEDS_CLARIFICATION else PlanStatus.BLOCKED_DATA.value,
        summary="Time-series forecast is blocked by the execution contract.",
        answer_text="Forecasting requires executable time-series observations and a forecast horizon.",
        structured_result={"blockers": blockers},
        warnings=blockers,
        provenance={"validator": "services.orchestrator.execution_validator.validate_execution_context"},
    )


from services.orchestrator.agent_execution_gate import validated_agent


@validated_agent('Time-Series Forecast Agent')
async def execute_time_series_forecast(request: AgentRequest) -> AgentResult:
    logger.info("Time-Series Forecast Agent started", task_id=request.task_id)
    qec = request.query_execution_context
    if not qec:
        return _blocked(request, ["BLOCKED_CONFIG: query_execution_context is required"])
    from services.orchestrator.execution_validator import is_execution_authorized
    if not is_execution_authorized(qec):
        return _blocked(request, qec.blockers or ["BLOCKED_DATA: time-series forecast context is not ready"])

    time_range = qec.slots.time_range or {}
    result = forecast_time_series(
        dataset_id=_slot_value(request, "dataset_id") or (qec.data_bindings[0].dataset_id if qec.data_bindings else None),
        source_path=_slot_value(request, "source_path"),
        timestamp_column=_slot_value(request, "timestamp_column"),
        value_column=_slot_value(request, "value_column"),
        station_column=_slot_value(request, "station_column"),
        station_id=_slot_value(request, "station_id"),
        start_time=_slot_value(request, "start_time") or time_range.get("start") or time_range.get("start_time"),
        end_time=_slot_value(request, "end_time") or time_range.get("end") or time_range.get("end_time"),
        horizon_steps=int(_slot_value(request, "horizon_steps", 3)),
        confidence_level=float(_slot_value(request, "confidence_level", 0.95)),
        model_endpoint=_slot_value(request, "model_endpoint"),
    )
    if result.get("status") != "PASS":
        blockers = result.get("blockers") or [f"{result.get('status')}: forecast failed"]
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="Time-Series Forecast Agent",
            agent_version="1.0.0-contract",
            status=AgentStatus.BLOCKED,
            error_code=PlanStatus.BLOCKED_DATA.value,
            summary="No forecast could be generated from the requested time-series source.",
            answer_text="Forecasting was blocked because the source data or configured forecast model was unavailable.",
            structured_result=result,
            warnings=blockers,
            provenance={"tool": "services.time_series_agent.tools.forecast_time_series"},
            tool_calls=[ToolCallLog(tool_name="timeseries.forecast", status="BLOCKED", execution_time_ms=0.0)],
        )

    forecast = result.get("forecast") or []
    summary = (
        f"Generated {len(forecast)} forecast steps with "
        f"{result.get('confidence_level')} confidence intervals using {result.get('method')}."
    )
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Time-Series Forecast Agent",
        agent_version="1.0.0-contract",
        status=AgentStatus.COMPLETED,
        summary=summary,
        answer_text=summary,
        structured_result=result,
        metrics={
            "forecast_steps": len(forecast),
            "confidence_level": result.get("confidence_level"),
            "point_count": result.get("point_count"),
            "residual_std": (result.get("model") or {}).get("residual_std"),
        },
        evidence=[result.get("source_path")],
        provenance={
            "tool": "services.time_series_agent.tools.forecast_time_series",
            "source_path": result.get("source_path"),
            "method": result.get("method"),
            "query_execution_context": qec.model_dump(mode="json"),
        },
        validation_payload={
            "type": "time_series_forecast",
            "status": result.get("status"),
            "forecast_steps": len(forecast),
            "confidence_level": result.get("confidence_level"),
        },
        tool_calls=[ToolCallLog(tool_name="timeseries.forecast", status="SUCCESS", execution_time_ms=0.0)],
    )
