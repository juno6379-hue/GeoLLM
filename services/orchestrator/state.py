import operator
from typing import TypedDict, Annotated, Dict, Any, List, Optional
from datetime import datetime

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus

class StateTransitionLog(TypedDict):
    previous_state: str
    next_state: str
    timestamp: str
    actor: str
    reason: str
    payload_reference: Optional[str]
    error_code: Optional[str]
    retry_count: int

def merge_logs(old_logs: List[StateTransitionLog], new_logs: List[StateTransitionLog]) -> List[StateTransitionLog]:
    if not old_logs: return new_logs
    if not new_logs: return old_logs
    return old_logs + new_logs

class OrchestratorState(TypedDict):
    task_id: str
    execution_revision: int
    query: str
    organization_id: str
    user_id: str
    spatial_context: Optional[Dict[str, Any]]
    
    # LangGraph Reducers
    status: AgentStatus
    state_history: Annotated[List[StateTransitionLog], merge_logs]
    
    agent_request: Optional[AgentRequest]
    agent_result: Optional[AgentResult]
    
    # HITL 및 분기 처리를 위한 상태 플래그
    approval_granted: Optional[bool]
    retry_count: int
    error_message: Optional[str]
    
    final_dict: Optional[Dict[str, Any]]
    task_plan: Optional[Any]
    query_execution_context: Optional[Dict[str, Any]]
    
    normalization_debug: Optional[List[str]]
    norm_result: Optional[Dict[str, Any]]
    active_workspace: Optional[Dict[str, Any]]
    workspace_context: Optional[Dict[str, Any]]
    available_layers: Optional[List[str]]
    uploaded_assets: Optional[List[str]]
    context_result: Optional[Any]
    normalized_query: Optional[str]
    extracted_slots: Optional[Dict[str, Any]]
    graph_context: Optional[Dict[str, Any]]
    graph_rag_context: Optional[Dict[str, Any]]
    candidate_trace: Optional[Dict[str, Any]]
    korean_query_analysis: Optional[Dict[str, Any]]
    query_contract_blocked: Optional[bool]
    source_mapping_handled: Optional[bool]
    selected_feature_handled: Optional[bool]
    data_discovery_result: Optional[Dict[str, Any]]
    clarification_questions: Optional[List[str]]
def log_transition(
    prev_state: str, 
    next_state: str, 
    actor: str = "System", 
    reason: str = "Success",
    error_code: Optional[str] = None,
    retry_count: int = 0
) -> List[StateTransitionLog]:
    return [{
        "previous_state": prev_state,
        "next_state": next_state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actor": actor,
        "reason": reason,
        "payload_reference": None,
        "error_code": error_code,
        "retry_count": retry_count
    }]
