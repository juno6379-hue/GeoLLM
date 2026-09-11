# 21. Current Architecture, DB, And Embedding Baseline

Date: 2026-09-11

This document records the current operating baseline after the S-101 Edition 2.0 restore, projection repair, accident relation build, and RAG dataset review.

## 1. Architecture Baseline

GeoLLM is currently organized around these runtime responsibilities:

| Area | Current component / object |
|---|---|
| Runtime orchestration | Docker Compose in `docker/docker-compose.yml` |
| Startup entrypoint | `start_geollm.bat` |
| Spatial database | `an_geollm_postgis` container, `gbhd_s101` database |
| API/backend | `backend` service on `localhost:8000` |
| Tile serving | tile server ports `11000-11002` |
| Embedding provider | Ollama on host, model `bge-m3` |
| Vector store | `knowledge.document_chunks` with pgvector embeddings |
| S-101 serving layer | `projection.s101_feature_valid` |
| Accident relation layer | `serving.accident_s101_relation_current` |

The key architecture decision is that S-101 Edition 2.0 is the default runtime target. Any query, projection, embedding, or validation path that can see mixed S-101 source versions must filter to the 2.0 identity:

```json
{
  "product_id": "S-101",
  "version": "2.0.0",
  "product_specification": "INT.IHO.S-101.2.0"
}
```

## 2. Database Baseline

The primary database is:

```text
container: an_geollm_postgis
database:  gbhd_s101
host port: localhost:5433
db port:   5432 inside Docker
```

The database contains restored S-101 data and derived serving objects. Because historical or earlier S-101 source rows may also exist in the same database, application code must not infer "current S-101" from table presence alone. The authoritative current layer is `projection.s101_feature_current`, rebuilt for S-101 2.0.

Verified counts:

| Object | Verified state |
|---|---:|
| `projection.s101_feature_current` | 787,102 rows, invalid geometry 0 |
| `projection.s101_feature_valid` | 787,102 rows, invalid geometry 0 |
| `projection.s101_feature_valid_anchor` | 787,102 rows |
| `serving.accident_events` | 4,636 rows |
| `serving.accident_s101_relation_current` | 23,180 rows |

## 3. Spatial Reliability Baseline

The former reliability risk was invalid `MULTIPOLYGON` geometry in `projection.s101_feature_current`. That risk is handled by the valid geometry serving path:

- `projection.s101_feature_valid` repairs geometries for spatial serving and joins.
- `projection.s101_feature_valid_anchor` provides representative points for index-friendly relation checks.
- `serving.accident_s101_relation_current` materializes accident-to-S-101 feature relationships.

Use `projection.s101_feature_valid` for geospatial API responses and spatial predicates. Use `projection.s101_feature_current` only when raw/current projection inspection is specifically needed.

## 4. Environment Baseline

Host-side defaults:

```text
POSTGIS_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/gbhd_s101
S101_DB_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/gbhd_s101
OLLAMA_HOST=http://localhost:11434
```

Container-side defaults:

```text
POSTGIS_URL=postgresql+psycopg2://postgres:postgres@db:5432/gbhd_s101
S101_DB_URL=postgresql+psycopg2://postgres:postgres@db:5432/gbhd_s101
OLLAMA_HOST=http://host.docker.internal:11434
```

## 5. Embedding Baseline

Embedding target:

```text
model: bge-m3
dimension: 1024
target table: knowledge.document_chunks
target chunk file: outputs/rag/s101_catalogue_db_chunks.jsonl
target embedding file: outputs/rag/s101_catalogue_db_embeddings.jsonl
```

Current checkpoint:

| Item | Count / state |
|---|---:|
| S-101 core chunks to embed | 1,869 |
| Partial embedding output | 1,333 rows generated |
| Loaded DB rows | 605 |
| Loaded rows with non-null embedding | 605 |

The database-loaded RAG set is still partial until the running/resumed embedding job completes and upserts all 1,869 S-101 2.0 chunks.

Currently loaded source groups:

```text
gbhd_s101_20_accident_relation_profile
gbhd_s101_20_db_feature_profile
gbhd_s101_20_db_text_values
gbhd_s101_20_valid_geometry_profile
s101_attribute_catalogue_v2_xml
s101_feature_catalogue_v2_xml
```

Remaining source groups expected after final embedding/upsert:

```text
s101_product_specification_2_0_pdf
s101_dceg_2_0_pdf
s101_portrayal_catalogue_2_0
s158_101_validation_checks_1_1
```

## 6. Verification Commands

Check running embedding jobs:

```powershell
docker ps --filter ancestor=docker-backend --format "table {{.ID}}\t{{.Status}}\t{{.Command}}"
```

Check embedding file progress:

```powershell
(Get-Content -Path outputs\rag\s101_catalogue_db_embeddings.jsonl).Count
```

Check DB-loaded RAG state:

```powershell
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -c "
select count(*) total,
       count(*) filter (where embedding is not null) embedded
from knowledge.document_chunks
where metadata @> '{\"product_id\":\"S-101\",\"version\":\"2.0.0\",\"product_specification\":\"INT.IHO.S-101.2.0\"}'::jsonb;
"
```

Expected final state:

```text
total >= 1,869
embedded = total
null embeddings = 0
embedding dimension = 1024
```

## 7. Completion Gate

The S-101 2.0 RAG and spatial baseline should be considered complete only when:

- S-101 2.0 rows in `knowledge.document_chunks` are at least 1,869.
- Every S-101 2.0 RAG row has a non-null 1024-dimensional embedding.
- Vector search applies the S-101 2.0 metadata filter by default.
- GeoLLM responses cite `source_file`, `section`, `source_id`, and `document_type`.
- Accident-related answers include evidence from `serving.accident_s101_relation_current`.
