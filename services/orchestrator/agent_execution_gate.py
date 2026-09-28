"""Common entry boundary for registry dispatch and direct specialist calls."""
import asyncio
import inspect
from functools import wraps

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, PlanStatus
from services.orchestrator.execution_validator import validate_agent_execution, is_execution_authorized


def blocked_agent_result(request, agent_name, qec):
    status = AgentStatus.NEEDS_CLARIFICATION if qec.readiness == PlanStatus.NEEDS_USER_INPUT else AgentStatus.BLOCKED
    return AgentResult(task_id=request.task_id, trace_id=request.trace_id, agent_name=agent_name,
        agent_version="execution-contract-v2", status=status, error_code=qec.readiness.value,
        summary="실행계약 검증을 통과하지 못해 Agent를 실행하지 않았습니다.",
        structured_result={"blockers": qec.blockers, "query_execution_context": qec.model_dump(mode="json")},
        warnings=qec.warnings, clarification_questions=qec.blockers if status == AgentStatus.NEEDS_CLARIFICATION else [],
        provenance={"execution_validation": qec.provenance.get("execution_validation")})


def _attach(result, qec):
    if isinstance(result, AgentResult):
        result.provenance["execution_validation"] = qec.provenance.get("execution_validation")
        result.provenance["query_execution_context"] = qec.model_dump(mode="json")
    return result


def validated_agent(agent_name):
    """Validate before any body/tool call; never infer permission from a returned result."""
    def decorate(function):
        def request_from(args, kwargs):
            return next((arg for arg in (*args, *kwargs.values()) if isinstance(arg, AgentRequest)), None)

        if inspect.iscoroutinefunction(function):
            @wraps(function)
            async def guarded(*args, **kwargs):
                request = request_from(args, kwargs)
                if request is None:
                    raise TypeError("AgentRequest is required")
                parent = request.query_execution_context
                qec = await asyncio.to_thread(validate_agent_execution, request, agent_name)
                if not is_execution_authorized(qec):
                    return blocked_agent_result(request, agent_name, qec)
                request.query_execution_context = qec
                try:
                    return _attach(await function(*args, **kwargs), qec)
                finally:
                    if qec.context.get("contract_scope") == "inspection":
                        request.query_execution_context = parent
        else:
            @wraps(function)
            def guarded(*args, **kwargs):
                request = request_from(args, kwargs)
                if request is None:
                    raise TypeError("AgentRequest is required")
                parent = request.query_execution_context
                qec = validate_agent_execution(request, agent_name)
                if not is_execution_authorized(qec):
                    return blocked_agent_result(request, agent_name, qec)
                request.query_execution_context = qec
                try:
                    return _attach(function(*args, **kwargs), qec)
                finally:
                    if qec.context.get("contract_scope") == "inspection":
                        request.query_execution_context = parent
        guarded.__execution_contract_agent__ = agent_name
        return guarded
    return decorate
