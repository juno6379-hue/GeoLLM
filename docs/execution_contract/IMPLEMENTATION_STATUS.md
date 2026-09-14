# 구현 현황

Run ID: 20260914-132336

## 완료

- `docs/CODEX_GEOLLM_EXECUTION_CONTRACT_PROMPT.md`를 분석하고 실행계약 개발 기준으로 반영했다.
- `shared.schemas.agent`에 실행계약 모델을 확장했다.
- `QueryExecutionContext`, `ExecutionSlots`, `DataBinding`, `ToolBinding`, `EvidenceBundle` 기반 구조를 추가했다.
- slot patch 병합 정책을 provenance와 함께 비파괴 방식으로 추가했다.
- `AgentResult`에 `answer_text`, `spatial_result_summary`, `EvidenceBundle`, `claims`, `task_results`를 추가했다.
- 오케스트레이터가 `contract_version`, request/task ID, `plan_hash`, readiness, blockers, warnings, snapshot, semantic resolution을 포함한 실행계약을 만들도록 수정했다.
- Spatial Agent와 RAG Agent가 `answer_text`를 우선 반환하도록 수정했다.
- 대시보드 결과 표시가 `final_result.answer_text`를 우선 사용하도록 수정했다.
- `SchemaBindingAdapter`를 추가하여 registry의 layer/tool/template ID를 실제 DB schema 검사와 연결했다.
- deterministic `ExecutionValidator`를 추가하고, agent 실행 전 gate로 연결했다.
- S-101 반경/영역/최근접 검색, RAG 문서 검색, 사고 relation 조회에 대한 `DataBinding`과 `ToolBinding`을 채우도록 했다.
- `QueryExecutionContext`가 준비되지 않은 경우 Spatial Agent, Accident/Risk Agent, AIS Analysis Agent 실행을 차단하도록 했다.
- 운영 실행 경로에서 LLM/geocoding/default fallback을 우회하고, 검증된 실행계약 기반 `QueryPlan`을 사용하도록 했다.
- `feature_dwithin`에서 거리 기본값을 조용히 넣던 SQL compiler fallback을 제거했다.
- Phase 5.5 KG 온톨로지 계약을 추가했다.
- KG 온톨로지 validator와 단위 테스트를 추가했다.
- `Dataset/용어사전.xls` 기반 Phase 5.6 용어 온톨로지 확장을 추가했다.
- `MarineTerm` taxonomy, 검토 큐, S-101 catalogue 기반 용어 매칭, KG taxonomy node/edge 생성을 추가했다.
- 수동 검증된 용어사전과 생성된 용어사전을 병합하되 수동 사전을 우선하도록 했다.
- QueryNormalizer가 생성 사전과 수동 사전을 함께 읽도록 수정했다.
- Phase 6 EvidenceBundle builder를 추가하여 KG/RAG/공간/사고 근거를 분리했다.
- Standard RAG Agent와 오케스트레이터 최종 응답에 typed `EvidenceBundle`을 연결했다.
- Phase 7 공간 레이어 registry를 확장했다.
  - 사고 relation
  - 수치조류도
  - 와류
  - 신항만예정지역
  - 도서지명
  - 바다갈라짐 예측정보
  - 선박안전교통관제구역
- AIS/V-PASS 동적 교통 registry를 정상 파일명 기준으로 정리하고 실행 검증에 연결했다.
- 공간 레이어 analysis type에 대한 schema binding과 execution validation을 확장했다.
- Accident/Risk Agent가 `serving.accident_s101_relation_current`를 읽기 전용으로 조회하도록 구현했다.
- `EvidenceBundle`에 `spatial_layer_evidence`를 추가하고 대시보드 카운트 표시를 연결했다.
- Phase 5.7 법령·고시 온톨로지 registry를 추가했다.
- KG에 법령, 고시, 기관, 공식자료 노드와 `authorizedBy`, `definedBy`, `publishedBy`, `derivedFrom` 관계를 추가했다.
- KG를 재생성했다.
  - nodes: `8799`
  - edges: `9539`
  - ontology validator: `PASS`
- `EvidenceBundle`에 `regulatory_evidence`를 추가하고 대시보드 카운트 표시를 연결했다.
- Phase 7.2 Dataset Adapter / Ingestion을 추가했다.
- shapefile 기반 공간 레이어 4종을 PostGIS serving table로 적재했다.
  - `island_gazetteer`: `serving.island_gazetteer_current`, 1,140건
  - `planned_port_area`: `serving.planned_port_area_current`, 12건
  - `eddy_hazard_area`: `serving.eddy_hazard_area_current`, 620건
  - `vessel_traffic_control_area`: `serving.vessel_traffic_control_area_current`, 40건
- 적재 완료 레이어는 registry에서 `executable`과 실제 `physical_table`로 승격했다.
- Phase 7.4 수치조류도 metadata adapter를 추가했다.
  - `serving.tidal_current_surface_metadata`
  - 상태: `metadata_only`
  - 조류 속도/방향 grid parser 확정 전까지 `current_tidal_lookup`은 `BLOCKED_DATA`로 차단한다.
- Phase 7.5 위험해역 adapter를 추가했다.
  - `serving.hazard_area_current`, 436건
  - 주의경계해역, 속도제한구역, 진입제한, 정박금지/투묘금지, 낚시금지/제한, 투기장
  - `hazard_area_lookup`은 `ExecutionValidator` 통과 후 실제 PostGIS SQL로 실행된다.
- 보호수역은 위험해역이 아니라 보호·보전 목적의 공간 제약 레이어로 재분류했다.
  - `serving.protected_area_current`, 1건
  - `protected_area_lookup`으로 별도 조회한다.
  - 법령 근거 후보: `해양생태계의 보전 및 관리에 관한 법률`
- KG를 재생성했다.
  - nodes: `8846`
  - edges: `9642`
  - ontology validator: `PASS`
- Phase 8.1 해양수산부 범용 Upper Ontology 1차를 추가했다.
  - KG Inventory
  - Upper Ontology
  - 해양수산 업무 Domain
  - S-100/S-101 Mapping
  - 보호수역을 `protected_area`로 분리한 구조를 상위 온톨로지에 반영했다.

## 부분 완료

- `ValidatedTaskPlan` 모델은 존재하지만, 불변 plan snapshot은 아직 `QueryExecutionContext.readiness`와 `plan_hash` 중심으로 표현된다.
- RAG citation 계약은 기존 `structured_result.citations`를 통해 부분 연결되어 있다. locator/hash/profile 검증은 추가 작업이 필요하다.
- 수치조류도는 metadata table까지 등록되었지만 조류 값 grid parser가 없어 value lookup은 차단된다.
- 바다갈라짐, AIS, V-PASS는 registry에 등록되었지만 아직 serving table로 ingestion되지 않았다.
- 미적재 레이어는 `BLOCKED_DATA`로 차단된다. mock fallback은 허용하지 않는다.
- Spatial Agent 내부 legacy code는 남아 있지만, 검증된 실행계약이 제공되면 contract path가 우선한다.
- Phase 5.6 taxonomy는 보수적 keyword 기반이므로 `outputs/review/kg_needs_review.jsonl` 검토 큐를 계속 줄여야 한다.
- 법령·고시 registry의 `CANDIDATE` 공식자료는 원천기관 메타데이터와 고시 여부를 추가 확인해야 한다.

## 실행하지 못한 것

- host pytest는 host Python에 일부 의존성이 없어 실행하지 못했다.
- backend container에는 `pytest`가 설치되어 있지 않아 전체 pytest는 실행하지 못했다.
- 전체 `ST_IsValid(geometry)` scan은 이전 baseline 작업에서 시간 제한으로 중단된 상태다.

## 다음 단계

1. 수치조류도 `.data` 바이너리 grid 사양을 확정하고 속도/방향 parser를 구현한다.
2. 바다갈라짐 예측정보와 도서/지점 geometry binding을 구현한다.
3. AIS/V-PASS 대용량 동적 교통 레이어의 샘플/증분 적재 정책을 확정한다.
4. 레이어별 geometry 컬럼, CRS, 시간 컬럼, 속성 스키마, 공간 index 검증 규칙을 추가한다.
5. KG의 `authorizedBy`, `definedBy`, `publishedBy`, `derivedFrom` 경로를 최종 응답의 `regulatory_evidence`로 자동 변환한다.
6. `outputs/review/kg_needs_review.jsonl`에 대한 전문가 검토 workflow를 만든다.
7. 비활성 mock 생성 블록을 테스트 fixture로 완전히 격리하거나 제거한다.
