# 24. Remaining RAG Development Plan

Date: 2026-09-11

This plan starts from the current S-101 2.0 baseline and lists the remaining work needed for a complete GeoLLM RAG path.

## 1. Current State

```text
S-101 core chunk target                  | 1,869
outputs/rag/s101_catalogue_db_embeddings | 1,333 rows generated
knowledge.document_chunks                | 605 rows loaded
DB rows with non-null embedding           | 605 rows
```

The embedding file is ahead of the database. The DB will remain partial until the embedding job completes and performs the final upsert.

Currently loaded source groups:

```text
gbhd_s101_20_accident_relation_profile
gbhd_s101_20_db_feature_profile
gbhd_s101_20_db_text_values
gbhd_s101_20_valid_geometry_profile
s101_attribute_catalogue_v2_xml
s101_feature_catalogue_v2_xml
```

Source groups still expected in the final DB load:

```text
s101_product_specification_2_0_pdf
s101_dceg_2_0_pdf
s101_portrayal_catalogue_2_0
s158_101_validation_checks_1_1
```

## 2. Step 1: Confirm Embedding Job Status

Check whether the long-running embedding container is still active:

```powershell
docker ps --filter ancestor=docker-backend --format "table {{.ID}}\t{{.Status}}\t{{.Command}}"
```

Check generated embedding rows:

```powershell
(Get-Content -Path outputs\rag\s101_catalogue_db_embeddings.jsonl).Count
```

Check DB upsert state:

```powershell
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -c "
select count(*) total,
       count(*) filter (where embedding is not null) embedded
from knowledge.document_chunks
where metadata @> '{\"product_id\":\"S-101\",\"version\":\"2.0.0\",\"product_specification\":\"INT.IHO.S-101.2.0\"}'::jsonb;
"
```

Decision rule:

```text
embedding file rows = 1,869 and DB rows = 1,869 -> embedding/upsert complete
embedding file rows = 1,869 and DB rows < 1,869 -> rerun upsert only
embedding file rows < 1,869 and no job running -> resume embedding
```

## 3. Step 2: Complete S-101 Core Embedding

Preferred resume command:

```powershell
docker compose -f docker\docker-compose.yml run --rm backend python -u /app/scripts/build_document_rag_chunks.py --input /app/outputs/rag/s101_catalogue_db_chunks.jsonl --output /app/outputs/rag/s101_catalogue_db_embeddings.jsonl --upsert --resume
```

Alternative full S-101 builder path:

```powershell
docker compose -f docker\docker-compose.yml run --rm backend python -u /app/scripts/build_s101_catalogue_db_rag.py --dataset-root /app/Dataset --embed --upsert --replace-source
```

## 4. Step 3: Verify Retrieval

Minimum smoke-test questions:

```text
DepthArea definition
Obstruction attribute profile
Wreck portrayal
S-101 validation check
Accident relation with S-101 feature
```

Pass conditions:

- Returned chunks contain `product_id = S-101`.
- Returned chunks contain `version = 2.0.0`.
- Returned chunks contain `product_specification = INT.IHO.S-101.2.0`.
- Results include useful provenance fields.
- S-101 1.0 or unrelated sources are not returned when the S-101 2.0 filter is active.

## 5. Step 4: Wire RAG Evidence Into GeoLLM Answers

Required answer contract:

```text
answer_text
spatial_result_summary when applicable
rag_evidence[]
  source_id
  source_file
  section
  document_type
  chunk_id
accident_relation_evidence[] when applicable
```

The model answer should separate three evidence types:

| Evidence type | Source |
|---|---|
| S-101 standard/catalogue evidence | `knowledge.document_chunks` |
| Spatial feature evidence | `projection.s101_feature_valid` |
| Accident relation evidence | `serving.accident_s101_relation_current` |

## 6. Step 5: Add Quality Gates

Add automated checks for:

- S-101 metadata filter is always applied for S-101 RAG calls.
- Top-k retrieval returns at least one expected source for known smoke-test prompts.
- Every generated answer includes provenance when RAG was used.
- Accident relation answers include relation distance/type evidence.
- No invalid geometry is exposed by the serving layer.

## 7. Step 6: Expand After S-101 Core Is Stable

Only after the S-101 2.0 RAG path passes the completion gate, expand in this order:

1. S-100 foundation documents and S-158-100 validation context.
2. Safety/legal context such as SOLAS and local maritime rules.
3. Accident statistics and terminology dictionaries.
4. External spatial layer metadata from ZIP datasets.
5. AIS/V-PASS metadata and analytic summaries.

Raw geometry and high-volume time-series rows should not be embedded directly. Store them in spatial/analytic tables and embed only metadata, schema, descriptions, and summaries.

## 8. Completion Gate

S-101 RAG is complete when:

```text
knowledge.document_chunks S-101 2.0 rows >= 1,869
null embeddings = 0
pgvector index exists
S-101 2.0 metadata filter smoke test passes
GeoLLM answer includes RAG provenance
Accident-S101 answer includes relation evidence
```
