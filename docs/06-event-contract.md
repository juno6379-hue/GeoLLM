# 06. 이벤트 스키마 계약 (Event Schema Contract)

## 1. 개요
Orchestrator, Agent, Tool 간의 비동기 통신 및 상태 추적을 위해 Message Broker(Kafka/RabbitMQ)를 통해 발행되는 이벤트(Event) 스키마를 정의합니다.

## 2. 이벤트 공통 필드 (Base Event)

모든 이벤트는 다음 공통 필드를 포함합니다.

```json
{
  "event_id": "evt-uuid-v4",
  "event_type": "task.created",
  "task_id": "task-uuid-v4",
  "trace_id": "trace-uuid-v4",
  "agent_name": "orchestrator",
  "timestamp": "2026-07-15T12:00:00Z",
  "payload_reference": "s3://bucket/events/evt-uuid-v4.json",
  "status": "SUCCESS"
}
```
*참고: 메시지 크기가 클 경우 `payload_reference`에 S3/MinIO 경로를 저장하고, broker에는 경량 메시지만 전송하는 Claim Check 패턴을 사용합니다.*

## 3. 주요 이벤트 유형 (Event Types)

### 3.1 Task Events
- `task.created`: 사용자 질의가 접수되어 신규 Task가 생성됨.
- `task.planned`: Orchestrator가 Agent 실행 계획(DAG)을 확정함.
- `task.completed`: 전체 태스크가 성공적으로 완료됨.
- `task.failed`: 태스크가 최종 실패함.
- `task.cancelled`: 사용자에 의해 취소됨.

### 3.2 Agent Events
- `agent.started`: Agent가 작업을 시작함.
- `agent.progress`: Agent가 중간 진행 상태를 보고함 (예: 데이터 다운로드 중).
- `agent.completed`: Agent가 성공적으로 결과를 산출함.
- `agent.failed`: Agent 실행 중 오류 발생.

### 3.3 Tool Events
- `tool.started`: Agent가 특정 Tool 호출을 시작함.
- `tool.completed`: Tool 실행 완료.

### 3.4 Validation & Review Events
- `validation.requested`: Agent 결과에 대해 Validation Agent에 검증 요청.
- `validation.completed`: 검증 완료 (PASS/WARNING/FAIL 반환).
- `review.requested`: HITL(전문가 검토)이 요청됨.
- `review.completed`: 전문가가 승인/반려/수정 처리함.

### 3.5 Output Events
- `map.generated`: Map Agent Adapter를 통해 지도 레이어 렌더링이 완료됨.
- `report.generated`: Report Agent를 통해 최종 문서/대시보드가 생성됨.

## 4. 이벤트 버스 구성 방안
- **Apache Kafka**: 대용량 실시간 로그 및 이벤트 스트리밍.
- **WebSocket Gateway**: 프론트엔드 클라이언트로 `agent.progress`, `task.completed` 이벤트를 실시간 중계하여 UI에 진행률 표시.
