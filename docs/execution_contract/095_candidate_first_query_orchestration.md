# Candidate-First Query Orchestration Contract

작성일: 2026-09-17

## 목적

GeoLLM 질의 처리는 더 이상 개별 fast path 조건을 계속 추가하는 방식으로 확장하면 안 된다. 사용자는 같은 단어를 쓰더라도 서로 다른 실행 의도를 가질 수 있다.

예:

- "독도를 찾아줘"는 한국의 섬 위치를 찾는 place lookup이다.
- "독도 3km 이내 위험객체를 찾아줘"는 기준 지점 해석 후 공간 반경 분석이다.
- "해양지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘"는 지명 검색이 아니라 Dataset provenance 질의다.
- "Obstruction 정의와 S-101 근거를 알려줘"는 전자해도 객체 검색이 아니라 표준/카탈로그 문서 질의다.

따라서 실행 흐름은 다음 원칙을 따른다.

```text
질문을 먼저 큰 실행경로로 분류한다
-> 필요한 Resolver/Dictionary/Tool 후보만 생성한다
-> Ontology/KG와 Registry가 후보를 검증한다
-> 검증되고 준비된 후보만 실행한다
-> 실행/차단/오분류 결과를 학습 로그로 남긴다
```

## 문제 정의

현재 구현은 여러 `_looks_like_*` fast path가 직접 route를 결정한다. 이 방식은 빠르게 문제를 고칠 수 있지만, 다음 한계가 있다.

- 새로운 질의 표현이 나올 때마다 수동 조건을 추가해야 한다.
- place lookup, gazetteer provenance, 용어 사전, S-101 object lookup, traffic analysis가 같은 단어를 공유하면 오분류된다.
- 실행 전에 어떤 resolver/tool 후보가 있었고, 왜 버렸는지 설명하기 어렵다.
- Ontology/KG 유사도와 Registry 검증이 실행 전에 충분히 쓰이지 못한다.
- 사용자 피드백이 route 후보, dictionary 후보, KG 연결, tool readiness 중 어디를 고쳐야 하는지로 분해되지 않는다.

### Rule Explosion Risk

현재 방식이 계속되면 rule explosion이 발생한다.

Rule explosion은 단순히 규칙 수가 많아지는 문제가 아니다. 서로 다른 domain의 단어가 겹칠 때, 규칙의 우선순위와 예외 조건이 계속 늘어나면서 전체 라우팅을 설명하거나 검증하기 어려워지는 상태다.

예:

- `독도`는 place lookup 후보지만, "독도 관련 법령"에서는 STANDARD_RAG 후보다.
- `gazetteer`는 지명 lookup 후보지만, "gazetteer 적재 근거"에서는 DATASET_PROVENANCE 후보다.
- `obstruction`은 S-101 feature 후보지만, "obstruction 정의"에서는 STANDARD_RAG 후보이고, "3km 이내 obstruction"에서는 SPATIAL_ANALYSIS 후보다.
- `부산항 입구`는 place 후보이지만, "통항량"과 결합하면 TRAFFIC_ANALYSIS의 공간 filter가 된다.

이 상태에서 `_looks_like_*` 조건을 계속 추가하면 다음 문제가 생긴다.

- 먼저 매칭된 규칙이 더 적합한 뒤쪽 규칙을 가린다.
- 새 예외를 넣으면 과거 질의가 회귀한다.
- 정확도/유사도 지표가 "왜 그 route가 선택됐는지"를 설명하지 못한다.
- 사용자 피드백을 받았을 때 dictionary를 고칠지, KG edge를 고칠지, route scorer를 고칠지 분리할 수 없다.

따라서 규칙은 최종 route 결정자가 아니라 candidate generator로 강등해야 한다. 규칙은 "이 후보를 살펴볼 가치가 있다"까지만 말하고, 실행 여부는 Ontology/KG와 Registry 검증 gate가 결정한다.

## Three-Layer Candidate Model

Rule explosion을 막기 위해 candidate orchestration은 세 층으로 분리한다.

```text
Multi-label router
-> Deterministic signal
-> Semantic capability retrieval
-> Ontology/KG and Registry verification
-> Ollama ambiguity resolver, only when needed
-> Verified execution
```

## Multi-Label Router

Multi-label router는 질의를 하나의 route로 너무 빨리 압축하지 않는다. 여러 route 후보를 점수와 함께 유지하고, 뒤 단계가 후보를 좁힐 수 있도록 한다.

단일 label router의 문제:

- `독도`를 PLACE_LOOKUP으로만 고르면 "독도 관련 법령"이 깨진다.
- `gazetteer`를 PLACE_LOOKUP으로만 고르면 "gazetteer 적재 근거"가 깨진다.
- `obstruction`을 STANDARD_RAG로만 고르면 "3km 이내 obstruction" 공간 질의가 깨진다.
- `통항량`을 TRAFFIC_ANALYSIS로만 고르면 "통항량 데이터 출처" provenance 질의가 깨진다.

Multi-label router 출력 예:

```json
{
  "query": "독도 3km 이내 위험객체를 찾아줘",
  "route_candidates": [
    {
      "route": "SPATIAL_ANALYSIS",
      "score": 0.93,
      "signals": ["radius_slot", "nearby_search", "hazard_target"]
    },
    {
      "route": "PLACE_LOOKUP",
      "score": 0.72,
      "signals": ["place_name", "find_intent"],
      "role": "supporting_route"
    },
    {
      "route": "STANDARD_RAG",
      "score": 0.18,
      "signals": ["feature_term_candidate"]
    }
  ]
}
```

여기서 `PLACE_LOOKUP`은 최종 답변 route가 아니라 `SPATIAL_ANALYSIS`를 위한 기준점 resolver route가 된다. 이처럼 multi-label router는 route를 경쟁 관계로만 보지 않고, parent route와 supporting route 관계도 남겨야 한다.

### Route Candidate Schema

```json
{
  "route": "SPATIAL_ANALYSIS",
  "score": 0.93,
  "role": "primary|supporting|fallback",
  "required_slots": ["anchor_geometry", "radius", "target_feature_group"],
  "available_slots": ["radius", "target_feature_group"],
  "missing_slots": ["anchor_geometry"],
  "deterministic_signals": ["3km", "이내", "위험객체"],
  "semantic_capabilities": [],
  "verification_status": "pending"
}
```

### Multi-Label Policy

- route 후보는 최소 top-3까지 유지한다.
- 점수 차이가 작거나 route 간 의존관계가 있으면 하나로 압축하지 않는다.
- primary route와 supporting route를 구분한다.
- supporting route는 단독 답변을 만들지 않고 parent route의 slot을 채운다.
- 최종 route 선택은 KG/Registry verification 이후에만 확정한다.
- Ollama는 multi-label 후보가 verification 이후에도 충돌할 때만 호출한다.

### Parent and Supporting Route Examples

| query | primary route | supporting route |
| --- | --- | --- |
| 독도를 찾아줘 | PLACE_LOOKUP | none |
| 독도 3km 이내 위험객체 | SPATIAL_ANALYSIS | PLACE_LOOKUP |
| 부산항 입구 최근 1년 통항량 | TRAFFIC_ANALYSIS | PLACE_LOOKUP or SPATIAL_FILTER |
| gazetteer 적재 근거 | DATASET_PROVENANCE | STANDARD_RAG optional |
| Obstruction 정의 | STANDARD_RAG | TERM_DICTIONARY |
| Obstruction 객체를 지도에 표시 | LAYER_INSPECTION or SPATIAL_ANALYSIS | FEATURE_DICTIONARY |

Multi-label router의 목표는 "한 번에 맞히기"가 아니라 "좋은 후보를 버리지 않기"다. 이후 deterministic signal, semantic retrieval, KG/Registry verification이 후보를 줄인다.

## Tool Graph

복합 Tool 관계는 list나 hard-coded pipeline이 아니라 graph로 관리한다.

이유:

- 하나의 질의가 여러 tool을 순차/병렬로 요구한다.
- supporting route가 만든 slot이 primary route tool의 입력이 된다.
- tool 실행 전후에 verification gate가 끼어든다.
- 실패 시 fallback 또는 clarification route가 필요하다.
- 지도 표시, evidence retrieval, answer generation은 같은 분석 결과를 서로 다른 방식으로 소비한다.

예:

```text
독도 3km 이내 위험객체를 찾아줘

place_resolver
  -> spatial_radius_builder
  -> hazard_feature_resolver
  -> s101_spatial_query
  -> portrayal_resolver
  -> map_layer_renderer
  -> evidence_bundle_builder
  -> answer_composer
```

각 tool node는 다음 스키마를 가진다.

```json
{
  "tool_id": "tool.s101_spatial_query",
  "kind": "execution_tool",
  "requires": ["anchor_geometry", "radius_m", "feature_type_candidates"],
  "produces": ["spatial_features", "feature_count", "query_extent"],
  "authority_inputs": ["registry.s101_feature_catalogue", "registry.spatial_layer_catalogue"],
  "verification": ["slot_complete", "geometry_valid", "table_ready"],
  "fallbacks": ["tool.layer_inspection", "clarification.ask_target_feature"],
  "side_effects": []
}
```

Tool graph edge는 단순 호출 순서가 아니라 dependency를 의미한다.

```json
{
  "from": "resolver.place_registry",
  "to": "tool.spatial_radius_builder",
  "provides": ["anchor_geometry", "canonical_name"],
  "condition": "place_candidate.status == verified_ready"
}
```

### Tool Graph Node Types

| node type | 역할 |
| --- | --- |
| `resolver` | place, feature, term, dataset 후보 생성 |
| `verifier` | KG/Registry/authority/data readiness 검증 |
| `execution_tool` | spatial SQL, traffic aggregation, RAG retrieval 실행 |
| `transformer` | geometry buffer, period normalization, feature grouping |
| `renderer` | map layer, legend, portrayal, click detail 구성 |
| `composer` | answer, evidence bundle, summary 작성 |
| `clarifier` | 누락 slot 또는 후보 충돌 질문 생성 |

### Tool Graph Policies

- tool은 registry에 등록된 node만 graph에 들어갈 수 있다.
- edge는 입력/출력 slot compatibility를 명시해야 한다.
- execution tool 앞에는 verification node가 있어야 한다.
- renderer는 분석 대상 object와 helper geometry를 구분해야 한다.
- helper geometry, 예를 들어 검색 반경 polygon은 object click detail을 가로채면 안 된다.
- traffic, spatial, RAG tool은 같은 answer에서 결합될 수 있지만, provenance와 quality metric은 tool별로 분리해야 한다.
- graph 실행 trace는 사용자가 "왜 이 결과가 나왔나"를 물었을 때 설명 가능해야 한다.

### Tool Graph Example: Traffic Analysis

```text
query: 부산항 입구 최근 1년 AIS/V-PASS 통항량을 분석해줘

multi_label_router
  -> place_resolver: 부산항 입구
  -> period_resolver: latest_available_12_months
  -> traffic_coverage_verifier
  -> traffic_aggregation_tool
  -> traffic_cell_renderer
  -> regional_summary_composer
```

이 경우 place lookup은 supporting route이고, traffic analysis가 primary route다. 지도 cell click detail은 전체 합계가 아니라 해당 cell의 AIS/V-PASS 월별 통계를 보여줘야 한다.

### Tool Graph Example: Dataset Provenance

```text
query: 해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘

multi_label_router
  -> dataset_provenance_resolver
  -> ingestion_report_verifier
  -> serving_table_registry_lookup
  -> evidence_bundle_builder
  -> answer_composer
```

이 경우 place resolver나 spatial renderer는 tool graph에 들어가면 안 된다.

```text
Deterministic signal
-> Semantic capability retrieval
-> Ontology/KG and Registry verification
-> Ollama ambiguity resolver, only when needed
-> Verified execution
```

### 1. Deterministic Signal Layer

Deterministic signal은 빠르고 설명 가능한 1차 신호다. 단, 이 층은 최종 route를 결정하지 않는다.

역할:

- 명확한 slot 추출: 반경 `3km`, 기간 `최근 1년`, 지명 후보 문자열, feature keyword
- 강한 negative/positive hint 추출: `근거`, `출처`, `적재`, `정의`, `통항량`, `이내`, `찾아줘`
- 위험한 실행 차단: 필수 slot 누락, authority 없음, tool 미준비
- 후보 retrieval query를 만드는 seed 제공

예:

| signal | 의미 |
| --- | --- |
| `3km 이내` | spatial radius analysis 후보 seed |
| `근거/출처/적재` | provenance/evidence 후보 seed |
| `정의/표준/S-101` | STANDARD_RAG 후보 seed |
| `최근 1년/통항량/AIS/V-PASS` | TRAFFIC_ANALYSIS 후보 seed |
| `찾아줘/위치/어디` | PLACE_LOOKUP 후보 seed |

중요 원칙:

- deterministic signal은 `candidate_hint`를 만든다.
- deterministic signal만으로 tool을 실행하지 않는다.
- deterministic signal 충돌은 정상 상태로 보고 semantic retrieval과 verification에 넘긴다.

### 2. Semantic Capability Retrieval Layer

Semantic capability retrieval은 등록된 Resolver, Dictionary, Tool, Evidence capability 중 질의와 가장 가까운 top-k 후보를 찾는다.

대상:

- Resolver registry
- Dictionary registry
- Tool registry
- Dataset/evidence registry
- Ontology capability descriptions
- Agent descriptions
- Dataset metadata
- Ontology class descriptions
- Marine terms
- Feature class descriptions

Capability 문서는 embedding 또는 hybrid search 대상으로 만든다.

예:

```json
{
  "capability_id": "resolver.place_registry",
  "kind": "resolver",
  "routes": ["PLACE_LOOKUP", "SPATIAL_ANALYSIS"],
  "description": "Resolve Korean place names, ports, islands, and curated maritime points to canonical geometry.",
  "input_slots": ["query_text", "place_name"],
  "output_slots": ["canonical_name", "geometry", "source_ref", "authority"],
  "authority_required": true
}
```

Top-k retrieval 결과는 실행 후보가 아니라 capability 후보다.

예:

```text
query: "독도 3km 이내 위험객체를 찾아줘"

top-k capabilities:
1. resolver.place_registry
2. resolver.s101_hazard_feature_dictionary
3. tool.spatial_radius_search
4. registry.s101_feature_catalogue
5. registry.portrayal_catalogue
```

이 층의 장점:

- 새로운 resolver/tool이 추가되어도 route code를 매번 수정하지 않는다.
- 질의 표현이 바뀌어도 semantic retrieval로 후보를 찾을 수 있다.
- deterministic signal이 놓친 후보를 보완한다.

### pgvector Capability Index

pgvector는 RAG 문서 chunk 검색뿐 아니라 capability 후보 검색에도 사용한다. 단, pgvector의 역할은 authoritative answer 생성이 아니라 top-k 후보 생성이다.

권장 embedding 대상:

| object type | embedding text | 사용 목적 |
| --- | --- | --- |
| `resolver_description` | resolver가 처리하는 질의 유형, 입력 slot, 출력 slot, authority 요구사항 | 어떤 resolver를 후보로 부를지 결정 |
| `agent_description` | agent 역할, 처리 가능한 route, 산출물, 제약 | primary/supporting agent 후보 검색 |
| `tool_description` | tool 입력/출력, 실패 조건, fallback, 비용 | Tool Graph node 후보 검색 |
| `dataset_metadata` | source file, table, schema, coverage, period, row count, domain | Dataset provenance와 analytical layer 후보 검색 |
| `ontology_class_description` | class label, aliases, parent/child, relation hints | KG seed와 class 후보 검색 |
| `marine_term` | 한국어/영어 용어, 약어, 동의어, 정의 출처 | term disambiguation |
| `feature_class_description` | S-101 object class, aliases, geometry type, portrayal, DCEG/catalogue ref | feature/object 후보 검색 |

권장 테이블 형태:

```sql
create table knowledge.capability_embeddings (
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

검색 정책:

```text
query
-> deterministic signal extracts route/slot hints
-> pgvector top-k over capability_embeddings
-> metadata filter by route_tags/object_type when signal is strong
-> Ontology/KG and Registry verification
-> verified candidates only enter Tool Graph
```

중요 원칙:

- pgvector similarity는 후보 점수이지 권위 점수가 아니다.
- `authority_ref` 또는 `registry_ref`가 없는 후보는 실행 후보가 아니라 탐색 후보로만 사용한다.
- Feature class, marine term, ontology class는 유사도가 높아도 catalogue/KG 검증을 통과해야 한다.
- Dataset metadata embedding은 raw AIS/V-PASS나 raw geometry row를 embedding하지 않는다. source/table/coverage/period/schema 설명만 embedding한다.
- Resolver/Agent/Tool description은 버전 관리되어야 하며, code 변경 시 embedding도 갱신해야 한다.

### 3. Ontology/KG and Registry Verification Layer

Verification layer는 top-k capability 후보 중 실제 실행 가능한 것만 남긴다.

검증 항목:

| 검증 | 질문 |
| --- | --- |
| intent compatibility | 이 capability가 broad route와 맞는가 |
| slot compatibility | 필요한 입력 slot이 채워졌는가 |
| ontology compatibility | KG에서 domain, object, relation path가 연결되는가 |
| authority | registry/catalogue/evidence provenance가 승인되었는가 |
| data readiness | table, geometry, embedding, row count, freshness가 준비되었는가 |
| tool readiness | 실제 실행 adapter가 있고 실패 조건이 관리되는가 |
| safety | 근거 없는 조항/날짜/정의를 생성하지 않는가 |

검증은 scoring만 하지 않고 reject reason을 남긴다.

예:

```json
{
  "candidate_id": "tool.spatial_radius_search",
  "status": "verified_ready",
  "accepted_because": [
    "route=SPATIAL_ANALYSIS",
    "place geometry resolved",
    "radius slot resolved",
    "target feature group verified by S-101 feature dictionary"
  ],
  "rejected_alternatives": [
    {
      "candidate_id": "tool.standard_rag_retrieve",
      "reason": "query asks for nearby objects, not definition or document evidence"
    }
  ]
}
```

### Layer Responsibility Boundary

| layer | 할 수 있는 일 | 하면 안 되는 일 |
| --- | --- | --- |
| Deterministic signal | slot/hint/guard 생성 | 최종 route 단독 결정 |
| Semantic retrieval | top-k capability 후보 검색 | authority 없이 실행 |
| KG/Registry verification | 후보 검증, reject reason 생성 | 없는 근거 생성 |
| Execution | 검증된 tool 실행 | 미검증 후보 실행 |

이 구조에서 규칙은 사라지는 것이 아니라 역할이 바뀐다. 규칙은 빠른 신호와 guardrail로 남고, 최종 선택은 semantic retrieval과 authority verification을 통과한 후보만 수행한다.

### Ollama as Ambiguity Resolver Only

Ollama 또는 local LLM은 기본 route 결정자가 아니다. 다음 조건에서만 제한적으로 호출한다.

- broad route 후보가 서로 비슷한 점수로 충돌하는 경우
- deterministic signal과 semantic retrieval 결과가 서로 다른 route를 가리키는 경우
- candidate는 있으나 질의의 대상/범위/근거 요청 여부가 애매한 경우
- 사용자에게 clarification을 물을지, 안전하게 차단할지 판단해야 하는 경우
- 한국어 조사/축약/문맥 때문에 slot 해석이 불확실한 경우

Ollama가 할 수 있는 일:

- 후보 간 intent disambiguation
- 누락 slot에 대한 clarification question 생성
- 사용자가 말한 대상이 place, feature, term, dataset, evidence 중 무엇인지 추론
- verification layer가 만든 reject reason을 사용자 친화적으로 요약

Ollama가 하면 안 되는 일:

- Registry에 없는 장소/feature/evidence를 authoritative한 것처럼 생성
- KG/Registry 검증을 우회해서 tool 실행 결정
- 조항, 날짜, feature 정의, 표준 근거를 새로 만들어 답변
- deterministic/KG 검증으로 이미 명확한 route를 다시 뒤집기

호출 정책:

```text
if verified_ready candidate is unique:
    execute without Ollama
elif candidates are ambiguous or required slot is unclear:
    call Ollama ambiguity resolver
elif no authoritative candidate exists:
    block or ask clarification without inventing evidence
```

Ollama 결과도 최종 결정이 아니라 verification layer로 되돌아가야 한다. 즉, Ollama는 "이 후보가 더 그럴듯하다" 또는 "이 slot을 물어봐야 한다"를 제안할 수 있지만, 실행은 여전히 Registry/KG 검증을 통과한 후보만 가능하다.

## 실행 단계

### 1. Broad Route Classification

첫 단계는 정답을 실행하지 않고, 큰 실행경로 후보를 만든다.

표준 route 후보:

| route | 목적 | 예시 |
| --- | --- | --- |
| `PLACE_LOOKUP` | 특정 지명, 섬, 항만, 해역의 위치 확인 | 독도를 찾아줘 |
| `SPATIAL_ANALYSIS` | 기준점/범위/대상 객체를 가진 공간 분석 | 부산항 입구 3km 이내 위험객체 |
| `DATASET_PROVENANCE` | Dataset 적재 근거, 출처, 파싱/표준화 상태 설명 | gazetteer가 어떤 근거로 적재되었는지 |
| `STANDARD_RAG` | 법령, 고시, 표준, S-101 카탈로그 문서 근거 검색 | Obstruction 정의 |
| `TRAFFIC_ANALYSIS` | AIS/V-PASS 통항량, 기간, 구역별 통계 | 최근 1년간 통항량 |
| `LAYER_INSPECTION` | 지도 레이어/객체 속성/portrayal 설명 | 주황색 폴리곤은 뭐야 |
| `QUALITY_REVIEW` | 오답, 오분류, 근거 부족, 정확도 검토 | 왜 다른 분석 결과가 나왔어 |

이 단계의 결과는 하나일 필요가 없다. 여러 후보와 점수를 남겨야 한다.

### 2. Candidate Discovery

Broad route 이후에는 실행하지 않고 후보만 모은다.

후보 종류:

| candidate kind | 후보 원천 |
| --- | --- |
| `place_candidate` | place registry, marine gazetteer, island gazetteer, 항만/항로표지 gazetteer |
| `feature_candidate` | S-101 Feature Catalogue, local feature dictionary, portrayal registry |
| `term_candidate` | 해양 용어 사전, S-100/S-101 용어, 법령 용어 |
| `dataset_candidate` | Dataset coverage report, ingestion report, serving table registry |
| `evidence_candidate` | `knowledge.document_chunks`, approved evidence registry, catalogue chunks |
| `tool_candidate` | spatial SQL executor, traffic aggregator, layer inspector, document retriever |
| `ontology_candidate` | KG node, KG edge, graph path, approved binding |

각 후보는 최소한 다음 스키마를 가진다.

```json
{
  "candidate_id": "place:dokdo",
  "kind": "place_candidate",
  "label": "독도",
  "source": "data/place_geometry_registry.yaml",
  "route": "PLACE_LOOKUP",
  "match_score": 0.98,
  "authority_score": 1.0,
  "kg_score": 0.85,
  "required_slots": [],
  "execution_readiness": "ready",
  "risk_flags": [],
  "explain": "Korean island place registry exact alias match"
}
```

후보는 실행 계획이 아니라 실행 가능한 재료다. 실행은 검증 gate 이후에만 가능하다.

### 3. Ontology/KG and Registry Verification

후보 검증은 다음 순서로 수행한다.

1. `intent-slot` 검증: 질의가 위치 검색인지, 근거 설명인지, 공간 분석인지 분리한다.
2. `authority` 검증: 후보가 authoritative registry, approved catalogue, Dataset ingestion report 중 어디에서 왔는지 확인한다.
3. `KG path` 검증: 후보가 Ontology/KG에서 관련 domain과 연결되는지 확인한다.
4. `schema/tool readiness` 검증: 실행할 tool이 필요한 slot, geometry, table, period, feature type을 갖추었는지 확인한다.
5. `data quality` 검증: mojibake, null geometry, stale layer, missing embedding, no approved evidence 같은 품질 flag를 확인한다.

검증 결과:

| status | 의미 |
| --- | --- |
| `verified_ready` | 실행 가능 |
| `verified_needs_slot` | 사용자에게 추가 질문 필요 |
| `candidate_rejected` | 의도/근거/권한/품질 문제로 제외 |
| `blocked_no_authority` | 근거 없이 답하면 안 됨 |
| `blocked_tool_not_ready` | 후보는 맞지만 실행 바인딩이 아직 없음 |

### 4. Selection and Execution Policy

선택 정책:

- `verified_ready` 후보만 실행한다.
- 동점 또는 충돌 후보가 있으면 먼저 clarification을 요청한다.
- `DATASET_PROVENANCE`와 `PLACE_LOOKUP`이 동시에 뜨면, "근거/출처/적재/검증" 표현이 있는 경우 Dataset provenance를 우선한다.
- `SPATIAL_ANALYSIS`는 기준점, 반경/영역, 대상 객체가 모두 있어야 실행한다.
- `TRAFFIC_ANALYSIS`는 기준 기간과 데이터 coverage를 먼저 확정한다.
- `STANDARD_RAG`는 approved evidence가 없으면 "근거 없음"으로 차단하고, 조항/날짜/정의를 생성하지 않는다.

실행 결과에는 다음을 포함한다.

- 선택된 route
- 선택된 후보
- 버려진 주요 후보와 사유
- `quality_metrics`
- 사용한 registry/KG/evidence/tool
- 지도에 표시한 layer/object의 의미와 click detail mapping

### 5. Learning and Quality Loop

실행 결과는 최종 답변만 기록하면 부족하다. 다음 단위까지 기록해야 한다.

```json
{
  "query": "독도를 찾아줘",
  "broad_route_candidates": [],
  "resolver_candidates": [],
  "verified_candidates": [],
  "selected_execution": {},
  "rejected_candidates": [],
  "quality_metrics": {},
  "user_feedback": null,
  "status": "pending_review"
}
```

`data/feedback/query_quality_issues.jsonl`에는 다음 유형을 남긴다.

- `wrong_broad_route`
- `missing_resolver_candidate`
- `wrong_candidate_selected`
- `kg_path_missing`
- `registry_authority_missing`
- `tool_binding_missing`
- `data_quality_flag`
- `ambiguous_without_clarification`
- `no_evidence_blocked`

이 로그는 다음 변경의 입력이 된다.

- query normalizer dictionary 갱신
- place/feature/term resolver alias 갱신
- Ontology/KG node/edge 추가
- Registry authority 보강
- evidence candidate 승인/반려
- tool readiness 또는 schema binding 보강
- route reranking weight 조정

## 현재 Fast Path에서의 이행 계획

### Phase 1. Dry-run Candidate Broker

기존 fast path 실행은 유지하되, 질의마다 candidate broker를 dry-run으로 돌린다.

산출물:

- broad route 후보
- resolver/tool/evidence 후보
- rejected candidate 사유
- selected fast path와 broker 추천 route의 차이

이 단계에서는 운영 결과를 바꾸지 않고 관측만 한다.

### Phase 2. Fast Path Gate Replacement

`_looks_like_known_place_search`, `_looks_like_dataset_evidence_query` 같은 직접 조건은 broker의 후보 결과를 읽는 adapter로 바꾼다.

원칙:

- 직접 route 결정 금지
- 후보 생성만 허용
- 실행은 verification gate 이후에만 허용

### Phase 3. Registry-Backed Resolver Catalog

Resolver, dictionary, tool을 코드에 흩뿌리지 않고 catalog로 관리한다.

예:

```yaml
resolvers:
  place_registry:
    routes: [PLACE_LOOKUP, SPATIAL_ANALYSIS]
    outputs: [geometry, canonical_name, authority]
  island_gazetteer:
    routes: [PLACE_LOOKUP]
    outputs: [name, geometry, source_file]
  s101_feature_dictionary:
    routes: [SPATIAL_ANALYSIS, STANDARD_RAG, LAYER_INSPECTION]
    outputs: [feature_type, catalogue_ref, portrayal_ref]
  dataset_provenance_registry:
    routes: [DATASET_PROVENANCE]
    outputs: [source_file, serving_table, row_count, ingestion_report]
```

### Phase 4. Supervised Reranking

품질 로그와 evidence review 결과가 쌓이면 후보 reranking을 학습한다.

학습 target:

- broad route accuracy
- selected candidate accuracy
- evidence acceptance rate
- user correction frequency
- execution success/failure

단, authority 없는 후보를 높은 점수로 rerank해서는 안 된다. Authority gate는 reranker보다 우선한다.

## 대표 질의 흐름

### "독도를 찾아줘"

```text
Broad route candidates:
- PLACE_LOOKUP high
- STANDARD_RAG low

Resolver candidates:
- place:dokdo from place_geometry_registry.yaml
- island_gazetteer:독도 if available

Verification:
- Korean island place registry exact alias
- geometry ready

Execution:
- place lookup map marker
- answer explains canonical place, coordinate, source registry
```

### "독도 3km 이내 위험객체를 찾아줘"

```text
Broad route:
- SPATIAL_ANALYSIS

Candidates:
- place:dokdo as 기준점
- feature group: hazard objects
- S-101 object classes: obstruction, wreck, rock, buoy/beacon if configured as hazard-relevant
- spatial SQL executor

Verification:
- 기준점 geometry exists
- radius slot exists
- target feature dictionary resolves
- spatial layer readiness ok

Execution:
- radius query
- each object rendered with scale-appropriate portrayal
- click detail shows feature information, not radius polygon details
```

### "해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘"

```text
Broad route:
- DATASET_PROVENANCE

Candidates:
- Dataset/해양수산부_공동활용체계_해양지명_20221231.csv
- Dataset/도서지명.zip
- serving.marine_gazetteer_current
- serving.island_gazetteer_current
- requested_dataset_layer_ingestion report

Verification:
- source files in Dataset coverage
- serving table row counts available

Execution:
- no spatial lookup
- answer describes source file, table, row count, ingestion evidence
```

### "Obstruction 정의와 S-101 근거를 알려줘"

```text
Broad route:
- STANDARD_RAG

Candidates:
- S-101 Feature Catalogue obstruction entry
- DCEG guidance chunks
- local term dictionary obstruction entry

Verification:
- product/version filter S-101 2.0
- approved evidence or catalogue source

Execution:
- definition with citations
- no map rendering unless user asks for objects on map
```

## 운영 원칙

- 질의가 모호하면 임의 실행보다 clarification을 우선한다.
- "근거/출처/적재/검증" 질의는 객체 검색보다 provenance를 우선한다.
- 장소명은 먼저 resolver 후보로만 생성하고, 실행 전 authority와 geometry를 검증한다.
- 지도에 그린 모든 피처는 legend, source, click detail, analysis role을 가져야 한다.
- 반경/검색범위 polygon은 분석 대상 object가 아니므로 click detail에서 object처럼 보이면 안 된다.
- AIS/V-PASS 같은 고용량 동적 데이터는 document embedding이 아니라 analytical layer/tool 후보로 취급한다.
- `estimated_accuracy`는 추정값이며, 실제 정확도는 사용자 피드백과 evidence review가 누적되어야 한다.

## 구현 체크리스트

- [ ] `QueryCandidateBroker` dry-run 모듈 추가
- [ ] route 후보와 rejected 후보를 `query_quality_issues.jsonl` 또는 별도 candidate trace에 기록
- [ ] place/feature/term/dataset/evidence/tool resolver catalog 정의
- [ ] 기존 `_looks_like_*` 조건을 broker 후보 adapter로 이동
- [ ] UI 디버그 패널에 route 후보, 선택 후보, 버려진 후보 사유 표시
- [ ] regression query set에 `독도를 찾아줘`, `gazetteer 근거`, `부산항 입구 3km 위험객체`, `Obstruction 정의` 추가
- [ ] feedback review 결과를 reranking weight와 dictionary/KG/registry 변경으로 연결
