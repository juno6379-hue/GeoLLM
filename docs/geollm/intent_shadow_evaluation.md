# GeoLLM 공통 의도 해석: Ollama shadow 후보 재평가

## 목적과 경계

새 표현마다 intent 분기를 추가하는 대신, 규칙·registry가 제안한 같은 후보를 Ollama가 문장 형태, 부정, 실행 슬롯, 지도·대화 문맥으로 재평가한다. 이번 구현은 **오프라인 replay 실험**이다. 운영 graph나 실행 route를 변경하지 않으며 모델 결과는 항상 `used=false`이다. 운영 요청마다 자동 수집하는 상시 shadow 연동은 아직 아니다.

`services/orchestrator/intent_shadow.py`는 후보별 적합도·문맥 적합도·필요 근거·누락 슬롯을 검증한다. 모르는 후보 ID, 후보 누락/중복, 비유한 점수, 최고점과 모순된 선택, 잘린 응답은 거부한다. 모델에 정답, split, 규칙 점수를 전달하지 않는다. 후보 순서는 질의와 ID 해시로 결정해 재현성을 유지한다.

Ollama에는 registry에서 준비한 후보당 최대 세 capability의 설명과 입력·출력 슬롯을 전달한다. 설명은 160자로 제한한다. v1에서는 둘만 전달해 C02의 반경 검색 설명이 누락됐으며 v2에서 수정했다. 원본 후보와 trace도 보존한다. JSON schema 전달 방식은 [Ollama 공식 API](https://github.com/ollama/ollama/blob/main/docs/api.md)에 따른다.

v2는 원문 인용(`query_quote`), 해당 후보의 capability ID, 판단 근거(`rationale`), 미충족 작업(`unmet_requirements`)을 필수로 받는다. 없는 인용과 다른 후보의 capability 참조는 거부한다. **검증 통과는 구조·참조 무결성만 뜻하며 설명 내용의 타당성까지 승인하지 않는다.** AI 사후 의견은 [문항별 판단 근거](intent_shadow_review.md)에 기록했다.

## 2026-09-25 실제 실험 결과

- `gemma2:latest`: 초기 2회 각각 180초 timeout. 축약 입력 C01은 통과했으나 307.9초여서 결과를 보존하고 배치를 중단했다. 의미 성능 비교 표본은 부족하다.
- `qwen2.5:1.5b`, `qwen-pilot-v1`: 16문항 완료. 계약 통과 **9/16**, 지연 중앙값 **55.62초**. 후보 집합 누락/불일치 2건, 점수 범위 위반 5건. 기존 API 관측 15건, 관측 timeout 1건.
- evaluation 10문항의 **잠정 단일 라벨 일치**는 규칙 2/10, Ollama 2/10, 세 혼합 방법 각각 3/10. 의미 정확도나 혼합 우월성의 증거가 아니다. evaluation의 계약 실패 5건에서 혼합은 규칙으로 fallback, Ollama는 abstain했다.
- reference label이 후보에 있는 문항은 8/10이다. label 부재는 요청 수행 기능 부재를 뜻하지 않는다. semantic candidate recall은 null이다.
- calibration의 유효 4문항으로 선택한 temperature는 4.0이다. 검수 전 라벨 기반이며 배포 불가다.
- `qwen-rationale-v2`: calibration C02/C03만 재실험. C02 구조·참조 검증 통과(151.66초), C03은 해당 후보에 없는 capability 인용으로 거부(88.80초). 점수 범위 위반은 없었지만 내용상의 기능 해석·대상 보존 문제는 남았다. prompt·입력·schema를 함께 변경했으므로 단일 요인의 개선 효과로 해석하지 않는다. v2 전체 evaluation은 미수행이다.
- shadow와 broker 회귀 테스트 **20 passed**. 운영 routing 변경·QLoRA 적용은 하지 않았다.

## 평가 방법

- 16문항은 자동 작성한 **검수 전 파일럿**이다. calibration 6문항, evaluation 10문항이며 독립 human gold/holdout을 확보했다고 주장하지 않는다. `gold_label_accuracy=null`을 유지한다.
- 규칙 baseline은 lexical candidate broker이다. pgvector와 기존 Ollama place prior를 끈다. 전체 운영 router의 정확도와 동일하지 않다.
- 각 방법에 동일한 최대 4개 후보를 준다. 잠정 reference label이 없는 문항도 전체 분모에 포함하며 `reference_label_coverage`를 별도 집계한다. 이는 실제 요청을 수행할 capability의 부재나 semantic candidate recall을 뜻하지 않는다.
- 비교: 규칙 softmax, Ollama softmax, 50:50 혼합, calibration 후 75:25 혼합, 규칙/Ollama/registry/문맥 55:25:10:10 혼합. 가중치는 실험 가설이며 검증된 최적값이 아니다.
- temperature는 calibration 문항에서만 NLL로 선택한다. evaluation label은 보정에 사용하지 않는다. `provisional_label_agreement`, 단일 라벨 macro-F1/NLL/Brier/ECE는 잠정 라벨과의 비교이며 요청 충족 정확도가 아니다. abstention/fallback, reference label 부재, 계약 검증 실패, 지연시간은 별도 관측한다.
- `registry_readiness`는 두 reference 검증 결과에 대한 보조값이다. 도구 실행 가능성이나 답변 정확도의 보증이 아니다. 문맥 완결성은 명시적으로 전달된 슬롯만 계산하며 질의에서 추출된 슬롯의 완전한 평가가 아니다.
- clarification/out-of-candidates는 혼합 방법의 advisory 선택을 보류한다. 모든 방법은 실행 권한이 없으며 근거 없는 분석을 실행하지 않는다.
- 실제 API 결과는 별도 관측한다. 현재 API 관측기는 spatial_context만 전달하므로 selected_layer/conversation 문항은 모델과 API가 받은 문맥이 다르다. 이 문항의 실행 성공 여부를 공정한 정책 간 승패로 해석하지 않는다.

## 재현

```powershell
docker cp configs/evaluation/. geollm_backend:/app/configs/evaluation
docker exec geollm_backend python -m scripts.run_intent_shadow --output outputs/intent-shadow/new-run --model qwen2.5:1.5b --timeout 180 --api-url http://localhost:8000
docker exec geollm_backend python -m pytest tests/unit/test_intent_shadow.py tests/unit/test_query_candidate_broker.py -q
```

실행마다 새로운 output 경로를 사용한다. manifest에는 모델 digest, Ollama version, prompt, dataset, registry/source hash, seed와 각 요청 옵션을 보존한다. raw_rows는 원본 요청·응답·기존 서비스 실행 관측을 포함한다. 도중 중단된 실험도 다음 명령으로 저장된 문항만 재평가할 수 있다. 원본 raw_rows는 변경하지 않는다.

```powershell
docker exec geollm_backend python -m scripts.run_intent_shadow --output outputs/intent-shadow/existing-run --summarize-only
```

런타임 로그와 원본 실행 산출물은 `outputs/intent-shadow/`에 보관하며 소스 커밋에 섞지 않는다. 부분 실행은 `run_complete=false`이다.

## 다음 실험과 QLoRA 판정

**사용자 검토 반영:** 침선 검색→사고 분석, 위치 조회→공간 분석을 route 이름만으로 오분류라고 단정하지 않는다. 관련·상하위·복합 기능이 요청 결과를 충족할 수 있다. 침선 사례는 위치·지정 반경·객체 검색 결과가 제공되는지, 위치 조회는 대상 위치를 올바르게 표시하는지 확인한다. 기존 API 실행은 Ollama 후보를 실행한 결과가 아니므로 API의 BLOCKED/COMPLETED만으로 그 후보의 적합성을 판정하지 않는다.

검수는 요청별 필수 작업과 허용 가능한 capability 조합을 먼저 정의하고, 출력·근거·슬롯 충족, 불필요한 실행, clarification 적절성을 각각 판단한다. 미검수 상태에서는 `task_adequacy=NOT_REVIEWED`와 semantic 지표 null을 유지한다. 계약 오류(점수 범위·후보 누락 등)와 의미 적합성을 섞지 않는다.

1. 검수자는 모델/규칙 예측을 보지 않고 원 질의와 문맥으로 요청 작업, 허용 capability 집합, 필요한 슬롯·근거, clarification 필요 여부를 판정한다. 불일치는 별도 adjudication한다. 검수자와 버전, lineage를 남긴다.
2. 후보 밖 요청과 잘못 순위 매긴 요청을 분리한다. 후보 누락은 QLoRA로 해결할 수 없다. registry capability의 입력·출력 계약으로 작업 조합을 제안하는 후보 생성기를 비교해야 하며, 질의별 `if/elif` 확장은 피한다.
3. 고정한 calibration/holdout으로 prompt와 모델을 비교한다. 새로운 오류에 맞춰 holdout을 수정하면 새 버전 평가로 분리한다. 충분한 표본에서 미관측 항만·용어, 근거 부족, 잘못된 실행, clarification precision/recall을 검증한다.
4. 상시 shadow trace는 지연 예산과 실패 격리를 검증한 뒤 연결한다. 관측만 하며 운영 실행 결정권은 승격하지 않는다.
5. prompt 개선 뒤에도 의도·슬롯·근거 선택 오류가 반복되고, 충분한 human gold/holdout, 기반 모델 라이선스, GPU, adapter 배포·rollback 조건이 모두 충족될 때 QLoRA 적용 여부를 판단한다. 현재 판정은 **DEFER**다.
