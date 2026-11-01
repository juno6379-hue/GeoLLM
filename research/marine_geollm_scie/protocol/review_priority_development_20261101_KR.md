# 초기 실행계획 검토 보완 — 연구 개발 기록

운영 Validator 수정과 분리한 연구 reviewer 개선이다. v3의 raw output, score, GOLD, structured_review_v1.json은 변경하지 않는다. 이 변경은 새로운 동결 실험에만 적용해야 한다.

## 관측 원인

v3 WRONG_FEATURE 원본에는 상위 target_features=Wreck, 실제 tool_calls.arguments.feature_types=Obstruction이 함께 있다. 모델은 상위 필드가 맞다는 이유처럼 정상 판정을 내고 실제 인자 불일치를 그대로 복사했다. 기존 prompt는 초기 계획 판정을 요구했지만 실행 인자와 상위 요약을 항목별로 대조하는 관측 가능한 출력이 없었다. 이것은 원인 가설이며 새 모델 실행 없이 개선 성공을 선언하지 않는다.

## 변경

- `structured_review_v2_initial_checks`: 모델이 초기 계획의 target/distance/crs/reference/source/tool_contract를 pass/fail/unknown/not_applicable로 표시한 뒤 기존 invalid·reason·plan을 출력한다.
- 입력 원질의와 공개 문맥을 실행되는 모든 tool argument와 대조하도록 명시한다. 상위 요약이 맞아도 실행 인자가 다르면 불일치다. 복합 질의는 모든 하위 도구 호출의 집합으로 보며 각 하위 호출에 모든 대상을 강제하지 않는다.
- 수정안의 결과로 초기 invalid 판정을 바꾸지 않도록 설명한다. 근거 없는 geometry/source 생성은 금지하며 plan.answer는 비워 출력 예산을 아낀다.
- 모델이 fail이라고 쓰면서 invalid=false라고 쓴 응답은 `REVIEW_VERDICT_CONTRADICTION` 계약 실패로 보존한다. 프로그램이 invalid=true로 고쳐 검출 성공으로 계산하지 않는다. 원본 응답을 유지하고 미측정/실패 분모에 남긴다. unknown을 프로그램이 실패로 승격하지도 않는다.
- B4는 여전히 독립 LLM 검토다. 결정론 원요청 비교 결과나 GOLD 정답을 모델에게 주지 않는다. H/P0의 Validator 효과와 혼합하지 않는다.

새 계약 파일은 `structured_review_v2.json`이다. 768 출력토큰·180초·한 번 호출·재시도0을 유지한다. 추가 필드 때문에 길이 종료가 늘 수 있으며 실제 프로브에서 반드시 점검해야 한다.

## 검증 및 다음 실행

실제 Qwen2.5:1.5b 개발4건은 모두 형식/stop 통과했지만 정상과 오류3건 모두 invalid=false와 모든 initial_checks=pass를 반환했다. `outputs/review_priority_development_20261101_v1`에 원본·digest·hash를 보존했다. 따라서 이 prompt 보완의 의미 검출 효과는 확인되지 않았으며 해결로 인정하지 않는다. 이미 설치된 Qwen2.5:7b는 별도 개발 후보로 검사하고 기존1.5b benchmark와 합산하거나 모델을 몰래 교체하지 않는다.

단위 검증은 형식·자기모순·미측정 보존·원문 인자 직렬화·종료사유·재시도 없는 동작을 다룬다. 모델 의미 판단 품질은 단위 테스트로 증명하지 않는다.

v3 fault를 보고 변경했으므로 같은 fault 재실행은 개발 진단이다. 독립 holdout 정확도로 보고하지 않는다. 정상 계획, 상위/내부 인자 충돌, 기준 geometry 누락, 단위 동등 표현, 복합 부분집합을 포함하는 별도 개발 프로브를 먼저 실행하고 형식·길이 종료·의미 판정을 따로 기록한다. holdout과 독립 인간 검수는 별도 확보한다. 새 전체 benchmark는 소스·프로토콜을 다시 동결한 후 실행한다.
