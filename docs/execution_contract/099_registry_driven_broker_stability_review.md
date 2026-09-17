# Registry-Driven Broker Stability Review

Date: 2026-09-17

## Purpose

The query path must avoid rule explosion. A query should be classified into broad routes first, then Resolver/Dictionary/Tool/Dataset/Ontology candidates should be retrieved, verified, and executed only when the registry and KG contract say the path is ready.

## Current Policy

1. Deterministic signals and registry lexical signals classify broad routes.
2. `knowledge.capability_embeddings` provides pgvector top-k candidate retrieval.
3. `data/capability_registry.yaml` supplements pgvector candidates when a deterministic/lexical signal matches a registered capability.
4. Registry/KG references remain the authority gate. pgvector similarity is candidate retrieval only.
5. Ollama is reserved for ambiguity resolution, not for overriding authority.
6. Execution happens only after verified capability readiness.

## Why This Was Changed

The accident lookup fast path worked, but the trace could still show place or gazetteer candidates above the accident capability because pgvector ranked semantically similar candidates before registry signal matches. That made the system harder to explain and risked future expansion regressions.

The broker now merges pgvector and registry-signal candidates. If the same capability appears from both sources, matched signals and the higher score are retained. Signal-backed candidates sort above otherwise similar candidates, so the trace explains why a path was selected.

## Verified Example

Query:

`창원 정비불량 사건을 찾아줘`

Observed API result:

- status: `COMPLETED`
- fast_path: `accident_event_structured_lookup`
- total_count: `59`
- returned_count: `59`
- terms: `창원`, `정비불량`
- top capability candidates:
  - `resolver.accident_event_terms`
  - `tool.accident_event_lookup`
  - `dataset.accident_events`

## Expansion Contract

When adding a new domain path:

1. Add lexical signals to `data/capability_registry.yaml`.
2. Register resolver/tool/dataset/ontology capabilities with deterministic hints.
3. Generate capability embeddings with `scripts/build_capability_embeddings.py`.
4. Keep factual/geometry authority in registry, KG, and serving tables.
5. Add a broker regression test that proves the route and executable capability become `verified_ready`.
6. Add a live API smoke result to the relevant execution-contract document.

## Known Remaining Work

- The older static route hint tables in `query_candidate_broker.py` still exist for compatibility. New domains should prefer registry lexical signals.
- Some PowerShell output renders UTF-8 Korean as mojibake; container-side Python output confirms the stored UTF-8 content.
- `pytest` is not installed in the current backend container, so unit tests were added but manual Python smoke checks were used for this run.
