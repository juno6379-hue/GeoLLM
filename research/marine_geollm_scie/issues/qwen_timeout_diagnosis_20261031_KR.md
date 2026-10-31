# Qwen 11회 timeout 상세 원인 및 실제 재현 — 2026-10-31

## 결론

확인된 직접 원인은 **CPU에서 모델 로드와 전체 JSON 생성을 끝내기 전에 caller의 2.5초 제한이 만료된 것**이다. 원래 11문항의 의미 오답·모델 서버 영구 장애로 분류할 수 없다. 새 smoke에서는 동일한 원본 요청 두 건을 180초 관측 제한으로 실행해 HTTP 200과 JSON 객체를 받았다. 운영 API와 연구 proxy 전체 경로를 재검증한 결과는 아니며, 원래 v5 실행을 덮어쓰지 않았다.

## 확인 자료

- 원본: `runs/20261030_full_execution_v5/graph/{model_calls.jsonl,stdout.log}`.
- 당시 Ollama: `outputs/ollama_resume3_stderr.log`, `outputs/ollama_resume3_stdout.log`.
- 새 실제 smoke: `runs/20261031_prior_timeout_smoke_v1/{manifest.json,calls.jsonl}`.
- 운영 caller: `services/orchestrator/semantic_prior.py`의 `_ollama_prior`.

원본 graph의 Qwen 요청 11개는 모두 `stream=false`, `format=json`, `temperature=0`이며 출력 토큰 상한을 명시하지 않았다. prompt는 604~699자이며 원문과 정규화 질의를 함께 넣는다. 장문 문서의 context overflow가 원인이라는 증거는 없다.

## 당시 서버 기록과 취소의 의미

1. 03:36:48 KST 첫 Qwen CPU 로드 시작, 03:36:51 caller 연결 종료로 로드를 취소했다. 서버는 `client connection closed before llama-server finished loading, aborting load`와 `context canceled`를 기록했다.
2. 다음 요청도 03:37:01 시작 후 03:37:03 같은 이유로 취소됐다.
3. 세 번째 요청에서는 서버가 약 2.04초 만에 로드를 완료했지만 전체 답변 생성까지는 완료하지 못했다.
4. 원본 11회 서버 HTTP 로그는 499 두 건, 500 아홉 건이다. 세 번째 로드 완료부터 graph 종료 사이에 runner의 `cancel task` 기록도 아홉 건이다. 연구 proxy에서는 caller 취소 후 upstream socket을 닫았으므로 응답 본문 없이 `client_disconnected=true/RemoteDisconnected`로 기록됐다. 이 로그만으로 서버의 500을 별도의 영구 모델 결함이라고 단정하지 않는다.

proxy의 취소 전달은 기존 caller의 시간 제한을 보존한다. timeout을 피하려고 취소 후에도 무기한 모델 작업을 남기는 것은 해결책이 아니다.

## 자원과 시간 관측

당시 Ollama 로그는 Intel Arc 내장 GPU를 비활성 처리하고 CPU backend를 사용했으며 `OLLAMA_NUM_PARALLEL=1`이었다. 하드웨어는 Intel Core Ultra 5 125H, 논리 프로세서 18개, 가용 메모리 총량 약 31.7 GiB다. 원본 첫 로드 당시 free memory는 약 10.4 GiB였다. 같은 시점의 CPU 사용률 시계열은 없으므로 CPU 경합이나 메모리 부족을 확정 원인으로 추가하지 않는다.

후속 baseline의 모델 호출 108개는 모두 응답을 받았다. 호출 지연 중앙값 23.63초, 범위 10.79~121.66초, 생성속도 중앙값 11.50 token/s였다. baseline은 입력·출력·context·예산이 다르므로 이를 semantic prior의 동일 조건 지연으로 대체하지 않는다.

이번 읽기전용 진단에서 앱 측 `server.log`에는 포트 11434 중복 바인딩 실패가 반복됐지만 별도 `ollama serve`가 실제 GET API를 정상 처리했다. 중복 앱 실행 정리는 별도 운영 문제이며 당시 11회 timeout의 직접 원인으로 확정하지 않는다.

## 동일 원본 입력 2건의 새 smoke

초기 `/api/ps`는 빈 목록이었다. 모델 digest를 실행 전후 확인했고 원본 request의 model/prompt/options/stream/format을 변경하지 않았다. host에서 같은 Ollama `/api/generate`에 순차 요청했으며 호출 제한만 180초다. 자동 재시도와 새 모델 설치는 없었다.

| 사례 | HTTP/JSON | 전체 시간 | 로드 | prompt 처리 | 생성 | 출력 토큰 |
|---|---|---:|---:|---:|---:|---:|
| Q1_01 등대 유형·정의 | 200 / 객체 | 18.288초 | 7.794초 | 3.493초 | 6.947초 | 73 |
| Q1_02 정박지 객체 | 200 / 객체 | 8.942초 | 0.083초 | 2.553초 | 6.259초 | 67 |

warm 요청도 2.5초 내 전체 JSON을 받지 못하는 조건임을 확인했다. 180초가 최적 timeout이나 운영 응답 SLO라는 뜻은 아니다.

두 출력은 `is_place_like=false`, `operation=unknown`이지만 place 후보는 각각 `marine_gazetteer`와 `port`에 confidence 1.0을 부여했다. 정상 JSON 수신과 의미 정합성은 별도다. 모델 후보를 실행 권위로 승격하거나 이 두 건을 정확도 100%로 표현하면 안 된다.

## 다음 실행의 성공 기준과 최적화 순서

1. 연구 timeout profile을 별도 명시한 새 graph run에서 18개 관측과 모델 호출별 성공·취소·지연을 모두 보존한다. 원본 11개 요청의 성공 응답·JSON schema 적합성을 확인한다. graph 라우팅 수정으로 호출 대상이 달라지면 호출 수 11을 강제로 맞추지 말고 차이를 기록한다.
2. HTTP 성공, JSON 구조 적합성, 의도/슬롯 의미, 실행 계약·최종 산출물 충족을 각각 집계한다. prompt 변경 없이 timeout만 바꾼 효과와 운영 routing 수정 효과를 합치지 않는다.
3. 운영에서는 동기 모델 호출이 event loop를 점유하지 않도록 격리하고 실제 API 동시 요청·취소·대기열을 검증한다. 연구의 긴 timeout을 그대로 웹 환경 전역에 넣지 않는다.
4. 출력 토큰 상한·JSON schema·prompt 중복 축소·warmup/keep_alive·동시성 제한은 가능한 후속 최적화다. 각각 출력과 비용에 영향을 주므로 별도 조건을 기록하고 변경 전후를 검증한다. 이번 smoke에는 적용하지 않았다.
5. backend와 Ollama의 CPU·메모리·모델 로드 상태를 시간에 맞춰 계측한 뒤 경합을 판단한다. 내장 GPU 활성화·양자화·모델 교체는 이번 문제 해결에 섞지 않는다.

신규 연구 runner의 timeout 설정 방법은 `protocol/model_graph_timeout_condition_20261031_KR.md`를 따른다. 모델 digest는 이전과 동일하며 기존 임베딩·원본 v5 결과도 유지했다.
