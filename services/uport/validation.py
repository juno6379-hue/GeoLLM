"""U-Port checks behind GeoLLM's common ExecutionValidator entrypoint."""

from shared.schemas.agent import PlanStatus, QueryExecutionContext


def validate_uport_plan(qec: QueryExecutionContext) -> QueryExecutionContext:
    """Validate selected capability metadata, entities and dataset readiness.

    Phase 5 can return PLAN_READY but never EXECUTION_READY. Actual Tool and
    dataset binding must be checked again before Agent execution in Phase 6.
    """
    current = qec.model_copy(deep=True)
    blockers = list(current.blockers)
    steps = current.route_plan.get("steps") or []
    if not steps:
        blockers.append("NEEDS_USER_INPUT: no U-Port capability matched the query")
    known_datasets = {"s101_current"}
    for step in steps:
        if step.get("registry_status") != "available":
            blockers.append(f"BLOCKED_DATA: {step['capability_id']} is unavailable")
        for dataset in step.get("required_dataset") or []:
            if dataset not in known_datasets:
                blockers.append(f"BLOCKED_DATA: {dataset} is not registered")
        for entity in step.get("required_entities") or []:
            if entity == "port" and not current.context.get("port_id"):
                blockers.append("NEEDS_USER_INPUT: port_id is required")
            elif entity == "vessel":
                blockers.append("NEEDS_USER_INPUT: verified vessel identity is required")
    current.blockers = list(dict.fromkeys(blockers))
    if any(item.startswith("BLOCKED_CONFIG") for item in blockers):
        current.readiness = PlanStatus.BLOCKED_CONFIG
    elif any(item.startswith("BLOCKED_DATA") for item in blockers):
        current.readiness = PlanStatus.BLOCKED_DATA
    elif blockers:
        current.readiness = PlanStatus.NEEDS_USER_INPUT
    else:
        current.readiness = PlanStatus.PLAN_READY
    return current
