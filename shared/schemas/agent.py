from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class AgentStatus(str, Enum):
    RECEIVED = "RECEIVED"
    INTENT_PARSING = "INTENT_PARSING"
    INTENT_PARSED = "INTENT_PARSED"
    CONTEXT_RESOLVING = "CONTEXT_RESOLVING"
    CONTEXT_RESOLVED = "CONTEXT_RESOLVED"
    PLAN_CREATING = "PLAN_CREATING"
    PLAN_CREATED = "PLAN_CREATED"
    AGENTS_SELECTED = "AGENTS_SELECTED"
    EXECUTING = "EXECUTING"
    WAITING_FOR_DATA = "WAITING_FOR_DATA"
    PARTIAL = "PARTIAL"
    RESULTS_AGGREGATED = "RESULTS_AGGREGATED"
    VALIDATING = "VALIDATING"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    NEEDS_HITL = "NEEDS_HITL"
    MAP_REPORT_GENERATING = "MAP_REPORT_GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"

class Intent(BaseModel):
    intent_type: str
    target_objects: List[str] = Field(default_factory=list)
    intent_understanding: str = "분석 불가"
    execution_plan: str = "분석 불가"
    spatial_conditions: List[str] = Field(default_factory=list)
    normalized_query: Optional[str] = None
    temporal_conditions: List[str] = Field(default_factory=list)
    output_format: str = "MAP"

    @field_validator('execution_plan', 'intent_understanding', mode='before')
    @classmethod
    def convert_list_to_str(cls, v):
        if isinstance(v, list):
            return "\n".join([str(item) for item in v])
        return str(v) if v is not None else "분석 불가"

class SpatialContext(BaseModel):
    base_location: Optional[str] = None
    place_id: Optional[str] = None
    place_version: Optional[str] = None
    location_resolution: Optional[Dict[str, Any]] = None
    geometry: Optional[str] = None
    buffer_distance: Optional[float] = None
    map_bounds: Optional[List[float]] = None
    crs: str = "EPSG:4326"

class TemporalContext(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_time: Optional[str] = None

class DatasetVersion(BaseModel):
    dataset_id: str
    version: str

class SecurityContext(BaseModel):
    clearance_level: str
    allowed_tool_scopes: List[str] = Field(default_factory=list)

class OrchestratorContext(BaseModel):
    priority: str = "NORMAL"
    timeout_seconds: int = 300

class TaskPlan(BaseModel):
    task_id: str
    status: str = "ROUTED"
    intent: str
    context: str
    analysis_type: str
    derived_concept: Optional[str] = None
    primary_agent: str
    secondary_agents: List[str] = Field(default_factory=list)
    slots: Dict[str, Any] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    data: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    clarification_required: bool = False
    confidence: float = 0.0
    execution_ready: bool = False
    route_plan_status: str = "UNKNOWN"

class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_USER_INPUT = "NEEDS_USER_INPUT"
    BLOCKED_CONFIG = "BLOCKED_CONFIG"
    BLOCKED_DATA = "BLOCKED_DATA"
    BLOCKED_POLICY = "BLOCKED_POLICY"
    PLAN_READY = "PLAN_READY"
    EXECUTION_READY = "EXECUTION_READY"

class TaskResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SUCCESS_EMPTY = "SUCCESS_EMPTY"
    NO_EVIDENCE = "NO_EVIDENCE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class FeatureTypeRef(BaseModel):
    product_id: Optional[str] = None
    edition: Optional[str] = None
    catalogue_version: Optional[str] = None
    feature_class: Optional[str] = None

class FeatureBinding(BaseModel):
    surface_term: Optional[str] = None
    concept_id: Optional[str] = None
    feature_type_ref: FeatureTypeRef = Field(default_factory=FeatureTypeRef)
    dataset_id: Optional[str] = None
    db_code: Optional[str] = None
    source: Optional[str] = None
    verification_status: str = "CANDIDATE"

class DataBinding(BaseModel):
    dataset_id: str
    relation: str
    geometry_column: str = "geometry"
    distance_column: Optional[str] = None
    srid: Optional[int] = None
    snapshot_version: Optional[str] = None
    layer_type: Optional[str] = None
    source_asset: Optional[str] = None
    execution_status: Optional[str] = None
    read_only: bool = True

class ToolBinding(BaseModel):
    tool_id: str
    operation: str
    query_template_id: Optional[str] = None
    schema_version: Optional[str] = None

class EvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: str
    summary: Optional[str] = None
    source_ref: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

class EvidenceBundle(BaseModel):
    spatial_feature_evidence: List[EvidenceItem] = Field(default_factory=list)
    spatial_layer_evidence: List[EvidenceItem] = Field(default_factory=list)
    accident_relation_evidence: List[EvidenceItem] = Field(default_factory=list)
    regulatory_evidence: List[EvidenceItem] = Field(default_factory=list)
    rag_evidence: List[EvidenceItem] = Field(default_factory=list)
    kg_provenance: List[EvidenceItem] = Field(default_factory=list)

class ValidatedTaskPlan(BaseModel):
    task_plan: TaskPlan
    plan_status: PlanStatus = PlanStatus.DRAFT
    plan_hash: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionSlots(BaseModel):
    surface_term: Optional[str] = None
    location: Optional[str] = None
    location_text: Optional[str] = None
    reference_geometry: Optional[str] = None
    geometry_ref: Optional[str] = None
    resolution_status: Optional[str] = None
    crs: Optional[str] = None
    distance_m: Optional[float] = None
    spatial_relation: Optional[str] = None
    time_range: Dict[str, Any] = Field(default_factory=dict)
    target_term: Optional[str] = None
    concept_id: Optional[str] = None
    derived_concept: Optional[str] = None
    context: Optional[str] = None
    analysis_type: Optional[str] = None
    operation: Optional[str] = None
    target_features: List[str] = Field(default_factory=list)
    target_area_features: List[str] = Field(default_factory=list)
    resolved_target_set: List[str] = Field(default_factory=list)
    alternative_target_sets: List[Dict[str, Any]] = Field(default_factory=list)
    feature_instance_ref: Dict[str, Any] = Field(default_factory=dict)
    feature_instance_id: Optional[Any] = None
    target_layers: List[str] = Field(default_factory=list)
    target_dynamic_layers: List[str] = Field(default_factory=list)
    nftc_codes: List[int] = Field(default_factory=list)
    inclusions: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    query_template: Optional[str] = None
    tool: Optional[str] = None
    output_type: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    unresolved_slots: List[str] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]]) -> "ExecutionSlots":
        payload = dict(payload or {})
        if payload.get("location") and not payload.get("location_text"):
            payload["location_text"] = payload["location"]
        if payload.get("target_feature_candidates") and not payload.get("target_features"):
            payload["target_features"] = payload["target_feature_candidates"]
        if payload.get("derived_concepts") and not payload.get("derived_concept"):
            concepts = payload["derived_concepts"]
            payload["derived_concept"] = concepts[0] if isinstance(concepts, list) and concepts else concepts
        allowed = set(cls.model_fields)
        normalized = {key: value for key, value in payload.items() if key in allowed}
        return cls(**normalized)

class QueryExecutionContext(BaseModel):
    contract_version: str = "geollm.execution.v1"
    request_id: Optional[str] = None
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    revision: int = 1
    plan_hash: Optional[str] = None
    original_query: Optional[str] = None
    slots: ExecutionSlots = Field(default_factory=ExecutionSlots)
    normalized_query: Optional[str] = None
    security_context_ref: Optional[str] = None
    semantic_resolution: Dict[str, Any] = Field(default_factory=dict)
    feature_bindings: List[FeatureBinding] = Field(default_factory=list)
    data_bindings: List[DataBinding] = Field(default_factory=list)
    tool_bindings: List[ToolBinding] = Field(default_factory=list)
    kg: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    route_plan: Dict[str, Any] = Field(default_factory=dict)
    data_discovery: Dict[str, Any] = Field(default_factory=dict)
    spatial: Dict[str, Any] = Field(default_factory=dict)
    rag: Dict[str, Any] = Field(default_factory=dict)
    readiness: PlanStatus = PlanStatus.DRAFT
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    snapshot_versions: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def merge_slot_patch(
        self,
        patch: Dict[str, Any],
        *,
        producer: str,
        source_ref: Optional[str] = None,
        reason_code: str = "MERGE",
        allow_clear: bool = False,
    ) -> "QueryExecutionContext":
        """Apply a typed slot patch without letting empty values erase prior facts."""
        current = self.model_copy(deep=True)
        slot_payload = current.slots.model_dump()
        applied: List[Dict[str, Any]] = []
        allowed = set(ExecutionSlots.model_fields)

        for key, value in (patch or {}).items():
            if key not in allowed:
                continue
            empty_value = value is None or value == "" or value == [] or value == {}
            if empty_value and not allow_clear:
                continue
            previous = slot_payload.get(key)
            if previous == value:
                continue
            slot_payload[key] = value
            applied.append({
                "producer": producer,
                "field_path": f"slots.{key}",
                "previous": previous,
                "new": value,
                "source_ref": source_ref,
                "reason_code": reason_code,
            })

        current.slots = ExecutionSlots(**slot_payload)
        if applied:
            current.revision += 1
            current.provenance.setdefault("patches", []).extend(applied)
        return current

class AgentRequest(BaseModel):
    task_id: str
    trace_id: str
    session_id: Optional[str] = None
    user_id: str
    organization_id: str
    agent_name: str
    original_query: str
    parsed_intent: Optional[Intent] = None
    spatial_context: Optional[SpatialContext] = None
    temporal_context: Optional[TemporalContext] = None
    available_datasets: List[DatasetVersion] = Field(default_factory=list)
    security_context: SecurityContext
    orchestrator_context: OrchestratorContext = Field(default_factory=OrchestratorContext)
    task_plan: Optional[TaskPlan] = None
    query_execution_context: Optional[QueryExecutionContext] = None
    previous_agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    requested_outputs: List[str] = Field(default_factory=list)
    callback: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MapOutputLayer(BaseModel):
    layer_id: str
    type: str

class ToolCallLog(BaseModel):
    tool_name: str
    status: str
    execution_time_ms: float

class AgentResult(BaseModel):
    task_id: str
    trace_id: str
    agent_name: str
    agent_version: str
    status: AgentStatus
    error_code: Optional[str] = None
    summary: Optional[str] = None
    answer_text: Optional[str] = None
    spatial_result_summary: Optional[Dict[str, Any]] = None
    clarification_options: Optional[List[Dict[str, str]]] = Field(default=None, description="질문에 대한 선택박스/버튼 옵션 배열. 예: [{'label': '1km', 'value': '1000'}]")
    structured_result: Dict[str, Any] = Field(default_factory=dict)
    features: Optional[str] = None  # URI to GeoJSON etc.
    metrics: Dict[str, Any] = Field(default_factory=dict)
    output_layers: List[MapOutputLayer] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    evidence_bundle: EvidenceBundle = Field(default_factory=EvidenceBundle)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    task_results: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    tool_calls: List[ToolCallLog] = Field(default_factory=list)
    source_dataset_versions: List[DatasetVersion] = Field(default_factory=list)
    validation_payload: Dict[str, Any] = Field(default_factory=dict)
    recommended_next_actions: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
