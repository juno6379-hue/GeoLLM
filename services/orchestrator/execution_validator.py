import math
import os
from typing import Any, Dict, List

from shapely import wkt
from shapely.errors import ShapelyError

from shared.schemas.agent import PlanStatus, QueryExecutionContext
from services.orchestrator.schema_binding_adapter import schema_binding_adapter


MAX_RADIUS_M = 50000.0
MAX_NEAREST_K = 100
MAX_FORECAST_HORIZON_STEPS = 168


def _has_reference_geometry(qec: QueryExecutionContext) -> bool:
    geometry = qec.slots.reference_geometry
    if geometry is None:
        spatial_context = qec.spatial.get("spatial_context") if isinstance(qec.spatial, dict) else None
        if isinstance(spatial_context, dict):
            geometry = spatial_context.get("geometry")
    # A geometry reference must be resolved to actual geometry before execution.
    if not isinstance(geometry, str) or not geometry.strip():
        return False
    try:
        parsed = wkt.loads(geometry)
        return not parsed.is_empty and parsed.is_valid and all(math.isfinite(v) for v in parsed.bounds)
    except (ShapelyError, TypeError, ValueError):
        return False


def _has_target_binding(qec: QueryExecutionContext) -> bool:
    slots = qec.slots
    return bool(slots.target_features or slots.nftc_codes or slots.resolved_target_set)


def _requested_integer(filters: Dict[str, Any], *keys: str, default: int) -> int:
    raw = next((filters[key] for key in keys if filters.get(key) is not None), default)
    if isinstance(raw, bool):
        return -1
    try:
        value = int(raw)
        if not isinstance(raw, str) and raw != value:
            return -1
        return value
    except (TypeError, ValueError, OverflowError):
        return -1


def _requested_k(qec: QueryExecutionContext) -> int:
    return _requested_integer(qec.slots.filters, "k", "limit", default=1)


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


def _has_time_series_source(qec: QueryExecutionContext) -> bool:
    if qec.slots.filters.get("source_path") or qec.slots.filters.get("dataset_id"):
        return True
    return bool(qec.data_bindings)


def _rag_profile_available(qec: QueryExecutionContext) -> bool:
    return bool(
        os.getenv("EMBEDDING_MODEL", "bge-m3")
        and (os.getenv("OLLAMA_EMBEDDING_URL") or os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
    )


def validate_execution_context(qec: QueryExecutionContext, *, binding_adapter=None) -> QueryExecutionContext:
    """공유 실행계약을 검증하는 결정론적 실행 gate."""
    if qec.route_plan.get("analysis_type") == "uport_query_plan":
        # Keep domain validation behind the same public gate as GeoLLM tools.
        # Planning remains non-executable until later binding verification.
        from services.uport.validation import validate_uport_plan
        return validate_uport_plan(qec)
    current = qec.model_copy(deep=True)
    blockers: List[str] = list(current.blockers or [])
    warnings: List[str] = list(current.warnings or [])
    slots = current.slots
    route_plan: Dict[str, Any] = current.route_plan or {}
    analysis_type = route_plan.get("analysis_type") or slots.analysis_type or slots.operation

    binding_result = (binding_adapter or schema_binding_adapter).build_bindings(route_plan, slots.model_dump())
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
                if not math.isfinite(distance):
                    blockers.append("NEEDS_USER_INPUT: distance_m must be finite")
                elif distance <= 0:
                    blockers.append("NEEDS_USER_INPUT: distance_m must be positive")
                elif distance > MAX_RADIUS_M:
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

    elif analysis_type == "accident_spatial_history_lookup":
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if slots.distance_m is None:
            blockers.append("NEEDS_USER_INPUT: distance_m is required")
        else:
            try:
                distance = float(slots.distance_m)
                if not math.isfinite(distance):
                    blockers.append("NEEDS_USER_INPUT: distance_m must be finite")
                elif distance <= 0:
                    blockers.append("NEEDS_USER_INPUT: distance_m must be positive")
                elif distance > MAX_RADIUS_M:
                    blockers.append(f"BLOCKED_POLICY: distance_m exceeds max radius {MAX_RADIUS_M:g}")
            except (TypeError, ValueError):
                blockers.append("NEEDS_USER_INPUT: distance_m must be numeric")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated accident event binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated accident spatial history tool binding")

    elif analysis_type in {"traffic_search_by_time_space", "dynamic_traffic_lookup"}:
        if not _has_reference_geometry(current):
            blockers.append("NEEDS_USER_INPUT: reference geometry is unresolved")
        if not current.data_bindings:
            blockers.append("BLOCKED_CONFIG: no validated dynamic traffic binding")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated dynamic traffic tool binding")

    elif analysis_type in {"observed_time_series_analysis", "time_series_observation_analysis", "observed_time_series_forecast", "time_series_forecast"}:
        filters = current.slots.filters or {}
        data_discovery = current.data_discovery if isinstance(current.data_discovery, dict) else {}
        api_params = data_discovery.get("api_params") if isinstance(data_discovery.get("api_params"), dict) else {}
        external_evidence = data_discovery.get("external_data_evidence") or api_params.get("external_data_evidence") or {}
        external_required = bool(data_discovery.get("requires_external_api") or api_params.get("domain") or external_evidence)
        if external_required:
            domain = api_params.get("domain") or "external_time_series"
            blockers.append(f"BLOCKED_DATA: external time-series source is not bound: {domain}")
        else:
            if not _has_time_series_source(current):
                blockers.append("BLOCKED_DATA: no executable time-series source is bound")
            has_time_series_binding = any(binding.relation for binding in current.data_bindings)
            if not (filters.get("timestamp_column") or filters.get("time_column") or has_time_series_binding):
                blockers.append("NEEDS_USER_INPUT: timestamp_column is required")
            if not (filters.get("value_column") or filters.get("metric") or filters.get("observed_property") or has_time_series_binding):
                blockers.append("NEEDS_USER_INPUT: value_column is required")
        if analysis_type in {"observed_time_series_forecast", "time_series_forecast"}:
            horizon_steps = _requested_integer(filters, "horizon_steps", "horizon", default=3)
            if horizon_steps <= 0:
                blockers.append("NEEDS_USER_INPUT: horizon_steps must be a positive integer")
            elif horizon_steps > MAX_FORECAST_HORIZON_STEPS:
                blockers.append(f"BLOCKED_POLICY: horizon_steps exceeds max {MAX_FORECAST_HORIZON_STEPS}")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated time-series tool binding")

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
    else:
        blockers.append(f"BLOCKED_CONFIG: unsupported operation: {analysis_type}")

    # Deduplicate while preserving order.
    current.blockers = list(dict.fromkeys(blockers))
    current.warnings = list(dict.fromkeys(warnings))

    if current.blockers:
        if any(item.startswith("BLOCKED_POLICY") for item in current.blockers):
            current.readiness = PlanStatus.BLOCKED_POLICY
        elif any(item.startswith("BLOCKED_DATA") for item in current.blockers):
            current.readiness = PlanStatus.BLOCKED_DATA
        elif any(item.startswith("BLOCKED_CONFIG") for item in current.blockers):
            current.readiness = PlanStatus.BLOCKED_CONFIG
        elif any(item.startswith("NEEDS_USER_INPUT") for item in current.blockers):
            current.readiness = PlanStatus.NEEDS_USER_INPUT
        else:
            current.readiness = PlanStatus.BLOCKED_CONFIG
    else:
        current.readiness = PlanStatus.EXECUTION_READY
    return current
