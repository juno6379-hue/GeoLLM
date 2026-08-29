from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from shared.schemas.agent import DatasetVersion, SecurityContext

class ToolMetadata(BaseModel):
    tool_name: str
    tool_version: str
    capability: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    security_scope: str
    owner: str
    created_at: datetime
    updated_at: datetime

class ToolRequest(BaseModel):
    task_id: str
    trace_id: str
    agent_name: str
    tool_name: str
    tool_version: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_references: List[str] = Field(default_factory=list)
    security_context: SecurityContext
    timeout: int = 60
    idempotency_key: Optional[str] = None

class ToolResult(BaseModel):
    task_id: str
    trace_id: str
    tool_name: str
    tool_version: str
    status: str
    error_code: Optional[str] = None
    structured_result: Dict[str, Any] = Field(default_factory=dict)
    output_references: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time: float
    source_dataset_versions: List[DatasetVersion] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
