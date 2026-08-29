# 07. Orchestrator 상태머신 설계 (Orchestrator State Machine)

## 1. 개요 및 핵심 기능
Orchestrator는 전체 플랫폼의 중앙 통제 계층으로서, 사용자 질의 접수부터 최종 결과(지도/보고서) 생성까지의 모든 데이터 흐름과 에이전트 생명주기를 통제합니다.

### 1.1 핵심 통제 기능 (Core Functions)
- **질의 해석**: 사용자 질의 접수, 의도 분류, 해양 전문용어 해석, 위치/공간범위/기간/분석조건/결과형식 추출
- **컨텍스트 인지**: 사용자 및 기관 권한 확인, 필요한 데이터 식별, Data Discovery Agent 호출
- **실행 계획**: 전문 Agent 및 Tool 선택, 작업 DAG(Directed Acyclic Graph) 생성
- **실행 제어**: 순차 및 병렬 실행, 장시간 작업 비동기 처리, 진행률 관리, 취소, 재시도 제어
- **결과 제어**: 부분결과 관리, 중간결과 저장, 결과 충돌 탐지, Validation/Human Review 호출, Map/Report Agent 호출, 최종 결과 통합

---

## 2. 상태 정의 (19개 State)

시스템의 유한 상태 기계(FSM)는 다음 19개의 상태를 갖습니다.

1. `RECEIVED`: 사용자 질의가 최초로 시스템에 접수됨.
2. `INTENT_PARSING`: LLM을 통한 의도 및 파라미터 파싱 진행 중.
3. `INTENT_PARSED`: 질의 의도, 공간, 시간 파라미터가 성공적으로 추출됨.
4. `CONTEXT_RESOLVING`: 사용자 권한 및 필요한 데이터(Catalog) 매핑 진행 중.
5. `CONTEXT_RESOLVED`: Data Discovery 완료 및 보안 컨텍스트 확정됨.
6. `PLAN_CREATING`: 전문 Agent 및 Tool 할당, 작업 DAG(실행계획) 생성 중.
7. `PLAN_CREATED`: 각 노드별 실행 계획 및 의존성 매핑이 완료됨.
8. `AGENTS_SELECTED`: 각 태스크를 수행할 전문 Agent 리소스가 할당됨.
9. `EXECUTING`: DAG에 따라 Agent들이 순차/병렬적으로 실행 중.
10. `WAITING_FOR_DATA`: 비동기 대규모 데이터 수집(예: 대용량 위성영상 다운로드) 대기 중.
11. `PARTIAL`: 일부 Agent 작업은 성공했으나, 일부 실패로 인해 부분 결과만 도출됨.
12. `RESULTS_AGGREGATED`: 여러 Agent의 병렬/순차 실행 결과가 하나로 통합됨.
13. `VALIDATING`: Validation Agent를 통해 공간적/논리적 교차 검증 진행 중.
14. `WAITING_FOR_REVIEW`: 검증 실패 또는 정책적 결정 요구에 의해 Human-in-the-Loop(전문가 승인) 대기 중.
15. `MAP_REPORT_GENERATING`: 검증/승인된 결과를 바탕으로 Map Layer 및 보고서 포맷 생성 중.
16. `COMPLETED`: 모든 작업이 성공적으로 종료되고 사용자에게 반환됨.
17. `FAILED`: 복구 불가능한 에러(시스템 장애 등)로 인해 작업이 실패로 종료됨.
18. `CANCELLED`: 사용자의 명시적 요청에 의해 작업이 취소됨.
19. `BLOCKED`: 보안 권한 부족 또는 데이터 품질 기준 미달로 작업이 차단됨.

### 2.1 상태 전이 로그 스키마
각 상태가 전이될 때마다 DB에 아래 정보가 저장되어 전체 라이프사이클을 추적합니다.
- `previous_state` (이전 상태)
- `next_state` (진입 상태)
- `timestamp` (발생 시각)
- `actor` (System / User / Admin)
- `reason` (상태 변경 사유, 예: 권한 부족)
- `payload_reference` (해당 시점의 State/Context 스냅샷 URI)
- `error_code` (실패 시 에러 코드)
- `retry_count` (현재 노드의 재시도 횟수)

---

## 3. 실행 정책 (Execution Policy)

Orchestrator는 다음과 같은 정책(Rule)을 기반으로 실행 흐름을 제어합니다.

1. **단순 질의 vs 복합 질의**: 단일 의도의 단순 질의는 단일 Agent를 직렬로 실행하며, 복합 질의는 의존성 그래프(DAG)를 생성하여 처리합니다.
2. **병렬 vs 순차 실행**: 의존성이 없는 독립 작업은 병렬로 동시 실행하고, 선행 결과가 필요한 작업은 순차적으로 실행합니다.
3. **지연 및 블로킹**:
   - 데이터 수집 지연 시 `WAITING_FOR_DATA` 상태로 전환.
   - 전문가 확인이 필요한 경우 `WAITING_FOR_REVIEW` 상태로 전환.
   - 사용자 권한이 부족하면 `BLOCKED` (BLOCKED_BY_PERMISSION) 상태로 즉시 종료.
   - 원천 데이터 품질 미달 시 `BLOCKED` (BLOCKED_BY_DATA_QUALITY) 상태로 종료.
4. **회복력(Resilience)**:
   - Tool 실패 시 지정된 Retry Policy(지수 백오프 등) 적용.
   - 반복 실패 시 대체 Tool(Fallback)이 존재할 경우 경로를 동적으로 우회.
5. **결과 보증**: Validation FAIL 시 외부 시스템(Map, Report)으로의 배포(Publishing)를 엄격히 금지.

---

## 4. 프레임워크 선정 근거: LangGraph vs 명시적 상태머신

본 플랫폼의 Orchestrator는 **"단순한 명시적 상태머신(Explicit State Machine)" 대신 "LangGraph"를 채택**하여 구현합니다. 주요 선정 근거는 다음과 같습니다.

### 1) DAG (병렬/순차) 실행의 내장 지원
복합 질의를 처리하기 위해 독립적인 전문 Agent들을 병렬(Parallel)로 실행하고, 결과를 결합(Join)하여 다음 순차(Sequential) 노드로 넘겨야 합니다. 단순 DB 기반의 명시적 상태머신을 사용하면 분기(Fork)와 결합(Join) 로직을 바닥부터 구현해야 하지만, LangGraph는 그래프 구조 자체로 병렬/순차 제어를 네이티브하게 지원합니다.

### 2) Human-in-the-Loop (HITL) 및 상태 체크포인트
본 시스템은 `WAITING_FOR_REVIEW` 등 외부(인간) 개입 시 실행을 완전히 멈추고 서버가 재시작되어도 상태를 기억해야 합니다. LangGraph의 **Checkpointer** 기능(Sqlite/Postgres)은 그래프의 특정 노드 진입 전후의 모든 컨텍스트 페이로드를 직렬화하여 DB에 자동 저장하므로, 손쉽게 실행을 멈추고(Interrupt) 사용자의 승인(Resume) 후 작업을 이어갈 수 있습니다.

### 3) 동적 에러 복구 및 대체 경로 라우팅
실행 정책 중 "Tool 실패 시 대체 Tool(Fallback)로 경로 변경"이 요구됩니다. LangGraph의 **Conditional Edges (조건부 엣지)**를 활용하면 노드의 실행 결과(오류/성공)에 따라 LLM Router가 즉시 그래프의 다음 경로(대체 Tool 호출 등)를 동적으로 결정할 수 있어 복원력(Resilience)이 뛰어납니다.

### 결론
Orchestrator의 요구사항은 단순한 선형 워크플로우가 아니라 **"상태를 기억하는 동적 병렬 추론 그래프"**입니다. 따라서 LangGraph를 기반 프레임워크로 채택하는 것이 아키텍처 원칙에 가장 부합합니다.
