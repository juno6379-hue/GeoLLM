# 16. 테스트 계획 (Test Plan)

## 1. 개요
해양공간 지능분석 플랫폼의 신뢰성을 보장하기 위해 단위, 계약, 통합, 시나리오, 성능 등 다계층 테스트 전략을 수립합니다. 모든 테스트는 CI/CD 파이프라인에서 자동화되어야 하며, Phase 전환의 필수 완료 조건입니다.

## 2. 테스트 계층

### 2.1 단위 테스트 (Unit Tests)
- **대상**: Schema(Pydantic), Registry 로직, State Machine, Agent/Tool Selection.
- **도구**: `pytest`
- **목표**: 핵심 비즈니스 로직 및 컨텍스트 메모리 처리의 분리된 기능 검증 (Mocking 활용). 커버리지 80% 이상.

### 2.2 계약 테스트 (Contract Tests)
- **대상**: Orchestrator ↔ Agent, Agent ↔ Tool, Agent ↔ Registry, Agent ↔ Map Agent.
- **방식**: OpenAPI 스키마(또는 JSON Schema) 기반으로 요청/응답 페이로드의 정합성 검증.
- **목표**: 100% 통과 필수. 계약 변경 시 의존성 있는 타 서비스에 미치는 영향 사전 탐지.

### 2.3 통합 테스트 (Integration Tests)
- **대상**: PostGIS 연동 공간 질의, Vector DB(pgvector) 검색, Message Broker 이벤트 발행/구독, Redis 캐싱, Object Storage 입출력.
- **도구**: `testcontainers`, `pytest-asyncio`
- **목표**: 실제 외부 종속성(DB, Queue 등)과의 연동이 올바르게 동작하는지 확인.

### 2.4 E2E 시나리오 테스트 (Scenario Tests)
- **대상**: 대표적인 분석 질의(부산항 위험객체, 통항분석, 해상풍력 후보지 등)의 파이프라인 관통.
- **방식**: Mock 데이터셋을 적재한 테스트 환경에서 Orchestrator에 API 호출 후 최종 Map/Report 결과물이 의도대로 도출되는지(또는 Validation에서 의도적으로 차단되는지) 확인.

### 2.5 성능 및 부하 테스트 (Performance & Load Tests)
- **대상**: API 응답 지연(Latency), 비동기 처리 큐(Queue) 적체량.
- **도구**: `Locust` 또는 `k6`
- **목표**: 다수의 동시 질의 시 Auto Scaling 동작, DB Connection 풀 고갈 여부 점검.

## 3. 테스트 환경 및 품질 기준
- **환경 구성**: 테스트 전용 Docker Compose 환경(가벼운 로컬 LLM 목업 포함) 구축.
- **정적 분석**: `Ruff` (Lint & Formatting), `Pyright/MyPy` (Type Check) 파이프라인 통과 필수.
- **장애 복구 테스트 (Chaos Testing)**: Agent 프로세스를 강제 종료했을 때 Orchestrator가 타임아웃을 감지하고 상태를 복구(Retry)하는지 점검.
