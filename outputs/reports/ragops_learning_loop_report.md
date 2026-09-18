# RAGOps/LLMOps Learning Loop Report

- generated_at: `2026-09-18T03:34:31.918723+00:00`
- status: `OK`
- failed_queries_collected: `78`
- labelled_issues: `78`
- improvement_candidates: `9`
- fine_tuning_candidates: `8`
- rejected_fine_tuning_candidates: `1`

## Stage Counts

- `3.registry_capability_kg_improvement`: `59`
- `4.embedding_regeneration`: `13`
- `2.error_labeling_and_slot_fix`: `3`
- `6.benchmark_regression`: `3`

## Label Counts

- `evidence.quality_metrics_missing`: `23`
- `execution.readiness`: `18`
- `kg.low_similarity`: `14`
- `evidence.low_or_missing`: `13`
- `intent.routing`: `4`
- `quality.low_estimated_accuracy`: `2`
- `slot.spatial_relation_or_anchor`: `2`
- `normalization.encoding`: `1`
- `output.map_table_evidence_consistency`: `1`

## Command Results

- `document_chunk_pgvector_upsert`: `OK`
- `dataset_embedding_live_validation`: `OK`

## Fine-Tuning Gate

Fine-tuning candidates were generated only as `REVIEW_ELIGIBLE` records.
No model training job is executed by this loop.
Authority-sensitive facts must remain in RAG/KG/Registry/serving tables.
