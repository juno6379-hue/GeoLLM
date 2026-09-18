# RAGOps, LLMOps, and Fine-Tuning Work Loop

Date: 2026-09-18

## Purpose

GeoLLM must improve from failed queries without creating rule explosion or letting unverified semantic candidates become executable facts. The learning loop is therefore split into two tracks:

- RAGOps/LLMOps loop: collect failures, label them, improve registry/KG/capability metadata, regenerate embeddings, upsert pgvector, and run benchmark regression.
- Fine-tuning loop: only after repeated, reviewed, non-registry-fixable failures remain, create a training candidate dataset. Fine-tuning must not run automatically.

The production rule remains:

`Capability Retriever -> candidate recall`
`Ontology/KG Validator -> precision gate`
`QueryExecutionContext -> confirmed values separated from candidates`
`ExecutionValidator -> execute only when required slots, data, and tools are ready`

pgvector is a candidate retrieval mechanism, not a source of authority. Registry, KG, serving tables, and evidence provenance remain authoritative.

## Korean Operating Summary

운영 개선은 다음 순서로 진행한다.

1. 실패 질의 수집
2. intent / slot / tool / evidence 오류 유형 라벨링
3. registry / capability / KG 후보 보강
4. embedding 재생성
5. pgvector upsert
6. benchmark regression 실행

각 단계는 반드시 오류 유형과 처리방안을 남긴다. 실패 질의가 반복되더라도 바로 fine-tuning으로 가지 않는다. 먼저 registry, KG, resolver, tool readiness, evidence, embedding, benchmark 문제인지 확인한다.

fine-tuning은 마지막 단계다. 모델이 더 잘 말하도록 만드는 목적에는 쓸 수 있지만, 좌표, 건수, 기간, 법령 조항, S-101 feature 정의, 데이터셋 근거 같은 authoritative fact를 모델 weight에 학습시키는 용도로 쓰면 안 된다. 그런 정보는 RAG, KG, Registry, serving table, EvidenceBundle에서 관리한다.

단계별 책임은 다음과 같다.

| 단계 | 목적 | 산출물 |
| --- | --- | --- |
| 1. 실패 질의 수집 | 실제 문제를 누락 없이 backlog화 | `query_quality_issues.jsonl`, 로그, smoke failure |
| 2. 오류 라벨링 | 의도/슬롯/도구/근거/지도/UI/성능 문제 분리 | reviewed issue label |
| 3. 후보 보강 | 하드코딩 대신 registry/KG 중심으로 확장 | registry diff, KG candidate/verified edge |
| 4. embedding 재생성 | 변경된 capability/document/dataset을 검색 가능하게 갱신 | embedding JSONL, validation report |
| 5. pgvector upsert | live retrieval store 갱신 | `knowledge.capability_embeddings`, `knowledge.document_chunks` |
| 6. benchmark regression | 기존 기능 회귀와 hallucination 방지 | benchmark report, smoke result |
| FT. fine-tuning 후보화 | 반복된 언어/추론 오류만 별도 후보화 | training candidate report |

## Operating Loop

### 1. Failed Query Collection

Collect failed or suspicious queries from:

- `data/feedback/query_quality_issues.jsonl`
- backend warning/error logs
- UI-reported map/table/evidence mismatches
- benchmark failures
- smoke-test failures

Required record fields:

- original query
- normalized query, if available
- task_id, user_id, organization_id, when available
- route plan
- candidate capabilities
- selected capability
- rejected candidates
- quality metrics
- evidence bundle summary
- map/table/result object IDs
- final status and error code

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| Missing `task_id`, `user_id`, or `organization_id` | API validation failure blocks diagnosis | create request defaults at API boundary and log missing caller context |
| Query stays in `RECEIVED` or `CONTEXT_RESOLVED` | user sees a stuck task | add timeout/error transition and capture last completed node |
| Wrong Korean normalization or mojibake in logs | wrong slot extraction or unreadable evidence | preserve UTF-8 end to end and store raw query plus normalized query |
| Map, table, and evidence object lists differ | user cannot trust result | log canonical object IDs for every output surface |
| `quality_metrics` unavailable | no learning signal | emit `quality_unavailable` issue with reason and route context |
| User correction not stored | repeated failure | add the correction as a pending review item, not as an automatic rule |

### 2. Intent, Slot, Tool, and Evidence Error Labeling

Every collected issue must be labeled before changing runtime behavior.

Label dimensions:

- intent error: wrong broad route, missing multi-label route, over-specific route
- slot error: missing place, distance, period, target feature, dataset, or evidence domain
- tool error: wrong tool selected, unready tool executed, slow fallback used
- evidence error: no evidence, wrong evidence domain, low similarity, unsupported citation
- output error: map geometry mismatch, wrong detail popup, legend mismatch, summary mismatch
- performance error: timeout, slow startup, slow query, repeated vector-store initialization

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| `부근` treated as `derived_concept` | spatial relation pollutes concept graph | label as `slot.spatial_relation`, never as ontology concept |
| Empty `location_text` but spatial tool selected | unsafe execution | ExecutionValidator must block and ask clarification |
| S-101 catalogue noise becomes executable | wrong tool/path selected | keep catalogue candidates in candidate-only context until KG/Registry verification |
| Accident query routed to place lookup only | missed row-level accident evidence | add or tune multi-label route for place + accident history |
| Evidence query routed to legal no-evidence path | wrong answer domain | label evidence domain first: dataset provenance, standard, legal, accident, spatial |
| UI shows confidence as 100% without metrics | false trust | use quality metrics only; deterministic path still says estimated confidence |

### 3. Registry, Capability, and KG Candidate Improvement

Approved labels are converted into registry/KG changes. Do not add ad hoc route rules when a registry-driven capability can express the behavior.

Allowed changes:

- add lexical/deterministic signals to `data/capability_registry.yaml`
- add resolver/tool/dataset capability records
- add ontology class or relation candidates
- promote reviewed candidate edges to verified KG edges
- add dataset metadata and authority references
- add benchmark cases for the corrected behavior

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| Rule explosion in router code | brittle behavior | move signals to registry/capability descriptions |
| Candidate edge promoted without review | KG precision loss | require provenance and reviewer status before verified promotion |
| Resolver description too vague | poor pgvector retrieval | include inputs, outputs, authority table, blockers, and examples |
| Tool readiness not encoded | unready execution | add required slots, data readiness, timeout, and authority references |
| Dataset metadata missing period/geometry | wrong analysis window or map output | standardize metadata before embedding |
| Same concept duplicated across registries | inconsistent routing | add canonical ID and aliases instead of new primary nodes |

### 4. Embedding Regeneration

Regenerate embeddings after approved registry, dataset, document, or KG description changes.

Current embedding targets:

- `knowledge.capability_embeddings`
- `knowledge.document_chunks`
- dataset supplemental chunks under `outputs/rag`
- registry, resolver, tool, dataset, ontology, marine term, and feature descriptions

Required checks:

- chunk count equals embedding count
- embedding dimension equals model dimension
- null embedding count is zero
- source SHA/provenance is preserved
- Korean text is readable before and after embedding

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| chunk count and embedding count mismatch | partial retrieval index | fail the build and do not upsert |
| null embeddings | silent retrieval gaps | reject merge until regenerated |
| stale capability embedding after registry change | wrong candidate ranking | rebuild capability embeddings on every registry change |
| source hash missing | cannot explain evidence provenance | compute and store source SHA-256 |
| Korean text corrupted | wrong semantic retrieval | validate representative Korean smoke queries |
| large structured rows embedded directly | slow/noisy RAG | embed profile/sample metadata, keep rows in serving/spatial DB |

### 5. pgvector Upsert

Upsert regenerated embeddings into live pgvector tables only after validation.

Current live targets:

- `knowledge.capability_embeddings`
- `knowledge.document_chunks`

Upsert requirements:

- use stable IDs
- keep metadata JSONB
- keep source_id and source_sha256
- create or maintain HNSW indexes
- run `ANALYZE`
- report total rows and null embedding count

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| duplicate unstable IDs | retrieval duplicates | derive IDs from source, section, chunk index, and version |
| HNSW index missing | slow candidate retrieval | create vector cosine index after load |
| metadata not indexed | filters become slow | maintain GIN indexes for metadata and route tags |
| production table overwritten by bad batch | service regression | use staged validation before live upsert |
| capability pgvector used as authority | unsafe plan | broker must pass candidates to KG/Registry validator |
| old chunks not retired | stale evidence | use source version and superseded metadata |

### 6. Benchmark Regression

Every learning-loop change must run a benchmark regression before it is accepted.

Required benchmark groups:

- routing and multi-label intent
- slot extraction and correction
- KG/Registry authority gate
- ExecutionValidator blocking cases
- RAG evidence citation
- map/table/evidence consistency
- negative no-evidence cases
- performance and timeout smoke tests

Common errors and treatment:

| Error | Risk | Treatment |
| --- | --- | --- |
| only positive examples tested | hallucination not caught | include negative and ambiguous cases |
| benchmark contains training candidate answer text | leakage | exclude benchmark cases from fine-tuning data |
| no map consistency assertion | UI mismatch survives | assert same canonical object IDs across map/table/evidence |
| timeout not tested | slow fallback returns | add max latency and terminal status checks |
| no authority-gate test | pgvector candidates execute directly | assert unverified candidates remain candidate-only |
| regression result not stored | cannot audit learning | write report to `outputs/reports` and link from execution contract |

## Fine-Tuning Plan

Fine-tuning is a later-stage option, not the default improvement mechanism.

Fine-tuning may be considered only when all conditions are true:

1. The failure is repeated across reviewed user queries.
2. Registry/KG/capability metadata changes do not solve the issue.
3. RAG evidence exists and is authoritative.
4. The desired behavior is linguistic or reasoning style, not factual authority.
5. Benchmark regression shows no simpler deterministic fix.
6. A human reviewer approves the training candidate set.

Fine-tuning must not be used for:

- adding missing facts that belong in documents, datasets, KG, or registries
- correcting coordinates, counts, dates, or legal citations
- bypassing ExecutionValidator
- making unverified pgvector candidates executable
- replacing evidence retrieval

Fine-tuning work stages:

| Stage | Output | Gate |
| --- | --- | --- |
| FT-1 candidate extraction | `outputs/model_learning/training_dataset_candidate.jsonl` | only reviewed failure logs |
| FT-2 leakage check | `outputs/model_learning/training_candidate_report.md` | exclude benchmark and test answers |
| FT-3 safety/authority filter | filtered candidate dataset | no unsupported facts, no hidden coordinates/counts |
| FT-4 offline evaluation | eval report against baseline | must improve target class without route regressions |
| FT-5 shadow deployment | non-production model comparison | no production traffic override |
| FT-6 controlled promotion | release note and rollback plan | human approval required |

Fine-tuning error and treatment matrix:

| Error | Risk | Treatment |
| --- | --- | --- |
| training data includes hallucinated answer | model learns false authority | require evidence-backed labels only |
| benchmark leakage | fake improvement | remove any benchmark/test-derived answer text |
| fine-tune used for facts | stale or wrong facts | move facts to RAG/KG/registry instead |
| fine-tune overrides tool gate | unsafe execution | keep ExecutionValidator outside model control |
| no baseline comparison | unknown regression | run fixed eval set before and after |
| no rollback plan | production instability | keep old model and routing config available |

## Acceptance Criteria

A learning-loop change is complete only when:

- the original failed query has a labeled issue record
- the selected treatment is documented
- registry/KG/embedding changes have provenance
- pgvector upsert validation reports zero null embeddings
- benchmark regression passes
- at least one smoke query proves the corrected path
- fine-tuning, if proposed, remains a reviewed candidate and is not automatically executed

## Implemented Runner

The operational runner is:

```bash
python scripts/run_ragops_learning_loop.py
```

It performs the six RAGOps/LLMOps stages as executable work:

1. reads failed query sources from `data/feedback` and benchmark failure outputs
2. labels intent, slot, tool, evidence, output, and performance errors
3. writes registry/KG/capability improvement candidates for human review
4. regenerates capability embeddings with `scripts/build_capability_embeddings.py`
5. upserts capability/document embeddings into pgvector and validates live rows
6. runs benchmark regression and benchmark failure analysis

It also writes fine-tuning candidate artifacts without launching training:

- `outputs/model_learning/training_dataset_candidate.jsonl`
- `outputs/model_learning/training_candidate_report.md`

Main reports:

- `outputs/learning/ragops_failed_queries.jsonl`
- `outputs/learning/ragops_error_labels.jsonl`
- `outputs/learning/ragops_improvement_candidates.jsonl`
- `outputs/reports/ragops_learning_loop_report.json`
- `outputs/reports/ragops_learning_loop_report.md`

The runner is deliberately review-gated. Registry/KG candidates are not automatically promoted, and fine-tuning candidates are emitted as `NEEDS_REVIEW`.
