# Phase 5 — U-Port Agent Core 계획 계층 결과

## 완료 작업

- 기존 `data/capability_registry.yaml`에 도메인별 U-Port Capability 5개와 의존 관계, 데이터 가용성, 공통 메타데이터를 등록.
- 기존 `QueryCandidateBroker`에 도메인 한정 후보 검색을 추가하고 GeoLLM의 일반 후보 Top-K에서는 U-Port 항목을 제외해 기존 라우팅 간섭을 방지.
- 지도 선택 이벤트를 공통 `QueryExecutionContext.slots.feature_instance_ref`와 `context`에 전달할 수 있는 입력 계약 추가.
- `uport_resolver_registry.yaml`을 통해 선택 객체의 S-101 Berth ontology 후보를 해석. 현재 DB의 해당 ID 존재 여부는 검증하지 않았으므로 `CANDIDATE`로 표시.
- Registry 의존 관계를 확장하는 다중 Capability 실행 순서 계획, 누락/순환 의존성 거부.
- 기존 `validate_execution_context` 진입점에 U-Port 계획 검증 분기 추가. 미연결 AIS·ETA·최적화 데이터와 누락된 Entity는 차단.
- `POST /api/v1/uport/query/plan` 추가. 결과는 기존 QEC 계약이며 `plan_only`, 최대 `PLAN_READY`이다. Tool 실행은 하지 않는다.

## 수정 파일

- `data/capability_registry.yaml`
- `services/orchestrator/query_candidate_broker.py`
- `services/orchestrator/execution_validator.py`
- `services/orchestrator/main.py`
- `services/orchestrator/static/uport/map.js`

## 신규 파일

- `data/uport_resolver_registry.yaml`
- `services/uport/fast_path.py`
- `services/uport/planning.py`
- `services/uport/planning_router.py`
- `services/uport/resolver_registry.py`
- `services/uport/validation.py`
- `tests/unit/test_uport_planning.py`
- `docs/uport/12_phase5_result.md`

## 재사용한 기존 구성과 아키텍처 변경

공통 `QueryExecutionContext`, `ExecutionSlots`, `PlanStatus`, `QueryCandidateBroker`, `ExecutionValidator`와 `/api/v1` 라우터 규칙을 재사용했다. U-Port의 계획 모듈만 새로 분리했다. FastPath는 명시적 지도 선택 신호만 생성하며 검증 단계를 우회하지 않는다. 실제 KG/DB 객체 ID 검증과 Tool 바인딩은 아직 이루어지지 않았으므로 실행 권한은 부여하지 않는다.

## 실행·테스트 결과

- 신규 U-Port 테스트와 기존 Capability 브로커 테스트: 18개 통과.
- GeoLLM 실제 앱 `TestClient`에서 계획 API HTTP 200 및 `PLAN_READY` 확인.
- Python 컴파일, JavaScript 문법, `git diff --check` 확인.
- 기존 `test_execution_validator.py` 26개 중 1개 실패: `test_sea_parting_blocks_until_ingested`가 예상 `BLOCKED_DATA` 대신 `BLOCKED_CONFIG` 반환. 수정한 U-Port 분기는 `analysis_type=uport_query_plan`에만 적용되며 해당 테스트의 분석 유형은 `sea_parting_prediction_lookup`이다. 해당 실패의 기준선 여부와 별도 원인은 추후 확인 필요.

## 발견된 문제와 남은 작업

- 지도 선택 선석 ID는 ontology 후보까지만 검증했다. DB 존재와 Dataset 버전 일치 확인이 필요하다.
- Port/Vessel/Time Resolver는 Registry 확장 전이다. 현재는 `port_id`가 입력되었는지만 검사하며 실제 항만 존재 검증은 하지 않는다.
- 실시간 AIS, ETA 모델, 항만 운영 데이터가 미연결이므로 관련 계획은 `BLOCKED_DATA`로 반환한다.
- Phase 6에서 전문 Agent/Tool에 연결하고, 실제 데이터 바인딩 및 실행 결과·근거 계약을 구현해야 한다.
