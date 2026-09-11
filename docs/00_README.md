# Documentation Index

This index reflects the current S-101 2.0 development baseline.

## Current Baseline

| Item | Value |
|---|---|
| Primary database | `gbhd_s101` |
| Runtime target | `INT.IHO.S-101.2.0` |
| Catalogue version | `2.0.0` |
| Spatial serving layer | `projection.s101_feature_valid` |
| Accident relation layer | `serving.accident_s101_relation_current` |
| RAG table | `knowledge.document_chunks` |
| Embedding model | Ollama `bge-m3`, 1024 dimensions |

## Current Work Documents

| Document | Purpose |
|---|---|
| `20-continuation-handoff.md` | Handoff state, runtime facts, and immediate next actions |
| `21-current-architecture-db-embedding.md` | Current architecture, DB, projection, and embedding baseline |
| `22-s101-spatial-reliability-accident-relations.md` | S-101 valid geometry and accident relation layer |
| `23-rag-embedding-dataset-review.md` | Dataset review and S-101 2.0 embedding scope |
| `24-rag-remaining-development-plan.md` | Remaining RAG and GeoLLM completion plan |

## Platform Architecture

| Document | Purpose |
|---|---|
| `00-current-system-analysis.md` | Earlier system analysis |
| `01-platform-requirements.md` | Platform requirements |
| `02-platform-architecture.md` | Platform architecture |
| `03-service-boundaries.md` | Service boundaries |
| `06-event-contract.md` | Event contract |
| `07-orchestrator-state-machine.md` | Orchestrator state machine |
| `08-registry-design.md` | Registry design |
| `09-map-agent-integration.md` | Map-agent integration |
| `10-validation-and-hitl.md` | Validation and HITL |
| `11-data-model-and-erd.md` | Data model and ERD |
| `12-api-specification.md` | API specification |
| `13-sequence-diagrams.md` | Sequence diagrams |
| `14-security-architecture.md` | Security architecture |
| `15-implementation-plan.md` | Implementation plan |
| `16-test-plan.md` | Test plan |
| `17-risk-and-technical-debt.md` | Risk and technical debt |

## S-101 And RAG Notes

| Document | Purpose |
|---|---|
| `19-s101-catalogue-db-rag.md` | S-101 catalogue and DB RAG notes |
| `18-radius-hazard-route.md` | Radius and hazard route notes |
| `semantic_routing_caching.md` | Semantic routing and caching notes |

## Legacy Natural-Language Spatial Query Notes

These documents remain useful for natural-language-to-spatial-query design, but they predate the current S-101 2.0 runtime baseline.

| Document | Purpose |
|---|---|
| `01_schema_registry.md` | Schema registry rules |
| `02_query_normalization_rules.md` | Query normalization rules |
| `03_marine_concept_dictionary.md` | Marine concept dictionary |
| `04_place_resolution_rules.md` | Place resolution rules |
| `05_intent_agent_routing_rules.md` | Intent and agent routing |
| `06_query_plan_sql_compiler.md` | Query plan and SQL compiler |
| `07_error_codes_tests.md` | Error codes and tests |

## Current Work Queue

1. Finish S-101 core embedding generation to 1,869 chunks.
2. Upsert all S-101 2.0 chunks into `knowledge.document_chunks`.
3. Verify S-101 2.0 metadata filtering and pgvector search.
4. Connect RAG provenance to GeoLLM spatial and accident-relation answers.
5. Add external spatial ZIP metadata ingestion only after S-101 core RAG is stable.
