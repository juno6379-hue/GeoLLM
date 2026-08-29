# 13. 시퀀스 다이어그램 (Sequence Diagrams)

## 1. 개요
사용자의 질의가 입력된 후 전체 플랫폼이 어떻게 동작하는지 대표적인 E2E 시나리오를 바탕으로 시스템 간 상호작용을 시각화합니다.

## 2. 기본 분석 시나리오 (순차적/병렬 처리 및 Map 생성)

**질의**: "부산항 입구 3km 이내의 위험객체를 분석해줘"

```mermaid
sequenceDiagram
    participant U as User / UI
    participant O as Orchestrator
    participant D as Data Discovery Agent
    participant S as Spatial Analysis Agent
    participant V as Validation Agent
    participant M as Map Agent Adapter
    participant ExistingMap as Existing Map System

    U->>O: POST /tasks (질의)
    O-->>U: task_id 반환 (202 Accepted)
    
    %% Intent & Data Discovery
    O->>D: AgentRequest (컨텍스트 및 데이터 탐색)
    D-->>O: AgentResult (가용 데이터: 부산항 ENC 등)
    
    %% Execution
    O->>S: AgentRequest (공간 교차 분석 실행)
    Note over S: Tool: postgis.dwithin 호출
    S-->>O: AgentResult (위험객체 12개, GeoJSON 경로)
    
    %% Validation
    O->>V: AgentRequest (결과 검증)
    V-->>O: AgentResult (PASS)
    
    %% Map Generation
    O->>M: AgentRequest (레이어 생성 요청)
    M->>ExistingMap: POST /layers (MapLayerSpecification)
    ExistingMap-->>M: map_session_id 갱신
    M-->>O: AgentResult (Map Layer URL)
    
    %% Completion
    O->>U: SSE/WebSocket: Task Completed (결과 및 지도 링크)
```

## 3. Human-in-the-Loop (충돌 시나리오)

**상황**: Agent 결과에 불확실성이 높아 Validation이 실패하거나 정책적 판단이 필요한 경우.

```mermaid
sequenceDiagram
    participant U as User / Reviewer
    participant O as Orchestrator
    participant A as AIS Analysis Agent
    participant V as Validation Agent
    participant R as Review Service (HITL)

    O->>A: AgentRequest (통항량 및 이상항적 분석)
    A-->>O: AgentResult (통계 산출, Confidence 0.6)
    
    O->>V: AgentRequest (결과 검증)
    Note over V: Confidence 임계치 미달 판단
    V-->>O: AgentResult (FAIL / HITL_REQUIRED)
    
    O->>R: Review 생성 요청
    R-->>U: 알림 (전문가 승인 필요)
    
    O-->>U: SSE: Task Paused (Waiting for Review)
    
    U->>R: POST /reviews/{id}/approve (승인)
    R->>O: Event: review.completed (Approved)
    
    O->>O: 다음 단계(Map/Report 생성) 재개
```

## 4. 시계열 및 RAG 병렬 처리 시나리오
**질의**: "해상풍력 후보지를 주변 수심과 법적 보호구역 측면에서 평가해줘."
이 경우 `Spatial Analysis Agent`와 `Standard·RAG Agent`가 동시에 병렬로 실행되며, 결과를 `Situation Interpretation Agent`가 종합합니다. (자세한 시퀀스는 생략하나, Ochestrator의 DAG 병렬 분기 로직이 적용됨)
