# GeoLLM 실행계약 통합 및 근거 기반 응답 안정화 — Codex CLI 작업 지시문

## 0. 역할과 작업 목표

너는 `D:\An_GeoLLM`의 실행 경로를 통합하는 소프트웨어 엔지니어다.
목표는 새 DB, 새 임베딩 또는 새 Agent를 무조건 만드는 것이 아니다.
이미 구현된 질의 이해, 슬롯 추출, Context/KG 해석, 데이터 탐색, 계획, 공간분석, RAG를
**버전 관리되는 공통 실행계약과 근거계약**으로 연결하고 테스트하는 것이다.

작업 결과는 실제 코드 수정, 회귀 테스트, 실행 가능한 문서여야 한다.
단, 실제 환경에서 실행하지 못한 항목은 `NOT_RUN` 또는 `BLOCKED`로 보고하고,
예상 결과나 테스트 fixture를 실제 DB 검증 결과로 바꾸어 보고하지 않는다.

### 사용자 제공 최신 상태 — 재확인할 기준이지 이미 검증된 사실이 아님

- `projection.s101_feature_valid`: invalid geometry 0건이라고 보고됨.
- `serving.accident_s101_relation_current`: 23,180행이라고 보고됨.
- S-101 2.0 문서 chunk 1,869개, embedding 1,869개, null embedding 0개라고 보고됨.
- source group 10개가 존재한다고 보고됨.
- 실제 geometry 컬럼은 `geometry`, 사고 관계의 거리 컬럼은 `distance_meters`라고 보고됨.
- 애플리케이션 일부는 `geom`, `distance_m`을 기대해 명칭 불일치가 있음.
- `extracted_slots`를 state에 등록하고 plan에 병합하는 수정이 진행됨.
- 이전 운영 설정에는 bge-m3, 1024차원 embedding이 사용되었으나,
  현재 활성 컬렉션의 실제 모델·revision·차원·전처리를 다시 확인해야 함.

1,869개는 S-101 2.0 집합의 보고값이다. 전체 RAG 데이터 총량으로 가정하지 않는다.
23,180행은 관계 레코드 수이지 서로 다른 사고 수 또는 위험객체 수가 아니다.

### 작업 범위

- 공통 QueryExecutionContext / ExecutionSlots / ValidatedTaskPlan / Evidence 모델.
- 단계별 상태 병합, 필드 소유권, ID와 이름의 구분.
- KG, Dictionary, Data/Tool Registry의 실행상 역할 분리.
- 실제 스키마를 반영하는 DB adapter와 검증된 Query Template 연결.
- 연산별 실행 전 검증, 운영 경로의 Mock 차단.
- 생성 LLM과 독립된 RAG 검색 및 일관된 citation.
- 공간·문서·사고관계·KG 근거 통합 및 Debug UI.
- 단위/통합/실DB read-only/E2E 회귀 테스트와 Markdown 문서.

### 작업 제외 및 보호 원칙

- 정상인 v2 DB를 다시 복원하지 않는다.
- 전체 embedding을 다시 생성하거나 기존 chunk·vector를 삭제하지 않는다.
- `DROP`, `TRUNCATE`, 대량 `DELETE/UPDATE`, projection 전면 재생성,
  active view 교체, 인덱스 교체, Docker volume 삭제, 권한/키 변경은 자동 실행하지 않는다.
- DB는 승인된 읽기 전용 계정으로 접근한다. 변경이 필요하면 migration/rollback 초안만 만들고 승인을 요청한다.
- 기존 비커밋 변경사항을 보존한다. `git reset --hard`, `git clean -fd`, 강제 checkout, 자동 push를 하지 않는다.
- 비밀번호, API Key, DSN 원문, 원시 개인 식별정보를 보고서·로그·프롬프트에 출력하지 않는다.
- `AGENTS.md`와 해당 하위 경로의 지침을 먼저 읽고 따른다. 기존 파일을 대체하지 않는다.
- 잠긴 의존성 버전을 우선 사용한다. 무조건 최신 버전으로 전체 업그레이드하지 않는다.
- 문서에 적힌 테이블·Agent·Tool 이름을 실제 구현 확인 없이 새로 등록하거나 실행하지 않는다.
- 대규모 Dataset, dump, embedding 본문 전체를 모델 컨텍스트에 넣지 않는다.
- 공개 API/응답 구조 변경은 adapter 또는 버전 호환 전략을 포함한다.

---

## Phase 0. 최신 실행 경로와 기준선 확인

1. 작업 경로와 git 상태, 현재 commit 및 로컬 변경사항을 확인한다.
2. Docker/앱의 실제 entrypoint, 사용 중인 소스 마운트·이미지, API endpoint를 확인한다.
   문서나 파일의 존재만으로 실행 중이라고 판정하지 않는다.
3. 다음 이름은 탐색 후보다. 같은 역할의 기존 모듈이 있으면 재사용한다.
   - QueryNormalizer, SlotExtractor, ContextResolver, GraphRAGRetriever
   - DataDiscovery, RoutePlanner, Spatial Agent, Standard/RAG Agent
   - AgentRequest, QueryPlan, TaskPlan, state, validator, map adapter
4. `extracted_slots`, `spatial_context`, `task_plan.slots`, `resolved_metadata`의
   생산자·소비자·덮어쓰기 위치를 파일/라인과 함께 추적한다.
5. Mock fixture 정의, production import, 예외 처리, 검색 0건 처리,
   `llm_api_enabled()`와 embedding 조건의 의존성을 추적한다.
6. 승인된 연결로 지정된 projection, 사고 relation, 실제 RAG relation의
   스키마·컬럼·키·타입·SRID·가용성·권한을 read-only 확인한다.
   전체 공간 DB를 무제한 스캔하지 않고 지정 relation부터 시작한다.
7. geometry 유효성 0건은 원본과 의미가 같음, 범위가 완전함, 좌표계가 맞음의 증거가 아님을 기록한다.
8. chunk 수·vector 수는 실제 product/version/source filter와 검사 SQL을 함께 기록한다.
   DB 무접근 시 사용자 보고값과 실측값을 구분한다.
9. 기존 테스트를 확인하고 핵심 문제의 최소 재현 테스트부터 만든다.
10. `docs/execution_contract/00_baseline.md` 및 machine-readable baseline을 생성한다.

완료 조건: 현재 실행 경로, 실제 스키마 계약, 수정 대상과 미확인 환경이 구분됨.

---

## Phase 1. 공통 실행계약 정의

기존 Pydantic/타입 시스템을 활용하되, 현재 프로젝트 버전에 맞게 구현한다.
원시 문자열의 정규화와 내부 계약의 엄격한 검증을 분리한다.
형식 검증을 통과한 것만으로 실제 실행 가능하다고 판단하지 않는다.

### 권장 모델

- QueryExecutionContext: 요청 수준 상태와 작업 목록의 공통 참조.
- ExecutionSlots: 정규화된 사용자 의도 입력.
- SemanticResolution: 확정된 의미와 대안 후보를 구분.
- FeatureTypeRef: product/edition/catalogue/class를 식별.
- FeatureBinding: 표준 class와 실제 dataset/code/filter의 검증된 연결.
- DataBinding: 실제 DB relation/column/키/버전/권한의 adapter 참조.
- ToolBinding: 승인된 tool/operation/template/schema 버전.
- TaskPlan: 작업별 연산, 입력, 의존성, expected output.
- ValidatedTaskPlan: 실행 게이트를 통과한 immutable plan snapshot.
- TaskResult: 성공/0건/실패/부분성공과 결과 참조.
- EvidenceBundle: 결과별 출처·계산·문서·KG 근거.

별도 서비스나 과도한 새 클래스를 만들기보다 기존 shared schema에 최소한으로 통합한다.

### 필수 구분

1. `surface_term`: 사용자의 원래 표현.
2. `concept_id`: 승인된 내부 업무 개념 ID.
3. `feature_type_ref`: S-101 표준 Feature class와 catalogue edition.
4. `feature_instance_ref`: 실제 객체의 dataset/cell/version + object key.
5. `db_code`: 해당 데이터셋에서 검증된 코드. 전역 S-101 표준 코드로 가정하지 않음.
6. `intent`: 하려는 일.
7. `context`: 업무 맥락.
8. `analysis_type/operation`: 수행할 연산.
9. `agent_id`, `tool_id`, `query_template_id`, `dataset_id`: 표시명 아닌 등록된 ID.

표준 Feature class와 실제 Feature instance를 같은 노드/키로 사용하지 않는다.
`위험객체`가 여러 Feature를 포함하는 것과, 사용자가 여러 의미 중 무엇을 뜻했는지
미확정인 것을 각각 `resolved_target_set`과 `alternative_target_sets`로 구분한다.

### QueryExecutionContext에 포함할 범주

- contract_version, request_id, conversation_id, task_id, revision, plan_hash
- original_query, normalized_query
- authenticated security context의 서버 내부 참조
- semantic resolution과 필드별 provenance
- location_text, reference_geometry 또는 geometry_ref, resolution_status, CRS
- spatial_relation, distance_m, time_range, inclusions, exclusions, outputs
- resolved feature bindings / unresolved alternatives
- dataset bindings, tool/template bindings
- retrieval_hints와 embedding_profile_ref
- task dependencies, readiness, blockers, warnings
- catalogue/KG/Registry/data snapshot version 또는 확인 시각

거리 문구는 파서에서 meter로 정규화하고, 검증된 내부 모델에는 숫자로 저장한다.
`location_text`와 해석 완료된 reference geometry를 구분한다.
RAG 전용 질의에 위치·반경·공간 Feature를 필수로 강제하지 않는다.
영역검색에 반경을 강제하지 않는다.
문서검색의 top_k, 공간검색의 radius, 사고관계 거리 등을 서로 다른 namespace에 둔다.

복합 질의는 요청 1개 안의 여러 TaskPlan으로 나눈다.
여러 작업이 하나의 전역 `distance_m`이나 `query_template`를 공유하며 덮어쓰지 않게 한다.

문서: `01_contract_schema.md`, JSON Schema와 최소 예제.

---

## Phase 2. 단계별 필드 소유권과 병합 규칙

현재 `extracted_slots` 수정은 유지·검증하고 새 저장 위치를 또 만들어 분산시키지 않는다.

### 담당 범위

- QueryNormalizer: 원문 보존, 표기·단위 표현 정리, 용어 후보.
- SlotExtractor: 사용자가 명시한 위치·거리·시간·대상·부정·출력 조건.
- ContextResolver: 업무맥락의 해석과 선택 근거. SQL/테이블 생성 금지.
- GraphRAGRetriever: 승인된 의미 연결, Feature/문서/도구 후보 및 graph path.
- DataDiscovery/LocationResolver: 실제 데이터 가용성·범위·스키마·권한·위치 해석.
- RoutePlanner: 검증 가능한 TaskPlan 구성. 이미 추출된 사용자 입력을 재추론하여 변경하지 않음.
- ExecutionValidator: 연산별 게이트를 통과시킬 유일한 모듈.
- 전문 Agent: ValidatedTaskPlan의 실행. 자연어를 다시 파싱하지 않음.

### 병합 규칙

- 사용자 명시값을 우선하고 적용한 default는 반드시 표시한다.
- KG의 후보와 승인된 확정값을 분리한다. 의미 유사도만으로 확정값을 덮어쓰지 않는다.
- 필드 미제공, unknown(null), 의도적 삭제/제외를 구분한다.
- 낮은 권한의 노드가 `None`, 빈 dict/list 또는 기본값으로 이전 확정값을 지우지 못하게 한다.
- 사용자 수정은 명시적인 patch로 처리하고 revision을 올린다.
  위치/반경/대상 변경 시 해당 validation, plan hash, downstream result/cache를 무효화한다.
- feature bindings와 evidence는 안정적 ID 기준으로 중복 제거한다.
- 같은 레이어명만으로 별개의 dataset/version을 합치지 않는다.
- 모든 patch는 producer, field_path, previous/new value, source_ref, reason_code를 기록한다.
- 인증·권한·테이블·SQL/template 확정 필드는 LLM/사용자 patch로 수정할 수 없다.

### LangGraph 주의

중첩 dict가 자동 deep merge된다고 가정하지 않는다.
권장 구현은 단일 context assembler가 타입화된 patch를 적용하고 검증한 context 전체를 교체하는 방식이다.
병렬 노드는 공통 슬롯을 직접 덮어쓰지 않고 task_id별 결과를 반환한다.
fan-in에서 request/task/revision ID로 합친다.
기존 reducer가 있으면 재사용하되, merge·재실행·중복 event 동작을 테스트한다.

### 이전 요청 계약 호환

`AgentRequest.spatial_context`, `task_plan.slots`, `resolved_metadata`를
임시 legacy adapter에서 한 번만 공통 계약으로 변환한다.
전문 Agent 내부의 다중 우선순위 `.get(...) or ...` 체인은 제거한다.
호환 경로 사용 로그와 폐기 계획을 남긴다.

문서: `02_state_merge_policy.md`.

---

## Phase 3. KG와 Registry의 역할 및 실제 DB binding

KG를 물리 DB·권한·실제 실행결과보다 상위의 무조건적인 정답원으로 만들지 않는다.
역할을 다음처럼 분리한다.

- 승인되고 버전 고정된 KG/Dictionary: 의미 관계와 후보 확장의 기준.
- Data/Tool/Template Registry + 실제 스키마 검사: 실행 메타정보의 기준.
- 인증 정책: 접근권한 기준.
- ExecutionValidator: 실행 허용 여부.
- 실제 tool result와 검증된 원문: 최종 결과·설명의 근거.

### KG 사용

- 승인된 mapping edge만 확정 실행 binding의 근거로 사용한다.
- `DEFERRED`, `CANDIDATE`, `NEEDS_REVIEW` 관계는 후보/경고로 유지한다.
- 최단 graph path나 높은 similarity만으로 supportsConcept를 VERIFIED 처리하지 않는다.
- `mentionsFeature`, `relatedTo`, `supportsConcept`, 실제 공간연산 관계를 구분한다.
- graph path에 실제 edge ID, source, version, 검증 상태를 포함한다.
- 검색 hop/fan-out/context 크기에 상한을 둔다.
- KG에서 tool ID를 얻어도 Tool Registry에서 실제 구현·버전·입출력 계약을 검증한다.
- KG가 없거나 관련 edge가 부족하면 승인된 Dictionary/Registry 경로만 명시적으로 허용한다.
  가짜 graph path를 생성하지 않는다.

### 스키마 adapter

우선 확인 대상:
- `projection.s101_feature_valid`
- `serving.accident_s101_relation_current`

실제 relation 종류, 컬럼, 키, type, SRID, geometry dimension, code mapping을 먼저 확인한다.
`geometry`, `distance_meters`라는 사용자 보고값도 실제 스키마에 대조한다.

외부 계약은 일관되게 `geometry`, `distance_m`을 사용하되,
사고 relation의 `distance_meters`는 adapter/SELECT alias에서 `distance_m`으로 변환할 수 있다.
물리 DB 컬럼 이름을 억지로 rename하지 않는다.
표준 이름과 DB NFTC의 매핑은 catalogue edition과 dataset namespace로 구분한다.
다른 dataset에서 같은 code가 다른 의미로 쓰이는 경우를 처리한다.

SQL은 검증된 template + 바인딩된 값만 실행한다.
테이블/컬럼 식별자는 승인된 Registry와 스키마 확인 결과에서 가져와 driver 방식으로 안전하게 quote한다.
사용자 문자열, 문서 내용, KG 설명 문자열을 SQL 식별자나 SQL 문장으로 실행하지 않는다.

실제 geometry가 geographic CRS인지 확인하기 전에 무조건 ::geography를 붙이지 않는다.
CRS/축 순서/단위가 불명확하면 차단하고 임의의 EPSG를 붙여 문제를 감추지 않는다.

문서: `03_schema_bindings.md`, `04_kg_authority_and_paths.md`.

---

## Phase 4. 연산별 deterministic ExecutionValidator

공통 계약이 모두 채워졌다는 이유만으로 ready를 만들지 않는다.
작업별 입력·도구·데이터·권한을 검사한다.

### radius feature search

- 명확한 기준 geometry 또는 접근 가능한 geometry ref.
- 검증된 CRS와 axis order.
- 유한한 양의 distance_m 및 서비스 범위 제한.
- 비어 있지 않은 승인된 feature target/filter와 제외 조건.
- 실제 dataset/컬럼/code binding과 조회권한.
- 해당 operation을 지원하는 Tool 및 Query Template.
- 입력 스키마 검증, timeout, result limit, pagination, 비용 예산.

### area search

- 검증된 AOI geometry 또는 명시적으로 채택된 workspace AOI.
- 대상 필터와 승인된 data/tool bindings.
- 반경은 필수 아님.

### nearest search

- 기준 geometry, 대상 필터, 허용된 k.
- `nearest`를 일반 location+target 분기보다 우선 처리.

### document search

- 질의, 접근 가능한 활성 collection, 인증 권한.
- query/document embedding profile 호환 또는 명시적으로 허용된 lexical mode.
- 위치·반경·S-101 geometry 불필요.

### accident-feature relation lookup

- 실제 relation의 join key와 관련 feature instance namespace 확인.
- 거리 단위, 산출 threshold, source snapshot, 사고 위치 정확도, 시간범위 확인.
- 사전계산 관계의 산출시점/범위를 벗어난 요청은 다시 계산할 수 있는지 판단하거나 보류.
- 관계 행 수를 사고 건수로 바로 쓰지 않는다. 통계는 고유키와 중복 규칙 명시.

### 결과 상태

계획 상태와 실행 결과 상태를 별도 enum으로 유지한다.
권장 계획 상태: DRAFT, NEEDS_USER_INPUT, BLOCKED_CONFIG, BLOCKED_DATA,
BLOCKED_POLICY, PLAN_READY, EXECUTION_READY.
권장 작업 결과: SUCCESS, SUCCESS_EMPTY, NO_EVIDENCE, FAILED, CANCELLED.
요청 전체 결과: SUCCESS, PARTIAL_SUCCESS, NEEDS_USER_INPUT, BLOCKED, FAILED.

- 낮은 context 점수 하나로 모든 요청을 clarification 처리하지 않는다.
- confidence를 임의로 0.9로 올려 실행시키지 않는다.
- execution_ready는 검증된 plan revision/hash에 귀속된다.
- 실행 직전 실제 연결/권한/버전 변경을 필요한 범위에서 재확인한다.
- 모든 질의에 RAG를 강제하지 않는다. 공간검색-only 작업은 문서 근거 부재와 분리한다.

문서: `05_execution_validation_and_errors.md`.

---

## Phase 5. 전문 Agent 단일 계약 실행 및 Mock 차단

Phase 1 이후부터 각 수정 경로에 즉시 적용하는 우선 차단 항목이다.

- Spatial Agent는 ValidatedTaskPlan만 받는다.
- 자연어 재해석, 다른 state 경로에서 슬롯 재수집, 임의의 위치/반경 생성 금지.
- DB 이름/테이블/컬럼 fallback이 조용히 다른 DB를 조회하지 않게 한다.
- 연결·SQL·매핑 오류와 정상 0건 결과를 구분한다.
- 오류 시 sample feature나 가상 법령을 만들어 반환하지 않는다.
- production에서는 mock provider import/DI 주입을 차단한다.
- test 모드 설정은 서버의 신뢰된 설정으로만 가능하며 사용자 요청으로 변경할 수 없다.
- 단위 테스트 fixture는 허용하되 is_mock=true, fixture_id를 포함하고 실제 성능/근거로 보고하지 않는다.
- retry는 읽기 전용 일시적 실패에만 제한적으로 적용한다. 스키마/인증 오류를 반복 재시도하지 않는다.

PostGIS 연산의 의미를 구분한다.
- ST_DWithin: 거리 임계값 이내 여부.
- ST_Intersects: 경계 접촉 등을 포함한 교차 여부.
- overlapsLayer/overlapsFeature: 팀에서 정의한 overlap 의미와 실제 predicate/차원 조건을 일치시킨다.
  ST_Intersects=true라는 이유만으로 면적 중첩이 입증됐다고 하지 않는다.
- occurredIn은 경계점 포함 정책과 위치 오차를 명시한다.

공간결과에는 실제 feature ID, dataset/cell/version, geometry, 거리/연산정보,
query execution ID, result limit/truncated 여부를 포함한다.
지도 원은 backend 또는 frontend 중 단일 소유자가 생성하고,
한 작업의 검색범위는 하나의 geometry로 전달한다.
반경 도형에 fill/outline 두 style layer가 필요한 것과 중복 반경을 구분한다.
동일 결과의 재전송/SSE 재연결에도 map result를 중복 추가하지 않는다.

문서: `06_agents_and_no_mock_policy.md`.

---

## Phase 6. RAG 검색과 생성 LLM 분리

기존 1,869개 S-101 chunk/embedding과 전체 컬렉션을 보존한다.
문서 전체 재임베딩으로 문제를 해결하려 하지 않는다.

### 가용성 분리

- vector_store_available
- query_embedding_available
- embedding_profile_compatible
- generation_llm_available
- lexical_search_available

`llm_api_enabled()` 하나로 모든 검색을 차단하지 않는다.
단, 벡터 검색에 query embedding이 필요하다는 조건까지 제거하지 않는다.
생성 LLM이 꺼져도 query embedding과 DB가 준비되면 근거 검색은 동작해야 한다.
query embedding이 없으면 검증된 동일 profile의 cache 또는 허용된 lexical 검색을 사용할 수 있다.
이때 retrieval_mode와 degraded reason을 표시한다.
가짜 vector/유사도를 만들거나 다른 embedding 공간을 섞지 않는다.

### 실제 profile 검증

model ID/revision/digest, dimension, pooling, normalization, input template,
tokenization/truncation 정책을 현재 활성 컬렉션과 질의 모델에서 대조한다.
같은 차원인 다른 모델을 호환된다고 판단하지 않는다.
활성 relation은 현재 코드/DB에서 확인한다. 새 active view를 자동 생성·전환하지 않는다.

### 검색

- 문서 권한/tenant/승인 상태/적용 버전 필터는 필수로 유지.
- KG 기반 topic/feature/concept 후보 필터는 검색 목적에 따라 optional hint로 사용.
- graph mapping이 불완전해 0건이면, 강제 보안·버전 조건은 유지한 채
  승인된 범위에서 topic filter 완화 또는 lexical/hybrid retrieval을 허용.
- exact vector search를 기준선으로 두고 현행 ANN index 결과와 비교한다.
- 필터+ANN에서 결과가 줄어드는 문제를 실제 버전/실행계획으로 확인한다.
  인덱스를 자동 재생성하지 않는다.
- embedding cosine similarity는 검색 점수다. 법적 타당성·증거 신뢰도 확률이 아니다.

### citation 계약

각 근거에는 적어도 다음을 반환한다.
- evidence_id, chunk_id, document_id, source_id/source_group
- source_file, title, section, document_type, product_id, edition/version
- page/row/span 중 실제 존재하는 source locator
- excerpt 및 content hash
- retrieval_mode, score_type, score (실제 제공된 경우)
- embedding_profile_ref, collection_version
- 연결된 graph path IDs, verification status, source kind

원문에 없는 조항·페이지 번호를 채우지 않는다.
법령 목록/요약 CSV를 법령 전문이나 최신 시행 조항으로 취급하지 않는다.
관련 용어가 있다는 사실과 분석 결론을 지지한다는 사실을 구분한다.

문서: `07_rag_retrieval_and_citations.md`.

---

## Phase 7. 결과 중심 EvidenceBundle 및 응답 통합

다음 상위 응답 구조를 구현하되 기존 public API와 호환될 adapter를 제공한다.

- status, request_id, contract_version
- answer_text
- task_plan (권한별 공개 필드 제한)
- spatial_result_summary
- rag_evidence[]
- spatial_feature_evidence[]
- accident_relation_evidence[]
- kg_provenance[]
- claims[]
- task_results[]
- warnings[], blockers[]
- execution_trace 또는 trace_id (권한 제한)

### 근거 유형별 의미

- spatial_feature_evidence: 실제 DB에서 조회한 객체와 실제 계산 결과.
- accident_relation_evidence: 특정 사고/객체/거리/기간을 연결하는 실제 관계 레코드.
- rag_evidence: 원문에서 검색한 관련 구절.
- kg_provenance: 대상/도구/문서 선택에 사용한 승인된 의미 경로.

KG에 `Wreck`가 존재하는 것은 특정 위치에 침선이 있다는 증거가 아니다.
사고가 객체 근처에서 발생한 것은 그 객체가 사고 원인이라는 증거가 아니다.
규정 chunk가 검색된 것은 위법/안전/운항가능성이 입증됐다는 의미가 아니다.
안전 판정이 아닌 객체 조회 결과는 "검색된 객체/주의 후보"로 표현한다.
부표 전체를 위험물로, DepthArea 전체를 저수심 위험으로 자동 분류하지 않는다.
승인된 개념 조건과 실제 속성·기준을 사용한다.

### 연결성과 검증

- stable request_id → task_id → query_execution_id → result/evidence_id를 연결한다.
- claims[].evidence_ids로 답변의 건수·거리·객체명·문서 설명을 실제 근거에 연결한다.
- evidence ID는 adapter가 생성하고 LLM은 허용 ID만 선택한다.
- 건수/거리/좌표는 SQL/tool 결과에서만 가져온다.
- summary의 전체 건수와 출력 페이지/지도 표시 건수를 구분한다.
- map/table/summary는 동일 result reference를 사용한다.
- 최종 validator가 dangling evidence ID, 결과와 다른 숫자, 버전 불일치를 검사한다.
- 선택적 RAG 실패 시 공간결과는 PARTIAL_SUCCESS로 유지할 수 있다.
  필수 의존 작업 실패 시 그 의존 결과를 성공으로 표시하지 않는다.
- 생성 LLM이 없으면 구조화된 결과/근거와 결정적 요약을 반환한다.

### Trace와 cache

trace에는 node 이름, 처리시간, context revision/hash, 필드 변경,
검증 gate, template ID/hash, 허용된 query params, 실제 result count, error code를 저장한다.
LLM의 비공개 추론 과정 대신 관측 가능한 데이터 흐름만 기록한다.
일반 사용자에게 credential·내부 DSN·민감 스키마·권한외 근거를 노출하지 않는다.
cache key에는 최소한 권한 scope, 계약/plan 버전, 위치·거리·제외조건,
데이터/문서/embedding/KG 버전을 포함한다. 다른 사용자나 다른 반경으로 재사용하지 않는다.

문서: `08_evidence_response_and_trace.md`.

---

## Phase 8. 회귀 테스트, 안전 적용 및 완료 기준

### 테스트 A. 계약·상태

- 위치/거리/대상이 각 단계의 직렬화·역직렬화 후 유지된다.
- 다음 노드의 None/빈 dict가 기존 명시 슬롯을 삭제하지 않는다.
- 사용자가 "부이 제외"라고 변경하면 명시적 제외가 유지된다.
- 승인된 KG 대상 확장과 의미 대안 후보가 구분된다.
- feature ID/코드의 dataset 또는 edition이 다른 경우 혼합되지 않는다.
- 슬롯 변경 후 예전 ValidatedTaskPlan과 cache를 재사용하지 않는다.
- 병렬 작업과 SSE 재전송이 다른 task의 상태를 덮어쓰거나 중복시키지 않는다.

### 테스트 B. 연산별 gate

- 반경검색에 위치명이 있지만 geometry 미확정 → 실행 차단.
- distance_m 누락/음수/NaN/무한대/상한 초과 → 실행 차단.
- 영역검색에 승인 AOI가 있으면 반경 없이 통과 가능.
- "부산항에서 가장 가까운 정박지"가 영역검색으로 바뀌지 않음.
- Tool ID가 미등록이거나 DB 컬럼이 없으면 BLOCKED_CONFIG.
- 권한 부족은 BLOCKED_POLICY. 사용자 질문이 모호하다고 응답하지 않음.
- 순수 문서 설명 질의는 공간 DB 없이도 검색 가능.

### 테스트 C. 실제 스키마 및 Mock

- 검증된 `geometry` binding으로 실제 query가 실행됨.
- `distance_meters`를 내부 `distance_m`으로 일관되게 반환.
- DB timeout/schema error는 FAILED로 반환하고 Mock을 생성하지 않음.
- 실제 검색 0건은 SUCCESS_EMPTY 또는 NO_EVIDENCE.
- production mock provider 설정은 시작 또는 실행 시 거부.
- test fixture 결과는 실제 DB 결과와 명확히 구분.

### 테스트 D. RAG

- 생성 LLM off + query embedder/DB on → 실제 근거 검색 가능.
- query embedder off → 명시적인 제한/허용된 lexical mode.
- query/document embedding profile 불일치 → 벡터검색 차단.
- 임베딩 차원이 같아도 모델 revision이 다르면 호환성 검사.
- 모든 반환 근거가 실제 chunk/source locator로 추적됨.
- PUBLIC 요청에 권한외 본문, citation, KG path, cache 내용이 노출되지 않음.
- soft KG filter 완화 시 hard security/edition filter 유지.
- index 기반 검색과 exact baseline의 후보/latency 비교.

### 테스트 E. 대표 end-to-end

1. "부산항 입구 3km 이내 위험객체를 찾아줘"
   - approved context/target 정책을 사용.
   - 위치가 확정되지 않으면 근거 없는 임의 좌표 대신 후보/보완 요청.
   - 확정된 실제 또는 승인된 테스트 기준점이면 3,000m 범위 조회.
   - 정답 건수는 fixture 또는 동일조건 기준 SQL 결과로 결정.
   - 지도·표·요약·evidence의 객체 ID와 건수 일치.

2. "부산항에서 가장 가까운 정박지를 찾아줘"
   - nearest operation 유지.

3. "부이를 제외하고 같은 범위의 위험객체를 보여줘"
   - 이전 범위와 명시적인 제외조건 유지.
   - "부이"의 일부가 조사 제거로 손상되지 않음.

4. "이 객체 근처에서 발생한 사고를 알려줘"
   - 실제 feature instance key, 관계 거리, 기간, 사고 ID를 반환.
   - 관계 레코드와 고유 사고 수 구분, 인과 추정 금지.

5. "S-101 2.0에서 해당 객체의 정의와 인코딩 지침을 설명해줘"
   - 실제 definition/DCEG source evidence.
   - 다른 edition 또는 단순 법령 목록을 근거로 바꾸지 않음.

6. "AIS 통항량과 위험객체를 함께 보여줘"
   - 실제 traffic 자료의 원시/집계/항로/시점/밀도값 유무에 따라 지원 범위 결정.
   - 항로 폴리라인만 있다고 통항량, CPA/TCPA, 실시간 충돌위험을 만들지 않음.

7. 실패 시나리오
   - DB 장애, RAG 0건, geometry 미확정, 잘못된 코드, 권한 부족, stale KG.
   - 모두 정직한 상태·blocker·부분 결과를 반환.

### 실제 데이터 보존 검증

- 수정 전후 승인된 동일 snapshot에서 projection/RAG/관계 기준선 비교.
- 새로운 데이터를 적재하지 않는 이번 수정으로 기존 1,869개 문서 집합이 손상되지 않음.
- source group 10개의 존재 여부와 실제 식별 기준을 확인.
- 외부 갱신으로 숫자가 바뀐 경우 원인/검사시간을 기록. 숫자를 억지로 맞추지 않음.
- 실제 DB 테스트와 mock/unit 테스트 결과를 별도 리포트로 작성.
- 실행하지 못한 DB·UI 테스트를 PASS로 표시하지 않음.

### 산출물

`docs/execution_contract/`
- 00_baseline.md
- 01_contract_schema.md
- 02_state_merge_policy.md
- 03_schema_bindings.md
- 04_kg_authority_and_paths.md
- 05_execution_validation_and_errors.md
- 06_agents_and_no_mock_policy.md
- 07_rag_retrieval_and_citations.md
- 08_evidence_response_and_trace.md
- 09_test_and_rollout.md
- IMPLEMENTATION_STATUS.md

`outputs/reports/execution_contract/<run_id>/`
- baseline.json
- unit_test_results.json
- integration_test_results.json
- live_readonly_test_results.json
- e2e_result_samples.json
- contract_field_lineage.jsonl
- final_report.md

문서에는 설계 예시와 실제 구현/실측 결과를 명확히 구분한다.
상태는 DONE / PARTIAL / BLOCKED / NOT_RUN 중 하나로 기록한다.

### 완료 기준

- 기존 데이터/임베딩 재구축 없이 단일 실행계약으로 end-to-end 동작.
- 슬롯 누락·덮어쓰기·명칭 불일치가 contract boundary에서 검출됨.
- Agent 존재만으로 execution_ready를 만들지 않음.
- 운영 Mock 정상응답 0건.
- 실제 공간검색 0건과 실패가 구분됨.
- 생성 LLM과 RAG 검색 가용성이 분리됨.
- 실제 결과와 모든 citation/evidence ID 연결이 검증됨.
- 대표 질의와 실패 시나리오 테스트 통과, 미실행 범위 명시.

---

## 실행 방식

처음에는 Phase 0~2를 구현하고 테스트한다.
다음 단계는 이전 단계의 테스트가 통과한 후 진행한다.
각 단계마다 변경 파일, command, 관측 결과, 미해결 blocker를 기록한다.
DB를 변경해야만 진행할 수 있다면 임의로 실행하지 말고 migration/rollback 계획과 사유를 제출한다.
기존 기능과 같은 모듈을 중복 생성하지 말고 현재 코드 구조에 최소 수정으로 통합한다.

첫 세션 목표:
**최신 상태 확인 → QueryExecutionContext 정의 → state 병합 안정화 → 회귀 테스트.**
기존의 정상 S-101 DB, RAG embedding, 사고 relation 데이터를 보존하는 것을 우선한다.

---

## 기술 참고 문서

아래는 구현 원리를 확인하기 위한 공식 문서다. 설치 버전의 실제 API/옵션과 대조한다.

- Codex CLI reference: https://developers.openai.com/codex/cli/reference/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md/
- Codex 사용/권한 관련 도움말: https://help.openai.com/en/articles/11369540
- Pydantic strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- LangGraph state/reducers: https://docs.langchain.com/oss/python/langgraph/graph-api
- PostGIS ST_DWithin: https://postgis.net/docs/ST_DWithin.html
- PostGIS ST_Intersects: https://postgis.net/docs/ST_Intersects.html
- pgvector: https://github.com/pgvector/pgvector
