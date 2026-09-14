# Schema Bindings

Status: PARTIAL

## Implemented

`services.orchestrator.schema_binding_adapter.SchemaBindingAdapter` now binds registry entries to actual DB schema observations.

Current deterministic bindings:

- `GBENC_S101_feature`
  - registry relation: `projection.s101_feature_current`
  - geometry column: `geometry`
  - code column: `feature_type_code`
  - SRID: `4326`
- `gbenc.s101_feature_search_by_radius`
  - operation: `feature_search_by_radius`
  - template: `feature_search_by_radius`
- `postgis.dwithin`
  - operation: `ST_DWithin`
  - template: `feature_search_by_radius`
- `serving.accident_s101_relation_current`
  - accident geometry: `accident_geometry`
  - anchor geometry: `anchor_geometry`
  - physical distance column: `distance_meters`
  - contract distance alias: `distance_m`

## Runtime Observations

Read-only schema probes confirmed:

- `projection.s101_feature_current`: exists, 787102 rows.
- `projection.s101_feature_valid`: exists, 787102 rows.
- `serving.accident_s101_relation_current`: exists, 23180 rows.

`current` is used as the executable registry relation. `valid` remains the quality-checked projection baseline.

## Blocking Behavior

The adapter returns `BLOCKED_CONFIG` blockers when:

- a required tool is not registered;
- a required query template is not registered;
- a layer is not registered;
- a registry relation does not exist;
- a required geometry/code column is absent.

It does not rename physical DB columns. For accident relation, `distance_meters` is recorded as the physical binding and should be aliased to the contract-level `distance_m` by a SELECT adapter.

## Still Partial

- Identifier quoting is still owned by downstream SQL compiler/executor.
- The adapter does not yet compare registry table choices against all alternate projections.
- Per-user DB permission checks are not yet implemented.

