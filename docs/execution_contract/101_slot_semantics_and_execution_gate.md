# Slot Semantics And Execution Gate Hardening

Date: 2026-09-17

## Issue

The query `독도 부근 사고 이력` exposed a slot semantics error:

- `부근` was promoted to `derived_concept`.
- `location_text` could be empty while a spatial tool was selected.
- `execution_ready` could become true before the common execution validator proved that reference geometry and bindings existed.
- KG/RAG seed expansion could carry unrelated semantic neighbors into the candidate context.

## Correct Semantics

- `부근`, `근처`, `주변`, `반경`, `이내` are spatial relation expressions.
- They must populate `spatial_relation`, not `derived_concept`.
- A spatial tool is executable only when a concrete `reference_geometry` or resolved geometry exists.
- `execution_ready=true` is valid only after `validate_execution_context()` returns `EXECUTION_READY`.

## Implemented Guards

- Added a non-derived term guard for spatial relation/action terms.
- Filtered GraphRAG seed `derived_concepts` to verified concept IDs only.
- Added schema-level protection so `ExecutionSlots.from_payload()` does not promote spatial relations to derived concepts.
- Added `accident_spatial_history_lookup` to the common schema binding adapter and execution validator.
- Updated the accident spatial history fast path to build a `QueryExecutionContext` and use validator readiness as the sole source of truth.

## Verified Result

For `독도 부근 사고 이력`:

- parsed intent: `ACCIDENT_ANALYSIS`
- target object: `accident_history`
- route analysis_type: `accident_spatial_history_lookup`
- location_text: `독도`
- reference_geometry: `POINT(131.864444 37.241389)`
- distance_m: `10000`
- spatial_relation: `nearby`
- derived_concept: `accident_event`
- readiness: `EXECUTION_READY`
- execution_ready: `true`

The same path without resolved geometry is blocked as:

`NEEDS_USER_INPUT: reference geometry is unresolved`
