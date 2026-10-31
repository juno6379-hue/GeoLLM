import math
import os
import hashlib
import json
from pathlib import Path
from functools import wraps
from typing import Any, Dict, List

from shapely import wkt
from shapely.errors import ShapelyError

from shared.schemas.agent import PlanStatus, QueryExecutionContext, ExecutionSlots, DataBinding, ToolBinding
from services.orchestrator.schema_binding_adapter import schema_binding_adapter


MAX_RADIUS_M = 50000.0
MAX_NEAREST_K = 100
MAX_FORECAST_HORIZON_STEPS = 168


def _decision_input(qec):
    return {"request_id": qec.request_id, "revision": qec.revision, "query": qec.original_query,
            "slots": qec.slots.model_dump(mode="json"), "spatial": qec.spatial,
            "analysis_type": qec.route_plan.get("analysis_type"),
            "dispatch_agent": qec.context.get("dispatch_agent"),
            "contract_scope": qec.context.get("contract_scope"),
            "security_context_ref": qec.security_context_ref,
            "coverage_validation": qec.provenance.get("coverage_validation"),
            "data_bindings": [b.model_dump(mode="json") for b in qec.data_bindings],
            "tool_bindings": [b.model_dump(mode="json") for b in qec.tool_bindings]}


def _input_hash(qec):
    return hashlib.sha256(json.dumps(_decision_input(qec), sort_keys=True, default=str).encode()).hexdigest()


def is_execution_authorized(qec):
    """A readiness flag alone is never a validation decision; slot changes invalidate it."""
    if not isinstance(qec, QueryExecutionContext):
        return False
    decision = qec.provenance.get("execution_validation") or {}
    return (qec.readiness == PlanStatus.EXECUTION_READY and not qec.blockers
            and decision.get("authority") == "ExecutionValidator"
            and decision.get("input_hash") == _input_hash(qec))


def project_execution_decision(qec, plan):
    """Project a validator decision; callers cannot derive approval from routing/result status."""
    fields = {"execution_ready": is_execution_authorized(qec), "status": qec.readiness.value,
              "route_plan_status": qec.readiness.value}
    if isinstance(plan, dict):
        plan.update(fields)
        plan["execution_validation"] = qec.provenance.get("execution_validation")
    else:
        for key, value in fields.items():
            setattr(plan, key, value)
    return plan


def apply_execution_decision(target, validated):
    """Copy the validated context into an executor-owned object without re-deciding."""
    for name in ("readiness", "blockers", "warnings", "data_bindings", "tool_bindings", "provenance", "route_plan"):
        setattr(target, name, getattr(validated, name))
    return target


def _finish(current, blockers, warnings):
    current.blockers = list(dict.fromkeys(blockers))
    current.warnings = list(dict.fromkeys(warnings))
    if current.blockers:
        current.readiness = next((status for status in (PlanStatus.BLOCKED_POLICY, PlanStatus.BLOCKED_DATA,
            PlanStatus.BLOCKED_CONFIG, PlanStatus.NEEDS_USER_INPUT)
            if any(item.startswith(status.value) for item in current.blockers)), PlanStatus.BLOCKED_CONFIG)
    else:
        current.readiness = PlanStatus.EXECUTION_READY
    current.provenance["execution_validation"] = {"authority": "ExecutionValidator", "version": "2",
        "readiness": current.readiness.value, "input_hash": _input_hash(current), "revision": current.revision,
        "operation": current.route_plan.get("analysis_type")}
    project_execution_decision(current, current.route_plan)
    return current


_LOOKUP_SOURCES = {
    "dataset_document_lookup": ("knowledge.document_chunks", {"chunk_id", "source_id", "source_sha256", "source_file", "metadata", "content", "embedding", "document_type", "title", "page_no", "section"}, "rag.dataset_document_retrieve"),
    "dataset_source_lookup": ("knowledge.document_chunks", {"chunk_id", "source_id", "source_sha256", "source_file", "metadata", "content", "embedding", "document_type", "title", "page_no", "section"}, "rag.dataset_source_retrieve"),
    "coastal_evidence_lookup": ("knowledge.document_chunks", {"chunk_id", "source_id", "source_sha256", "source_file", "metadata", "content", "embedding", "document_type", "title", "page_no", "section"}, "rag.coastal_evidence_retrieve"),
    "accident_event_lookup": ("serving.accident_events", {"event_id", "geom", "authority", "cause", "accident_type"}, "accident.event_lookup"),
    "dataset_evidence_lookup": ("knowledge.document_chunks", {"metadata", "content", "embedding"}, "rag.dataset_profile_retrieve"),
    "traffic_coverage": ("serving.dynamic_traffic_layer", {"layer_source", "observed_month"}, "diagnostics.traffic_coverage"),
    "document_coverage": ("knowledge.document_chunks", {"metadata", "embedding"}, "diagnostics.document_coverage"),
    "capability_vector": ("knowledge.capability_embeddings", {"id", "embedding"}, "diagnostics.capability_vector"),
}


def _validate_lookup(current, adapter):
    operation = current.route_plan.get("analysis_type")
    blockers, warnings = list(current.blockers), list(current.warnings)
    current.data_bindings, current.tool_bindings = [], []
    if not _has_document_query(current):
        blockers.append("NEEDS_USER_INPUT: lookup query is required")
    if operation == "public_catalogue_document_lookup":
        from services.orchestrator.catalogue_document import resolve_catalogue_document
        entry = resolve_catalogue_document(current.original_query or "")
        source_ref = "data/s101_feature_catalogue_v2_parsed.json"
        tool_id = "catalogue.document_lookup"
        try:
            digest = hashlib.sha256((Path(__file__).resolve().parents[2] / source_ref).read_bytes()).hexdigest()
        except OSError:
            digest = None
        if not entry or entry.get('source_sha256') != digest or not entry.get('features') or not entry.get('evidence', {}).get('locators'):
            blockers.append("BLOCKED_DATA: public catalogue document evidence unavailable")
        elif (adapter.tool_registry.get('tools', {}).get(tool_id, {}).get('operation') != operation
              or adapter.tool_registry.get('tools', {}).get(tool_id, {}).get('source') != source_ref
              or adapter.tool_registry.get('tools', {}).get(tool_id, {}).get('read_only') is not True):
            blockers.append("BLOCKED_CONFIG: catalogue document tool unavailable")
        else:
            current.data_bindings = [DataBinding(dataset_id='s101_feature_catalogue_v2', relation=source_ref, geometry_column='', snapshot_version=digest, read_only=True)]
            current.tool_bindings = [ToolBinding(tool_id=tool_id, operation=operation, schema_version=entry['evidence']['edition'])]
    elif operation == "public_catalogue_attribute_lookup":
        from services.orchestrator.public_catalogue_attribute import resolve_public_catalogue_attribute
        source_ref = "data/s101_feature_catalogue_v2_parsed.json"
        tool_id = "catalogue.attribute_lookup"
        entry = resolve_public_catalogue_attribute(current.original_query or "")
        try:
            digest = hashlib.sha256((Path(__file__).resolve().parents[2] / source_ref).read_bytes()).hexdigest()
        except OSError:
            digest = None
        if (not entry or entry.get("source_ref") != source_ref or not digest
                or entry.get("source_sha256") != digest or not entry.get("feature_code")
                or not entry.get("attribute_code") or not entry.get("definition")
                or not entry.get("locators")):
            blockers.append("BLOCKED_DATA: verified public catalogue attribute evidence is unavailable")
        elif (adapter.tool_registry.get("tools", {}).get(tool_id, {}).get("operation") != operation
                or adapter.tool_registry.get("tools", {}).get(tool_id, {}).get("source") != source_ref):
            blockers.append("BLOCKED_CONFIG: catalogue attribute lookup tool binding is unavailable")
        else:
            current.data_bindings = [DataBinding(dataset_id="s101_feature_catalogue_v2", relation=source_ref,
                geometry_column="", snapshot_version=digest, read_only=True)]
            current.tool_bindings = [ToolBinding(tool_id=tool_id, operation=operation,
                schema_version=str(entry.get("source_version") or ""))]
            current.provenance["catalogue_attribute"] = {key: entry.get(key) for key in (
                "feature_code", "attribute_code", "source_ref", "source_sha256", "xml_source_sha256", "locators")}
    elif operation in {"definition_lookup", "terminology_relation_lookup"}:
        from services.orchestrator.definition_router import resolve_definition
        entry = resolve_definition(current.original_query or "")
        if not entry or not entry.get("definition_ko") or not entry.get("source_ref"):
            blockers.append("BLOCKED_DATA: grounded definition is unavailable")
        else:
            current.data_bindings = [DataBinding(dataset_id=entry["source_kind"], relation=entry["source_ref"], geometry_column="")]
            current.tool_bindings = [ToolBinding(tool_id="definition.registry_lookup", operation=operation)]
    elif operation in {"local_document_lookup", "resolver_registry", "metadata_discovery", "evidence_validation"}:
        root = Path(__file__).resolve().parents[2]
        files = {"resolver_registry": ("capability_registry.yaml",),
                 "metadata_discovery": ("data_registry.yaml", "agent_registry.json"),
                 "evidence_validation": ("validation_rule_registry.yaml",)}
        for name in files.get(operation, ("s101_catalogue.json", "legal_notice_registry.yaml")):
            if (root / "data" / name).is_file():
                current.data_bindings.append(DataBinding(dataset_id=name, relation=f"data/{name}", geometry_column=""))
        if not current.data_bindings:
            blockers.append("BLOCKED_DATA: local document sources unavailable")
        current.tool_bindings = [ToolBinding(tool_id=f"inspection.{operation}" if operation in {"metadata_discovery", "evidence_validation"} else "definition.registry_lookup", operation=operation)]
    else:
        relation, columns, tool = _LOOKUP_SOURCES[operation]
        info = adapter._inspect_relation(relation)
        current.provenance["schema_binding"] = {"inspected_relations": {relation: info}}
        actual = {c["name"] for c in info.get("columns", [])}
        if not info.get("exists") or not info.get("has_select") or not columns <= actual:
            blockers.append(f"BLOCKED_DATA: lookup source unavailable: {relation}")
        else:
            current.data_bindings = [DataBinding(dataset_id=relation, relation=relation, geometry_column="")]
        current.tool_bindings = [ToolBinding(tool_id=tool, operation=operation)]
        if operation in {'coastal_evidence_lookup','dataset_source_lookup'}:
            harbour_relation = 'serving.small_harbour_guide'
            harbour = adapter._inspect_relation(harbour_relation)
            required = {'source_id','name','properties','provenance','geom'}
            if not harbour.get('exists') or not harbour.get('has_select') or not required <= {c['name'] for c in harbour.get('columns',[])}:
                blockers.append('BLOCKED_DATA: harbour guide source unavailable')
            else:
                current.data_bindings.append(DataBinding(dataset_id=harbour_relation,relation=harbour_relation,geometry_column='geom'))
        if operation == 'dataset_source_lookup':
            relation = 'serving.dataset_source_records'
            source = adapter._inspect_relation(relation)
            required = {'source_id','source_sha256','source_file','source_member','row_index','properties','geometry_valid'}
            if not source.get('exists') or not source.get('has_select') or not required <= {c['name'] for c in source.get('columns',[])}:
                blockers.append('BLOCKED_DATA: dataset source records unavailable')
            else:
                current.data_bindings.append(DataBinding(dataset_id=relation,relation=relation,geometry_column=''))
        if operation == "accident_event_lookup" and not current.slots.filters.get("terms"):
            blockers.append("NEEDS_USER_INPUT: accident filters are required")
    return _finish(current, blockers, warnings)


def validate_lookup_request(state, operation, *, slots=None, binding_adapter=None):
    qec = QueryExecutionContext(request_id=str(state.get("task_id") or "local"), original_query=state.get("query") or "",
        slots=ExecutionSlots.from_payload(slots or {}), route_plan={"analysis_type": operation},
        spatial={"spatial_context": state.get("spatial_context") or {}})
    return validate_execution_context(qec, binding_adapter=binding_adapter)


def validate_agent_execution(request, agent_name):
    """Bind approval to a declared agent operation, request and security context."""
    from services.orchestrator.agent_registry import registry
    agent = registry.get_agent(agent_name) or {}
    policy = agent.get("execution_contract") or {}
    scope = policy.get("scope")
    if scope == "inspection":
        current = QueryExecutionContext(request_id=request.task_id, task_id=request.task_id,
            original_query=request.original_query, route_plan={"analysis_type": policy.get("operation")},
            context={"parent_request_id": getattr(request.query_execution_context, "request_id", None)})
    else:
        current = request.query_execution_context.model_copy(deep=True) if request.query_execution_context else QueryExecutionContext(
            request_id=request.task_id, task_id=request.task_id, original_query=request.original_query)
    blockers = list(current.blockers)
    current.context.update(dispatch_agent=agent_name, contract_scope=scope)
    current.security_context_ref = f"user:{request.user_id}@org:{request.organization_id}:{request.security_context.clearance_level}"
    if scope not in {"inspection", "execution"}:
        blockers.append("BLOCKED_CONFIG: agent has no supported execution contract")
    if scope == "execution" and request.query_execution_context is None:
        blockers.append("BLOCKED_CONFIG: query_execution_context is required")
    if current.original_query != request.original_query or any(value and value != request.task_id for value in (current.request_id, current.task_id)):
        blockers.append("BLOCKED_POLICY: execution context belongs to another request")
    levels = {"PUBLIC": 1, "RESTRICTED": 2, "CONFIDENTIAL": 3, "SECRET": 4}
    if levels.get(request.security_context.clearance_level, 0) < agent.get("clearance_level", 1):
        blockers.append("BLOCKED_POLICY: agent clearance requirement is not met")
    operation = current.route_plan.get("analysis_type") or current.slots.analysis_type or current.slots.operation
    selected_agent = current.route_plan.get("primary_agent")
    if selected_agent and selected_agent != agent_name:
        blockers.append("BLOCKED_POLICY: plan selects a different agent")
    if operation not in policy.get("operations", [policy.get("operation")]):
        blockers.append(f"BLOCKED_CONFIG: operation {operation!r} is not supported by {agent_name}")
    if blockers:
        return _finish(current, blockers, current.warnings)
    current.request_id = current.task_id = request.task_id
    current.route_plan["analysis_type"] = operation
    return validate_execution_context(current)


def reject_agent_execution(request, agent_name, reason):
    current = request.query_execution_context.model_copy(deep=True) if request.query_execution_context else QueryExecutionContext(
        request_id=request.task_id, task_id=request.task_id, original_query=request.original_query)
    current.context["dispatch_agent"] = agent_name
    return _finish(current, [*current.blockers, f"BLOCKED_CONFIG: {reason}"], current.warnings)


def execution_gate_failure(state, qec):
    status = "NEEDS_CLARIFICATION" if qec.readiness == PlanStatus.NEEDS_USER_INPUT else "BLOCKED"
    summary = "실행 검증을 통과하지 못했습니다. " + "; ".join(qec.blockers)
    error_code = "EXECUTION_GATE"
    if status == "NEEDS_CLARIFICATION" and "NEEDS_USER_INPUT: accident filters are required" in qec.blockers:
        error_code = "ACCIDENT_FILTERS_REQUIRED"
        summary = "조회할 사고의 해역·관할 또는 사고 유형과 기간을 알려주세요. '최근'만으로 임의 기간을 적용하지 않습니다. 사고 검색은 아직 실행하지 않았습니다."
    final = {"task_id": state.get("task_id"), "status": status, "error_code": error_code,
             "summary": summary, "answer_text": summary,
             "clarification_questions": [summary] if status == "NEEDS_CLARIFICATION" else [],
             "structured_result": {"original_query": state.get("query"), "analysis_type": qec.route_plan.get("analysis_type"),
                                   "search_execution": {"status": "NOT_RUN", "reason": error_code}, "count": None},
             "orchestrator_v2": {"route_plan": qec.route_plan, "query_execution_context": qec.model_dump(mode="json")}}
    return {"status": status, "final_dict": final, "task_plan": qec.route_plan,
            "query_execution_context": qec.model_dump(mode="json")}


def attach_execution_decision(final, validated):
    """Keep the approval scope separate from execution success/partial/failure."""
    orch = final.setdefault("orchestrator_v2", {})
    plan = orch.setdefault("route_plan", {})
    project_execution_decision(validated, plan)
    context = orch.setdefault("query_execution_context", {})
    context.update(validated.model_dump(mode="json"))
    context["route_plan"] = validated.route_plan
    return final


def validated_lookup(operation, *, slot_builder=None, delegate_if=None):
    """Legacy lookup adapter: preflight first, never approve by inspecting the result."""
    def decorate(function):
        @wraps(function)
        async def guarded(state):
            import asyncio
            if delegate_if and delegate_if(state):
                return await function(state)
            slots = slot_builder(state) if slot_builder else {}
            validated = await asyncio.to_thread(validate_lookup_request, state, operation, slots=slots)
            if not is_execution_authorized(validated):
                return execution_gate_failure(state, validated)
            update = await function(state)
            if isinstance(update.get("final_dict"), dict):
                final = attach_execution_decision(update["final_dict"], validated)
                update["task_plan"] = final["orchestrator_v2"]["route_plan"]
                update["query_execution_context"] = final["orchestrator_v2"]["query_execution_context"]
            return update
        return guarded
    return decorate


def validate_uport_execution_context(qec, agent, db, selection):
    current = qec.model_copy(deep=True)
    blockers = list(current.blockers)
    if current.readiness != PlanStatus.PLAN_READY:
        blockers.append("BLOCKED_CONFIG: UPort plan is not ready")
    if db is None or selection is None or agent is None:
        blockers.append("BLOCKED_CONFIG: UPort execution dependencies are missing")
    if any(step.get("capability_id") not in {"uport.s101.berth.search", "uport.map.visualize"} for step in current.route_plan.get("steps", [])):
        blockers.append("BLOCKED_CONFIG: UPort operation has no executable adapter")
    if not blockers:
        agent.validate(current, db)
        current.data_bindings = [DataBinding(dataset_id=str(selection.dataset_id), relation="projection.s101_feature_valid",
                                  srid=4326, snapshot_version=str(selection.dataset_version_id))]
        current.tool_bindings = [ToolBinding(tool_id="uport.map.berths", operation="selected_berth_lookup")]
    return _finish(current, blockers, current.warnings)


def validate_place_resolution(query, payload, *, task_id=None):
    """Resolved server evidence permits display only; never promotes analysis authority."""
    resolution = payload.get("location_resolution") or {}
    qec = QueryExecutionContext(request_id=task_id, original_query=query,
        route_plan={"analysis_type": "place_lookup"},
        slots=ExecutionSlots(reference_geometry=payload.get("geometry"), crs=payload.get("crs"),
                             location_text=payload.get("location_text"), analysis_type="place_lookup"),
        provenance={"location_resolution": resolution, "execution_permission": payload.get("execution_permission")})
    blockers = []
    if payload.get("status") != "RESOLVED":
        prefix = "NEEDS_USER_INPUT" if payload.get("status") == "NEEDS_CLARIFICATION" else "BLOCKED_DATA"
        return _finish(qec, [f"{prefix}: {payload.get('error_code') or 'location requires confirmation'}"], [])
    if not _has_reference_geometry(qec) or qec.slots.crs != "EPSG:4326":
        blockers.append("NEEDS_USER_INPUT: valid geographic location is required")
    elif not all(-limit <= value <= limit for value, limit in zip(wkt.loads(qec.slots.reference_geometry).bounds, (180, 90, 180, 90))):
        blockers.append("NEEDS_USER_INPUT: geographic location is out of bounds")
    if not resolution.get("source_ref"):
        blockers.append("BLOCKED_DATA: location source is missing")
    qec.data_bindings = [DataBinding(dataset_id="place_resolution", relation=resolution.get("source_ref") or "unresolved", srid=4326)]
    qec.tool_bindings = [ToolBinding(tool_id="place.resolve", operation="map_view_only")]
    qec.warnings = ["Location validation permits map display only, not analysis authority."]
    return _finish(qec, blockers, qec.warnings)


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
    return bool(slots.target_features or slots.target_layers or slots.nftc_codes or slots.resolved_target_set)


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
    current.readiness = PlanStatus.DRAFT
    current.route_plan.update(execution_ready=False, status="DRAFT", route_plan_status="DRAFT")
    current.provenance.pop("execution_validation", None)
    if current.route_plan.get("analysis_type") in {*_LOOKUP_SOURCES, "public_catalogue_document_lookup", "public_catalogue_attribute_lookup", "definition_lookup", "terminology_relation_lookup", "local_document_lookup", "resolver_registry", "metadata_discovery", "evidence_validation"}:
        return _validate_lookup(current, binding_adapter or schema_binding_adapter)
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

    if analysis_type == 'selected_feature_lookup':
        identifier = slots.feature_instance_id
        if isinstance(identifier, bool) or not str(identifier).isascii() or not str(identifier).isdigit() or not 0 < int(identifier) < 2**63:
            blockers.append('NEEDS_USER_INPUT: valid selected feature ID is required')
        if (slots.feature_instance_ref or {}).get('source_ref') != 'projection.s101_feature_valid':
            blockers.append('NEEDS_USER_INPUT: selected feature source is unresolved')
        if not current.data_bindings or not current.tool_bindings:
            blockers.append('BLOCKED_CONFIG: selected feature bindings are unavailable')
    elif analysis_type in {"feature_search_by_radius", "feature_dwithin", "source_attribute_search"}:
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

        if analysis_type == 'source_attribute_search':
            from services.orchestrator.marine_s101_mapping import resolve_mappings
            from services.orchestrator.korean_query_analysis import constraints
            query = current.original_query or ''
            scope = constraints(query)
            mappings = resolve_mappings(query, scope)
            if any(c['scope_status'] == 'EXPLICIT_LOCAL_SCOPE' and c['kind'] in {'exclusion', 'absence_predicate'} for c in scope):
                blockers.append('BLOCKED_POLICY: attribute search cannot execute negative constraints')
            if len(mappings) != 1 or not mappings[0]['search_enabled']:
                blockers.append('BLOCKED_CONFIG: executable source mapping is required')
            else:
                mapping = mappings[0]
                if (slots.target_features != [mapping['feature']] or
                    slots.filters.get('attribute_filters') != mapping['filters'] or
                    slots.filters.get('mapping_registry_sha256') != mapping['registry_sha256'] or
                    slots.filters.get('fc_sha256') != mapping['fc_sha256']):
                    blockers.append('BLOCKED_CONFIG: source mapping snapshot or predicates mismatch')
            if _has_reference_geometry(current):
                point = wkt.loads(slots.reference_geometry)
                if point.geom_type != 'Point' or not (-180 <= point.x <= 180 and -90 <= point.y <= 90):
                    blockers.append('NEEDS_USER_INPUT: attribute search requires a geographic point')
            if slots.crs != 'EPSG:4326':
                blockers.append('NEEDS_USER_INPUT: attribute search requires EPSG:4326')

    elif analysis_type in {"feature_within_area", "spatial_feature_search", "feature_search_by_area"}:
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

    elif analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"}:
        if not _has_document_query(current):
            blockers.append("NEEDS_USER_INPUT: document search query is required")
        if not _rag_profile_available(current):
            blockers.append("BLOCKED_CONFIG: query embedding profile is not configured")
        if not current.tool_bindings:
            blockers.append("BLOCKED_CONFIG: no validated RAG tool binding")
        if not current.data_bindings:
            blockers.append("BLOCKED_DATA: no validated document source binding")

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
        elif slots.distance_m is None and wkt.loads(slots.reference_geometry or current.spatial["spatial_context"]["geometry"]).geom_type not in {"Polygon", "MultiPolygon"}:
            blockers.append("NEEDS_USER_INPUT: distance_m or map bounds is required")
        if slots.distance_m is not None:
            try:
                distance = float(slots.distance_m)
                if not math.isfinite(distance) or distance <= 0:
                    blockers.append("NEEDS_USER_INPUT: distance_m must be finite and positive")
                elif distance > MAX_RADIUS_M:
                    blockers.append(f"BLOCKED_POLICY: distance_m exceeds max radius {MAX_RADIUS_M:g}")
            except (TypeError, ValueError):
                blockers.append("NEEDS_USER_INPUT: distance_m must be numeric")
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

    from services.orchestrator.spatial_coverage import SPATIAL_OPERATIONS, assess_coverage
    if analysis_type in SPATIAL_OPERATIONS:
        receipt = assess_coverage(current, getattr(binding_adapter or schema_binding_adapter, 'layer_registry', {}))
        current.provenance['coverage_validation'] = receipt
        if receipt['status'] in {'OUT_OF_COVERAGE', 'PARTIAL'}:
            blockers.append('BLOCKED_DATA: DATA_OUT_OF_SCOPE')
        elif receipt['status'] == 'UNKNOWN':
            if receipt['required']:
                blockers.append('BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED')
            else:
                warnings.append('DATA_COVERAGE_UNVERIFIED: returned rows describe source observations only')
    return _finish(current, blockers, warnings)
