# Benchmark Design

## Case Schema

Each benchmark case is stored as one JSON object per line in `tests/benchmark/benchmark_cases_v1.jsonl`.

Important fields:

- `case_id`: Stable identifier.
- `query`: User-visible query text.
- `category`: Benchmark category.
- `domains`: Domain tags.
- `api_request`: Exact parameters passed to the task API.
- `expected_semantics`: Expected normalized or derived semantic concepts.
- `expected_slots`: Expected slots such as `location_text`, `distance_m`, or filters.
- `expected_analysis_type`: Expected `TaskPlan.analysis_type`.
- `expected_agent`: Expected `TaskPlan.primary_agent`.
- `expected_tools`: Tools that should be routed when applicable.
- `expected_behavior`: `EXECUTE`, `BLOCK`, `CLARIFY`, `DOCUMENT_ANSWER`, or `NO_EVIDENCE`.
- `expected_status`: Acceptable final result status values.
- `expected_route_plan_status`: Acceptable route plan statuses.
- `expected_external_data`: Required external source behavior, if any.
- `forbidden_behavior`: Safety constraints.
- `llm_judge`: Optional natural-language rubric for LLM-assisted review.

## API Parameter Flow

The benchmark runner sends only parameters supported by `TaskCreateRequest`:

```json
{
  "query": "...",
  "organization_id": "benchmark",
  "user_id": "benchmark-runner",
  "task_id": "optional stable id",
  "spatial_context": {
    "base_location": "optional",
    "geometry": "optional WKT",
    "buffer_distance": 3000,
    "crs": "EPSG:4326"
  }
}
```

Expected outputs are read from:

- SSE `node_finished.task_plan`
- SSE final `debug_trace`
- SSE final `final_result`
- `final_result.orchestrator_v2.route_plan`
- `final_result.orchestrator_v2.query_execution_context`
- `final_result.external_data_requirement`

## LLM Usage

LLM usage is optional and must never be the only source of failure classification.

Allowed:

- summarizing ambiguous answer quality
- flagging unsupported or overconfident claims
- reviewing whether final Korean wording satisfies a case-specific rubric

Forbidden:

- overriding deterministic trace failures
- marking fabricated data as correct
- auto-approving registry, ontology, KG, or Agent changes

