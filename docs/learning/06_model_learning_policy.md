# Model Learning Policy

Model learning and fine-tuning are last-resort candidates.

The normal improvement path is RAGOps/LLMOps:

1. collect failed queries
2. label intent, slot, tool, and evidence errors
3. improve registry, capability, and KG candidates
4. regenerate embeddings
5. upsert pgvector
6. run benchmark regression

Fine-tuning may be considered only after those six steps fail to fix a repeated, reviewed behavior problem.

The benchmark loop may create:

- `outputs/model_learning/training_candidate_report.md`
- `outputs/model_learning/training_dataset_candidate.jsonl`

It must not automatically run fine-tuning or alter production model weights.

Training candidates must exclude benchmark test leakage.

Fine-tuning must not be used to add or correct factual authority. Coordinates, counts, legal citations, feature definitions, dataset provenance, and execution readiness must remain controlled by RAG evidence, KG, registries, serving tables, and `ExecutionValidator`.

Detailed operating rules are maintained in `docs/execution_contract/103_ragops_llmops_retraining_loop.md`.
