# Candidate-First Orchestration Implementation Sequence

작성일: 2026-09-17

## 목표

`095_candidate_first_query_orchestration.md`의 정책을 실제 개발 순서로 분해한다.

핵심 변경 방향:

```text
manual fast path rules
-> dry-run multi-label candidate trace
-> pgvector capability index
-> KG/Registry verifier
-> Tool Graph planner
-> verified-only execution
```

## Phase 1. Dry-Run Candidate Broker

상태: 시작됨

목표:

- 기존 fast path 실행 결과를 바꾸지 않는다.
- 모든 질의에 대해 candidate-first 판단 trace를 생성한다.
- multi-label route 후보, capability 후보, verification 후보를 관측한다.

구현 항목:

- `data/capability_registry.yaml`
  - Resolver description
  - Agent description
  - Tool description
  - Dataset metadata
  - Ontology class description
  - Marine terms
  - Feature class description
- `services/orchestrator/query_candidate_broker.py`
  - deterministic signal scan
  - multi-label route candidate generation
  - registry-backed semantic capability candidate retrieval fallback
  - authority/registry presence verification
  - Tool Graph candidate sketch
  - Ollama ambiguity-needed flag
- `services/orchestrator/state.py`
  - `candidate_trace` state field
- `services/orchestrator/graph.py`
  - parse intent 단계에서 broker dry-run 실행
  - map report 결과에 `orchestrator_v2.candidate_trace` 연결
- `services/orchestrator/router.py`
  - fast path 종료 응답에도 state의 candidate trace를 stream payload에 주입

성공 기준:

- `독도를 찾아줘`에서 `PLACE_LOOKUP` 후보가 유지된다.
- `독도 3km 이내 위험객체`에서 `SPATIAL_ANALYSIS` primary와 `PLACE_LOOKUP` supporting 후보가 함께 나온다.
- `gazetteer 적재 근거`에서 `DATASET_PROVENANCE` 후보가 나온다.
- `최근 1년 통항량`에서 `TRAFFIC_ANALYSIS` 후보가 나온다.
- 기존 fast path 결과가 바뀌지 않는다.

## Phase 2. pgvector Capability Index

목표:

- `knowledge.capability_embeddings`를 만들고 capability registry entries를 embedding한다.
- lexical fallback 대신 pgvector top-k retrieval을 사용한다.
- pgvector는 후보 생성 전용으로 제한한다.

권장 테이블:

```sql
create table if not exists knowledge.capability_embeddings (
    id text primary key,
    object_type text not null,
    object_id text not null,
    label text not null,
    description text not null,
    route_tags text[] not null default '{}',
    input_slots text[] not null default '{}',
    output_slots text[] not null default '{}',
    authority_ref text,
    registry_ref text,
    metadata jsonb not null default '{}',
    embedding vector(1024),
    updated_at timestamptz not null default now()
);
```

구현 항목:

- capability registry -> JSONL chunk generator
- embedding generator
- upsert script
- retrieval adapter with metadata filters
- validation report

성공 기준:

- Resolver/Agent/Tool/Dataset/Ontology/Term/Feature capability row가 모두 검색된다.
- route hint가 강한 경우 metadata filter가 적용된다.
- authority 없는 capability는 실행 후보가 되지 않는다.

## Phase 3. KG/Registry Verification Gate

목표:

- candidate score와 authority score를 분리한다.
- top-k 후보마다 accept/reject reason을 남긴다.

검증 항목:

- intent compatibility
- slot compatibility
- ontology/KG path
- registry authority
- data readiness
- tool readiness
- safety/no-fabrication rule

성공 기준:

- 후보가 버려진 이유를 응답 trace와 품질 로그에서 볼 수 있다.
- `gazetteer 근거`가 place lookup으로 실행되지 않는다.
- `obstruction 정의`가 spatial object search로 실행되지 않는다.

## Phase 4. Tool Graph Planner

목표:

- 복합 tool 관계를 graph로 관리한다.
- supporting route가 primary route의 slot을 채우게 한다.

예:

```text
place_resolver
-> spatial_radius_builder
-> hazard_feature_resolver
-> s101_spatial_query
-> portrayal_resolver
-> map_layer_renderer
-> evidence_bundle_builder
-> answer_composer
```

성공 기준:

- 각 tool node의 requires/produces가 trace에 남는다.
- helper geometry와 분석 object가 분리된다.
- 검색 범위 polygon이 object click detail을 가로채지 않는다.

## Phase 5. Fast Path Replacement

목표:

- `_looks_like_*` 조건을 최종 route 결정자가 아니라 candidate generator로 낮춘다.
- 기존 direct fast path를 broker + verifier + tool graph 실행으로 교체한다.

전환 원칙:

- 한 번에 전부 교체하지 않는다.
- place lookup, dataset provenance, standard RAG, traffic, spatial radius 순서로 전환한다.
- 각 전환마다 regression query set을 추가한다.

성공 기준:

- manual rule 수가 줄어든다.
- 새 resolver/tool 추가 시 route code 변경이 최소화된다.
- 오분류는 `wrong_broad_route`, `wrong_candidate_selected`, `kg_path_missing` 등으로 분해 기록된다.

## Phase 6. Ollama Ambiguity Resolver

목표:

- verification 이후에도 애매한 경우에만 Ollama를 호출한다.
- Ollama는 최종 실행을 결정하지 않는다.

호출 조건:

- route 후보 점수 차이가 작다.
- deterministic signal과 semantic retrieval이 충돌한다.
- 필수 slot이 애매하다.
- clarification question이 필요하다.

성공 기준:

- verified-ready 후보가 하나면 Ollama를 호출하지 않는다.
- Ollama 결과는 다시 KG/Registry verification을 통과해야 한다.

## Regression Query Set

```text
독도를 찾아줘
독도 3km 이내 위험객체를 찾아줘
부산항 입구 3km 이내 위험객체를 찾아줘
해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘
Obstruction 정의와 S-101 근거를 알려줘
Obstruction 객체를 지도에 표시해줘
부산항 입구 최근 1년 AIS/V-PASS 통항량을 분석해줘
통항량 데이터 출처와 기간을 설명해줘
주황색 폴리곤은 뭐야
검색 범위 정보를 보여줘
```

## 현재 주의점

- Phase 1은 dry-run이므로 실제 route 선택을 바꾸지 않는다.
- capability registry similarity는 authority가 아니다.
- pgvector index가 생기기 전까지 broker는 registry lexical fallback으로 동작한다.
- fast path 결과와 broker trace가 다르면 품질 로그 검토 대상으로 삼는다.

