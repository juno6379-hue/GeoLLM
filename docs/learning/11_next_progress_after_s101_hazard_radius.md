# Next Progress After S-101 Hazard Radius Execution

Generated: 2026-09-15

## Current Stop Point

Development is intentionally stopped at the point where the first real S-101 spatial execution case is working through the API:

- Query: `부산항 입구 3km 이내 위험객체를 찾아줘`
- Status: `COMPLETED`
- Route: `parse_intent -> fast_s101_hazard_radius_execute`
- Data: `GBENC_S101_feature`
- Relation: `projection.s101_feature_current`
- Tool: `postgis.dwithin`
- Result: 119 hazard features found, nearest 30 returned
- API latency: 891ms in the final targeted run

The evidence wording variant is also working:

- Query: `결과의 근거까지 포함해서 부산항 입구 위험객체를 찾아줘`
- Status: `COMPLETED`
- API latency: 1196ms

## Error / Bottleneck Logged

Issue: `ISSUE-20260915-012`

The original bottleneck was that the orchestrator understood the query but stopped at `BLOCKED_DATA` because these four links were not connected:

- 부산항 입구 geometry resolve
- S-101/GBENC feature layer
- hazard feature mapping: `Wreck`, `Obstruction`, `UnderwaterAwashRock`
- `postgis.dwithin` or equivalent spatial query template

The fix connected all four links and added a direct execution node with a PostGIS bounding-box prefilter plus exact geography-distance filtering.

## Verification Summary

Final API checks:

- `SPATIAL_RADIUS_001`: `PASS`, `COMPLETED`, 891ms
- `EVIDENCE_001`: `PASS`, `COMPLETED`, 1196ms
- `METAMORPHIC_RADIUS_001A`: `PASS`, `COMPLETED`, 1228ms
- `METAMORPHIC_RADIUS_001B`: `PASS`, `COMPLETED`, 1132ms
- `METAMORPHIC_RADIUS_001C`: `PASS`, `COMPLETED`, 1358ms
- Invalid input category: 0 `FAIL`; invalid requests stayed `BLOCKED` within 1234ms

Artifacts:

- `outputs/learning/benchmark_results_spatial_radius_001_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_spatial_radius_001_real_s101_final.json`
- `outputs/learning/benchmark_results_evidence_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_evidence_real_s101_final.json`
- `outputs/learning/benchmark_results_metamorphic_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_metamorphic_real_s101_final.json`
- `outputs/learning/benchmark_results_invalid_real_s101_final.jsonl`
- `outputs/learning/baseline_metrics_invalid_real_s101_final.json`

## Next Progress Items

### 1. Move Current Fast Path Into Registries

The working code path should be generalized so it is not hardcoded in the graph:

- move place aliases into a gazetteer or geometry registry
- move hazard feature code mapping into ontology/KG/registry
- move layer metadata into `data/query_template_registry.yaml` or an equivalent schema binding registry
- move SQL into a named query template
- keep the current node as the readiness-aware executor until the registry path is fully stable

### 2. Add UI/API Result Surface

Expose the new result payload clearly in the local site:

- total count
- nearest returned feature count
- feature type breakdown
- source layer
- reference geometry
- map layer/GeoJSON
- evidence bundle
- whether web/RAG was used

For this case, web/RAG is not used; the result comes from local PostGIS S-101 data.

### 3. Expand Spatial Execution Coverage

Apply the same pattern to other currently blocked spatial classes:

- vessel traffic control area
- protected area
- planned port area
- island gazetteer
- eddy hazard area
- accident relation overlays

### 4. Production Hardening

Keep the 3-second product target as a hard budget:

- add warm-ready health checks after container restart
- measure cold start separately from request latency
- add concurrency tests for simultaneous spatial radius queries
- keep exact distance count and nearest-feature return limit separate
- add index/EXPLAIN checks for each new spatial template

## Known Residual Risks

- 부산항 입구 geometry is a curated local binding, not yet an authoritative gazetteer lookup.
- Hazard mapping currently covers only the three priority S-101 feature types.
- API benchmark runs require backend restart after code edits because the Docker process keeps the old graph in memory.
- The current implementation is correct for the known S-101 current-feature table, but should be template-driven before adding many new locations or layers.
