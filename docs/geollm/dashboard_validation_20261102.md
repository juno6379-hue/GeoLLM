# 통합 대시보드 전문 검증 — 2026-11-02

운영 `http://localhost:8000/`의 기존 기록을 사용했다. 신규 Qwen/Ollama 추론, DB 수정, 컨테이너 재시작, 연구/홀드아웃 변경은 하지 않았다. 기존 index.html의 관리자 script 태그와 admin-workspace.js 변경은 보존했다.

## 실제 사례 원문

원본: `outputs/dashboard_validation_20261102_v1/busan_entry_0.json`–`busan_entry_2.json`. SQLite를 `mode=ro`로 열어 기존 record 문자열을 그대로 보존했다. GET 비교 이력 2건도 `comparisons.json`에 보존했다.

| 비교 ID | 요청 문맥 | 실제 실행 판단 | Qwen 비교 |
|---|---|---|---|
| 9db410ca-ac11-4b9a-a832-d118960431d7 | 빈 문맥 | NEEDS_CLARIFICATION / DISTANCE_REQUIRED, location/location_text 누락 | FAILED / TimeoutError |
| 289cdbf9-2fa3-4f04-8d2a-a6cf45fe670e | 인천권 map_bounds | 명시 부산항 입구 대신 MAP_BOUNDS area 계획 → DATA_COVERAGE_UNVERIFIED | FAILED / TimeoutError |
| 93433c64-6134-4c7c-8464-cebe9a8d9d7f | 빈 문맥 | NEEDS_CLARIFICATION / DISTANCE_REQUIRED | QUEUE_FULL |

지도 범위 대체 사례의 bbox는 `[126.48147680679334,37.363194766127506,126.61279776016248,37.44732932109275]`다. 명시적 부산항 입구 해소보다 viewport가 선택된 문제 및 빈 문맥의 위치 슬롯 누락은 별도 운영 수정 에이전트에 전달했다. 이 문서의 UI 변경으로 해당 backend 문제가 해결됐다고 주장하지 않는다.

규칙 후보 순위는 실행 승인과 다르다. 이 사례의 실제 선택 경로는 SPATIAL_ANALYSIS다. Qwen 비교 실패는 공간 실행의 실패/허용 판단이 아니며, timeout 원인을 모델의 의미 해석 오류로 단정하지 않는다.

## 이번 표시 수정

`services/orchestrator/static/intent-comparison.js`:

- 순위가 없는 Qwen·융합 행을 생략하지 않고 시간 초과/대기열 초과/중단/대기/기록 없음으로 구분한다.
- 실제 실행 상태·error_code·summary를 별도로 보존해 비교 FAILED와 구분한다.
- 누락/null/nonfinite 점수를 `.toFixed()`로 처리해 패널 전체가 반복 오류로 바뀌는 경우를 방지한다. 누락 점수는 미기록이며 0점이 아니다.
- `needs_clarification`, `disagreement`, `latency_ms` 미기록을 각각 불필요·일치·0초로 표시하지 않는다.
- 새 질의 시작 시 이전 비교 내용을 지우고 늦은 이전 응답을 무시하는 기존 동작을 유지한다.

## 검증

- `node --test tests/unit/test_intent_comparison_ui.js`: 4 passed.
- `node --check services/orchestrator/static/intent-comparison.js`, 대상 `git diff --check`: 통과.
- `outputs/dashboard_validation_20261102_v1/replay.cjs`: 저장된 실제 3 record를 이전/수정 JS에 각각 DOM 재생. `dom_replay.json`에 원본·코드 SHA와 표시 내용을 보존했다. 합성 결측 부정 사례는 별도 회귀 검사이며 실제 서비스 오류 관측 수에 합산하지 않는다.
- `GET /intent-comparison.js`: HTTP200, 로컬 수정 파일과 SHA256 일치(`f15949d39e34f1d0257dd0428d866fd4d85969e01e190fc8f1535c14e44f905f`). 원본 `static_http_verification.json`.
- index/admin/evidence 파일의 작업 전 사본을 출력 폴더에 보존했다. 이 세 파일은 이번 에이전트가 수정하지 않았다.

## 한계와 다음 검증

CUA 탭 연결 2회 및 native helper 초기화 1회가 timeout으로 실패했다. 실제 화면 렌더링·메뉴 클릭·지도 조작은 미검증이며 HTTP 자산 확인/DOM 재생과 구분한다. 기존 열린 탭은 새로고침 후 새 JS를 사용한다.

다음은 운영 수정 에이전트의 입구 reference/반경/viewport 계약을 검토하고, 모델 호출 없는 대표·부정 재현으로 명시 부산항 입구를 다른 지도 영역에 치환하지 않는지 확인하는 것이다. 이후 자원 여유 시 실제 브라우저에서 화면·메뉴·접근성과 최종 질의 흐름을 확인한다. 통합 대시보드 전체 오류가 해결됐다는 선언은 아니다.

## 상단 답변 후속 보완

부모 검토에서 실제 상단 문구가 `execution-view.js` 경로임을 확인했다. 해당 Qwen 해석·융합 행에도 시간 초과/대기열 초과/중단/완료됐으나 결과 없음과 실행 판단 분리를 적용했다. 원래 `DISTANCE_REQUIRED` 코드만으로 "기준 위치는 확인"이라고 하던 단정도 제거했다. 이 코드 하나는 입구 위치의 해소 증거가 아니다. 기존 테스트와 상단 FAILED/QUEUE_FULL/미산출·위치 미확정 테스트를 함께 실행한다. 위 HTTP 해시 확인은 접이식 비교 JS에 한정하며 상단 후속 변경의 브라우저 렌더링 검증은 별도 남는다.

부모 항만 후보 후속: `radius-results.js`는 `selection_scope=PARENT_PLACE_ONLY` 또는 `qualifier_binding_verified=false` 후보를 "세부 위치 미확인 — 선택 불가"로 표시하고 버튼 및 클릭 handler에서 막는다. 부모 geometry를 입구 좌표로 재전송하지 않는다. 상단 후보 선택 가능 개수에서도 제외하고 세부 위치 근거를 요청한다. 기존 수동 좌표 form 및 실제 입구 후보 경로는 유지한다. index/admin 변경은 없다.
