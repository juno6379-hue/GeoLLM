# 한국어 슬롯·KG·도구 연결 구현 및 shadow 검증

2026-09-26. 범위는 공통 GeoLLM 질의 파이프라인이다. 기존 registry, 온톨로지/KG, PostGIS와 도구 실행 구조를 유지했다. 사용자 피드백 JSONL과 실행 산출물은 소스와 분리한다.

## 무엇을 왜 바꿨는가

원문 구간과 값의 종류를 검증하지 않으면 '12개월'이 반경이 되고, 문서 주제만 맞아도 분석이 완료됐다고 보고할 수 있다. `slot_evidence.py`에서 Unicode code point 구간, 원문 hash, 출처, 거리/기간 차원을 검증하고 1해리를 1852m로 변환한다. 버전·기간·수심을 검색 반경과 구분한다. 파서의 반경 제안은 원문 수량 또는 명시된 지도 입력과 대조하며 근거가 없으면 제거하고 거부 이유를 기록한다.

`korean_query_analysis.py`는 Kiwi를 프로세스당 한 번 초기화하고 기존 해양 용어 사전에서 사용자 사전을 만든다. 토큰 구간과 원문을 보존하며 초기화 실패·비활성 상태를 명시한다. 분석은 이벤트 루프 밖에서 실행한다. Kiwi는 형태 근거이며 완성된 의도 분류기가 아니다. 지원하는 명시적 부정·제외 범위를 보존하고, 실행기가 충족할 수 없는 제외/부재 조건을 무시해 실행하지 않는다. 현재 이 조건들은 BLOCKED이며 부정 조건 실행 구현 완료가 아니다.

`semantic_slot_binding.py`는 원문 용어 → 사전 canonical ID → 온톨로지의 타입이 맞는 KG 관계 → capability 입력/출력 계약을 연결한다. 침선은 실제 Wreck 노드와 관계에 연결되고 1해리 슬롯은 도구의 `radius_m=1852`에 연결된다. geometry 같은 미해소 입력은 별도로 남긴다. 관계의 verification status와 provenance를 보존하며 KG 연결만으로 실행을 허가하지 않는다. 로드된 사전·온톨로지·노드·관계의 hash를 남긴다. 이 seed는 실제 graph RAG에 전달하되 복합 요구에 필요한 기존 seed를 함께 유지한다.

registry의 같은 참조를 요청 안에서 반복 확인하던 부분은 요청 단위로 재사용한다. 다음 요청까지 DB 검증 결과를 캐시하지 않아 오래된 readiness가 전파되지 않는다.

`request_obligations.py`는 route 이름과 별개로 필요한 산출물을 검사한다. 모든 그래프 종료 경로가 공통 검사를 거치며, 필수 근거 없는 COMPLETED는 PARTIAL로 낮춘다. 지도 선택 객체가 없으면 선택을 요청하고 원천 자료 처리 방식 질문은 dataset 근거 경로로 보낸다. 필드 존재 검사는 의미 정답 검증이 아니므로 `EVIDENCE_PRESENT_REVIEW_REQUIRED`로 구분한다.

## 실제 관측과 해석

- S0에 이전 실제 API 100개 응답을 그대로 고정했다. `s0-baseline-v1/`의 원본 SHA-256은 `bc439f48f976621b619bbb426f00244569024badb1d17458b0da4d5313d80fdd`다. 과거 요청 기준 시각은 기록되지 않아 사후 생성하지 않았다.
- 동일 모델 입력 `frozen-model-inputs-v1.json`은 100개 중 실제 후보 trace가 있는 85개와 없는 15개를 구분한다. 후보는 기존 helper의 2–4개 route, route별 처음 3개 capability, 설명 전체를 고정했다. 전체 registry 검색 결과나 독립 정답셋이라고 부르지 않는다.
- `web-samples-v1/`: 실제 웹 preset 100개를 SSE API로 실행했다. COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8이다. 이 분포는 정답률이 아니며 불필요 질문률도 아직 측정하지 못했다.
- 이후 76번의 dispatch 우선순위를 고쳐 `p0-followup-v2/`에서 46/47/48/76/84를 재검증했다. 46 PARTIAL, 47/48 선택 객체 필요, 76 데이터 근거 PARTIAL, 84 기준 위치 필요다. 76의 원천→정제 전체 이력은 확보되지 않았다.
- 기존 실제 API 계약 `existing-contracts-v1.jsonl` 13/13, 신규 구간·단위·부정·KG/도구 계약 `live-contracts-v1.jsonl` 7/7 통과했다. 브라우저 화면 클릭 검증과 구분한다.
- 초기 관련 단위 207개 통과, 평가기 신규 테스트도 별도 통과했다. 최종 수정 이후의 재검증 결과는 아래 후속 기록으로 구분한다.

## 효율 측정의 범위

`benchmark-v1.json`: 100개 질의의 warm 한국어 분석 p50 1.218ms / p95 2.717ms, semantic binding p50 0.239ms / p95 0.661ms. 최초 Kiwi 초기화 7204.951ms, 첫 KG index 구성 1322.449ms가 따로 관측됐다. 모델 다운로드와 다른 작업이 있던 개발 환경의 단일 관측이며 배포 SLO가 아니다.

동일 참조 검증은 대표 8개 후보에서 호출 16→10회, 관측 152.101→77.227ms였다. 순서·DB 캐시 효과를 통제한 반복 실험이 아니므로 전체 API가 두 배 빨라졌다는 결론을 내리지 않는다. 구조상 중복 호출 감소와 측정된 부분 지연만 보고한다.

## Qwen3.5 비교와 승격 판단

Kiwi 0.23.2 / model 0.23.0 / jsonschema 4.26.0을 설치하고 `pyproject.toml`에 고정했다. Ollama 0.34.2에서 Qwen3.5:4b를 실제 다운로드했다. 모델 digest는 `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`, 실제 metadata는 4.7B Q4_K_M이다. 컨테이너 가시 메모리는 약 15.5GiB이며 GPU 용량은 확인되지 않았다. `/api/ps`의 해당 모델 `size_vram=0`으로 CPU 실행을 관측했다.

첫 2개 시험은 기본 thread 설정과 1400 출력 토큰 한도를 썼고 일부 테스트와 겹쳤으므로 이후 시험과 지연을 직접 비교하지 않는다. `qwen35-isolated-v2/`는 API/단위 부하를 함께 실행하지 않고 thread 4, context 8192, 출력 700, thinking off, temperature 0, seed 20260925, timeout 120초로 대표 10개를 시험했다.

4B 결과는 구조·인용·슬롯 근거 최종 통과 3/10, 원문 인용 불일치 5, 슬롯 근거 실패 1, timeout 1이다. p50 95.835초 / p95 120.067초다. **3/10은 의미 정확도가 아니다.**

동일 snapshot·설정의 `qwen25-isolated-v2/`는 최종 통과 2/10, 슬롯 근거 거부 5, 선택 후보와 점수 모순 3, timeout 0, p50 29.855초 / p95 37.215초였다. `paired-report-v2.json`에 두 모델의 raw 판단·오류·동일 입력 hash를 연결했다. 4B는 6개, 1.5B는 3개가 앞선 검증 단계에서 실패해 슬롯 검토까지 도달하지 못했다. 검토된 슬롯 중 거부율만 비교하면 선택 편향이 생기므로 전체 실패와 함께 본다. 이 표본에서 4B의 의미 정확도 우위는 입증되지 않았으며 지연은 더 컸다.

- 21번 정박지 Feature 질문: 표준/사전 경로와 함께 장애물 용어 도구를 제안했다. 원문 'S-101'은 존재하지만 핵심 대상 정박지를 충분히 반영했는지 문제이며, 구조 통과가 정답을 보장하지 않는다.
- 28번 통항량 질문: 통항 집계와 위치 누락은 파악했으나 원문 '1년간'을 '1 년간'으로 반환했다. 원문 구간 계약 실패이며 의도 전체가 틀렸다고 단정하지 않는다.
- 79번 pgvector 질문: dataset registry 선택만으로 실제 DB top-k 동작 검사를 충족하지 못한다. 모델도 미충족 작업을 남겼다. 질문을 더 하는 것이 해결책인지 별도 검수가 필요하다.
- 87번 사고+보호구역 질문: 장소 해소는 필요한 선행 작업이므로 PLACE_LOOKUP을 골랐다는 이유만으로 오분류하지 않는다. 보호구역 조회와 사고 조회를 모두 계획에 포함했는지, 필요한 반경과 위치를 구분했는지가 핵심이다.

smoke에서 timeout과 원문 계약 실패가 발생했으므로 이 설정을 전체 85개 비교나 상시 서비스 호출로 확대하는 조건을 충족했다고 보지 않는다. 100개 실제 API 회귀와 10개 모델 비교를 혼동하지 않는다. 9B는 RAM/VRAM 여유·10개 timeout 없는 실행·API 부하 조건을 입증하지 못해 보류한다. GPU가 물리적으로 없다고 단정하지 않는다.

`used_for_execution=false`를 유지한다. 혼합 순위는 보존하되 temperature=1 가중합을 학습된 calibration이라고 부르지 않는다. 독립 human gold가 없으므로 작업 충족·슬롯 의미 정확도·질문 품질·과잉 실행의 정답 지표는 null이다. 모델 출력 없는 개발 검수 양식 100개와 [검수 지침](korean_shadow_annotation_guide.md)을 만들었다. 이것은 독립 holdout 수집을 대신하지 않는다. **QLoRA DEFER**.

## 남은 구현과 다음 순서

1. portrayal rule→symbol 실제 연결, 선택 객체 원천 조회, 원천→정제→serving lineage와 복합 작업 실행을 완성한다. 현재는 근거 없는 완료를 막는 계약이며 이 기능들을 구현했다고 주장하지 않는다.
2. 부정/제외 조건의 실행 지원, 문맥으로 공급된 슬롯의 검증·참조, 명시 날짜/상대 기간의 완전한 해소를 보강한다. 모든 한국어 부정 표현을 지원하지 않는다.
3. shadow 원문 선택을 자유 생성에서 검증된 span 선택으로 제한하는 후속 adapter를 별도 버전으로 비교한다. 현재 결과를 덮어쓰지 않는다. 모델 부족과 후보 capability 부족을 나눠 기록한다.
4. 자원과 timeout을 해결한 설정으로 smoke를 통과한 후 85개 실제 후보 비교를 확대한다. 후보 trace 없는 15개는 누락 원인을 먼저 해결하며 lexical 후보를 대체 정답으로 넣지 않는다.
5. 독립 human gold/calibration/holdout 확보 후 작업·슬롯·질문·과잉 실행·지연을 평가한다. 그 전에는 상시 shadow 승격과 QLoRA를 수행하지 않는다.

재현 원본은 `outputs/korean-intent-shadow/`에 보존한다. 실행 산출물은 ignored 파일이며 소스 커밋에 포함하지 않는다.

## 최종 확정 관측과 정답 근거 설계

`web-samples-v3`에서 45번은 완료 이벤트를 수신했지만 실제 상태는 FAILED였다. SQLAlchemy 2.1의 기본 PostgreSQL 드라이버 변경으로 설치되지 않은 psycopg를 요청했다. SQLAlchemy를 `>=2.0.31,<2.1`로 제한하고 lock/image를 재생성해 2.0.54와 psycopg2를 확인했다. 수집기도 이벤트 수신과 도메인 실패를 구분하도록 수정했다.

최종 `web-samples-v4`는 100/100 완료 이벤트, FAILED 0, 관측 오류 0이며 45번도 COMPLETED였다. 상태는 COMPLETED 9 / PARTIAL 15 / NEEDS_CLARIFICATION 68 / BLOCKED 8이다. 추가 질문의 필요성이나 답변 의미 정확도는 이 상태만으로 평가할 수 없다. S0와 동일 원문/ID 100개를 `stage-matrix-v1.json`에 대조했고 주요 단계 변화 5개를 기록했다. 최종 이미지 `pip check`와 평가 지표 테스트 11개가 통과했다(기존 테스트와 중복).

검수 gold에 대한 intent accuracy/macro-F1, tool-plan 대안 조합 F1, raw 슬롯 종류·값 F1, clarification F1을 구현했다. 모델 실패도 분모에 유지한다. human gold가 없으므로 현재 실제 의미 지표는 null이며 구조/원문 검사 통과 3/10 또는 2/10을 정확도로 표현하지 않는다.

사용자 제안에 따라 [해양 정답 근거 기준](maritime_evaluation_reference_standard.md)과 참조 정책 YAML을 추가했다. 공식 사전 위키·일반 위키의 역할, S-101 FC/PC/DCEG 2.0.0·법령·고시·실제 공간 데이터의 적용 범위, 주장별 근거와 행동별 정답의 구분을 명시했다. `development-review-v2.jsonl` 100개에는 빈 출처/주장 검수 필드가 포함된다. 문서 설계와 검수 양식 확장이며 원천 자동 검증·human gold 완료를 의미하지 않는다.

## 최종 후속 검증

- 원문 없는 반경 제거, 제외 용어의 입력 바인딩 방지, KG 버전 hash, null 근거 감사, 빈 gold 대안 방지를 검사했다. S-101 실행기까지 확장하자 공통 종료 노드의 enum 상태 타입 회귀 2건을 발견해 수정했다. 새 이미지에서 관련 14개 테스트 파일 **324 passed**. 전체 저장소 테스트 완료를 의미하지 않는다.
- `1,000m`와 `.5km`도 원문을 보존해 처리한다. S-101 반경 실행기와 일반/통항 실행기가 같은 수량·범위 판정을 사용하며 수심 8m와 반경 1해리를 혼동하지 않는다. S-101의 기존 공개된 기본 부근 반경 정책은 유지하며 모델 생성 기본값과 구분한다.
- Compose 설정, `poetry check --lock`, 이미지 빌드의 `pip check` 통과. 실제 생성된 `poetry.lock`을 소스에 추가하고 패키지 버전을 재현 가능하게 고정했다. Dockerfile의 후속 wheel 설치가 packaging을 비호환 버전으로 올리던 문제를 `<25` 제약으로 고쳤다.
- `.dockerignore`에서 Compose로 마운트하는 outputs, 처리 결과, 임시 파일, 환경 파일과 상태 DB를 제외했다. 첫 빌드는 context 4.11GB 전송 중 중단했고 수정 후 전체 context는 197.01MB였다. standalone 이미지에는 runtime outputs가 없으므로 Compose의 outputs 마운트가 필요하다. 원본 파일을 삭제하지 않았다.
- backend만 새 이미지로 재생성했고 `/health` 200, Kiwi/model/jsonschema/packaging 버전을 재확인했다. DB·타일 서비스는 재생성하지 않았다.
- `live-contracts-v2.jsonl`은 7/8이었다. 실제 부산항 명칭이 항만/도서지명 원천에 중복되어 실행 전 추가 선택이 필요했기 때문이다. 기대를 몰래 완화하지 않고 최초 응답을 보존했다.
- `live-contracts-v3.jsonl`은 **8/8**. 거리 실행 사례만 API가 반환한 실제 항만 후보를 평가 harness가 명시 선택해 후속 요청했다. 후보 ID `harbour:598357`, source `projection.s101_feature_valid`, 후보 버전·geometry를 그대로 전달하고 최초 응답을 함께 기록했다. 운영의 모호한 위치 확인 정책을 우회하거나 가짜 좌표를 넣지 않았다.
- 후속 요청은 실제 `gbenc.s101_feature_search_by_radius` / `postgis.dwithin`으로 **1852m 이내 Wreck 8건**을 반환했다. 거리 범위 1354.49821204–1585.96430809m, 객체 근거 8개와 query execution ID를 확인했다. 단순 후보·슬롯 검사와 실제 도구 실행을 구분한 증거다.
- `GEOLLM_KIWI_ENABLED=false`는 Kiwi만 비활성화한다. 슬롯 근거/부정/산출물 검사는 유지된다. 검증기를 끄는 별도 flag는 구현하지 않았으며 rollback은 해당 코드 변경의 복원과 API 재검증이 필요하다.
- 새 컨테이너의 기존 API 계약도 `existing-contracts-v2.jsonl` **13/13** 통과했다.
- `web-samples-v2/`는 100개 중 99개 완료 이벤트, 45번 `STREAM_ENDED_WITHOUT_COMPLETION`이었다. legacy 응답에 final_dict가 없을 때 새 공통 종료 노드가 빈 update를 반환해 LangGraph가 거부했다. 상태를 보존하는 update와 agent_result 산출물 감사 경로를 추가했다. 실패 원본을 보존했고 관련 후속 76개 테스트가 통과했다. 최종 재실행은 별도 run으로 기록한다.
