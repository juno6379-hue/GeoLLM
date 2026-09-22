# Marine GeoLLM Seed Expansion Prompt v1.0

Generate registry-grounded candidate cases from an explicitly APPROVED golden seed.
Output JSONL conforming to `training.models.TrainingCase` and the generated JSON Schema.

## Inputs

- One APPROVED seed, including `lineage` and `registry_snapshot`
- Read-only snapshots of agent, tool, data, spatial-layer, query-template, derived-concept, ontology, and S-101 dictionaries
- A protected holdout fingerprint list
- Generation profile (`dry_run` or `full`)

## Rules

1. Never invent an ontology, registry, agent, tool, dataset, layer, query-template, feature-class, citation, coordinate, count, or dynamic result.
2. Copy the supplied registry snapshot into every candidate. Unknown references make the case `REVIEW_REQUIRED`; never create a missing registry entry.
3. Every output has `origin=synthetic_from_seed`, `review_status=CANDIDATE`, and the seed's ID in `lineage.parent_seed_id`.
4. Keep Feature Class, Feature Instance, Derived Concept, Dataset, Layer, Tool, Agent, and Document Chunk distinct.
5. Preserve slot provenance: `user_explicit`, `conversation_context`, `inferred_from_policy`, `resolved_from_registry`, or `not_provided`.
6. If a required slot is absent, set `execution_ready=false`, include a blocker, use `NOT_EXECUTED`, and ask only the necessary clarification.
7. Never put a dynamic reference answer in a case without a named frozen fixture and timestamp.
8. Hard negatives must be plausible and structured in `negative_constraints`, with the reason in `quality.review_notes`.
9. Do not emit a query matching or nearly matching the protected holdout. Keep a whole seed family in one split.
10. Definition requests such as `X란` or `X이란` are identified compositionally: morphology + dictionary existence + absence of temporal/spatial/execution slots. Do not create term-specific suffix exceptions.
11. Response-generation cases include actual fixture route/result/evidence inputs. An evidence requirement is not execution evidence.
12. Do not auto-approve generated data.

## Full profile per seed

- 5 semantic paraphrases
- 3 slot/value variations
- 3 hard negatives
- 2 ambiguity or missing-slot cases
- 2 conversational follow-ups
- 1 cross-domain case when supported

The dry-run profile may reduce counts but must exercise every applicable category.

## Pre-emission checks

- UTF-8 and Unicode normalization
- JSON Schema/Pydantic validation
- ontology and registry references
- S-101 feature-class membership
- tool → template → layer/data dependency chain
- required-slot/readiness consistency
- semantic preservation
- exact and near-duplicate leakage
- seed-family and conversation-family split isolation
- no fabricated dynamic claims

On failure, emit to quarantine as `REVIEW_REQUIRED` with machine-readable review notes; do not silently repair semantic labels.
