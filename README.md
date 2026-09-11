# An_GeoLLM

An_GeoLLM is a marine geospatial intelligence platform for S-100/S-101 chart data, PostGIS spatial analysis, and RAG-based standard/catalogue Q&A.

The current development baseline is S-101 Edition 2.0. The runtime, spatial projection, accident relation layer, and embedding pipeline should all target S-101 2.0 unless a task explicitly says otherwise.

## Current Runtime Baseline

| Item | Value |
|---|---|
| Database container | `an_geollm_postgis` |
| Primary database | `gbhd_s101` |
| Product specification | `INT.IHO.S-101.2.0` |
| Catalogue version | `2.0.0` |
| PostGIS port | `localhost:5433 -> container:5432` |
| Backend port | `localhost:8000` |
| Tile server ports | `localhost:11000-11002` |
| Embedding model | Ollama `bge-m3`, 1024 dimensions |

`gbhd_s101` can contain both S-101 1.0 and 2.0 source rows. Production queries, projections, and RAG metadata filters must target:

```json
{
  "product_id": "S-101",
  "version": "2.0.0",
  "product_specification": "INT.IHO.S-101.2.0"
}
```

## Implemented State

- Docker Compose runtime has been standardized around the PostGIS container, backend, tile server, and Ollama host settings.
- The PostGIS image includes `pgvector` support for local vector search.
- `projection.s101_feature_current` is rebuilt for S-101 2.0 only.
- `projection.s101_feature_valid` provides repaired valid geometry for serving and spatial joins.
- `projection.s101_feature_valid_anchor` provides representative anchor points for geometry-safe joins and indexing.
- `serving.accident_events` contains normalized accident points.
- `serving.accident_s101_relation_current` stores nearest/containing accident-to-S-101 feature relations.
- The S-101 2.0 RAG builder covers catalogue XML, product specification PDF, DCEG fallback material, portrayal catalogue, validation checks, DB feature profiles, valid-geometry profile, and accident-relation profile.

## Verified Data Checkpoint

| Object | Count / status |
|---|---:|
| `projection.s101_feature_current` | 787,102 rows, invalid geometry 0 |
| `projection.s101_feature_valid` | 787,102 rows, invalid geometry 0 |
| `projection.s101_feature_valid_anchor` | 787,102 rows |
| `serving.accident_events` | 4,636 rows |
| `serving.accident_s101_relation_current` | 23,180 rows |

RAG checkpoint:

| Item | Count / status |
|---|---:|
| S-101 core chunk target | 1,869 chunks |
| Partial embedding output | 1,333 rows generated |
| Loaded rows in `knowledge.document_chunks` | 605 rows |

The embedding job may still be running locally. `knowledge.document_chunks` should be treated as partial until the S-101 core embedding file reaches 1,869 rows and the upsert step completes.

## Start Runtime

Recommended local startup:

```powershell
.\start_geollm.bat
```

Direct Compose startup:

```powershell
docker compose -f docker\docker-compose.yml up -d db backend tile-server
```

Health check:

```powershell
curl.exe -fsS http://localhost:8000/health
```

## Important Environment Variables

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

## Rebuild S-101 Projection And Relations

```powershell
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_gbhd_s101_20_projection.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_s101_valid_geometry_and_accident_relations.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_s101_valid_geometry_anchor.sql
docker exec -i an_geollm_postgis psql -U postgres -d gbhd_s101 -f /scripts/ensure_accident_s101_relations.sql
```

## Build S-101 Core RAG

Generate chunks:

```powershell
docker compose -f docker\docker-compose.yml run --rm backend python /app/scripts/build_s101_catalogue_db_rag.py --output /app/outputs/rag/s101_catalogue_db_chunks.jsonl
```

Resume embeddings and upsert:

```powershell
docker compose -f docker\docker-compose.yml run --rm backend python -u /app/scripts/build_document_rag_chunks.py --input /app/outputs/rag/s101_catalogue_db_chunks.jsonl --output /app/outputs/rag/s101_catalogue_db_embeddings.jsonl --upsert --resume
```

## Key Documentation

| Document | Purpose |
|---|---|
| `docs/20-continuation-handoff.md` | Current handoff, runtime state, and next actions |
| `docs/21-current-architecture-db-embedding.md` | Current architecture, DB, projection, and embedding baseline |
| `docs/22-s101-spatial-reliability-accident-relations.md` | Valid geometry and accident relation design |
| `docs/23-rag-embedding-dataset-review.md` | Dataset review and embedding scope |
| `docs/24-rag-remaining-development-plan.md` | Remaining RAG and GeoLLM development plan |

## Completion Criteria For S-101 2.0 RAG

- `knowledge.document_chunks` contains at least 1,869 S-101 2.0 rows.
- All S-101 core rows have non-null 1024-dimensional embeddings.
- A pgvector index exists for vector search.
- RAG retrieval is filtered to S-101 2.0 metadata.
- GeoLLM answers include provenance such as `source_file`, `section`, and `source_id`.
- Accident/S-101 answers include spatial relation evidence from `serving.accident_s101_relation_current`.
