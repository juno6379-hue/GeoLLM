# Radius Hazard Route Contract

This document defines the executable Registry contract for queries such as:

> Find navigation hazard objects within 3 km of Busan Port entrance.

## 1. Interpretation

The query is resolved into four separate concepts:

| Field | Value |
|---|---|
| `derived_concept` | `navigation_hazard_object` |
| `context` | `navigation_safety` |
| `analysis_type` | `feature_search_by_radius` |
| `primary_agent` | `Spatial Analysis Agent` |

`feature_search_by_radius` is an operation. It is not a domain context and
must not be stored in the `context` field.

## 2. Registry resolution

`data/derived_concept_registry.yaml` defines the concept and its default
context. Its `default_analysis_type` is `feature_search_by_radius`.

`data/agent_capability_registry.yaml` resolves the operation to the following
route:

- Primary agent: `Spatial Analysis Agent`
- Secondary agents: `Data Discovery Agent`, `Map Report Agent`, `Validation Agent`
- Outputs: `GeoJSON`, `MapLayer`, `FeatureTable`, `Summary`

Required tools:

```text
geocoder.resolve_location
gbenc.s101_feature_search_by_radius
postgis.dwithin
```

Required datasets:

```text
GBENC_S101_feature
GBENC_codeinformation
s101_feature_dictionary
marine_term_dictionary
location_gazetteer
```

All required tools must be present in `data/tool_registry.yaml`, and all
required datasets must be present in `data/data_registry.yaml`. Missing
registry entries make the route non-executable.

## 3. Required slots

The route requires:

- `location`, resolved by `geocoder.resolve_location`
- `search_radius`, supplied by `distance_m`, `radius_m`, or `buffer_m`
- `target_features`, resolved from `navigation_hazard_object`

For the example query, the expected values are:

```yaml
location: Busan Port entrance
distance_m: 3000
target_features:
  - Wreck
  - Obstruction
  - Rock
  - UnderwaterAwashRock
  - BuoyIsolatedDanger
  - BeaconIsolatedDanger
```

## 4. Map output contract

The Map Adapter returns a primary GeoJSON layer for hazard objects. Search
boundaries are represented as a separate overlay:

```yaml
map_layers:
  - metadata.layer_role: hazard_objects
  - metadata.layer_role: search_buffer
```

The adapter deduplicates search-buffer features by geometry and emits no more
than one buffer feature. Buffer features are excluded from the primary
`feature_count`. The legacy `map_layer` field continues to point to the
primary hazard layer.

## 5. Execution readiness

The route is `ROUTED` and `execution_ready: true` only when the context,
analysis type, agent, required tools, required datasets, location, radius,
and target feature group are resolved. Otherwise the orchestrator must return
`NEEDS_CLARIFICATION` with the unresolved slots.
