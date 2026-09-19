"""Registry-driven U-Port planning on GeoLLM's QueryExecutionContext."""

from uuid import uuid4
from pydantic import BaseModel, Field
from services.orchestrator.execution_validator import validate_execution_context
from services.orchestrator.query_candidate_broker import query_candidate_broker
from shared.schemas.agent import ExecutionSlots, QueryExecutionContext


class MapSelection(BaseModel):
    """Typed chart feature identity; this is not a live berth occupancy ID."""
    entity_type: str = Field(pattern=r"^s101_berth$")
    feature_id: int = Field(gt=0)
    dataset_id: int = Field(gt=0)
    dataset_version_id: int = Field(gt=0)


class UportPlanRequest(BaseModel):
    """Plan-only input; it never directly invokes an Agent or Tool."""
    query: str = Field(min_length=1, max_length=2000)
    port_id: str | None = Field(default=None, max_length=120)
    map_selection: MapSelection | None = None


def _ordered_steps(selected: list[str], definitions: dict[str, dict]) -> list[dict]:
    """Expand Registry dependencies and reject cycles or missing definitions."""
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(capability_id: str) -> None:
        if capability_id not in definitions:
            raise ValueError(f"unknown capability dependency: {capability_id}")
        if capability_id in visiting:
            raise ValueError(f"cyclic capability dependency: {capability_id}")
        if capability_id in visited:
            return
        visiting.add(capability_id)
        for dependency in definitions[capability_id].get("depends_on") or []:
            visit(dependency)
        visiting.remove(capability_id)
        visited.add(capability_id)
        ordered.append(capability_id)

    for capability_id in selected:
        visit(capability_id)
    return [{
        "capability_id": capability_id,
        "depends_on": definitions[capability_id].get("depends_on") or [],
        "required_entities": definitions[capability_id].get("required_entities") or [],
        "required_dataset": definitions[capability_id].get("required_dataset") or [],
        "registry_status": definitions[capability_id].get("status"),
        "tool": definitions[capability_id].get("tool"),
    } for capability_id in ordered]


def plan_query(request: UportPlanRequest) -> QueryExecutionContext:
    """Retrieve multiple capabilities and validate a shared execution context."""
    definitions = query_candidate_broker.domain_capability_definitions("uport")
    retrieved = query_candidate_broker.retrieve_domain_capabilities(request.query, "uport")
    selected = [row["candidate_id"] for row in retrieved]
    # A selected chart berth is a deterministic map signal. It joins the
    # natural-language candidates without a query-specific routing branch.
    from services.uport.fast_path import UportFastPathRouter
    fast_path_capability = UportFastPathRouter().capability_for_selection(request.map_selection)
    if fast_path_capability and fast_path_capability not in selected:
        selected.insert(0, fast_path_capability)
    # Visualization consumes the other result steps, so its dependencies are
    # derived from selected Registry entries instead of query word order.
    if "uport.map.visualize" in selected:
        definitions = {key: dict(value) for key, value in definitions.items()}
        definitions["uport.map.visualize"]["depends_on"] = [
            capability_id for capability_id in selected
            if capability_id != "uport.map.visualize"
        ]
    try:
        steps = _ordered_steps(selected, definitions)
        planning_errors: list[str] = []
    except ValueError as exc:
        steps = []
        planning_errors = [f"BLOCKED_CONFIG: {exc}"]
    selection = request.map_selection
    slots = ExecutionSlots()
    resolved_entity = None
    if selection:
        # Import here so the Registry resolver can type its MapSelection input
        # without a module initialization cycle. It validates ontology class
        # metadata but deliberately leaves live DB existence unverified.
        from services.uport.resolver_registry import resolve_map_selection
        try:
            resolved_entity = resolve_map_selection(selection)
        except (OSError, ValueError, KeyError) as exc:
            planning_errors.append(f"BLOCKED_CONFIG: map resolver failed: {exc}")
        slots.feature_instance_ref = {
            "feature_instance_id": selection.feature_id,
            "dataset_id": selection.dataset_id,
            "dataset_version_id": selection.dataset_version_id,
            "feature_type": "Berth",
        }
    qec = QueryExecutionContext(
        request_id=str(uuid4()), original_query=request.query, slots=slots,
        context={"domain": "uport", "port_id": request.port_id,
                 "selected_map_entity": selection.model_dump() if selection else None,
                 "resolved_entity": resolved_entity},
        route_plan={"analysis_type": "uport_query_plan", "domain": "uport",
                    "intents": selected, "steps": steps,
                    "retrieved_capabilities": retrieved, "execution_mode": "plan_only",
                    "fast_path_capability": fast_path_capability},
        blockers=planning_errors,
        provenance={"capability_registry": "data/capability_registry.yaml",
                    "resolver_registry": "data/uport_resolver_registry.yaml"},
    )
    return validate_execution_context(qec)
