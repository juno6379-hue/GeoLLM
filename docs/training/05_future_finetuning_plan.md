# Future Fine-tuning Plan

No model weights, embeddings, registries, or ontology verification states are changed by this work. Before fine-tuning: expand domain-approved seeds, measure class balance and semantic deduplication, freeze validation/test/holdout families, define per-view metrics, and run baseline evaluation against the existing deterministic orchestrator.

FastPath Router can use multiclass/multilabel evaluation. Capability Retriever needs recall@k and hard-negative ranking metrics. Planner and Execution Validator require exact structured-contract checks. Response Generator requires groundedness and evidence-attribution evaluation against frozen fixtures.
