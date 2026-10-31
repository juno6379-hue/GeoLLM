# Qwen 시간 초과·정책 우회 재개 조사 및 수정 검증

## 원인과 변경

### Qwen 생성이 전부 시간 초과된 원인

운영 semantic_prior의 기본2.5초 제한이 CPU에서 모델 로드와 stream=false 전체 JSON 생성을 기다리는 조건에 맞지 않았다. 원본11회에서 처음2회는 모델 로드가 취소됐고 이후9회는 생성이 취소됐다. 서버499/500과 proxy RemoteDisconnected는 caller 취소와 연결된다. prompt는 약613자이며 긴 문서 입력 때문이라고 볼 근거는 없다.

같은 모델·원본prompt·options로 timeout만180초로 둔 별도smoke2회는 모두HTTP200/JSON객체였다. 냉시작18.288초(load7.794초), warm8.942초. CPU backend/18논리코어는 확인했지만 당시CPU경합 시계열은 없어 경합 원인은 미확정이다. 전체실행 baseline108호출도 성공해 모델 자체가 항상 실패하는 상태는 아니었다.

운영 기본timeout을 전역으로180초로 바꾸지 않았다. 연구 profile에서만2.5~180초를 명시하고 worker환경·manifest·문항별 조건을 검증한다. 원본run은 보존한다. 정상 JSON 수신과 의도정답은 별개이며 smoke2출력에도 is_place_like=false와 고신뢰place후보가 동시에 나오는 모순이 있었다.

### 공개 표준 설명의 오차단과 비공개 요청 우회

기존 정책predicate는 제한구역/restricted 표현을 곧바로 비공개자료로 취급했다. 반대로 진입제한 공공레이어 예외와 공간fastpath가 일반policy검사보다 먼저여서 명시비공개 요청이 DatasetPlaceResolver/NEEDS_CLARIFICATION으로 끝났다. 또한 parse노드에서 일부 실행모듈을 직접 호출하므로 conditional edge만 앞당겨도 모든 선행실행을 막지 못한다.

수정은 원문policy검사를 parse최초에 수행하고 기존 검증차단 경로로 종료한다. edge방어도 유지한다. 비공개차단은 BLOCKED_POLICY로 명시한다. 공개 feature+attribute+코드설명 문법과 FC의 실제feature/attribute binding을 확인한 요청은 전용 읽기전용 원천조회로 처리한다. 좌표·자료추출·비공개·복합공간 요청은 이 설명경로에서 제외한다.

공개 응답은 FC2.0.0 restriction 허용코드29개와 definition/판/parsed파일hash/XML출처hash/locator를 반환한다. ExecutionValidator가 실제sourcehash와 등록tool binding을 검사하고 승인receipt를 발행한 경우에만 COMPLETED를 반환한다. Qwen이 코드를 생성하거나 위치를 확정하지 않는다.

### API 지연과 비동기 처리

async graph노드 안에서 cache조회/저장, semantic route, slot추출, graph retrieval의 동기 네트워크 호출이 직접 실행되고 있었다. 이를 asyncio.to_thread로 분리했다. 느린검색을 기다리는 동안 다른 async 요청이 진행되는 회귀시험을 추가했다. 과거모든지연을 이 원인하나로 단정하지 않으며 모델시간·CPU경합·서버초기화도 구분한다.

## 실제 API 검증

원본5건 실패와 수정후 관측은 별도run에 보존했다. 최종 `runs/20261031_restriction_policy_integrated/verified_contracts.json`:

| 입력 | 수정 전/중간 | 최종 |
|---|---|---|
| 한국어 공개 제한코드 설명 | 정책차단→120초관측timeout | COMPLETED,29코드원문일치·출처hash일치·승인유효 |
| 영어 공개 제한코드 설명 | 정책차단→통신timeout | COMPLETED,동일근거검증 |
| 비공개 제한구역+코드 혼합 | BLOCKED | BLOCKED_POLICY,승인없음 |
| 비공개 진입제한 구역 좌표 | NEEDS_CLARIFICATION | BLOCKED_POLICY,선행공간실행없음 |
| classified military 좌표 | BLOCKED | BLOCKED_POLICY,승인없음 |

공개응답의 공간검색은 NOT_RUN이다. 문서설명을 공간0건 성공으로 표현하지 않는다. 초기통합관측 health3회중3초timeout1회를 보존했다. 이후 연구실행중 health10회는 모두200,약6.78~203.73ms였다. 이는 해당관측이며 전체서비스 SLO나 병행부하완료 선언은 아니다.

## 검증과 재실험

관련회귀57passed + 신규catalogue승인gate10passed(별도비중복). 최초존재하지않는 테스트파일명 호출은 수집실패였고 올바른경로로 재실행했다. 새 `20261031_graph_timeout180_v1`은180초연구조건과 정책/FC/async변경이 함께 들어가므로 timeout-only ablation이 아니다. 원본K1의 baseline90/graph18을 덮지 않는다. 새graph18 실제실행 결과는 완료후 이 문서와 인계에 추가한다.

남은 별도범위는 일반 정의/속성의fastpath오진입, AOI/복합대상/coverage 계약, 독립holdout·K5·recovery/ablation 및 전체모델의미품질이다. 본수정의 통신/정책/공개코드계약 검증과 구분한다.

## 새 graph v1 관측과 초기화 문제

180초조건 v1은18문항 관측완료, Qwen11/11 HTTP200, 생성호출7.774~23.335초로 기존2.5초취소는해소됐다. 소스전후hash일치. 그러나 IMPORT_WARMUP /api/embeddings1회가 프록시의 사전 /api/tags 10초 확인단계에서 URLError로 실패했다. 첫 ContextResolver FAISS인덱스생성실패 뒤 두번째인스턴스는성공했으므로 영향없음으로간주할수없다. v1원본은보존하고 post_run_audit.json에 DEGRADED_WARMUP으로해석을추가기록했다.

모델identity GET만 제한된1회재시도·안전한오류원인기록을추가하고, 최종초기화실패가남으면 실행성공으로인정하지않는gate를보완한뒤 별도v2에서재검증한다. 추론실패를자동반복해성공결과로교체하지않는다.

## 최종 v2 검증 결과

`runs/20261031_graph_timeout180_v2/graph/model_graph_manifest.json`: worker_exit_code=0, EXECUTION_OBSERVED, 18/18문항, source_unchanged_after=true. tool_registry hash도 동결·검증했다. 초기화85호출(embedding84, version1) 전부성공, identity재시도0회. 문항 embedding22회와 Qwen생성11회도 모두 RETURNED/HTTP200이며 생성11개 모두 JSON객체로 파싱됐다. 생성시간6.026~20.016초. 따라서 연구조건에서 원본11/11 timeout 문제는 재현되지 않았다. 운영2.5초 기본정책 자체는 유지하므로 운영 Qwen 응답보장이나 전체의미정확도 개선으로 확대해석하지 않는다.

graph상태는 COMPLETED11/BLOCKED3/NEEDS_CLARIFICATION3/PARTIAL1. 원본10/4/3/1과 달리 공개 restriction코드 설명이 정상완료됐다. 단순 COMPLETED는 정답을 뜻하지 않는다. 이전 baseline90을 같은snapshot에서 새graph18과 대조한 보고서는 `runs/20261031_graph_timeout180_v2/report/comparison_KR.md`. P18은 평가구조매핑 부재로 여전히 미측정이며 모델승률·정답률 비교를 주장하지 않는다. timeout·정책·FC·비동기변경이 함께 있으므로 timeout단독 ablation도 아니다.

정책을 앞당기는 과정에서 발견한 일반 공개공간요청 오차단도 수정했다. `제한구역`이라는 레이어이름 자체는 비공개자료가 아니다. `runs/20261031_restriction_policy_spatial_regression/verified_contracts.json`의4/4실제API검증에서 일반공개공간요청은 LOCATION_UNCONFIRMED/NEEDS_USER_INPUT으로 진행하고, 공개FC설명은 유효승인으로완료하며, 명시비공개/제한데이터요청은 BLOCKED_POLICY로차단했다. 앞선통합5/5와 구분해보존했다.

최종 관련회귀76passed, 기존ExecutionValidator/authority/definition33passed, proxy초기화/embedding9passed: 서로다른시험목록 총118passed. 원본run과 warmup실패가있던v1은 모두보존했다. 재현은 `protocol/model_graph_timeout_condition_20261031_KR.md`의명령에서 새출력디렉터리를사용한다. 완료된v2디렉터리를재사용하지않는다.

### 남은 우선순위

1. P0: 정의/속성질의의 공간fastpath오진입(예: Q1_01/Q1_02/Q2_01), AOI없는 intersects와 복합대상 부분완료의 계약위반을 별도재현·수정한다. 현재상태를 정상답안으로채점하지않는다.
2. P0 연구평가: P서술출력의 계약평가매핑을 원출력근거로구현하고 baseline과 공통측정범위를확정한다. 검색excerpt로 답안을소급보완하지않는다.
3. P1: API동시부하와 장시간SLO검증, 운영2.5초shadow timeout정책의 별도지연예산검토. health10/10관측만으로 전체지연문제해결을선언하지않는다.
4. 연구제한: 독립human GOLD/holdout, K5, recovery/ablation, 공간coverage, 기존벡터의역사적digest 미확정. 정상Qwen JSON도 의미모순이있으므로 후보생성기역할을유지한다.
