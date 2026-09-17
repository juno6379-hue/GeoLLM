# 23. RAG Embedding Dataset Review

Date: 2026-09-11

Update 2026-09-16: the S-101 2.0 core embedding target has been completed and merged into the live `gbhd_s101.knowledge.document_chunks` table. A Dataset supplemental coverage pass was also completed; see `docs/24-rag-remaining-development-plan.md` and `outputs/reports/dataset_embedding_validation.md` for the current counts.

This review defines what should be embedded for the S-101 2.0 GeoLLM baseline.

## 1. Decision

The first production RAG scope is `s101_core`. It should be completed before adding broader S-100 foundation material, Korean maritime law, accident statistics, or external spatial layer metadata.

The reason is practical: GeoLLM must first answer S-101 2.0 chart-feature questions with reliable source provenance and matching database evidence.

## 2. Required S-101 Core Sources

| Source group | Purpose | Status |
|---|---|---|
| `s101_feature_catalogue_v2_xml` | Feature names, codes, bindings, definitions | Loaded in DB |
| `s101_attribute_catalogue_v2_xml` | Attribute names, codes, definitions | Loaded in DB |
| `s101_product_specification_2_0_pdf` | Product rules and official specification text | Embedded file in progress |
| `s101_dceg_2_0_pdf` | Data classification and encoding guidance | Embedded file in progress |
| `s101_portrayal_catalogue_2_0` | Portrayal rules and symbolization context | Pending DB upsert |
| `s158_101_validation_checks_1_1` | S-101 validation checks | Pending DB upsert |
| `gbhd_s101_20_db_feature_profile` | Actual feature distribution in `gbhd_s101` | Loaded in DB |
| `gbhd_s101_20_db_text_values` | Important real DB text values | Loaded in DB |
| `gbhd_s101_20_valid_geometry_profile` | Valid geometry status | Loaded in DB |
| `gbhd_s101_20_accident_relation_profile` | Accident relation summary | Loaded in DB |

## 3. Current Checkpoint

```text
target chunk file: outputs/rag/s101_catalogue_db_chunks.jsonl
target chunks: 1,869
partial embedding file: outputs/rag/s101_catalogue_db_embeddings.jsonl
partial embedding rows: 1,333
loaded DB rows: 605
loaded DB rows with embedding: 605
embedding model: bge-m3
embedding dimension: 1024
```

The DB currently contains only the rows from the earlier successful partial upsert. The embedding output file has progressed further than the DB. The next successful `--upsert` completion should bring `knowledge.document_chunks` to the full S-101 2.0 target.

## 4. Metadata Contract

Every S-101 2.0 chunk must include:

```json
{
  "product_id": "S-101",
  "version": "2.0.0",
  "product_specification": "INT.IHO.S-101.2.0"
}
```

Recommended additional metadata:

```text
source_id
source_file
document_type
section
chunk_id
feature_code or attribute_code when applicable
```

## 5. Excluded For Now

These datasets are useful but should be added after `s101_core` is complete and tested:

| Dataset group | Reason to defer |
|---|---|
| S-100 foundation documents | Broader context, but not required for first S-101 2.0 evidence path |
| SOLAS / maritime law / policy documents | Different citation and legal provenance requirements |
| Accident statistics beyond normalized event/relation profile | Needs separate analytical schema and temporal aggregation |
| External spatial ZIP geometry | Geometry should stay in spatial DB; only metadata should be embedded later |
| AIS/V-PASS raw tracks | High-volume time-series data should be queried analytically, not embedded as raw rows |

## 6. Verification Queries

Source-group count:

```sql
SELECT source_id, COUNT(*) total,
       COUNT(*) FILTER (WHERE embedding IS NULL) null_embeddings
FROM knowledge.document_chunks
WHERE metadata @> '{"product_id":"S-101","version":"2.0.0","product_specification":"INT.IHO.S-101.2.0"}'::jsonb
GROUP BY source_id
ORDER BY source_id;
```

Embedding completeness:

```sql
SELECT COUNT(*) total,
       COUNT(*) FILTER (WHERE embedding IS NULL) null_embeddings
FROM knowledge.document_chunks
WHERE metadata @> '{"product_id":"S-101","version":"2.0.0","product_specification":"INT.IHO.S-101.2.0"}'::jsonb;
```

## 7. Next Step

Resume or allow the current embedding job to finish, then verify:

```text
S-101 2.0 rows >= 1,869
null_embeddings = 0
all required source groups present
RAG retrieval returns S-101 2.0 chunks only
```
