# 15. 단계별 구현 계획 (Implementation Plan)

## 1. 개요
해양공간 지능분석 플랫폼은 거대한 시스템이므로 총 15개 페이즈(Phase)로 나누어 점진적으로 개발, 테스트, 통합을 진행합니다.

## 2. Phase 별 세부 계획 및 완료 기준

### Phase 0. 현재 시스템 및 저장소 분석
- **내용**: 저장소 환경 세팅 및 아키텍처, 계약, API 설계 문서 작성.
- **완료기준**: 설계 문서 18종 작성 완료 및 승인 획득.

### Phase 1. 공통 기반 (Common Foundation)
- **내용**: Pydantic 공통 스키마(Agent/Tool/Event), 에러 코드, 보안 컨텍스트, Database(PostgreSQL/PostGIS) 모델 및 Alembic 마이그레이션 구성. Registry(Agent, Tool, Dataset, Model) MVP API 구현. Observability 설정(structlog, OpenTelemetry).
- **완료기준**: 공통 라이브러리 패키지 빌드 성공, DB 스키마 생성, 단위 테스트 커버리지 80% 이상.

### Phase 2. Orchestrator MVP
- **내용**: LLM 기반 Intent Parsing 모듈, State Machine (LangGraph 등 기반) 뼈대 구축. 비동기 Task API(`POST /tasks`) 구현. Mock Agent를 연동한 E2E 동작 테스트.
- **완료기준**: 단순 질의 수신 후 Mock Agent 호출 및 결과 병합 로직 정상 동작 (시퀀스 관통).

### Phase 3. Data Discovery Agent
- **내용**: Dataset Registry를 조회하여 질의 컨텍스트(공간/시간/키워드)에 맞는 메타데이터 식별 및 보안 권한 필터링 로직 구현.
- **완료기준**: 특정 지역/시간을 포함하는 질의에 대해 가용 데이터셋 목록을 정확히 반환.

### Phase 4. Standard·RAG Agent
- **내용**: IHO/IMO 표준 및 법령 문서를 Chunking/임베딩하여 pgvector에 적재. RAG 검색 및 출처(Evidence) 인용 로직 구현.
- **완료기준**: 규정 관련 질문 시 관련 조항과 정확한 출처 메타데이터가 `AgentResult`에 포함됨.

### Phase 5. Spatial Analysis Agent
- **내용**: PostGIS, GeoPandas 연계 툴(Tool Registry) 개발. LLM이 Tool 파라미터를 추출해 쿼리 템플릿을 호출하도록 구현.
- **완료기준**: 거리, 버퍼, 교차 분석 결과가 올바른 GeoJSON 객체 및 통계치로 도출됨. (임의 결과 생성 방지 확인)

### Phase 6. 기존 Map Agent 연계 (Adapter)
- **내용**: AgentResult의 공간 데이터를 파싱해 `MapLayerSpecification` 생성 로직 구현. (기존 Map Agent와의 통신 모방 목업 연결 포함)
- **완료기준**: GeoJSON 덤프 파일 생성 및 지도 표출용 스타일 명세가 정상 반환됨.

### Phase 7. Validation Agent
- **내용**: 공간 CRS 일치 여부, 결과 객체 수와 텍스트 요약 수 일치 등 룰 베이스 검증 엔진 구현.
- **완료기준**: 불량 결과(데이터 범위 이탈 등)를 주입했을 때 `FAIL` 판정을 내리고 차단함.

### Phase 8. AIS Analysis Agent
- **내용**: 선박 항적 분석 Tool, 밀도 분석 Tool 개발 및 Agent 통합.
- **완료기준**: 특정 기간/영역의 통항량 산출 및 위험 구간 식별 성공.

### Phase 9. Time-Series Agent
- **내용**: 관측소 시계열 데이터 조회, 결측 처리, 이상치 탐지 Tool 통합.
- **완료기준**: 시계열 분석 결과가 통계 메트릭 형식으로 정상 반환됨.

### Phase 10. Time-Series Forecast Agent
- **내용**: 단/중기 예측 모델 엔드포인트 연동.
- **완료기준**: 시계열 예측값 및 신뢰 구간(Confidence Interval) 반환 성공.

### Phase 11. Vision·EO Agent
- **내용**: 위성/항공 영상 검색 API 및 변화 탐지/객체 탐지 비전 모델 엔드포인트 연계.
- **완료기준**: 지정된 이미지에서 탐지된 폴리곤과 확신도(Confidence) 반환 성공.

### Phase 12. Situation Interpretation Agent
- **내용**: Spatial, AIS, Vision 등 여러 Agent 결과를 LLM에 종합 주입하여 상황 해석 및 충돌 점검 수행.
- **완료기준**: 다중 분석 결과를 바탕으로 논리적 모순이 없는 종합 요약 및 권고문 생성.

### Phase 13. Human-in-the-Loop (HITL)
- **내용**: Validation 실패 또는 특정 조건 시 Task를 Paused 상태로 두고 Review UI에서 승인 대기. Reviewer 액션에 따른 재개/반려 기능.
- **완료기준**: 리뷰 승인 시 이벤트 버스를 통해 Orchestrator가 동작을 이어감.

### Phase 14. Report·Dashboard·API·Event 연계
- **내용**: Report Agent를 통한 최종 PDF/Markdown 문서 생성. 대시보드 API, WebSocket 이벤트 스트리밍 완성.
- **완료기준**: E2E 시나리오(부산항 위험객체 등) 전체 흐름 통과 및 리포트/알림 수신 확인.

### Phase 15. MLOps·LLMOps 및 운영화
- **내용**: 모델 관리, 프롬프트 레지스트리 버저닝, 로그 수집 파이프라인(OpenTelemetry) 연동, CI/CD 배포 스크립트(Docker Compose/K8s) 정리.
- **완료기준**: 성능 및 부하 테스트 통과, 한국어 운영 가이드 작성 완료. 시스템 론치 준비.
