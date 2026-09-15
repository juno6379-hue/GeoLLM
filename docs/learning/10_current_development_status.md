# Marine GeoLLM Current Development Status

Generated: 2026-09-15

## Summary

The Marine GeoLLM learning and validation loop has reached a stable second-loop benchmark state.

The first high-priority blocked spatial case has now been converted into a real execution path: `부산항 입구 3km 이내 위험객체를 찾아줘` executes against the local S-101/GBENC PostGIS layer and returns actual hazard features instead of a blocked-data response.

The orchestrator now avoids full graph execution for queries that cannot yet be answered from trusted local data, official external data, or validated spatial/traffic bindings. Instead, it returns fast, explicit, auditable states such as `BLOCKED_DATA`, `NO_AUTHORITATIVE_EVIDENCE`, `BLOCKED_POLICY`, or deterministic clarification requirements.

## Latest Full Benchmark

Artifact:

- `outputs/learning/benchmark_results_all_after_second_loop_fast.jsonl`
- `outputs/learning/baseline_metrics_all_after_second_loop_fast.json`

Result:

- Total cases: 50
- PASS: 10
- FAIL: 0
- BLOCKED: 40
- NOT_RUN: 0
- Min latency: 633ms
- p50 latency: 1008ms
- p95 latency: 1478ms
- Max latency: 1621ms

This means the previous 30-40 second bottlenecks and benchmark failures have been removed for the current benchmark suite.

## Latest Targeted Execution Upgrade

Artifact:

- `outputs/learning/benchmark_results_spatial_radius_001_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_spatial_radius_001_real_s101_final.json`
- `outputs/learning/benchmark_results_evidence_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_evidence_real_s101_final.json`
- `outputs/learning/benchmark_results_metamorphic_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_metamorphic_real_s101_final.json`
- `outputs/learning/benchmark_results_invalid_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_invalid_real_s101_final.json`

Result:

- `SPATIAL_RADIUS_001`: `PASS`, `COMPLETED`, 891ms.
- `EVIDENCE_001`: `PASS`, `COMPLETED`, 1196ms.
- Metamorphic radius cases: 3/3 `PASS`, max 1358ms.
- Invalid input category: 0 `FAIL`; unsafe or invalid requests remained blocked within 1234ms.
- Actual 부산항 입구 3km result: 119 S-101 hazard features found, nearest 30 returned.

Execution binding:

- Reference geometry: `부산항 입구` -> `POINT(129.075 35.075)`.
- Layer: `projection.s101_feature_current`.
- Dataset contract: `GBENC_S101_feature`.
- Hazard mapping: `UnderwaterAwashRock`/`Wreck`/`Obstruction`.
- Tool/template: `postgis.dwithin`.
- Route: `parse_intent -> fast_s101_hazard_radius_execute`.

## Completed Development

### Benchmark and Learning Loop

- Added benchmark runner support for API/SSE execution.
- Added benchmark failure analysis and proposal generation.
- Added issue logging in markdown and JSONL.
- Added full benchmark case coverage for external data, spatial search, traffic, RAG, legal/no-evidence, observation, policy, invalid input, and cross-domain queries.

### Orchestrator Fast Paths

- External tide/weather missing-data fast path.
- Authoritative S-101/S-100 document answer fast path.
- Legal/no-evidence document fast block.
- Spatial/traffic blocked-data fast path.
- S-101 hazard-object radius execution path for 부산항 입구.
- VTS control-area specific routing.
- Accident relation lookup routing.
- Protected-area, eddy-hazard, planned-port, island-gazetteer layer routing.
- Tidal-current and sea-parting observation routing.
- Explicit time-series request routing.
- Security policy block routing.
- Ambiguous hazard clarification routing.

### Performance Improvements

- Removed semantic-cache/vector/full-graph traversal for deterministic blocked-data cases.
- Skipped slot extraction for deterministic fast-block requests.
- Reduced full benchmark p95 latency from about 38.6 seconds to 1.478 seconds.
- Reduced full benchmark max latency from about 41.1 seconds to 1.621 seconds.

### Safety and Evidence Behavior

- Prevented mock/fabricated tide, weather, spatial, traffic, legal, and feature results.
- Added explicit blockers and route-plan status for missing official data or missing data bindings.
- Added no-evidence document response behavior for unsupported legal/standard claims.
- Preserved future execution paths so ready data bindings can later convert `BLOCKED` cases into `COMPLETED` cases.

## Current Meaning of BLOCKED

The previous full benchmark had 40 `BLOCKED` cases. These are not benchmark failures.

They indicate that the query was understood and safely routed, but the required real source is not yet bound or execution-ready. Examples:

- KHOA tide/spring-tide/time-series data
- Marine weather and wave forecast data
- Tidal-current layers
- Sea-parting prediction data
- Protected-area layers
- Planned port development layers
- Island gazetteer data
- Eddy hazard layers
- AIS/V-PASS dynamic traffic layers
- Accident relation index
- Authoritative legal notice corpus

One important spatial blocked case has now moved to `COMPLETED`: S-101 hazard-object radius search near 부산항 입구.

## Remaining Work

### 1. Promote S-101 Spatial Execution From Local Fast Path to Registry-Driven Template

Move the current code constants into registry/ontology-backed configuration:

- known marine place/gazetteer binding
- hazard feature code mapping
- `projection.s101_feature_current` relation metadata
- `postgis.dwithin` query template
- response schema and evidence contract

### 2. Convert More BLOCKED Cases to COMPLETED

Bind official datasets and validated layers, then make the existing fast-block routing readiness-aware:

- If source is not ready: return `BLOCKED_DATA`.
- If source is ready: execute the correct agent/tool/query template.

### 3. External Data Integration

Prioritized sources:

- KHOA tide prediction and tide stations
- KHOA tidal-current or current observation sources
- KHOA sea-parting prediction
- KMA/KHOA marine weather and wave forecasts
- AIS/V-PASS traffic feeds or approved local archives

### 4. Spatial Layer Binding

Prioritized layers:

- `protected_area`
- `planned_port_area`
- `vessel_traffic_control_area`
- `island_gazetteer`
- `eddy_hazard_area`
- accident relation overlays

### 5. Legal and Standard Evidence Corpus

- Build authoritative legal/notice corpus.
- Add metadata filters for law, notice, section, date, issuer, and source.
- Keep no-evidence behavior when no authoritative source is found.

### 6. Production Runtime

- Add warm-ready health checks beyond simple `/health`.
- Tune backend concurrency and worker/resource isolation.
- Keep benchmark latency target below 3 seconds for interactive responses.

### 7. UI/API UX

Expose blocked-data details clearly:

- required source
- recommended official source
- whether web search was performed
- whether local RAG is suitable
- blocker code
- retry condition after data binding

## Key Files

- `services/orchestrator/graph.py`
- `scripts/run_marine_benchmark.py`
- `scripts/analyze_benchmark_failures.py`
- `tests/benchmark/benchmark_cases_v1.jsonl`
- `docs/learning/09_benchmark_issue_log.md`
- `outputs/learning/benchmark_issue_log.jsonl`
- `data/time_series_registry.yaml`
- `data/query_template_registry.yaml`
- `data/tool_registry.yaml`
- `data/agent_capability_registry.yaml`
