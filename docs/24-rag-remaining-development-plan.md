# 24. RAG Embedding Current State and Remaining Work

Date: 2026-09-16

This document records the current GeoLLM RAG embedding baseline after the Dataset coverage pass.

Related execution-flow note: `docs/execution_contract/094_query_quality_fast_path_learning.md`
explains how query intent, KG/RAG evidence similarity, fast path routing, and
estimated accuracy are exposed for continuous review and learning.
Candidate-first orchestration note: `docs/execution_contract/095_candidate_first_query_orchestration.md`
defines the migration from manual fast-path discovery to broad route
classification, resolver/tool candidate discovery, KG/Registry verification, and
verified-only execution.
Implementation sequence: `docs/execution_contract/096_candidate_first_implementation_sequence.md`
tracks the dry-run broker, pgvector capability index, verification gate, tool
graph planner, and fast-path replacement order.

## 1. Current State

```text
knowledge.document_chunks total rows       | 8,402
rows with non-null embedding               | 8,402
null embeddings                            | 0
embedding model                            | bge-m3
embedding dimension                        | 1,024
live database                              | gbhd_s101
```

The previous partial S-101 state has been superseded. S-101 2.0 core rows are loaded with embeddings, and Dataset supplemental metadata/doc chunks have been merged into the same live pgvector table.

Current live counts by major group:

```text
law                                      | 3,922
S-101 2.0 related rows                   | 2,907
dataset_profile                          | 108
supplemental_document                     | 21
accident_data                            | 29
```

## 2. Dataset Coverage Pass

The Dataset coverage pass classified 154 files:

```text
already embedded files                   | 23
supplemental chunks generated             | 129
supplemental embeddings generated          | 129
supplemental rows merged into live DB      | 129
```

Artifacts:

```text
outputs/reports/dataset_embedding_coverage.md
outputs/reports/dataset_embedding_coverage.json
outputs/rag/dataset_supplemental_chunks.jsonl
outputs/rag/dataset_supplemental_embeddings.jsonl
outputs/reports/dataset_embedding_validation.md
```

Policy applied:

- Core S-100/S-101/S-104/S-111/S-124/S-158 and law/accident sources are treated as already embedded.
- Spatial ZIP/CSV geometry is not embedded as raw rows; only layer metadata is embedded.
- AIS/V-PASS raw/high-volume rows are not embedded; traffic is queried through analytical layers, while Dataset source metadata is embedded.
- Large supplemental PDFs are represented as metadata profiles unless promoted to a dedicated full-text ingestion task.
- Older S-101 1.1.0 catalogue material is excluded from the current S-101 2.0 runtime baseline.

## 3. Verification

Validation command:

```powershell
docker exec geollm_backend python /app/scripts/verify_dataset_embedding_coverage.py
```

Validation result:

```text
status                         | OK
coverage_files                 | 154
supplemental_chunks            | 129
supplemental_embeddings         | 129
live_total                     | 8,402
live_null_embeddings            | 0
live_dataset_supplemental_rows  | 129
```

Retrieval smoke:

```text
query                          | AIS 위치정보 통계 데이터셋
filter                         | document_type = dataset_profile
top results                    | AIS주요통항로분석, AIS주요통항로분석, AIS항로분석
```

## 4. Remaining Work

1. Promote selected large supplemental PDFs to full-text ingestion only when a product requirement needs exact citation from that source.
2. Add source-specific tests for SOLAS, accident casebooks, marine gazetteer metadata, and AIS/V-PASS metadata retrieval.
3. Keep S-101 retrieval filtered to `product_id=S-101`, `version=2.0.0`, and `product_specification=INT.IHO.S-101.2.0` for chart-feature evidence.
4. Keep raw AIS/V-PASS and raw geometry out of document embeddings; use dynamic traffic/spatial tables for quantitative analysis.
5. Extend the UI answer provenance view so Dataset supplemental hits show `source_file`, `document_type`, `chunk_id`, and similarity.

## 5. Completion Gate

RAG embedding is considered operational when:

```text
knowledge.document_chunks null embeddings = 0
Dataset coverage validation passes
S-101 2.0 smoke retrieval passes under metadata filter
Dataset supplemental retrieval passes for non-S-101 metadata queries
GeoLLM answers include source provenance and similarity
```
