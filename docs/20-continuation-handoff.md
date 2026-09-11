# 20. Continuation Handoff

Date: 2026-09-11

This handoff captures the current GeoLLM development state.

## 1. Runtime Target

The active target is S-101 Edition 2.0:

```text
database: gbhd_s101
product_specification: INT.IHO.S-101.2.0
catalogue_version: 2.0.0
postgis_container: an_geollm_postgis
embedding_model: bge-m3
```

`gbhd_s101` may contain more than one S-101 source generation. All current runtime logic must use the S-101 2.0 projection and metadata filter.

## 2. Runtime Objects

| Object | Current role |
|---|---|
| `projection.s101_feature_current` | Current S-101 2.0 feature projection |
| `projection.s101_feature_valid` | Geometry-repaired serving layer |
| `projection.s101_feature_valid_anchor` | Anchor-point helper layer |
| `serving.accident_events` | Normalized accident event points |
| `serving.accident_s101_relation_current` | Materialized accident-to-S-101 relations |
| `knowledge.document_chunks` | RAG chunks and pgvector embeddings |

Verified spatial counts:

```text
projection.s101_feature_current          | 787,102 rows, invalid geometry 0
projection.s101_feature_valid            | 787,102 rows, invalid geometry 0
projection.s101_feature_valid_anchor     | 787,102 rows
serving.accident_events                  | 4,636 rows
serving.accident_s101_relation_current   | 23,180 rows
```

## 3. RAG State

Current checkpoint:

```text
S-101 core target chunks: 1,869
partial embedding rows: 1,333
DB loaded rows: 605
DB loaded rows with embedding: 605
```

The next operator should first determine whether the embedding job is still running. If it has completed, verify the DB upsert. If it stopped before 1,869 rows, resume it.

## 4. Immediate Next Commands

Check embedding container:

```powershell
docker ps --filter ancestor=docker-backend --format "table {{.ID}}\t{{.Status}}\t{{.Command}}"
```

Check embedding file progress:

```powershell
(Get-Content -Path outputs\rag\s101_catalogue_db_embeddings.jsonl).Count
```

Check DB RAG state:

```powershell
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -c "
select count(*) total,
       count(*) filter (where embedding is not null) embedded
from knowledge.document_chunks
where metadata @> '{\"product_id\":\"S-101\",\"version\":\"2.0.0\",\"product_specification\":\"INT.IHO.S-101.2.0\"}'::jsonb;
"
```

Resume embedding/upsert if required:

```powershell
docker compose -f docker\docker-compose.yml run --rm backend python -u /app/scripts/build_document_rag_chunks.py --input /app/outputs/rag/s101_catalogue_db_chunks.jsonl --output /app/outputs/rag/s101_catalogue_db_embeddings.jsonl --upsert --resume
```

## 5. Completion Criteria

Before marking S-101 RAG complete:

- `knowledge.document_chunks` has at least 1,869 S-101 2.0 rows.
- Every S-101 2.0 row has a non-null embedding.
- Retrieval applies S-101 2.0 metadata filters.
- Smoke tests return catalogue/product/DCEG/portrayal/validation sources.
- GeoLLM responses include source provenance.
- Accident answers include relation evidence from `serving.accident_s101_relation_current`.

## 6. Git Notes

The current repository target is:

```text
remote: https://github.com/juno6379-hue/GeoLLM
branch: main
```

Do not add generated embedding files or local report artifacts unless explicitly requested.
