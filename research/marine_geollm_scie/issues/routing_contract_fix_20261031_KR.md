# 정의·공간·복합 요청 실행계약 보완 — 2026-10-31

## 원인과 수정

- 공개 FC 정의/속성 요청이 레이어 이름만으로 반경 fast path에 들어갔다. 원문 요청의 문서형태/실행슬롯을 분리하고, 실제 FC 코드 또는 단일후보 사전 항목을 해소하는 `catalogue_document.py`를 추가했다. 실제 XML digest와 parsed source digest, 정의/기하/속성binding/출처 locator를 반환하며 ExecutionValidator만 실행승인을 발급한다. 코드만 맞았다고 의미정확도100%로 표현하지 않는다.
- 새 설명 경로가 좌표/지도표시를 함께 요구한 질의를 삼키는 회귀를 독립 코드검토에서 발견해 수정했다. 한국어·영어 복합4사례를 부정시험에 포함했다. 좌표계/위치정확도/within연산자의 정의는 값조회와 구분한다.
- selected area intersects는 선택영역 없이 문서결과만 COMPLETED로 반환했다. 이제 AOI없음은 AOI_REQUIRED/NEEDS_CLARIFICATION이다. AOI가있어도 현재 전용교차실행 미연결이므로 INTERSECTION_EXECUTION_NOT_SUPPORTED로 명시하며 반경검색으로바꾸지않는다.
- 등대+난파선 중 Wreck만검색하고완료하던 경로는 대상별 실제완료근거가없는경우 PARTIAL로내린다. target_features의요청라벨만으로실행증명하지않으며 per_target_execution의source/status/receipt를요구한다. 미실행검색을0건정답으로표현하지않는다.
- 사전의 ASCII age 부분치환으로 AnchorageArea가 손상되던 문제를 ASCII토큰경계로 수정했다. 독립 age용어정규화는유지한다.

## 검증

- 최종집중회귀83passed30.89s: 신규계약/공개속성승인/정책범위/definition router/ExecutionValidator.
- 별도기존출력의무33개중31passed2failed: 사고필터누락시험이 ACCIDENT_FILTERS_REQUIRED 대신 EXECUTION_GATE. HEAD의request_semantics/request_obligations/query_normalizer/korean_query_analysis/execution_validator/graph 6모듈을git show로읽어메모리에exec한동일시험도2failed18deselected4.04s,정확히같은EXECUTION_GATE불일치를확인했다. 무제한사고DB조회는호출되지않았다. 작업파일을덮지않고기존오류임을확인했으며별도오류코드정합성미비로유지한다. 그래프import시host.docker.internal:11434연결timeout도관측됐고연구추론결과로계수하지않는다.
- 실제API검증과새frozen run은부모에이전트가수행한다. 단위통과를실서비스완료로간주하지않는다.

## 잔여 제한

등대의구조물/등화다중객체매핑은현재운영사전에서권위있는단일매핑으로확정되지않았다. 연구GOLD의객체목록을운영코드에복사하지않았다. 이질의는불필요한공간검색을피하고문서경로로처리하되완전한설명정확도를선언하지않는다. AOI교차실행과복합대상별실행완성은여전히미지원이며명시적으로표시한다. 본변경은false COMPLETED를고친것이지없는기능을구현한척하는것이아니다.

## 실제 API v2 재검증에서 발견한 추가 오류

등대 정의와 within 연산자 정의는 공간오진입을피했지만 exact 전용 FastDocumentAnswer에배정돼 원문일치가없으면 FAILED/null로끝났다. 이는출처부족을런타임실패처럼표현한디스패치오류다. 정확한FC객체/표준관계가없으면기존StandardRAG create_plan 경로로보내실제문서검색을하게수정했다. exact함수직접호출의방어도추가하여불일치시BLOCKED/EXACT_DOCUMENT_BINDING_UNAVAILABLE, local_exact_registry_lookup, full_corpus_searched=false를반환한다. 전체문서에근거가없다고확대하지않는다. 신규AST디스패치/구조화응답포함집중26tests passed17.25s. 수정후실제API는부모가재검증한다.

## 지도 복합질의 지연·문서만 완료하는 오류 추가 수정

실제API v2의 `Explain Wreck attributes and show wrecks on the map.`는150초관측timeout뒤268초에문서2건만COMPLETED로끝났다. 독립감사에서캐시후라우팅실패의ChatOpenAI fallback이운영gemma2 CPU추론을251.6초기다리는것을확인했다. 모델호출에명시timeout/retry제한이없었고영어show/map가공간fastpath에인식되지않았다.

- 지도출력의검색범위가없으면parse최초계약검사에서MAP_SCOPE_REQUIRED/NEEDS_CLARIFICATION. 지도geometry/bounds/기준지명및명시위치구문은보존해후속resolver검증으로보낸다.
- 지도요청은map_spatial_result출력의무를갖는다. 실제PostGIS실행의유효ExecutionValidator승인, 성공공간결과, FeatureCollection, map_layers가모두있어야충족한다. 문서만검색하거나요청geometry/가짜빈collection을내는것은완료근거가아니다. 보존된Q4실제지도결과는새검사True로확인했다.
- fallback에transport timeout기본15초(환경변수GEOLLM_ROUTING_FALLBACK_TIMEOUT_SEC,0.1~60초유한범위), max_retries=0, 전체awaitable asyncio.wait_for를적용했다. 기존예외fallback은유지하며semantic_prior연구180초조건과별개다. 실제네트워크호출없이멈춘비동기모델의취소/1회호출을시험했다.
- guard의기존readiness=NEEDS_CLARIFICATION/BLOCKED가QEC enum에맞지않는것을실제API검증에서발견했다. QueryExecutionContext모델로NEEDS_USER_INPUT/BLOCKED_CONFIG를생성하며실행승인은발급하지않는다.
- 최종집중58tests passed8.53s, diffcheck통과. API v3는부모재기동후검증대기이며이시험만으로실서비스완료를선언하지않는다.

## 설명 완결성의 추가 출력 의무

API v3는실행경계12검사를통과했지만답변내용독립검토에서등대질의가LightVessel관련발췌만으로COMPLETED,연산자정의는문서0건으로COMPLETED인것을발견했다. 실행경계통과를의미정확도로오해하지않는다. 일반용어/속성설명에는grounded_term_explanation 의무를추가했다. 실제FC/정의사전/속성조회승인과요청주제에맞는원문·출처연결을확인하며단순retrieved_count·문서제목·발췌존재는설명완료의증명이아니다. 미충족이면PARTIAL/OUTPUT_OBLIGATIONS_UNMET로노출한다.

기존복합검색+속성설명은별도feature_attribute_explanation 의무를유지한다. 순수문서찾기는설명을강요하지않고, nearest공간질문의what-is를정의형으로오인하지않는다. 실제소스기반Wreck/AnchorageArea/조석예보정의와한국어·영어restriction29코드정상완료회귀를포함하여최종71tests passed11.05s, diffcheck통과. 이전단계시험과중복되므로누적합산하지않는다. 운영소스편집종료후부모가APIv4/동결연구실행을진행한다.
