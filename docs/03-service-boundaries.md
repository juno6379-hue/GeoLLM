# 03. 서비스 경계 정의 (Service Boundaries)

## 1. 개요
플랫폼은 독립적으로 배포 및 확장 가능한 여러 서비스(Microservices)의 조합으로 설계됩니다. 본 문서는 각 마이크로서비스 간의 경계(Boundary)와 책임을 명확히 합니다.

## 2. 코어 서비스 그룹

### 2.1 API Gateway & API Service
- **책임**: 클라이언트(사용자 UI, 외부 시스템)의 요청 접수, 인증/인가(AuthN/AuthZ), Rate Limiting 통제, 정적 리소스 서빙, WebSocket을 통한 실시간 상태(Progress) 브로드캐스트.
- **기술**: FastAPI

### 2.2 Orchestrator Service
- **책임**: 전체 태스크(Task) 라이프사이클 관리, 의도 분석(Intent Parsing), 컨텍스트 주입, Agent 선택 및 DAG(Directed Acyclic Graph) 실행 계획 생성, 작업 상태 머신 제어.
- **의존성**: Registry Service, LLM Engine (의도 분석용), Message Broker.

### 2.3 Registry Service
- **책임**: Agent, Tool, Model, Dataset 등 플랫폼 내 모든 컴포넌트의 메타데이터 및 버전 정보를 관리.
- **데이터**: Registry Database (PostgreSQL).

### 2.4 Review Service (HITL)
- **책임**: Validation 결과가 WARNING/FAIL 이거나 정책 검토가 필요한 작업의 승인 프로세스(Approval Workflow) 상태 관리 및 Audit Log 보관.

## 3. 에이전트 서비스 그룹 (Specialized Agents)

각 Agent는 공통 계약(`AgentRequest`, `AgentResult`)을 준수하는 독립적인 서비스로 동작하며, HTTP API 또는 Message Queue를 통해 이벤트를 수신합니다.

- **Data Discovery Agent Service**: 사용자 권한과 질의 컨텍스트를 바탕으로 Data Lake/DB에서 사용 가능한 메타데이터 카탈로그 제공.
- **Standard·RAG Agent Service**: Vector DB (pgvector) 질의, 문서 Chunk 검색, 출처(Evidence) 추출.
- **Spatial Analysis Agent Service**: 공간 분석 Query Template 호출 관리, PostGIS 연계 제어.
- **AIS Analysis Agent Service**: AIS 데이터 스토어 연동, 선적/항적/통항량 계산 Tool 호출 제어.
- **Vision·EO Agent Service**: 위성 이미지 다운로드/추출 제어, GPU 기반 비전 모델 파이프라인 연동 제어.
- **Time-Series Agent Service**: 시계열 DB(또는 Parquet/Xarray) 데이터 조회 및 전처리 Tool 호출 제어.
- **Time-Series Forecast Agent Service**: MLOps의 모델 엔드포인트 연동, 예측 Tool 호출 제어.
- **Situation Interpretation Agent Service**: 텍스트 분석 및 다중 결과의 논리적 충돌 해결.
- **Validation Agent Service**: 결과의 룰 베이스 및 LLM 베이스 무결성 검증, 맵 데이터와의 싱크 검증.

## 4. 인티그레이션 서비스 그룹

### 4.1 Map Agent Adapter Service
- **책임**: 시스템 내부의 `AgentResult`를 기존 Map Agent 시스템의 API 규격 및 지도 레이어 포맷(GeoJSON, Vector Tile 등)으로 렌더링하도록 연계.

### 4.2 Report Service
- **책임**: 수치 데이터, 지도 스크린샷, 텍스트 요약을 조합하여 최종 PDF, Word, 대시보드 마크다운 보고서로 컴파일.

## 5. 서비스 간 통신 방식 (Inter-Service Communication)
- **동기(Synchronous)**: 짧은 시간 내 응답이 필요한 메타데이터 조회(Registry), 권한 체크 등 (REST/HTTP).
- **비동기(Asynchronous)**: 대부분의 Agent 실행, 공간 연산, AI 추론 (Kafka / RabbitMQ를 통한 이벤트 드리븐 또는 gRPC/HTTP + Webhook 구조).
- **데이터 공유**: 대용량의 중간 분석 결과(GeoJSON 덤프, 위성 이미지 등)는 메시지에 직접 담지 않고 Object Storage (MinIO)에 업로드 후 Reference URL(URI)만 전달.
