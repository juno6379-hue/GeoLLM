# 22. S-101 Spatial Reliability And Accident Relations

Date: 2026-09-11

This document records the current spatial reliability work for S-101 2.0 and the accident relation layer.

## 1. Problem

Earlier inspection found invalid `MULTIPOLYGON` geometry in the S-101 projection path. Invalid geometry can break or distort spatial predicates such as containment, intersection, nearest-neighbor search, and tile rendering.

The fix is to expose repaired geometry through a dedicated serving layer while preserving the current feature projection for audit and comparison.

## 2. Current Serving Design

| Object | Purpose |
|---|---|
| `projection.s101_feature_current` | Current S-101 2.0 projected feature rows |
| `projection.s101_feature_valid` | Geometry-repaired serving view/materialized layer |
| `projection.s101_feature_valid_anchor` | Representative anchor points for stable joins |
| `serving.accident_events` | Normalized accident event point data |
| `serving.accident_s101_relation_current` | Materialized accident-to-S-101 feature relations |

Application reads should prefer `projection.s101_feature_valid` for spatial predicates and map serving.

## 3. Verified State

```text
projection.s101_feature_current          | 787,102 rows, invalid geometry 0
projection.s101_feature_valid            | 787,102 rows, invalid geometry 0
projection.s101_feature_valid_anchor     | 787,102 rows
serving.accident_events                  | 4,636 rows
serving.accident_s101_relation_current   | 23,180 rows
```

The prior invalid geometry risk is now handled for the serving path. Continue to keep the valid layer as the default spatial query source.

## 4. Rebuild Scripts

The current scripts are:

```text
scripts/ensure_gbhd_s101_20_projection.sql
scripts/ensure_s101_valid_geometry_and_accident_relations.sql
scripts/ensure_s101_valid_geometry_anchor.sql
scripts/ensure_accident_s101_relations.sql
```

Recommended rebuild order:

```powershell
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_gbhd_s101_20_projection.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_s101_valid_geometry_and_accident_relations.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_s101_valid_geometry_anchor.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_accident_s101_relations.sql
```

## 5. Validation Queries

Invalid geometry check:

```sql
SELECT COUNT(*) AS invalid_count
FROM projection.s101_feature_valid
WHERE geom IS NOT NULL
  AND NOT ST_IsValid(geom);
```

Relation count:

```sql
SELECT COUNT(*) AS relation_count
FROM serving.accident_s101_relation_current;
```

Distance sanity check:

```sql
SELECT relation_type,
       COUNT(*) AS total,
       MIN(distance_m) AS min_distance_m,
       AVG(distance_m) AS avg_distance_m,
       MAX(distance_m) AS max_distance_m
FROM serving.accident_s101_relation_current
GROUP BY relation_type
ORDER BY relation_type;
```

## 6. Application Contract

GeoLLM responses that combine accidents and S-101 features should include:

```text
accident_id
feature_id or feature_identifier
feature_acronym/name when available
relation_type
distance_m
source layer: serving.accident_s101_relation_current
```

This prevents the LLM from inventing spatial relationships and gives the answer a verifiable database-backed trace.

## 7. Remaining Work

- Add automated regression checks for invalid geometry count.
- Add a smoke test for accident relation retrieval.
- Connect `serving.accident_s101_relation_current` to the GeoLLM answer provenance path.
- Document relation thresholds once the product owner fixes the final operational distances.
