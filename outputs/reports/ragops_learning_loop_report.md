# RAGOps/LLMOps Learning Loop Report

- generated_at: `2026-09-18T01:07:27.598252+00:00`
- status: `OK`
- failed_queries_collected: `72`
- labelled_issues: `72`
- improvement_candidates: `9`
- fine_tuning_candidates: `8`

## Stage Counts

- `3.registry_capability_kg_improvement`: `55`
- `4.embedding_regeneration`: `12`
- `6.benchmark_regression`: `3`
- `2.error_labeling_and_slot_fix`: `2`

## Label Counts

- `evidence.quality_metrics_missing`: `22`
- `execution.readiness`: `16`
- `kg.low_similarity`: `13`
- `evidence.low_or_missing`: `12`
- `intent.routing`: `4`
- `quality.low_estimated_accuracy`: `2`
- `normalization.encoding`: `1`
- `slot.spatial_relation_or_anchor`: `1`
- `output.map_table_evidence_consistency`: `1`

## Command Results

- `capability_embedding_regeneration_and_upsert`: `OK`
- `document_chunk_pgvector_upsert`: `OK`
- `dataset_embedding_live_validation`: `OK`
- `benchmark_regression`: `OK`
- `benchmark_failure_analysis`: `OK`

## Fine-Tuning Gate

Fine-tuning candidates were generated only as `NEEDS_REVIEW` records.
No model training job is executed by this loop.
Authority-sensitive facts must remain in RAG/KG/Registry/serving tables.
