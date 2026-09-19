# Phase 6 — U-Port Domain Agent 실행 경계 결과

## 완료 작업

- S-101 전문 Agent를 읽기 전용 선석 피처 조회 경로에 연결했다.
- 지도에서 전달된 정수형 선석/데이터셋/버전 ID와 S-101 2.0 제품 규격을 DB에서 재검증한 후에만 Tool을 실행한다.
- 실제 DB 피처에서 GeoJSON, 기존 `MapLayerSpecification`, `EvidenceItem`과 짧은 사실 설명을 생성한다.
- Capability 메타데이터의 Agent 이름과 실제 구현 Adapter를 별도 Registry에서 교차 확인한다. 현재 실행 가능한 Adapter는 `S101Agent`뿐이다.
- AIS, ETA 예측, 선석 최적화, 항만 지식은 Agent 이름이 등록되어 있어도 원천 데이터/구현이 없으면 실행되지 않는다.
- `POST /api/v1/uport/query/execute`를 추가했다. 오류는 `DATASET_NOT_AVAILABLE`, `ENTITY_NOT_FOUND`, `TOOL_TIMEOUT`, `TOOL_EXECUTION_ERROR`, `INVALID_GEOMETRY`, `VALIDATION_FAILED` 등으로 구분한다.

## 수정 파일

- `data/capability_registry.yaml`
- `services/uport/planning.py`
- `services/uport/planning_router.py`
- `tests/unit/test_uport_planning.py`

## 신규 파일

- `services/uport/agent_registry.py`
- `services/uport/s101_agent.py`
- `services/uport/execution.py`
- `tests/unit/test_uport_execution.py`
- `docs/uport/13_phase6_result.md`

## 재사용한 기존 구성과 아키텍처 변경

기존 `QueryExecutionContext`, `DataBinding`, `ToolBinding`, `EvidenceItem`, `MapLayerSpecification`과 GeoLLM Capability Registry를 사용한다. QEC가 `PLAN_READY`이고 DB에서 선택 ID/데이터셋/버전이 확인된 경우에만 `EXECUTION_READY`로 바뀐다. LLM은 조회 수치나 지오메트리를 생성하지 않는다.

## 실행·테스트 결과

- U-Port 단위/계약 테스트와 기존 Capability 브로커 테스트 22개 통과.
- 실제 GeoLLM 앱 `TestClient`에서 미설정 S-101 DB의 `/api/v1/uport/query/execute`가 `DATASET_NOT_AVAILABLE`로 차단되는 것을 확인.
- DB 경계 테스트에서 ID/버전 일치 시 Feature·지도 레이어·Evidence를 반환하고, 불일치 시 Tool 실행 전 중단하며, AIS 질의는 DB 접근 없이 차단됨을 확인.
- Python 컴파일과 `git diff --check` 통과.

## 발견된 문제와 남은 작업

- 호스트 Python의 로컬 PostGIS 인증/문자 인코딩 오류 때문에 신규 실행 API의 실제 DB 성공 응답은 검증하지 못했다. DB 내부 S-101 피처 존재와 스키마는 이전 단계에서 확인했다. 성공 경로 테스트는 DB 경계 대역으로 검증했다.
- AIS, Prediction, BerthOptimization, PortKnowledge의 실제 Adapter와 Provider는 아직 없다. 이를 성공 처리하거나 역사 AIS CSV를 실시간 선박 위치로 대체하지 않는다.
- 현재 실행 경로는 지도에서 선택한 **S-101 선석 피처 1개** 조회에 한정된다. 항만 운영상의 선석 점유·배정은 제공하지 않는다.
- Phase 7에서는 예측 모델 인터페이스, 모델 가용성 및 평가 계약을 구축한다.
