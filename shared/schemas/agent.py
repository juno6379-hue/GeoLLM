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
    clarification_questions: Optional[List[str]] = None
    clarification_options: Optional[List[Dict[str, str]]] = Field(default=None, description="질문에 대한 선택박스/버튼 옵션 배열. 예: [{'label': '1km', 'value': '1000'}]")
    structured_result: Dict[str, Any] = Field(default_factory=dict)
    features: Optional[str] = None  # URI to GeoJSON etc.
    metrics: Dict[str, Any] = Field(default_factory=dict)
    output_layers: List[MapOutputLayer] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
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
