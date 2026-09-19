# Phase 13 — U-Port 대화창의 S-101 위험객체 자연어 검색

## 완료 작업

- Capability Registry에 현재 지도 범위 위험객체 검색을 추가하고, 대화창이 `POST /api/v1/uport/query/route`로 실행 경로를 먼저 확인하도록 했다.
- “지도 범위 위험객체를 보여줘”는 현재 Leaflet bbox를 `POST /api/v1/uport/s101/hazards/query`에 전달한다. 백엔드는 기존 GeoLLM 자연어 S-101 검색 경로로 원문 질문과 bbox를 전달한다.
- 공유 경로가 반환한 GeoJSON·피처 근거·출처 레이어가 일치할 때만 대화창 목록과 지도 위험객체 레이어에 표시한다. 목록 클릭 시 해당 위험객체를 지도에서 강조한다.
- “이 선박 주변의 S-101 항행 위험 객체”는 AIS 위치가 없으므로 지도 범위 검색으로 바꿔 실행하지 않는다. 선택한 S-101 선석 질문은 기존 버전 검증 API를 유지한다.

## 수정 파일

- `data/capability_registry.yaml`
- `services/uport/planning_router.py`
- `services/uport/hazard_router.py`
- `services/orchestrator/static/uport/agent.js`
- `services/orchestrator/static/uport/map.js`
- `services/orchestrator/static/uport/index.html`
- `services/orchestrator/static/uport/dashboard.css`
- `tests/unit/test_uport_agent_ui.js`
- `tests/unit/test_uport_hazard_map_ui.js`
- `tests/unit/test_uport_hazard_viewport.py`

## 신규 파일

- `docs/uport/20_phase13_chat_hazard.md`

## 재사용 구성과 아키텍처

- 기존 Capability Registry 검색과 GeoLLM `execute_radius_request`의 Feature Resolver, Catalogue 승인, PostGIS 질의, QEC, 결과 검증 및 Evidence를 재사용한다.
- U-Port 대화창은 도메인 Registry가 선택한 실행 경로로 요청한다. 항행 위험 객체 유형이나 SQL을 대화창에서 하드코딩하지 않는다.
- 선박 주변 질의는 AIS 데이터가 확인될 때까지 `unavailable`로 유지한다.

## 실제 DB 실행 결과

- PostGIS가 설정된 `geollm_backend` 컨테이너에서 울산항 bbox `(129.35,35.45,129.45,35.55)`의 공유 자연어 위험객체 검색을 실행했다.
- 결과: 전체 615건, 첫 페이지 500건, 피처 근거 500건, 지도 레이어 피처 500건. 세 목록의 피처 ID와 Evidence ID 일치를 확인했다. 첫 피처는 `Obstruction` Point다.
- 새 U-Port 라우터와 해당 Registry 코드를 컨테이너의 임시 디렉터리에 복사해 실제 DB 설정으로 `POST /api/v1/uport/s101/hazards/query`를 TestClient 호출했다. HTTP 200, 전체 615건·반환 500건·피처 근거 500건을 확인했고 각 반환 피처의 `evidence_id`가 근거 목록과 일치했다. 첫 피처 ID는 `1168747`, 출처는 `projection.s101_feature_current`다.
- 이 검증은 **설정된 컨테이너 안의 임시 코드 경로**에서 수행했다. 실행 중인 서비스에 새 라우터를 배포하거나 실제 브라우저에서 지도를 렌더링한 검증은 아니다.
- 호스트 로컬 복제본에서 원본 `.env`를 로드한 API 시도는 `INVALID_EXECUTION_CONFIG`(503)으로 차단됐다. 호스트 DB 연결 실패의 세부 원인은 확정하지 못했다.

## 테스트 결과

- Registry 라우팅, 선박 중심 검색 차단, 자연어 API의 원문·bbox 전달, GeoJSON/근거 불일치 차단을 테스트했다.
- 대화창 질의 → 현재 지도 bbox → 위험객체 결과 목록·지도 이벤트, 지도 레이어 성공·실패 UI 이벤트를 테스트했다.
- 실제 Leaflet 브라우저 화면의 시각 검증은 브라우저 세션이 없어 수행하지 못했다.

## 발견된 문제와 남은 작업

- U-Port 새 라우터를 정식 실행 환경에 배포한 뒤 브라우저 지도 표시를 직접 검증해야 한다.
- AIS 실시간 위치가 확보되기 전에는 선박 주변 위험객체 검색과 AIS-S-101 공간결합을 실행할 수 없다.
- S-101의 속성·수심·항로·공간관계 및 선석 주변 객체 검색은 문서 11번의 남은 기능이다.
