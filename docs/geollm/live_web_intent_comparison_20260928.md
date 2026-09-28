# 웹 요청의 규칙 / Qwen / 융합 비교

## 적용 범위와 처리 순서

웹의 `POST /api/v1/tasks/stream` 요청은 빠른 지명 이동을 포함해 요청마다 고유 comparison_id를 발급한다. 같은 task_id를 재개해도 별도 비교 기록을 만든다.

1. 기존 규칙/슬롯/근거 검증 경로로 요청을 실행한다.
2. 별도 단일 worker가 QueryCandidateBroker로 후보를 만든다. 이 비교 기준선에서는 legacy Ollama semantic prior를 호출하지 않는다.
3. 동일한 2–4개 후보와 capability 입력/출력 계약을 Qwen에 제공한다. 규칙 점수는 모델에 노출하지 않는다. 후보 순서는 질의 hash로 고정한다.
4. Ollama에서 Qwen을 실제 호출한다. 후보 ID를 키로 하는 필수 점수 객체와 원문 선택지/JSON null 슬롯 스키마를 사용한다. 수량은 공통 slot_evidence 추출기를 사용하며 반경에는 원문 거리 수량만 허용한다. 후보 전체 점수, 원문 인용·위치/반경/시간 슬롯, capability 참조, 선택과 점수의 일관성을 검사한다. 통과는 구조/원문 근거 검사이며 의미 정확도 승인이 아니다.
5. 규칙 순위, Qwen 순위, 두 정규화 점수의 동일 가중치 융합 순위와 disagreement를 기록한다. calibration은 UNFITTED, human_gold는 null이다.
6. 웹 비교 패널은 결과를 별도로 갱신한다. 실제 실행 상태와 실행 허용 범위도 함께 표시한다. 모델 비교 결과는 도구 선택이나 실행 권한을 바꾸지 않는다.

기존 실행 경로의 최종 route_plan과 비교용 broker 기준선은 별도 기록이다. 순위 불일치를 곧바로 의도 오류로 집계하지 않는다. 최종 필수 작업, 슬롯, capability, 실제 실행 근거와 사람 검수가 필요하다. 전체 일반 라우터를 이 비교 worker로 교체한 것이 아니다.

## 실행 허용 보완

`해운대구로 이동`처럼 명시적 이동/가줘 명령인 경우, 행정지명 도메인의 후보가 하나이고 원문 지명과 정확히 일치하며 EPSG:4326 좌표와 출처가 유효하면 지도 화면 이동만 허용한다. 현재 자동 허용 문법은 공백 없는 한글 행정지명으로 제한한다. 후보의 단순 신뢰 점수나 Qwen 점수로 허용하지 않는다.

- `scope=map_view_only`, `analysis_authority=false`, `registry_promoted=false`를 결과에 보존한다.
- 복수 후보, 비정확 이름, 유효하지 않은 좌표/출처, 분석·복합 질의와 제외/대상 조건은 이 허용 경로로 통과하지 않는다.
- 일반 `/places/resolve`와 분석용 위치 resolver의 근거 정책은 유지한다. 지도 이동 허용은 authoritative 승격이나 분석 입력의 자동 확인이 아니다.
- 지명 이동 마커는 좌표를 임의로 흔들거나 선석/S-101 객체로 표시하지 않는다.
- 기존 문구의 “authoritative 승격 전이므로 확인”을 “요청 위치에 맞는 후보 선택”으로 바꾸어 사용자 확인과 registry 승격을 구분한다.

## 기록과 운영 한계

`GET /api/v1/intent-comparisons/{comparison_id}`에서 입력·문맥, 후보, registry/source/prompt hash, 모델 tag/digest, 실제 모델 요청/응답, 지연, 실행 관측을 조회한다. 저장 파일은 `geollm_results/web_intent_comparison.sqlite3`다. 런타임 기록은 소스 커밋에서 제외한다.

단일 backend 프로세스와 단일 추론 worker, 대기열 8개를 전제로 한다. 넘으면 QUEUE_FULL, 재기동 중단은 INTERRUPTED, 모델 통신/출력 검증 실패는 FAILED로 남긴다. 실패를 규칙 fallback의 성공적인 Qwen 비교로 표시하지 않는다. 재기동된 대기 작업을 자동 재실행하지 않는다. 다중 uvicorn worker 운영은 별도 공용 큐/소유권 설계가 필요하다.

웹 기본 모델은 `qwen2.5:1.5b`, CPU thread 4, context 4096, output 500 tokens, timeout 180초다. 이 PC의 `ollama ps`에서 Qwen 4B는 CPU 100% 실행이었고 입력을 압축해도 180초 timeout이 발생해 설치된 1.5B로 조정했다. 4B는 `GEOLLM_WEB_SHADOW_MODEL` 설정으로 별도 재평가할 수 있다. 비교는 SSE 응답 완료와 독립적으로 진행되므로 지도/분석 응답을 모델 완료까지 보류하지 않는다. 이 지연은 실시간 모델 실행 결정을 허용하는 근거가 아니다.

## 검증

- 최초 관련 단위 49 passed. 확대 회귀 110 passed / 3 failed: 스트림에 불필요한 빈 execution_permission 필드를 추가한 회귀였다. 필드가 있을 때만 보존하도록 수정 후 신규 비교/스트림 70 passed.
- 실제 SSE 1차: 이동 COMPLETED, 위험객체 요청 NEEDS_CLARIFICATION. 두 Qwen 4B 호출은 각각 180초 timeout으로 FAILED. 원본 `outputs/web-intent-audit/20260928-live-comparison-v1/` 및 비교 DB에 보존했다.
- 2차: 중복 capability 설명과 추론 입력/출력 한도를 줄여도 4B는 timeout. 3차: 1.5B는 실제 응답했으나 이동 요청은 문자열 `"null"` 위치 슬롯(72.4초), 분석 요청은 중복 후보 점수/누락(80.9초)으로 거절했다. 원본 v2/v3 및 DB 기록을 보존했다. 이를 유효 Qwen 비교로 집계하지 않는다.
- 후보 필수 점수 객체와 원문 enum 스키마로 보완 후 신규 비교/스트림 단위 71 passed. 최종 관련 전체 회귀 **114 passed**, 경고 2개. 최종 재현: `python scripts/check_live_intent_comparison.py --output outputs/web-intent-audit/20260928-live-comparison-v4`.
- 최종 실제 SSE 및 비교 **2/2 계약 통과**. 이동은 COMPLETED + map_view_only, 위험객체 요청은 NEEDS_CLARIFICATION이며 지도 이동 특례를 적용하지 않았다. Qwen 호출/구조·원문 검증/세 순위 기록 모두 완료했다. 지연은 각각 62.832초 / 59.407초(대기열 시간 제외)다. 비교 ID는 `6506c29b-d4cf-469c-a807-9c3c935d2ce3`, `9d60b25e-be10-47bb-adf3-f66a1d292c95`다.
- 의미 품질 한계: 이동 요청에서 Qwen은 PLACE_LOOKUP/SPATIAL_ANALYSIS에 모두 1점, 위험객체 요청에서는 4개 후보 모두 1점을 주었다. 후자는 PLACE_LOOKUP을 선택하고 추가 확인 불필요라고 판단했지만 실제 실행은 추가 확인을 요구했다. 이동의 위치 슬롯은 `해운대구`, 반경/시간은 null이었다. 후보의 구분력과 추가 확인 판단을 검수해야 하며 2/2는 의미 정확도가 아니다. 동점의 저장된 `disagreement=false`는 정렬상 첫 후보가 같다는 뜻에 한정한다. 웹은 공동 1위와 동점 때문에 단순 일치 판정이 불가능함을 별도로 표시한다.
- 브라우저 도구는 Windows sandbox helper 초기화 오류로 시작되지 않았다. 실제 UI 클릭/시각 E2E는 미검증이며 API 성공과 구분한다.

남은 과제: 전체 질의 gold/holdout 기반 의미 평가·calibration·지연/부하 검증, 다른 P0 오해석(사건/VTS/예측/신항만예정지역), 기본 반경 정책 불일치. QLoRA 및 모델 실행 권한 승격은 보류한다.
