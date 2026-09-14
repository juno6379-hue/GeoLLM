# State Merge Policy

Status: PARTIAL

## Implemented

`QueryExecutionContext.merge_slot_patch()` applies typed slot patches and records patch provenance.

Rules implemented:

- Unknown slot fields are ignored.
- `None`, empty string, empty list and empty dict do not erase previous values by default.
- Explicit clearing requires `allow_clear=True`.
- Applied changes increment `revision`.
- Applied changes append provenance records with `producer`, `field_path`, `previous`, `new`, `source_ref`, and `reason_code`.

## Current Orchestrator Behavior

- QueryNormalizer and SlotExtractor output are merged into `extracted_slots`.
- `_build_query_execution_context()` now creates the shared contract with:
  - request/task identity
  - original/normalized query
  - plan hash
  - readiness state
  - semantic resolution snapshot
  - KG/RAG/data discovery snapshots
  - snapshot versions from environment
- If target features are available, they are copied into `resolved_target_set` through the patch mechanism.

## Still Partial

- LangGraph fan-in is not yet fully converted to typed patch objects.
- Authentication and DB binding fields are still references/snapshots, not immutable validated bindings.
- Existing legacy fields `spatial_context`, `task_plan.slots`, and `resolved_metadata` still exist for compatibility.

