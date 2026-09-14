# Contract Schema

Status: PARTIAL

The first implementation pass extends existing `shared.schemas.agent` models instead of creating a parallel schema package.

## Added Or Extended Models

- `PlanStatus`
- `TaskResultStatus`
- `FeatureTypeRef`
- `FeatureBinding`
- `DataBinding`
- `ToolBinding`
- `EvidenceItem`
- `EvidenceBundle`
- `ValidatedTaskPlan`
- `ExecutionSlots`
- `QueryExecutionContext`
- `AgentResult`

## Compatibility Strategy

Existing public fields are preserved. New fields are additive:

- `AgentResult.answer_text`
- `AgentResult.spatial_result_summary`
- `AgentResult.evidence_bundle`
- `AgentResult.claims`
- `AgentResult.task_results`
- `QueryExecutionContext.contract_version`
- `QueryExecutionContext.request_id`
- `QueryExecutionContext.task_id`
- `QueryExecutionContext.revision`
- `QueryExecutionContext.plan_hash`
- `QueryExecutionContext.readiness`
- `QueryExecutionContext.blockers`
- `QueryExecutionContext.warnings`

`summary` remains available for legacy consumers. User-facing UI now prefers `answer_text`, then falls back to `summary`.

## Minimum Example

```json
{
  "contract_version": "geollm.execution.v1",
  "request_id": "task-1",
  "task_id": "task-1",
  "revision": 1,
  "plan_hash": "sha256...",
  "original_query": "부산항 입구 3km 이내 위험객체를 찾아줘",
  "normalized_query": "부산항 입구 3000m 이내 위험객체를 찾아줘",
  "readiness": "EXECUTION_READY",
  "slots": {
    "location_text": "부산항 입구",
    "distance_m": 3000,
    "target_term": "위험객체",
    "resolved_target_set": ["Wreck", "Obstruction"]
  }
}
```

## Still Partial

- `DataBinding` and `ToolBinding` are defined but not fully populated from registry/schema adapters yet.
- `EvidenceBundle` is defined and response-compatible, but citation-level IDs for RAG and accident relation evidence still need deeper adapter work.

