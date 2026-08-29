# 17. 위험 관리 및 기술 부채 (Risk and Technical Debt)

## 1. 개요
초기 아키텍처 수립 단계에서 예상되는 주요 기술적 위험(Risk)과 잠재적인 기술 부채(Technical Debt)를 식별하고, 이에 대한 완화 전략(Mitigation Strategy)을 수립합니다.

## 2. 주요 리스크 (Risks)

### 2.1 LLM의 환각(Hallucination) 및 Tool 오선택
- **위험**: LLM이 분석에 적합하지 않은 Tool을 선택하거나 존재하지 않는 파라미터를 생성할 위험.
- **완화 전략**: Tool Registry의 설명을 명확히 하고, Pydantic을 이용해 Tool 입력 파라미터를 엄격하게 구조화(Structured Output) 및 검증. 실패 시 재시도 프롬프트(Auto-Correction) 구현.

### 2.2 장기 실행 분석의 비동기 타임아웃
- **위험**: 대용량 위성 영상 분석이나 복잡한 공간 연산이 HTTP 타임아웃을 초과하거나 중간에 멈출 위험.
- **완화 전략**: Orchestrator를 LangGraph 또는 Temporal과 같은 지속성(Durability)을 보장하는 프레임워크로 구현하여 프로세스 재시작 시에도 중단점에서 재개할 수 있도록 설계.

### 2.3 다중 Agent 간의 상태/결과 불일치
- **위험**: 공간 분석 결과와 시계열 분석 결과가 특정 지역에 대해 서로 다른 해석을 내놓을 위험.
- **완화 전략**: Situation Interpretation Agent를 두어 충돌을 감지하고, 최종 Validation Agent에서 공간 범위와 데이터 시점 등을 기계적으로 교차 검증. 해결 불가 시 HITL로 넘김.

## 3. 잠재적 기술 부채 (Technical Debt)

### 3.1 룰 엔진의 하드코딩
- **이슈**: Validation Agent의 규칙이나 보안 통제 로직이 코드로 하드코딩될 경우 유지보수가 어려움.
- **방향**: 초기에는 코드로 구현하되(MVP), 점진적으로 OPA(Open Policy Agent)나 Rule Registry 기반의 설정 테이블로 추상화 필요.

### 3.2 기존 Map Agent와의 강한 결합
- **이슈**: Map Agent Adapter가 특정 버전에 종속되어 지도 엔진 변경 시 어댑터 전체를 재개발해야 함.
- **방향**: `MapLayerSpecification`을 OGC API 표준이나 범용 GeoJSON 규격에 최대한 맞추어 중립성 확보.

### 3.3 대용량 지형 데이터 처리 지연
- **이슈**: 고해상도 S-102 수심 데이터를 실시간 분석에 사용할 경우 병목 발생.
- **방향**: 원천 데이터 처리 파이프라인에서 분석용 저해상도 캐시/인덱스를 미리 생성해 두고, 상세 분석에만 고해상도 데이터를 로드하는 최적화 필요.
