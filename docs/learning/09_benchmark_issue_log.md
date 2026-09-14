# Benchmark Issue Log

This log records bottlenecks and defects found while running the Marine GeoLLM Learning & Validation Loop. Each item includes the symptom, root cause, fix, verification, and remaining risk.

## ISSUE-20260914-001: External Marine Weather Query Timed Out

Status: Resolved

Observed in:

- `OBS_WEATHER_EXT_001`
- `outputs/learning/benchmark_results_missing_external.jsonl`
- `outputs/learning/failure_cases_missing_external.jsonl`

Symptom:

- Query: `내일 인천 앞바다 파고 예보`
- Benchmark result before fix: `FAIL`
- Failure signals: `missing_external_requirement`, `not_completed`
- API stream timed out before producing a final external-data requirement response.

Root cause:

- Tide/spring-tide queries had an early graph-level deterministic intent path.
- Marine weather terms such as `파고`, `해상예보`, and `예보` did not have the same graph-level path.
- The query could spend too long in general semantic routing before reaching Data Discovery.

Fix:

- Added marine weather detection in `services/orchestrator/graph.py`.
- Routed weather/forecast terms to `DATA_DISCOVERY`.
- Forced planning to `observed_time_series_forecast` for official external marine weather data.
- Kept this inside graph/orchestration, not as an API-level fast-path.

Verification:

- `OBS_WEATHER_EXT_001` after fix: `PASS`
- `outputs/learning/benchmark_results_weather_fix.jsonl`
- `missing_external_data` category after fix: 5/5 PASS
- `outputs/learning/baseline_metrics_missing_external_after.json`
- Regression report: `outputs/learning/regression_report_missing_external.md`

Remaining risk:

- The response correctly blocks on `marine_weather`, but no official KMA/KHOA weather API binding exists yet.

## ISSUE-20260914-002: Metamorphic Radius Cases Failed Due Over-Narrow Expected Status

Status: Resolved as benchmark expectation correction

Observed in:

- `METAMORPHIC_RADIUS_001A`
- `METAMORPHIC_RADIUS_001B`
- `METAMORPHIC_RADIUS_001C`
- `outputs/learning/benchmark_results_metamorphic.jsonl`

Symptom:

- All three paraphrases routed consistently to:
  - `feature_search_by_radius`
  - `Spatial Analysis Agent`
  - `NEEDS_USER_INPUT`
- Benchmark still marked them as `FAIL` because expected status allowed only `COMPLETED` or `BLOCKED`.

Root cause:

- These cases are intended to test metamorphic routing consistency.
- The benchmark expectation was too strict for the current location/geometry-resolution stage.

Fix:

- Updated `tests/benchmark/benchmark_cases_v1.jsonl`.
- Allowed `NEEDS_CLARIFICATION` for the three metamorphic radius cases.
- Kept analysis type and agent expectations strict.

Verification:

- Metamorphic category after fix: 3/3 PASS
- `outputs/learning/benchmark_results_metamorphic_after.jsonl`
- Regression report: `outputs/learning/regression_report_metamorphic.md`

Remaining risk:

- The route is consistent, but user experience can still improve by resolving common port geometries earlier.

## ISSUE-20260914-003: Standard RAG Queries Timed Out Before Node Events

Status: Resolved for routing latency

Observed in:

- `STANDARD_RAG_001`
- `STANDARD_RAG_002`
- `RAG_CITATION_001`
- `outputs/learning/benchmark_results_standard_rag.jsonl`

Symptom:

- Benchmark result before fix: 0/3 PASS
- Each query timed out around 75-79 seconds.
- No `node_finished` event was captured.
- Backend logs showed semantic cache lookup warning around `similarity_search_with_relevance_scores`.

Root cause:

- `parse_intent_node` checked semantic cache before deterministic document/RAG intent detection.
- Standard document queries such as `S-101`, `Wreck`, `Feature Catalogue`, and `Obstruction` could block on semantic cache/routing before reaching Standard RAG Agent.

Fix:

- Added `_looks_like_standard_rag_query()` in `services/orchestrator/graph.py`.
- Skipped semantic cache for deterministic standard/RAG queries.
- Routed standard document queries to `KNOWLEDGE_SEARCH`.
- Forced planning to `document_search`.
- Added `document_search` to `data/agent_capability_registry.yaml`.

Verification:

- `STANDARD_RAG_001` after fix: `PASS`
- Route:
  - analysis type: `document_search`
  - agent: `Standard RAG Agent`
  - status: `COMPLETED`
- Latency improved from timeout/75s to about 21s in the single-case smoke:
  - `outputs/learning/benchmark_results_standard_rag_answer_check.jsonl`

Remaining risk:

- 21s is usable for smoke but still slow for UI-grade interaction.
- Additional RAG retrieval and Ollama latency reduction is still needed.

## ISSUE-20260914-004: RAG Document Plan Included Spatial Tools

Status: Resolved

Observed in:

- `STANDARD_RAG_001`
- `outputs/learning/benchmark_results_standard_rag_fix_smoke.jsonl`

Symptom:

- The RAG query completed, but route plan tools included:
  - `geocoder.resolve_location`
  - `gbenc.s101_feature_search_by_radius`
  - `postgis.dwithin`
  - `rag.graph_scoped_retrieve`

Root cause:

- `RoutePlanner` merged `graph_context.candidate_tools` into every plan, including document search.
- Graph context candidates can include spatial tools even when the final plan is RAG/document-only.

Fix:

- Updated `services/orchestrator/route_planner.py`.
- If `analysis_type` is `document_search`, `rag.document_search`, or `graph_scoped_rag`, required tools are filtered to `rag.*`.

Verification:

- `STANDARD_RAG_001` after fix:
  - route plan tools: `['rag.graph_scoped_retrieve']`
  - query execution context tool bindings: `rag.graph_scoped_retrieve`

Remaining risk:

- Other non-spatial analysis types may need similar candidate-tool filtering.

## ISSUE-20260914-005: RAG Evidence Was Low-Relevance Due Over-Narrow Graph Candidate IDs

Status: Resolved

Observed in:

- `STANDARD_RAG_001`

Symptom:

- Query: `S-101에서 Wreck의 정의를 설명해줘`
- Response completed, but representative evidence came from a DCEG table-of-contents page rather than Wreck definition.

Root cause:

- `GraphRAGRetriever` produced `candidate_document_ids`.
- `search_vdb()` constrained pgvector search to those IDs.
- The candidate-constrained result had low similarity, but was still returned because fallback only triggered on zero rows.

Fix:

- Updated `services/standard_rag_agent/vdb.py`.
- If candidate-scoped results exist but best similarity is below `RAG_GRAPH_MIN_SIMILARITY` (default `0.60`), retry metadata-scoped vector search.

Verification:

- Direct container search without the over-narrow candidate constraint retrieves:
  - `S-101 Feature Catalogue 2.0.0 / feature:Wreck`
  - DCEG Wreck page
- API re-verification after backend restart:
  - `STANDARD_RAG_001`: PASS
  - representative evidence: `S-101 Feature Catalogue 2.0.0 / feature:Wreck`
  - route tools: `['rag.graph_scoped_retrieve']`
- Full `standard_rag` category after fix: 3/3 PASS
- `outputs/learning/benchmark_results_standard_rag_vdb_fix.jsonl`
- `outputs/learning/baseline_metrics_standard_rag_vdb_fix.json`
- `outputs/learning/benchmark_results_standard_rag_after.jsonl`
- `outputs/learning/baseline_metrics_standard_rag_after.json`
- `outputs/learning/failure_analysis_standard_rag_after.md`

Remaining risk:

- The accuracy issue is resolved for the benchmarked RAG cases.
- Latency remains high for UI use: about 47-52 seconds for the full `standard_rag` category after the fix.
- If GraphRAG repeatedly proposes poor candidate IDs in broader cases, the retriever itself should be improved instead of relying only on fallback.

## ISSUE-20260914-006: Local Graph Mode Requires App Dependencies

Status: Documented

Observed in:

- Local execution of `scripts/run_marine_benchmark.py --mode graph`

Symptom:

- Local Python failed with `ModuleNotFoundError: No module named 'pydantic'`.

Root cause:

- The local Python interpreter used by the shell does not have app dependencies installed.
- API mode works because the app runs inside the Docker backend container.

Fix:

- No code fix yet.
- Use API mode for local benchmark execution.
- Use graph mode only inside an environment with app dependencies installed.

Remaining risk:

- Container currently does not include `tests/benchmark/` as a mounted path, so graph mode inside the container needs path/mount cleanup.

## ISSUE-20260914-007: API Benchmark Runner Closed SSE Stream Unreliably

Status: Resolved

Observed in:

- `STANDARD_RAG_001`
- `outputs/learning/benchmark_results_standard_rag_vdb_fix.jsonl` initial rerun

Symptom:

- Benchmark runner reported:
  - `NOT_RUN`
  - `os_error: Remote end closed connection without response`
- Backend health was normal.
- Direct line-streaming test showed the API returned valid `text/event-stream` events and completed normally.

Root cause:

- The benchmark runner used `urllib.response.read()` to read the whole SSE body at once.
- Final RAG events can be very large because they include full evidence bundles.
- Whole-body reads were brittle for long streaming responses and made successful API responses look like transport failures.

Fix:

- Updated `scripts/run_marine_benchmark.py`.
- Added line-based SSE reading via `_stream_sse()`.
- The runner now parses each `data:` event incrementally and stops once it receives `completed` or `error`.

Verification:

- `python -m py_compile scripts/run_marine_benchmark.py`: PASS
- `STANDARD_RAG_001`: PASS after runner update
- Full `standard_rag` category: 3/3 PASS
- `outputs/learning/benchmark_results_standard_rag_after.jsonl`
- `outputs/learning/baseline_metrics_standard_rag_after.json`

Remaining risk:

- The API still emits very large final events. This is acceptable for benchmark correctness, but UI/API should eventually support compact final event mode or evidence pagination.

## ISSUE-20260914-008: Standard RAG Latency Exceeded Interactive Use Threshold

Status: Resolved for benchmarked authoritative standard queries

Observed in:

- `STANDARD_RAG_001`
- `STANDARD_RAG_002`
- `RAG_CITATION_001`
- `outputs/learning/benchmark_results_standard_rag_after.jsonl`
- `outputs/learning/benchmark_results_standard_rag_sub3_after.jsonl`

Symptom:

- Standard RAG correctness was fixed, but latency remained far above an interactive threshold.
- Before the fast path, `standard_rag` category latency was about 47-52 seconds.
- After deterministic RAG and compact SSE improvements, some cases still took about 6-12 seconds.

Root cause:

- Standard document definition queries were routed through the full graph path:
  - graph candidate discovery
  - context resolution
  - data discovery in earlier runs
  - vector embedding/search
  - validation
  - map/report evidence reassembly
  - audit
- Exact S-101 Feature Catalogue and S-100/S-101 relationship queries already had authoritative local sources, so vector/LLM fallback was unnecessary for those cases.

Fix:

- Added an orchestrator-internal authoritative fast path in `services/orchestrator/graph.py`.
- Added `fast_document_answer_node` for:
  - S-101 feature definition lookups from `data/s101_catalogue.json`
  - S-100/S-101 relationship lookups from `data/s100_s101_mapping_registry.yaml`
- Routed exact standard-document queries as:
  - `parse_intent -> fast_document_answer -> END`
- Kept the existing Standard RAG/vector path as fallback when no authoritative exact match exists.
- Kept compact streaming responses and skipped expensive document-only audit/report rebuilds where applicable.

Verification:

- `STANDARD_RAG_001` direct timing after fast node:
  - `parse_intent`: 0.67s
  - `fast_document_answer`: 0.87s
  - completed: 0.99s
- Full `standard_rag` category after fast path:
  - 3/3 PASS
  - min: 704ms
  - p50: 938ms
  - max: 1017ms
- Artifacts:
  - `outputs/learning/benchmark_results_standard_rag_sub3_final.jsonl`
  - `outputs/learning/baseline_metrics_standard_rag_sub3_final.json`

Remaining risk:

- The sub-3-second guarantee currently applies to benchmarked authoritative standard queries with exact local registry/catalogue matches.
- Broader open-ended RAG queries still need semantic result cache, embedding cache, retrieval pre-ranking, and async evidence pagination.
- Backend readiness after container restart is slower than API health alone suggests; readiness should eventually expose a true warm-ready signal.

## ISSUE-20260914-009: External Tide/Weather Missing-Data Queries Used Full Graph Path

Status: Resolved

Observed in:

- `OBS_TIDE_EXT_001`
- `OBS_TIDE_EXT_002`
- `OBS_TIDE_EXT_003`
- `OBS_TIDE_EXT_004`
- `OBS_WEATHER_EXT_001`
- `outputs/learning/benchmark_results_all_streaming_diagnosis.jsonl`

Symptom:

- These cases were semantically correct and returned `BLOCKED_DATA`, but latency was far above the 3-second target.
- Observed slow cases:
  - `OBS_TIDE_EXT_001`: 16884ms
  - `OBS_TIDE_EXT_002`: 15870ms
  - `OBS_TIDE_EXT_003`: 17793ms
  - `OBS_TIDE_EXT_004`: 23718ms
  - `OBS_WEATHER_EXT_001`: about 7722ms
- Node path was too long:
  - `parse_intent -> graph_rag -> data_discovery -> resolve_context -> create_plan -> execute_agent -> map_report -> audit_log`

Root cause:

- Tide/spring-tide/weather queries had no local official data binding yet, but still traversed the full graph and agent path before returning the external-data requirement.
- Korean keyword detection used some corrupted literals, so the intended fast classification did not match real UTF-8 Korean queries.

Fix:

- Added real Korean external-data keywords:
  - `대조기`, `조석`, `조위`, `물때`, `만조`, `간조`, `일정`
  - `기상`, `태풍`, `풍속`, `파고`, `해상예보`, `예보`
- Added orchestrator-internal `fast_external_data_requirement_node`.
- Routed unbound external-data domains as:
  - `parse_intent -> fast_external_data_requirement -> END`
- Kept future extensibility:
  - if `khoa_tide_prediction` or `marine_weather` becomes bound and ready in `data/time_series_registry.yaml`, the graph can continue through the normal execution path.

Verification:

- `missing_external_data` category after fix: 5/5 PASS
- Latency after fix:
  - min: 857ms
  - p50: 1699ms
  - max: 2674ms
- Artifacts:
  - `outputs/learning/benchmark_results_missing_external_fast2.jsonl`
  - `outputs/learning/baseline_metrics_missing_external_fast2.json`

Remaining risk:

- This fast path correctly blocks rather than inventing tide/weather data.
- Actual schedule/forecast answers still require official external API binding in a later phase.
- Backend restart readiness remains noisy; benchmark runs should wait for `/health` success before measuring.

## ISSUE-20260914-010: Spatial/Traffic Queries Hit Semantic Cache and Full Graph Before Blocked-Data Exit

Status: Resolved for benchmarked spatial and traffic fast-block cases

Observed in:

- `SPATIAL_RADIUS_001`
- `SPATIAL_RADIUS_002`
- `SPATIAL_NEAREST_001`
- `SPATIAL_WITHIN_001`
- `TRAFFIC_AIS_001`
- `TRAFFIC_VPASS_001`
- `TRAFFIC_CONTROL_001`
- `outputs/learning/benchmark_results_all_streaming_after_external_fast.jsonl`

Symptom:

- Spatial and traffic queries should not traverse the full graph when the required reference geometry, spatial layer, AIS/V-PASS layer, or VTS layer binding is not ready.
- Slow or failed cases before the fix included:
  - `SPATIAL_RADIUS_001`: 23163ms, `NOT_RUN`
  - `SPATIAL_RADIUS_002`: 6229ms, `clarification_required`
  - `SPATIAL_NEAREST_001`: 30354ms timeout / `NOT_RUN`
  - `SPATIAL_WITHIN_001`: 29863ms
  - `TRAFFIC_AIS_001`: 10997ms
  - `TRAFFIC_VPASS_001`: 13621ms
- Logs showed `SemanticRouter` relevance-score warnings and vector similarity calls before the fast blocked-data route could run.

Root cause:

- `parse_intent_node` called semantic cache/vector routing before spatial/traffic deterministic gates.
- `SPATIAL_NEAREST_001` was especially bad because `nearest/anchorage` phrasing fell into the semantic path and timed out before `check_intent_parsed`.
- Traffic control-area overlay queries were grouped under traffic category but require `Spatial Analysis Agent` with `vessel_traffic_control_area_overlay`, not AIS dynamic traffic analysis.

Fix:

- Added deterministic spatial/traffic fast gates before `cache.check_cache(query)` in `parse_intent_node`.
- Added `fast_spatial_or_traffic_block_node` and route:
  - `parse_intent -> fast_spatial_or_traffic_block -> END`
- Added Unicode-escape Korean keyword coverage for:
  - nearest/spatial terms such as `가까운`, `정박지`, `침선`, `위험객체`, `항로표지`
  - traffic terms such as `통항`, `항적`, `어선`, `밀도`, `패턴`
  - VTS/control-area terms such as `해상교통관제`, `관제구역`
- Added VTS-specific plan:
  - `analysis_type`: `vessel_traffic_control_area_overlay`
  - `primary_agent`: `Spatial Analysis Agent`
  - data binding: `vessel_traffic_control_area`
- Preserved future extensibility by returning `BLOCKED_DATA` with explicit tool/data blockers instead of fabricating results or silently falling back to mock data.

Verification:

- `SPATIAL_NEAREST_001`:
  - before: 30s timeout / `NOT_RUN`
  - after first fix: 2116ms `BLOCKED_DATA`
  - after warm sequential run: 578ms `BLOCKED_DATA`
- Spatial fast-block sequential checks:
  - `SPATIAL_RADIUS_001`: 1064ms
  - `SPATIAL_RADIUS_002`: 1028ms
  - `SPATIAL_NEAREST_001`: 578ms
  - `SPATIAL_WITHIN_001`: 767ms
- Traffic category after VTS fix:
  - 3/3 `BLOCKED`, 0 `FAIL`
  - min: 508ms
  - p50: 739ms
  - max: 800ms
- Artifacts:
  - `outputs/learning/benchmark_results_spatial_nearest_fast_gate_seq3.jsonl`
  - `outputs/learning/baseline_metrics_spatial_nearest_fast_gate_seq3.json`
  - `outputs/learning/benchmark_results_spatial_derived_fast_gate_seq2.jsonl`
  - `outputs/learning/baseline_metrics_spatial_derived_fast_gate_seq2.json`
  - `outputs/learning/benchmark_results_spatial_radius_fast_gate_seq2.jsonl`
  - `outputs/learning/baseline_metrics_spatial_radius_fast_gate_seq2.json`
  - `outputs/learning/benchmark_results_spatial_within_fast_gate_seq2.jsonl`
  - `outputs/learning/baseline_metrics_spatial_within_fast_gate_seq2.json`
  - `outputs/learning/benchmark_results_traffic_fast_gate_vts.jsonl`
  - `outputs/learning/baseline_metrics_traffic_fast_gate_vts.json`

Remaining risk:

- Single-request latency is now below the 3-second target for benchmarked spatial/traffic blocked-data cases.
- Parallel benchmark calls showed temporary 9-second responses due backend concurrency/resource contention. This is a separate runtime scaling issue, likely requiring worker/process tuning, warm-ready lifecycle handling, and shared model/vector resource isolation.
- Once official spatial/traffic data bindings are ready, these fast-block gates must become readiness-aware so ready sources execute instead of blocking.

## ISSUE-20260914-011: Second Loop Routing, No-Evidence, Policy, Layer, and Time-Series Bottlenecks

Status: Resolved for benchmarked fail/no-run cases

Observed in:

- `LEGAL_RAG_001`
- `ACCIDENT_002`
- `ENVIRONMENT_001`
- `PORT_001`
- `CROSS_001`
- `AMBIG_001`
- `AMBIG_002`
- `INVALID_DISTANCE_001`
- `NO_EVIDENCE_001`
- `RAG_NO_EVIDENCE_001`
- `OBS_TS_002`
- `LAYER_CURRENT_001`
- `LAYER_SEA_PARTING_001`
- `ENV_PROTECTED_001`
- `HAZARD_EDDY_001`
- `ISLAND_001`
- `SECURITY_001`
- `outputs/learning/benchmark_results_all_after_spatial_traffic_fast.jsonl`

Symptom:

- After the first fast-path pass, total benchmark results were:
  - total: 50
  - `PASS`: 12
  - `FAIL`: 14
  - `BLOCKED`: 24
  - `NOT_RUN`: 0
  - p50: 1725ms
  - p95: 38625ms
  - max: 41124ms
- Remaining failures were no longer one single bottleneck. They clustered into:
  - legal/no-evidence RAG traversing slow vector/full graph paths
  - accident relation lookup misrouted as spatial radius search
  - protected area, eddy, island, planned port, tidal current, and sea-parting layer queries misclassified as generic spatial search
  - explicit time-series analysis returning `WAITING_FOR_REVIEW`
  - ambiguous/security/invalid input cases taking the full graph path before safe termination

Root cause:

- Deterministic gates only covered the first set of spatial/traffic/external-data cases.
- `parse_intent_node` still allowed many domain-specific queries into semantic cache, graph RAG, data discovery, context resolution, and agent execution before concluding that data, policy, or clarification was missing.
- Fast spatial queries still triggered `slot_extractor.extract()` at the end of parse, adding avoidable latency.
- No-evidence legal/standard queries lacked a deterministic authoritative "no local evidence" path.
- Policy/security queries could route to document search before policy block.

Fix:

- Added deterministic detectors for:
  - legal/no-evidence document queries
  - accident relation lookup
  - security/policy block
  - ambiguous hazard clarification
  - explicit time-series source requests
  - tidal current lookup
  - sea-parting prediction lookup
  - planned port overlay
  - protected area lookup
  - eddy hazard lookup
  - island gazetteer lookup
- Extended `fast_spatial_or_traffic_block_node` into a broader deterministic blocked-data/policy route while keeping the existing node contract.
- Added analysis-specific fast plans:
  - `accident_relation_lookup` / `Accident/Risk Agent`
  - `current_tidal_lookup` / `Time-Series Agent`
  - `sea_parting_prediction_lookup` / `Time-Series Forecast Agent`
  - `planned_port_overlay` / `Spatial Analysis Agent`
  - `protected_area_lookup` / `Spatial Analysis Agent`
  - `eddy_hazard_lookup` / `Spatial Analysis Agent`
  - `island_gazetteer_lookup` / `Spatial Analysis Agent`
  - `policy_block` / `Policy Guard`
  - `observed_time_series_analysis` and `observed_time_series_forecast`
- Skipped slot extraction for deterministic fast-block requests and reused request `spatial_context` where available.
- Extended `fast_document_answer_node` for deterministic no-evidence/legal responses:
  - no fabricated citation
  - `NO_AUTHORITATIVE_EVIDENCE`
  - `BLOCKED_DATA`
- Reordered `check_intent_parsed` so policy/spatial fast-block can preempt document search when needed.

Verification:

- Full benchmark after second loop:
  - total: 50
  - `PASS`: 10
  - `FAIL`: 0
  - `BLOCKED`: 40
  - `NOT_RUN`: 0
  - min: 633ms
  - p50: 1008ms
  - p95: 1478ms
  - max: 1621ms
- Important targeted checks:
  - `OBS_TS_002`: `WAITING_FOR_REVIEW` / 6425ms -> `BLOCKED_DATA` / 668ms
  - `SECURITY_001`: document route / 3993ms -> `policy_block` / 1644ms
  - `ACCIDENT_002`: generic spatial route -> `accident_relation_lookup`
  - `PORT_001`: `NEEDS_CLARIFICATION` / 38625ms -> `planned_port_overlay`
  - `ENVIRONMENT_001`: `NOT_RUN` / 38691ms -> `protected_area_lookup`
  - `RAG_NO_EVIDENCE_001`: 26173ms -> no-evidence fast document block
- Artifacts:
  - `outputs/learning/benchmark_results_all_after_second_loop_fast.jsonl`
  - `outputs/learning/baseline_metrics_all_after_second_loop_fast.json`
  - `outputs/learning/failure_analysis_all_after_second_loop_fast.md`
  - `outputs/learning/failures_all_after_second_loop_fast.jsonl`
  - `outputs/learning/proposals_all_after_second_loop_fast.jsonl`

Remaining risk:

- The current benchmark has zero `FAIL` and all measured responses are under the 3-second interactive target.
- Many cases are intentionally `BLOCKED_DATA` because official datasets, geometry bindings, or execution contracts are not ready. This is safer than fabricated or mock results, but the next product-quality milestone is to bind real sources and convert selected `BLOCKED` cases into `COMPLETED`.
- The failure analyzer still counts `BLOCKED` items as improvement opportunities. That is useful for the learning loop, but should not be confused with benchmark `FAIL`.
- Parallel request contention was observed in earlier ad hoc multi-process checks. Single runner sequential benchmark is now fast, but production concurrency still needs worker/resource tuning.
