# Phase 12 — S-101 항행 위험객체 지도 범위 검색

## 완료 작업

- 기존 GeoLLM의 S-101 위험객체 공간검색 파이프라인을 U-Port 지도에서 호출하는 `POST /api/v1/uport/s101/hazards/viewport` API를 추가했다.
- 이 API는 WGS84 bbox를 검증한 뒤 기존 Feature Catalogue·Derived Concept Registry 승인 대상, QueryBuilder, PostGIS 공간검색, 결과 도형 검증, Evidence 생성 결과를 재사용한다.
- 지도에 선택형 ‘S-101 항행 위험객체’ 레이어를 추가했다. 검색 성공 시 결과 건수와 표시 건수를 구분해 보여 주고, 조회 실패 시 이전 레이어를 비운다.
- 위험객체를 클릭하면 S-101 유형과 피처 ID를 표시한다. 선박 위험도나 AIS와의 공간결합 결과로 표시하지 않는다.

## 수정 파일

- `services/orchestrator/main.py`
- `services/orchestrator/static/uport/index.html`
- `services/orchestrator/static/uport/map.js`

## 신규 파일

- `services/uport/hazard_router.py`
- `tests/unit/test_uport_hazard_viewport.py`
- `tests/unit/test_uport_hazard_map_ui.js`
- `docs/uport/19_phase12_s101_hazard_viewport.md`

## 재사용 구성과 아키텍처

- `services/orchestrator/s101_radius_execution.py`의 `prepare_bounds_request`와 `execute_radius_request`를 재사용했다. U-Port 전용 공간 SQL이나 위험객체 하드코딩 목록을 만들지 않았다.
- `services/uport/map_router.py`의 bbox 유효성 검사와 기존 Leaflet 지도를 재사용했다.
- 자연어 파이프라인은 기존 GeoLLM Agent가 제공한다. U-Port 대시보드의 새 레이어는 지도 범위 검색을 직접 호출하며, U-Port 대화창의 자유 질의와 위험객체 검색은 아직 연결되지 않았다.

## 실행 및 테스트 결과

- 공유 파이프라인 사전검증에서 지도 bbox와 `Wreck`, `Obstruction`, `UnderwaterAwashRock` 등 승인된 피처 유형을 확인했다.
- U-Port API의 성공 응답 전달, 잘못된 bbox, 소스 차단, 반환 건수 불일치 차단을 테스트했다.
- 지도 레이어 스위치의 bbox 요청·표시 상태·실패 상태 UI 이벤트 테스트 통과. JavaScript 구문 검사와 기존 U-Port 지도·실행·수용 테스트 통과.
- 실제 로컬 복제본에서 공유 파이프라인을 실행하면 `DB_NOT_CONFIGURED`로 차단됐다. 실 PostGIS 성공 결과나 실제 Leaflet 화면은 확인하지 못했다.

## 발견된 문제와 남은 작업

- 문서 11번 항목 중 Feature 조회·선석 표시·지도 범위 항행 위험객체 검색은 연결됐다. 속성 검색, 위치 검색의 일반화, 공간관계·항로·수심 분석, 항만시설·선석 주변 객체 검색, AIS-S-101 공간결합은 아직 완료되지 않았다.
- 다음 단계에서 U-Port 대화창과 공유 자연어 위험객체 파이프라인을 연결하고, PostGIS 설정이 갖춰진 환경에서 실제 결과·근거·지도 표시를 검증한다.
