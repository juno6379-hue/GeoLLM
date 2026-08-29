# 12. API 명세서 (API Specification)

## 1. 개요
FastAPI 기반의 RESTful API 인터페이스를 정의합니다. 본 API는 프론트엔드 UI(사용자 질의, 대시보드, 지도), 외부 연계 시스템, 그리고 내부 Agent 간 통신에 사용됩니다.

## 2. 공통 Task API (Orchestrator)

### POST /api/v1/tasks
- **설명**: 새로운 자연어 분석 태스크 생성.
- **Request**:
  ```json
  {
    "query": "부산항 입구 3km 이내 위험객체 분석",
    "organization_id": "org-ocean-01"
  }
  ```
- **Response**: `202 Accepted`
  ```json
  {
    "task_id": "uuid-v4",
    "status": "RECEIVED"
  }
  ```

### GET /api/v1/tasks/{task_id}
- **설명**: 태스크 현재 상태, 진행률 및 결과 요약 조회.

### GET /api/v1/tasks/{task_id}/stream
- **설명**: Server-Sent Events (SSE) 또는 WebSocket을 통한 실시간 상태 및 진행률 스트리밍.

### POST /api/v1/tasks/{task_id}/cancel
- **설명**: 실행 중인 태스크 강제 취소.

## 3. Registry API

### GET /api/v1/registry/agents
- **설명**: 시스템에 등록된 가용 Agent 목록 및 상태 반환.

### GET /api/v1/registry/tools
- **설명**: 허용된 Tool 목록 및 입력 스키마 반환.

### GET /api/v1/registry/datasets
- **설명**: BBOX 및 시간 조건으로 접근 가능한 데이터셋 검색.
- **Query Params**: `min_lon`, `min_lat`, `max_lon`, `max_lat`, `start_time`, `end_time`

## 4. Agent 내부 API (내부망 통신용)

### POST /api/v1/agents/{agent_name}/execute
- **설명**: Orchestrator가 특정 Agent에게 작업 실행 지시.
- **Request Body**: `AgentRequest` 구조체 참조.
- **Response**: 비동기 처리를 위한 `202 Accepted`. 결과는 Message Broker 또는 Callback URL로 반환.

## 5. Review (HITL) API

### GET /api/v1/reviews
- **설명**: 대기 중인(Pending) 승인 요청 목록 조회 (권한 기반 필터링).

### POST /api/v1/reviews/{review_id}/approve
- **설명**: 전문가가 태스크 결과를 승인.
- **Request Body**: `{"comments": "승인합니다."}`

### POST /api/v1/reviews/{review_id}/reject
- **설명**: 태스크 결과 반려.

## 6. 에러 응답 표준
```json
{
  "error": {
    "code": "DATA_ACCESS_DENIED",
    "message": "해당 데이터셋에 접근할 권한이 없습니다.",
    "trace_id": "uuid-v4"
  }
}
```
