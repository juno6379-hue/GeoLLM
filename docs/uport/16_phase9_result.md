# Phase 9 — 지도 ↔ Agent 연동 결과

## 완료 작업

- 대시보드 AI 패널의 질문 입력을 활성화하고 지도에서 선택한 S-101 선석 피처의 ID·데이터셋·버전을 기존 `POST /api/v1/uport/query/execute`에 전달한다.
- 백엔드가 실제 조회에 성공한 선석 피처만 결과 목록과 지도 강조 레이어에 표시한다. 응답의 피처 ID·데이터셋·버전이 선택 객체와 일치하는지 UI에서도 확인한다.
- 결과 목록의 버튼으로 피처에 다시 이동할 수 있다. 지도·목록·향후 알림은 `uport:focus-feature` 이벤트를 공유한다.
- 지도 선택이 바뀌면 진행 중 요청을 취소하고 이전 결과 목록을 지운다. 선석 레이어를 끄면 Agent 선택도 해제한다.
- 결과 설명은 서버의 도구 기반 서술을 `textContent`로 표시하고 근거 개수를 따로 보여 준다. 실행 차단과 통신 오류는 명시적으로 표시한다.

## 수정 파일

- `services/orchestrator/static/uport/index.html`
- `services/orchestrator/static/uport/dashboard.css`
- `services/orchestrator/static/uport/map.js`

## 신규 파일

- `services/orchestrator/static/uport/agent.js`
- `tests/unit/test_uport_agent_ui.js`
- `docs/uport/16_phase9_result.md`

## 재사용 구성과 아키텍처

- 기존 Leaflet S-101 지도, `uport:map-selection` 이벤트, GeoLLM QEC·실행 API·Evidence·MapLayer 결과를 재사용했다.
- Agent → Map 강조는 서버가 검증한 GeoJSON에 한정한다. 지도 → Agent는 차트 피처 식별자를 전달하며 실제 존재 여부는 백엔드가 DB에서 다시 확인한다.
- AIS, 선석 점유, 최적화 배정, 알림을 지도에 생성하지 않는다. 해당 운영 데이터 공급자는 여전히 미연결이다.

## 실행·테스트 결과

- Node UI 이벤트 테스트에서 지도 선택 → 실행 요청 → 검증된 피처 강조와 목록 → 지도 이동을 확인했다. 선택 누락과 데이터셋 불일치 결과가 강조되지 않는 것도 확인했다.
- 기존 U-Port 실행·계획·지도 Python 테스트 통과. JavaScript 구문 검사 통과.

## 발견된 문제와 남은 작업

- 브라우저 세션이 없어 실제 Leaflet 렌더링과 반응형 화면은 시각 검증하지 못했다.
- 실제 백엔드 DB 성공 응답은 로컬 호스트 PostGIS 인증 문제 때문에 이 단계에서 재검증하지 못했다. UI 이벤트는 검증된 응답 Fixture로 테스트했다.
- Phase 10에서 요구 시나리오 A~F의 Intent, Resolver, 실행 차단, Evidence, 지도 표시를 운영 데이터 연결 여부에 맞춰 검증한다.
