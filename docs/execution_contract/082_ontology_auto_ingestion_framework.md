# Phase 8.2 온톨로지 자동 수집 프레임워크

## 목적

새로운 해양수산 데이터가 `Dataset`에 추가되었을 때, 시스템이 파일 구조와 이름, 공간 필드, 표준 문서 신호를 읽고 온톨로지 후보를 자동 제안한다. 단, 자동 제안은 실행 권한이 아니다. 실행은 `QueryExecutionContext -> ExecutionValidator PASS -> Tool 실행 -> EvidenceBundle 반환` 경로를 통과해야 한다.

## 처리 흐름

1. `scripts/profile_dataset_for_ontology.py`
   - `Dataset` 파일을 순회한다.
   - 압축 파일 구성, Shapefile 헤더, 필드명, 좌표계 추정, 포맷 신호를 `outputs/ontology/dataset_profiles.jsonl`에 저장한다.
   - 대용량 압축은 기본적으로 내부 목록만 읽고 `metadata_only` 후보로 남긴다.

2. `scripts/propose_ontology_bindings.py`
   - `data/ontology_ingestion_rules.yaml`의 규칙을 적용한다.
   - Upper Ontology, 해양수산 업무 도메인, S-100/S-101/S-104/S-111/S-124 제품 후보를 제안한다.
   - 결과는 `outputs/ontology/ontology_binding_proposals.jsonl`, `outputs/ontology/registry_patch_proposals.yaml`, `outputs/review/ontology_binding_needs_review.jsonl`에 저장한다.

3. 검토 및 승격
   - `NEEDS_REVIEW`는 사람 또는 별도 승인 도구가 검토한다.
   - 검토된 후보만 `data/spatial_layer_registry.yaml`, `data/data_registry.yaml`, `data/*_registry.yaml`에 병합한다.
   - 병합 후 KG 재생성 및 ontology validator를 통과해야 `VERIFIED`로 승격한다.

## 안전 원칙

- 자동 제안은 KG의 `VERIFIED` 관계가 아니다.
- `execution_status: executable`은 자동 생성하지 않는다.
- LLM이 후보 설명을 보강할 수는 있지만 Tool 실행 권한의 근거가 될 수 없다.
- 공간 실행은 물리 테이블, geometry column, SRID, 지원 연산, schema adapter 검증이 있어야 한다.
- RAG/법령/사고/공간 근거는 EvidenceBundle에서 분리 반환한다.

## 현재 분류 축

- 항행 위험 객체: 침선, 장애물, 암초, 간출암, 세암, 어초, 와류
- 규제·제한 해역: 진입제한, 속도제한, 정박금지, 조업 제한, 투기장, 통항분리
- 보호·보전 해역: 보호수역, 해양보호, 수산자원보호, 바다목장
- 해양관측·수로조사: 수치조류도, 조류, 조석, 조위, 바다갈라짐, 갯골
- 선박교통: AIS, V-PASS, 항로, 통항, 관제, 계선부표, 정박지
- 해양사고: 조난, 충돌, 좌초, 인명사고, 해양안전심판원, 해양경찰
- 해양 지명: 도서지명, 해양지명, 어항구, 항만, 신항만
- 법령·표준 문서: 법령, 행정규칙, 고시, S-100 계열 표준, DCEG

## 다음 보강

- 검토 완료 후보를 registry에 병합하는 승인 전용 스크립트
- S-101 Feature Catalogue와 DCEG의 feature/attribute 자동 매칭 점수화
- 법령·고시 RAG chunk와 데이터 레이어의 `authorizedBy`, `definedBy` 연결 자동 제안
- QueryExecutionContext DataBinding/ToolBinding 후보를 제안하되, ExecutionValidator가 최종 차단하도록 통합
