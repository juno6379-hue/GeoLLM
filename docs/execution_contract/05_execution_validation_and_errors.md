# Execution Validation And Errors

Status: PARTIAL

## Implemented Gates

`services.orchestrator.execution_validator.validate_execution_context()` now handles separate deterministic gates for:

- radius feature search
- area feature search
- nearest feature search
- document/RAG search
- accident-feature relation lookup

## Radius Feature Search

Required:

- reference geometry or geometry reference
- positive numeric `distance_m`
- distance within service limit
- target feature binding
- validated S-101 data binding
- validated tool/template binding

Errors:

- `NEEDS_USER_INPUT: reference geometry is unresolved`
- `NEEDS_USER_INPUT: distance_m is required`
- `NEEDS_USER_INPUT: distance_m must be positive`
- `BLOCKED_POLICY: distance_m exceeds max radius 50000`
- `NEEDS_USER_INPUT: target feature binding is required`
- `BLOCKED_CONFIG: no validated data/tool binding`

## Area Search

Required:

- AOI/reference geometry
- target feature binding
- validated S-101 data binding
- validated tool/template binding

Radius is not required.

## Nearest Search

Required:

- reference geometry
- target feature binding
- positive integer `k`, defaulting to 1 when omitted
- `k <= 100`
- validated data/tool binding

Errors:

- `NEEDS_USER_INPUT: nearest k must be a positive integer`
- `BLOCKED_POLICY: nearest k exceeds max 100`

## Document Search

Required:

- document query text from `normalized_query` or `original_query`
- configured embedding profile
- validated RAG tool/template binding

Location, radius, and S-101 geometry are not required.

## Accident-Feature Relation Lookup

Required:

- `feature_instance_id` or `feature_instance_ref`
- validated `serving.accident_s101_relation_current` binding
- validated `accident.s101_relation_lookup` tool/template binding

Physical `distance_meters` remains a DB binding and should be surfaced as contract-level `distance_m` only through a SELECT/result adapter.

## Status Mapping

- User-fixable missing inputs: `NEEDS_USER_INPUT`
- Configuration/schema/tool/template failures: `BLOCKED_CONFIG`
- Policy limits: `BLOCKED_POLICY`
- Otherwise ready: `EXECUTION_READY`

## Still Partial

- Per-user DB authorization checks are not implemented yet.
- Document collection/version/profile compatibility is checked only at configuration level.
- Accident relation result execution and evidence IDs are not yet implemented.

