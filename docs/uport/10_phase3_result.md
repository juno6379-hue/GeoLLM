# Phase 3 — U-Port 메뉴와 대시보드 셸 결과

## 완료 작업

- GeoLLM 메인 좌측 메뉴에 U-Port Agent 링크 추가.
- `/uport/`를 독립 정적 경로로 등록해 직접 방문·새로고침 시 대시보드 문서 제공.
- `U-Port_UI.png`의 정보 순서를 참고한 대시보드 셸 작성: 좌측 메뉴, KPI, 중앙 지도, 오른쪽 AI 패널, 하단 운영 카드.
- 실제 Provider가 없는 항목은 대기 상태로 표시. 질문 전송은 비활성화.

## 수정 파일

- `services/orchestrator/main.py`
- `services/orchestrator/static/index.html`

## 신규 파일

- `services/orchestrator/static/uport/index.html`
- `services/orchestrator/static/uport/dashboard.css`
- `docs/uport/10_phase3_result.md`

## 재사용한 기존 구성과 아키텍처 변경

기존 FastAPI 앱의 `NoCacheStaticFiles`와 메인 페이지 메뉴 스타일을 재사용했다. `/uport` 마운트를 기존 `/` catch-all 마운트보다 먼저 등록했다. API, Agent, DB, 지도 실행 파이프라인은 변경하지 않았다.

## 실행·검증 결과

`fastapi.testclient.TestClient`로 GeoLLM 앱을 로드해 `/`, `/uport/`, `/uport/dashboard.css`, `/uport/` 재요청이 모두 HTTP 200임을 확인했다. `git diff --check`에서 공백 오류가 없었다. 브라우저 연결 가능 세션이 없어 데스크톱/모바일 화면의 시각 검증은 수행하지 못했다. CSS에는 1100px 및 680px 반응형 규칙을 정의했다.

## 발견된 문제와 남은 작업

기존 앱 초기화 과정에서 ContextResolver가 외부 임베딩 엔드포인트에 접속하지 못했다는 로그가 발생했다. 이번 정적 페이지 응답은 성공했다. Phase 4에서 실제 데이터와 지도를 연결하고, 브라우저 세션이 준비되면 배치·메뉴 클릭·좁은 화면을 시각 검증해야 한다. 현재 화면은 운영 수치, 실시간 AIS, S-101 레이어, Agent 질의를 제공하지 않는다.
