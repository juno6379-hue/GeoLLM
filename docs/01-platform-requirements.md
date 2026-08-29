# 01. 플랫폼 요구사항 정의서 (Platform Requirements)

## 1. 개요
본 문서는 "해양공간 지능분석 플랫폼"의 기능적(Functional) 및 비기능적(Non-Functional) 요구사항을 정의합니다.

## 2. 기능적 요구사항 (Functional Requirements)

### 2.1 사용자 인터페이스 및 질의 처리
- **자연어 질의 처리**: 사용자의 자연어 기반 해양공간 질의를 이해하고 의도를 파악.
- **Context 추출**: 질의에서 공간, 시간, 대상, 조건, 분석 목적 등을 추출.
- **다중 Agent 오케스트레이션**: 질의 해결을 위해 적합한 여러 전문 Agent를 선택하고, 작업 순서(순차/병렬)를 계획 및 실행.

### 2.2 전문 Agent 기능
- **Data Discovery Agent**: 분석에 필요한 데이터셋 검색, 가용성 및 품질 등급 확인.
- **Standard·RAG Agent**: IHO/IMO S-100 표준, 법령, 보고서에서 문서 검색 및 인용/근거 추출.
- **Spatial Analysis Agent**: GIS 툴(PostGIS 등)을 이용한 거리, 버퍼, 교차, 포함 등의 공간 연산 수행 (LLM 임의 생성 금지).
- **AIS Analysis Agent**: AIS 데이터를 기반으로 선박 통항량, 밀도, 속도, 이상항적 탐지 등 분석.
- **Vision·EO Agent**: 위성/항공 영상을 이용한 해안선 추출, 시설 탐지, 변화 탐지 수행.
- **Time-Series Agent**: 해양관측 및 환경 데이터의 결측처리, 추세, 이상치 탐지 수행.
- **Time-Series Forecast Agent**: ML 모델을 이용한 단/중기 시계열 예측 및 신뢰구간 산출.
- **Situation Interpretation Agent**: 각 Agent의 분석 결과를 종합하여 상황을 해석하고 위험도 판별 및 대응 제안.
- **Map·Report Agent Adapter**: 분석 결과를 기존 Map Agent용 규격으로 변환하고 최종 종합 보고서 생성.

### 2.3 검증 및 Human-in-the-Loop (HITL)
- **Validation Agent**: 산출된 공간, 시간, 문서, 수치 데이터의 타당성 및 정합성 교차 검증 (PASS/WARNING/FAIL 판정).
- **HITL (전문가 승인)**: Validation 실패, 신뢰도 부족, 정책적 판단이 필요한 경우 최종 결과를 차단하고 전문가의 검토(승인/반려/보류) 요청.

### 2.4 공통 관리 기능
- **Registry 관리**: Agent, Tool, Model, Dataset의 버전 및 메타데이터를 관리하는 Registry 제공.
- **추적 및 로깅**: Task ID, Trace ID 기반의 Agent/Tool 실행 이력 기록(실행시간, 파라미터, 모델 버전, 데이터 버전 등).

## 3. 비기능적 요구사항 (Non-Functional Requirements)

### 3.1 신뢰성과 안전성 (Reliability & Safety)
- **환각(Hallucination) 방지**: LLM은 좌표, 수치, 예측값 등을 임의로 생성하지 않아야 하며, 실제 계산은 검증된 Tool(PostGIS, ML 모델 등)에서만 수행.
- **결과 재현성**: 동일한 입력 질의와 동일한 데이터 버전이 주어지면 재현 가능한 결과를 보장.
- **보안 실행 환경**: LLM이 운영 환경에서 raw SQL, 쉘 명령어, 임의 파이썬 코드를 실행하지 못하게 강력히 차단(Template 기반 실행).

### 3.2 성능 및 확장성 (Performance & Scalability)
- **비동기 처리**: 장시간 소요되는 공간 분석 및 AI 추론은 비동기로 실행되며 사용자에게 상태(Progress)를 제공.
- **수평 확장 (Auto-Scaling)**: Orchestrator, 각 Agent, DB(Read Replica), GPU Worker(Vision/Forecast)는 독립적으로 확장 가능해야 함.
- **캐싱**: Redis를 활용한 동일 질의, 레이어 렌더링 데이터 캐싱.

### 3.3 보안 및 접근 통제 (Security & Authorization)
- **인증 및 인가**: OAuth2/OIDC, JWT 기반 사용자 인증.
- **세밀한 권한 통제(ABAC/RBAC)**: 사용자/기관 소속, 데이터 보안 등급에 따라 Agent, Tool, Dataset 접근 권한 통제 (Row-Level Security 적용 포함).

### 3.4 MLOps 및 관측성 (MLOps & Observability)
- **모니터링**: API 응답 시간, LLM 토큰 사용량, 에러율, 검증 실패율 모니터링 (Prometheus, Grafana).
- **LLMOps**: 프롬프트 버전 관리, 응답 평가 체계, Tool 선택 및 RAG 검색 성능 평가.
