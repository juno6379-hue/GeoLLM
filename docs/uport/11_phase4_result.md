# Phase 4 — S-101 지도 및 데이터 경계 결과

## 완료 작업

- 기존 GeoLLM Leaflet 스택과 `localhost:11002/encService`의 S-101 WMS를 대시보드 지도에 연결.
- S-101 2.0 `projection.s101_feature_valid`의 `Berth` 피처를 현재 지도 범위에서 조회하는 읽기 전용 API 추가.
- WGS84 bbox 검증, 최대 범위, 200개 응답 상한, SQL 시간 제한, 데이터셋/제품 버전 출처 표시.
- 선석 피처 선택 시 안정적 ID와 데이터셋을 화면에 표시하고 `uport:map-selection` 이벤트에 컨텍스트 제공.
- S-101 해도와 선석 레이어 제어 추가. 실시간 AIS는 미연결로 표시하고 역사 CSV를 실시간 위치로 오인하지 않도록 Provider 계약과 503 응답 추가.

## 수정 파일

- `services/orchestrator/main.py`
- `services/orchestrator/static/uport/index.html`
- `services/orchestrator/static/uport/dashboard.css`

## 신규 파일

- `services/orchestrator/static/uport/map.js`
- `services/uport/__init__.py`
- `services/uport/map_router.py`
- `services/uport/providers.py`
- `tests/unit/test_uport_map.py`
- `docs/uport/11_phase4_result.md`

## 재사용한 기존 구성과 아키텍처 변경

기존 S-101 WMS URL과 Leaflet을 재사용했다. FastAPI `/api/v1`에 U-Port 도메인 라우터를 추가했고, GeoLLM DB 세션 제공 함수 `get_s101_db`를 사용한다. 실제 선박 위치와 선석 점유 상태를 만드는 신규 저장소나 Mock은 추가하지 않았다.

## 실행·테스트 결과

- S-101 WMS `GetCapabilities`: HTTP 200.
- PostGIS 내부 SQL: 울산항 테스트 bbox `(129.25,35.35,129.55,35.65)`에서 현재 S-101 2.0 `Berth` 피처 43개 확인. 이는 **API 응답이 아닌 DB 조회 결과**다.
- `tests/unit/test_uport_map.py`: 6개 통과. bbox 오류와 미연결 Provider의 503 확인.
- 실제 GeoLLM 앱 `TestClient`: `/uport/`, `/uport/map.js`는 200, 미설정 Provider를 강제한 선석·AIS API는 503.
- `node --check`, Python `compileall`, `git diff --check` 통과.

## 발견된 문제와 남은 작업

- 호스트 Python에서 PostGIS에 직접 접속하는 smoke test가 인증/문자 인코딩 오류로 실패해 실제 신규 API의 성공 응답은 확인하지 못했다. 컨테이너 내부 SQL과 테스트 클라이언트 오류 경로만 검증했다.
- 실시간 AIS 개별 선박 위치 Provider와 항만 운영 DB가 미연결이다. `standardized.dynamic_traffic_observation`은 집계 관측 데이터이므로 실시간 MMSI 위치로 사용하지 않았다. 선박 선택 및 선석 점유/배정 상태는 제공하지 않는다.
- 브라우저 세션이 없어 지도 타일, 클릭, 반응형 화면의 시각 검증은 수행하지 못했다. CDN 또는 WMS에 접속하지 못하면 UI가 연결 실패 상태를 보여준다.
- Phase 5에서는 선택된 지도 객체를 공통 `QueryExecutionContext`로 전달하고 Capability/Resolver/Validator와 연결한다.
