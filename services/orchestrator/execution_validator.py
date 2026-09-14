import os
from typing import Any, Dict, List

from shared.schemas.agent import PlanStatus, QueryExecutionContext
from services.orchestrator.schema_binding_adapter import schema_binding_adapter


MAX_RADIUS_M = 50000.0
MAX_NEAREST_K = 100


def _has_reference_geometry(qec: QueryExecutionContext) -> bool:
    if qec.slots.reference_geometry or qec.slots.geometry_ref:
        return True
    spatial_context = qec.spatial.get("spatial_context") if isinstance(qec.spatial, dict) else None
    if isinstance(spatial_context, dict) and spatial_context.get("geometry"):
        return True
    return False


def _has_target_binding(qec: QueryExecutionContext) -> bool:
    slots = qec.slots
    return bool(slots.target_features or slots.nftc_codes or slots.resolved_target_set)


def _requested_k(qec: QueryExecutionContext) -> int:
    raw = qec.slots.filters.get("k") or qec.slots.filters.get("limit") or 1
    try:
        return int(raw)
    except (TypeError, ValueError):
        return -1


def _has_feature_instance_ref(qec: QueryExecutionContext) -> bool:
    slots = qec.slots
    if slots.feature_instance_id not in (None, ""):
        return True
    if slots.feature_instance_ref:
        return bool(
            slots.feature_instance_ref.get("feature_instance_id")
            or slots.feature_instance_ref.get("id")
            or slots.feature_instance_ref.get("foid")
        )
    if slots.filters.get("feature_instance_id"):
        return True
    return False


def _has_document_query(qec: QueryExecutionContext) -> bool:
    return bool((qec.normalized_query or qec.original_query or "").strip())


def _rag_profile_available(qec: QueryExecutionContext) -> bool:
    return bool(
        os.getenv("EMBEDDING_MODEL", "bge-m3")
        and (os.getenv("OLLAMA_EMBEDDING_URL") or os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
    )


def validate_execution_context(qec: QueryExecutionContext) -> QueryExecutionContext:
    """공유 실행계약을 검증하는 결정론적 실행 gate."""
    current = qec.model_copy(deep=True)
    blockers: List[str] = list(current.blockers or [])
    warnings: List[str] = list(current.warnings or [])
    slots = current.slots
    route_plan: Dict[str, Any] = current.route_plan or {}
    analysis_type = route_plan.get("analysis_type") or slots.analysis_type or slots.operation

    binding_result = schema_binding_adapter.build_bindings(route_plan, slots.model_dump())
    current.data_bindings = binding_result.data_bindings
    current.tool_bindings = binding_result.tool_bindings
    blockers.extend(binding_result.blockers)
    warnings.extend(binding_result.warnings)
    current.provenance.setdefault("schema_binding", {})["inspected_relations"] = binding_result.inspected_relations

    if analysis_type in {"feature_search_by_radius", "feature_dwithin"}:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if slots.distance_m is None:
            blockers.append("NEEDS_USER_INPUT: distance_m is required")
        else:
            try:
                distance = float(slots.distance_m)
                if distance <= 0:
                    blockers.append("NEEDS_USER_INPUT: distance_m must be positive")
                if distance > MAX_RADIUS_M:
                    blockers.append(f"BLOCKED_POLICY: distance_m exceeds max radius {MAX_RADIUS_M:g}")
            except (TypeError, ValueError):
                blockers.append("NEEDS_USER_INPUT: distance_m must be numeric")
        if not _has_target_binding(current):
            blockers.append("NEEDS_USER_INPUT: target feature binding is required")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated data binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated tool binding")

    elif analysis_type in {"feature_within_area", "spatial_feature_search"}:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: AOI geometry is unresolved")
        if not _has_target_binding(current):
            blockers.append("NEEDS_USER_INPUT: target feature binding is required")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated data binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated tool binding")

    elif analysis_type in {"nearest_feature", "nearest_feature_search"}:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if not _has_target_binding(current):
            blockers.append("NEEDS_USER_INPUT: target feature binding is required")
        k = _requested_k(current)
        if k <= 0:
            blockers.append("NEEDS_USER_INPUT: nearest k must be a positive integer")
        elif k > MAX_NEAREST_K:
            blockers.append(f"BLOCKED_POLICY: nearest k exceeds max {MAX_NEAREST_K}")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated data binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated tool binding")

    elif analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"} or route_plan.get("primary_agent") in {"Standard RAG Agent", "standard-rag-agent"}:
        if not _has_document_query(current):
            blockers.append("NEEDS_USER_INPUT: document search query is required")
        if not _rag_profile_available(current):
            blockers.append("BLOCKED_CONFIG: query embedding profile is not configured")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated RAG tool binding")

    elif analysis_type in {"accident_feature_relation", "accident_relation_lookup", "occurred_in_lookup"}:
        if not _has_feature_instance_ref(current):
            blockers.append("NEEDS_USER_INPUT: feature_instance_id is required for accident relation lookup")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated accident relation binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated accident relation tool binding")

    elif analysis_type in {"traffic_search_by_time_space", "dynamic_traffic_lookup"}:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated dynamic traffic binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated dynamic traffic tool binding")

    elif analysis_type in {
        "spatial_layer_overlay",
        "current_tidal_lookup",
        "eddy_hazard_lookup",
        "hazard_area_lookup",
        "protected_area_lookup",
        "planned_port_overlay",
        "island_gazetteer_lookup",
        "sea_parting_prediction_lookup",
        "vessel_traffic_control_area_overlay",
    }:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated spatial layer binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated spatial layer tool binding")

    # Deduplicate while preserving order.
    current.blockers = list(dict.fromkeys(blockers))
    current.warnings = list(dict.fromkeys(warnings))

    if current.blockers:
        if any(item.startswith("NEEDS_USER_INPUT") for item in current.blockers):
            current.readiness = PlanStatus.NEEDS_USER_INPUT
        elif any(item.startswith("BLOCKED_POLICY") for item in current.blockers):
            current.readiness = PlanStatus.BLOCKED_POLICY
        elif any(item.startswith("BLOCKED_DATA") for item in current.blockers):
            current.readiness = PlanStatus.BLOCKED_DATA
        else:
            current.readiness = PlanStatus.BLOCKED_CONFIG
    else:
        current.readiness = PlanStatus.EXECUTION_READY
    return current
