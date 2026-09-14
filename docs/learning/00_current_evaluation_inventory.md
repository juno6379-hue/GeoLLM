# Current Evaluation Inventory

## Scope

This inventory maps the current `D:\An_GeoLLM` project to the first phase of the Marine GeoLLM Learning & Validation Loop.

## Existing Assets

Unit tests exist under `tests/unit/` for schemas, orchestration, data discovery, RAG, map adaptation, execution validation, KG/ontology validation, evidence building, spatial analysis, and accident/risk behavior.

End-to-end tests exist under `tests/e2e/`, but they are not yet a reusable benchmark corpus with expected execution-path assertions.

The orchestrator exposes two relevant task APIs:

- `POST /api/v1/tasks`: asynchronous accepted-state task creation.
- `POST /api/v1/tasks/stream`: SSE task execution stream used by the benchmark runner.

The streaming API accepts:

- `query`
- `organization_id`
- `user_id`
- `task_id`
- `spatial_context`

The streaming API emits node-level events containing:

- `node`
- `status`
- `task_plan` when created
- `context_result` when available
- `normalized_query`
- `normalization_debug`
- final `debug_trace`
- final `final_result` when completed

## Current Gaps

The following Learning Loop assets were not present before this phase:

- `tests/benchmark/`
- `configs/evaluation/`
- `docs/learning/`
- `scripts/run_marine_benchmark.py`
- `scripts/analyze_benchmark_failures.py`
- `scripts/compare_benchmark_runs.py`
- `outputs/learning/`

## Initial Benchmark Strategy

Golden answers should focus on execution semantics rather than fabricated result rows.

For data-backed questions where the exact live result is unknown, benchmark cases should assert:

- expected analysis type
- expected primary agent
- expected route-plan status
- expected blockers or external-data requirement
- forbidden behavior such as mock leakage, invented feature counts, invented tide dates, or unsupported claims

## External Data Pattern

The query `9월 인천 대조기 일정` is treated as an Observation/Missing Data benchmark case.

Expected behavior:

- Route through the normal graph path.
- Select `observed_time_series_forecast`.
- Select `Time-Series Forecast Agent`.
- End with `BLOCKED_DATA` until official KHOA tide prediction data is bound.
- Do not use local RAG to fabricate schedule dates.
- Do not perform web search inside the local site.
- Return `external_data_requirement` with source recommendations.

