"""Research-only request telemetry; no production monkeypatch or raw SQL retention."""
from .spatial_execution_observer import SpatialExecutionObserver

# Logical domain operations, not every nested helper. Generic agent dispatch
# is one operation; its SQL/model work is counted separately to avoid inflation.
OPERATIONS = frozenset({
    'graph_rag_node','data_discovery_node','resolve_context_node','execute_agent_node',
    'fast_definition_answer_node','fast_pipeline_diagnostic_node','fast_document_answer_node',
    'fast_dataset_evidence_answer_node','fast_s101_hazard_radius_execute_node',
    'fast_dynamic_traffic_execute_node','fast_s101_nearest_feature_execute_node',
    'fast_requested_spatial_layer_execute_node','fast_accident_spatial_history_lookup_node',
    'fast_accident_event_lookup_node','fast_place_lookup_node',
})
VERSION = 'research_request_telemetry_v1'


class ReliabilityObserver(SpatialExecutionObserver):
    def __init__(self, task_id):
        super().__init__(task_id)
        self.domain_frames = set()

    def profile(self, frame, action, arg):
        if action == 'call' and frame.f_globals.get('__name__') == 'services.orchestrator.graph':
            if frame.f_code.co_name in OPERATIONS and frame not in self.domain_frames:
                # Async resumption produces repeated profile 'call' events.
                self.domain_frames.add(frame)
                self.record('domain_operation_started', frame.f_code.co_name)
        super().profile(frame, action, arg)

    def telemetry(self, final_state=None):
        final = final_state or {}
        complete = self.complete and not self.instrumentation_issues
        def count(kind):
            return sum(e['kind'] == kind for e in self.events) if complete else None
        status = str(final.get('status', '')).split('.')[-1].upper()
        from shared.schemas.agent import AgentStatus
        known_states={state.value for state in AgentStatus}
        needs_review = status in {'NEEDS_HITL','WAITING_FOR_REVIEW','AWAITING_APPROVAL','PENDING_REVIEW','NEEDS_REVIEW','REQUIRES_REVIEW'}
        return {'version': VERSION, 'task_id':self.task_id, 'complete':complete,
                'tool_calls':count('domain_operation_started'), 'sql_calls':count('sql_submitted'),
                'tool_call_scope':'GRAPH_LOGICAL_DOMAIN_OPERATION_ENTRY; nested helpers excluded',
                'sql_call_scope':'ALL_INSTRUMENTED_DBAPI_SUBMISSIONS; metadata included',
                'retries':final.get('retry_count') if complete and type(final.get('retry_count')) is int else None,
                'retry_scope':'ORCHESTRATOR_EXPLICIT_RETRY_COUNTER; model attempts separately counted',
                'human_escalation':needs_review if complete and status in known_states else None,
                'human_escalation_scope':'EXPLICIT_FINAL_REVIEW_STATE; clarification is not human review',
                'instrumentation_issues':list(self.instrumentation_issues),
                'events':self.events}
