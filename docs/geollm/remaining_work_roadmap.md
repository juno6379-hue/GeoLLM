# GeoLLM 현재 상태와 다음 작업


## 2026-11-01 GOLD v2 8방법 새 동결 v2 재실행 — 최신 인계

- **실제 실행중**: `research/marine_geollm_scie/runs/20261101_gold_v2_eight_k1_v2/status.json`, 부모 PID33808. 새 snapshot `outputs/scie_gold_v2_eight_snapshot_20261101_v2/snapshot_manifest.json`. 실행중 소스/모델/공통입력/GOLD/예산 변경 및 중복 worker 금지. 실제 PID와 status를 우선 확인한다.
- 운영 수정 `6508224`: 명시 nearest를 radius로 변환하지 않고 미지원 사유로 차단, 실제 선택 대상에서 빠진 복합 family/미지원 비교를 차단. 지원 복수 검색 유지. [운영 검증](fast_path_contract_fix_20261101.md). 4 실제SSE: nearest UNSUPPORTED_OPERATOR, 비교 UNSUPPORTED_COMPOSITE_TASK, Wreck0행 PARTIAL/UNKNOWN, Wreck+Obstruction18건 COMPLETED. 최초 초기화 연결실패 v1 별도보존. shadow4건은 모두종료했지만 multi는 selection/score mismatch 실패다.
- 연구 수정 `27445e6`: 모델 source=list와 잘못된 구조를 교정하지 않고 실패 보존; projector/report 장애 격리, nonfinite JSON거절, 새공통V2schema covers지원. 주검증 통합121passed, 운영guard 축소후40passed(중복합산금지). v1 원본59파일hash 동일, immutableGOLD8파일 재검증. [연구 실행 조건](../../research/marine_geollm_scie/protocol/eight_execution_20261101_KR.md).
- 기존 place graph suite 28passed/1failed: execution_revision3→QEC1. 새guard 비활성화 재현도실패, 과거commit재생은아님. 기존dirty테스트/UI는보존. 승인coverage/nearest등대/canonicalpolygon인터페이스/복합비교는 미완료; 정확한차단과 전체기능완성을 혼동하지 않는다.
- v2 freeze/profiles exit0, 연구DB6관계 전체hash 재검증 완료 후 graph 실행 중(자식30760). v2는 P1도신규실행하고 B0/B1/B2/B3/B4/P0/H/P1 각18=144, 별도fault9×3=27 및 report_with_faults/comparison_KR.md까지 supervisor가 순차진행한다. v1 실패관측 재사용금지. 768토큰절단 등실제모델실패도포함, 독립GOLD미수령으로 인간정확도/과학적완료주장금지.
- heartbeat `geollm-gold-v2-8` 30분 점검 활성. 상태변화없으면조용히종료, 원본hash/완료gate/실제PID 확인. 실패시원본보존→별도수정·테스트→소스변경이면새전체run. 보고서·인계완료후자동점검종료. 결과목록은 research/marine_geollm_scie/RESULTS_INDEX_KR.md. push 요청없음.

## 2026-11-01 GOLD v2 8방법 v1 중단 원인·새 동결 재실행 준비

- `runs/20261101_gold_v2_eight_k1_v1`은 P1 18/18 이후 comparison 10행에서 STOPPED_REQUIRES_REVIEW. 원인은 `v2_answer_projection.render`가 모델의 source=list를 coverage dict key로 사용한 TypeError. 모델 오답과 연구 harness 오류를 구분하며 원본 run/snapshot/log는 보존한다. 실제 supervisor/runner PID 종료 확인.
- 별도 연구 에이전트가 malformed 응답을 자동 교정하지 않고 실패 관측으로 보존하도록 수정·회귀 검증 중. 운영 에이전트는 nearest→radius 오변환 및 composite 대상 누락 gate를 별도로 보완 중. 평가 에이전트는 보고서/fault 경로를 독립 감사한다. 수정 후 새 snapshot/run에서 P1 포함 전체8방법을 다시 실행해야 한다.
- 첫 paired case B3/B4/P0/H 초기plan hash 동일, B4/H review hash 동일. B2의 768토큰 소진 JSON 절단과 B1 첫문항 근거0개를 실제 제한으로 보존한다. 예산은 실행 중 변경하지 않는다. P1의 잔여 실패는 [별도 원인·수정 계획](next_reliability_fixes_20261101.md)에 기록했다.
- 후속 heartbeat `geollm-gold-v2-8` 생성: 30분 간격, 최신 인계/실제PID/원본hash/완료gate 점검. 중복 실행 금지, 변화 없는 점검은 조용히 유지, 보고서와 인계 완료 후 종료. 독립 GOLD 미수령, scientific_completion=false.
- 다음: 수정 테스트와 실제 운영 API 검증 → 운영/연구 별도 커밋 → 새 frozen v2 전체144+fault27 → 보고서·원시hash 검증. 현재 전체 비교 완료 아님.

## 2026-11-01 운영 coverage·시간초과 보완 후 GOLD v2 8방법 K1 실제 실행

- 사용자 승인으로 운영과 연구를 3에이전트로 분리. 운영7c7f9ff: 서버 hash-pinned coverage 계약 검사, UNKNOWN 최근접/완전성필수 차단, 승인hash에coverage포함, SQL단계계측. 실제 승인된 운영coverage 원천은 아직 없으므로 UNKNOWN을 꾸미지 않음. [운영검증](coverage_gate_20261101.md).
- 재현된 DB_TIMEOUT은 feature_code_verification 30,049.747ms/57014. 운영 gbhd_s101에 name/code covering index 추가; 전후56쌍hash동일, IndexOnlyScan 확인. 원천행/연구DB/timeout변경없음. API v2 3/3: 부산1m0행PARTIAL, 1km25건성공,60km차단. 관련177passed; cold-cache SLO완료 아님.
- 연구7c8fefc: 동일query/common source input/모델/snapshot, B3/B4/P0/H 공유계획 및B4/H공유검토, P0lossless, 실제read-only SQL/nativeValidator, 긴polygon stdin지원, 직접psycopg2/SQLAlchemy 공간계측, 실제raw채점/report. 주검증63passed 및 실제polygon covers0/dwithin정박지3·제한21확인. 별도통제fault9×3=27예정, 인간GOLD아님.
- **당시 시작 기록(현재 v1 중단·원본보존):** research/marine_geollm_scie/runs/20261101_gold_v2_eight_k1_v1/status.json. 부모31440; 실제PID/status와로그 대조필수. freeze 완료: outputs/scie_gold_v2_eight_snapshot_20261101_v1/snapshot_manifest.json, 6관계전체재추출hash동일,272소스동결. 현재graph→7분기126+P1새18합계144→보고서→fault27→통합보고서. 모델/운영API추가호출·동결소스편집 금지. 코드변경은새run전체재실행.
- 현재완료값은실제 status/graph/current_case.json/production_rows.jsonl/comparison/manifest.json을확인. 예상관측을완료로기록하지않음. 중복worker금지, 실패원본보존. 최종보고서는 report_with_faults/comparison_KR.md 예정(생성전없음). 이전K5/goldimmutable원본불변. 독립GOLD미수령, shadow/QLoRA보류.

## 2026-11-01 신뢰성 정책 분리·운영 빈 결과 오류 수정

- 사용자 지정 Reliability Judgment Policy를 3에이전트로 정책40사례/대표명세30개·운영감사·연구동결 검사로 분리 구현하고 주에이전트가 통합검증했다. [분리 정책](reliability_delivery_policy.md), [실제 검증·재현·남은 작업](reliability_verification_20261101.md), [논문 결과 위치](../../research/marine_geollm_scie/RESULTS_INDEX_KR.md). 30명세는 NOT_EXECUTED이며 논문 실험 결과가 아니다.
- radius/bbox의 coverage 미검증 SQL0행을 SUCCESS_EMPTY로 확정하던 오류를 PARTIAL/NO_EVIDENCE·UNKNOWN·확정count=null/observed_count=0으로 수정. 실제조회성공은 보존하고 GIS 미실행이라 하지 않는다. 실행 전 coverage gate·다른executor·시설dedup·recovery 의미보존은 미완료.
- 주검증 운영162passed/연구39passed, 감사40ID·소스hash·GOLD immutable8파일/18사례 일치. 실제SSE v2 3/3: 부산1m 관측0/PARTIAL, 1km25개정상, 60km차단. 최초v1 POINT(150 0)1km DB_TIMEOUT73.735초는 원본보존/미해결. outputs/reliability_empty_runtime_20261101_v1,v2. UI브라우저검증 아님.
- GOLD immutable manifest feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c 불변. 연구 report gate는 구현/단위검증 완료지만 실제runner연결 미완료. **새8방법모델실험 미실행**. production 변경으로 새동결전체재실행 필수; 기존 K5를 새결과로 재사용금지. 독립GOLD미수령/shadow/QLoRA보류 유지.
- 다음: 시간초과 SQL단계재현→권위coverage·정책계약/Validator gate→8방법adapter·fault/recovery동일조건연결→새frozen실행·RQ별분모/오류/지연보고. 운영UI/기존feedback변경보존. 이번 로컬커밋만 수행하며 push 요청 없음.


## 2026-11-01 GOLD v2 Oracle·동일 초기 계획·P0 무손실 컴파일

- 사용자 승인: 독도 Q3-01/Q5-01/Q5-03은 OUT_OF_COVERAGE Safe Abstention, 공간 GOLD=null이며 0건 아님. Q3-03은 추가입력/미실행. 별도 부산권 보충 문항은 원래18개와 분리한다. [검증·설계·다음 실행](../../research/marine_geollm_scie/protocol/gold_v2_oracle_and_paired_design_20261101_KR.md).
- 단일 snapshot 부산항 polygon1137770/101KR00658D00.000을 고정(법적 전체항계 주장 없음). 실제 DB2관계 COPY hash 일치, 독립 SQL/Shapely109객체 판정 일치. Q3-02 covers0, Q5-02 2km 정박지3/제한구역21. Wreck172의 실제값805개 FC연결은 부산권 진단이며 독도 GOLD로 전용하지 않는다. v1 SQLtimeout/v2 union 판정1불일치 원본보존, 단일polygon v3검산통과.
- 최신참조 benchmark/gold_v2_20261031_r2/manifest.json, 계약hash550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4. 이전 첫생성 gold_v2_20261031은 준비이력이며 r2가최신. 연구 raw outputs/gold_v2_oracle_audit_20261031_v3는소스와분리. K5/frozen_v5불변.
- B3/B4/P0/H는같은 frozen initial plan/hash; B4/H검토결과도공유. P0/H분기에lossless QEC컴파일을강제: 명시단위변환만허용, CRS/geometry/dataset누락그대로, feature/소스교정금지, Validator의슬롯변경·dataset자동선택시branch오류. 승인권한추가없음. 관련33tests passed.
- **아직8조건모델비교미실행/model_comparison_ready=false**. 다음은실제B0/B1/B2·paired reviewer/Validator/executor·P1단일polygon어댑터검증→GIS와문서SQL구분관측→v2채점통합→새동결K1전체8조건/K5. 운영SchemaBindingAdapter의자동binding이P0무손실원칙을위반하지않는지실제검증필수. 기존K5 B0도구허용을새DirectLLM으로이름만바꿔재사용금지. 독립GOLD검수미수령/QLoRA보류 유지.

## 2026-10-31 Q3-03 사용자 승인 비실행 GOLD·연구 harness 관측

- [계약·검증·범위](../../research/marine_geollm_scie/protocol/q303_execution_gold_20261031_KR.md). 별도 q303_behavior_v1: Wreck/intersects, selected_geometry REQUIRED, NEEDS_USER_INPUT/MISSING_REFERENCE_GEOMETRY, 네 실행 필드 false. 기존 frozen_v5/K5 원본·점수 불변(6 raw hash 재확인).
- 연구 model_graph_session에 요청별 Agent/도구/SQLAlchemy 실행 관측 추가. 중단/누락은 null, 실제 시도·실패 SQL은 true. 전용 worker 한정이며 직접 DBAPI/외부 GIS/자식 프로세스 계측은 미지원이다. 운영 코드·UI 변경 없음.
- 실제 네트워크 차단·무모델 그래프 진단: NEEDS_CLARIFICATION/AOI_REQUIRED, 영역 요청, 관측 완료·네 필드 false, 행동7/7. 관련31tests passed. outputs/q303_execution_audit_20261031_v1; import embedding 연결 거부는 조건상 제한으로 원본 보존. 전체 semantic GOLD 채점·모델 활성 K5 재실행 완료 아님.
- 다음: 새 동결 계약/profile/run으로 모델 활성 검증, B0–B4에도 동일 관측 정의/범위 적용 후 비교. 기존 행은 소급 false 금지. Q3-01 전체 등대 최근접/Q3-02 부산항 항계 포함은 별도 원천·중복·경계 정책 확정과 GOLD 계산 필요. 독립 검수 미수령, Qwen shadow/QLoRA 보류 유지.

## 2026-10-31 운영 Dataset 본문 연결 수정·6질의 재검증 완료

- 사용자명시 별도수정에이전트로 정보질문→문서조회→검증원문을 최종summary/answer_text에 연결했다. [수정/전후결과/한계](dataset_answer_fix_20261031.md). 기존본체답변후 근거첨부만하던 문제와 '관한'검색어로 무관문서반환을 보완. Qwen/좌표권한승격없음, 문서SELECT는ExecutionValidator만승인.
- 관련단위96passed/14.00초. 실제same6 SSE after_v3 **근거반영검사6/6**: 긍정5개 각원문3개+출처/hash/원문일치/PARTIAL, 음성문서0/Qwen인용0/BLOCKED. 준비전 after_v2 연결실패6은보존. source_unchanged_after=true. 통제3건은이동/지도복합NEEDS_CLARIFICATION,비공개BLOCKED_POLICY로 문서경로강탈없음(지도성공아님).
- 운영배포완료, 원본 outputs/dataset_live_followup_20261031_{v1,after_v2,after_v3}, controls outputs/dataset_answer_controls_20261031_v1. 소스변경후K5원본540관측/평가는불변이며 재비교시새동결run필요. 독립GOLD미수령유지.
- 잔여: 별도공간근거API 양식장/수로OperationalError, 동의어/복합표현recall, 입구국소문장선택·종합설명·자료최신성, 이동최종본문/복합지도정보결합,55원본형식/OCR/수치조류/canonical의미연결. 이들은완료로보지않는다. 다음우선은 공간조회timeout격리개선→복합산출물→원천완전성검수. 이번6질의수정/검증완료로 geollm-k5 후속점검종료.

## 2026-10-31 K5 540관측 완료·운영 종단 점검 시작

- K5 v2 20:44:50KST COMPLETED_OBSERVATIONS/DONE, baseline450/P90 전체 기대집합·원시hash·소스246·모델digest 및 P5회 warmup gate 재검증. 연구worker/proxy/부모종료 확인. [한글결과](../../research/marine_geollm_scie/protocol/k5_results_20261031_KR.md), run/report/comparison_KR.md. 독립GOLD미수령·scientific_completion=false 유지.
- P각회7기계통과/5미충족/6미측정포함, 통과여부변동0(측정12문항). Qwen50/50 HTTP200,3.237~23.038초. Baseline schema420/invalid28/error2. 전체 의미정확도/모델우열아님. 지연의 순서/계산예산/운영감사병행 교란 명시.
- 별도 HTTP500 재현2건 모두HTTP200/스키마통과(74.831/87.474초), 원인미상·원본실패불변. outputs/k5_http500_reproduction_20261031. 양식장 공간오류는 readonly SQL pgcode57014/statement_timeout3초 재현, 수로는5행1.85초 정상. 모듈 import 실패후 /app runpy로 재검증한 기록을 구분한다.
- 운영 종단6질의 runner PID26052 시작: outputs/dataset_live_followup_20261031_v1/status.json, rows.json, *_events.json, manifest.json. stdout/stderr outputs/dataset_audit_20261031/live_followup.*.log. 스크립트 outputs/dataset_audit_20261031/run_live_followup.py, 소스변경 없이 실제SSE→comparison완료대기→semantic→Qwen인용 순차. 운영 자체shadow/semanticprior 병행은 서비스현상으로 보존.
- 다음: 실제PID/로그확인(중복runner금지)→6질의완료/오류 및 최종본문에근거반영여부대조→Dataset보고서·인계갱신→자동점검종료. 실패원본보존, raw연구결과수정금지. 55파일처리미확인/OCR/수치조류/canonical의미연결미완료는 별도남은작업으로 명시한다.

## 2026-10-31 K5 baseline450 완료·P 두 번째 반복 진입

- 20:27:54 KST baseline450 원시관측 완료/exit0/완료gate 및 hash 검증 통과. completed420/invalid_response28/HTTP500 error2이며 의미정확도가 아니다. 새 stage graph_repeat_1, supervisor8920/child19884 생존 확인. P 나머지72 및 최종보고서는 아직 미완료.
- HTTP500 두 건 원인 미상 및 운영Dataset 읽기전용 감사 병행부하의 지연 교란 가능성을 postfix_execution_20261031_KR.md에 기록했다. 원본 유지/종료후 별도재현. 동결 소스·모델 검증 통과. 운영 SSE/semantic 추가호출은 K5 종료 후 진행한다.

## 2026-10-31 운영 Dataset 재감사·종단 답변 검증 대기

- 사용자 요청으로 [운영 Dataset 감사](dataset_audit_20261031.md)를 수행했다. 원본244개/고유hash229, 기존manifest와 전체hash 변경0. 운영DB 문서23,215/벡터23,215지만 profile311 포함이며 전체 원본 처리 완료가 아니다.
- 새 원본별audit: 추출32/record추출42/기존본문완전성미검증84/기존record미검증31/형식별확인55. 공간원천1,338,776행·유효geometry206,120; 정적공간3,832 제외와 CSV 무geometry를 구분한다. 그래프23,232관계 전부derivedFromSource이며 canonical 의미 관계 완료 아님.
- 실제 lexical 근거API8건:6완료/양식장·수로2PARTIAL(공간OperationalError), 본문은 positive7개 각5건/negative0. 부산항입구 상위 사고사례집의 현재 안내 관련성 미검증. 원본 outputs/dataset_audit_20261031.
- 일반SSE는 최종답변 생성 뒤 coastal_evidence를 추가하며 근거패널 검색을 본문 활용 완료로 보지 않는다. semantic도 ILIKE 필터/lexical 우선. K5 실행 중 추가모델호출/소스변경 없이 점검했으며 신규종단생성 검증은 대기.
- 다음: K5완료→운영 SSE/semantic/Qwen 인용 및 본문 대조 별도run→공간오류격리재현→55개형식/중첩archive/OCR·canonical 의미 연결 검수. automation geollm-k5에 후속을 추가했으며 운영점검까지 마친 뒤 종료. 연구독립GOLD미수령·동결조건 유지.


## 2026-10-31 K5 v2 실제 재개 — 현재 실행 기준

- **후속확인: graph_repeat_0 18/18완료, 현재 baselines_k5 RUNNING.** 초기화85/85·Qwen생성10/10 HTTP200/JSON객체, 소스불변gate통과. 첫P기계채점7통과/5실패/6미측정포함(의미정확도아님), 상태COMPLETED10/PARTIAL4/NEEDS_CLARIFICATION4. interim_graph_repeat0_audit.json 보존. baseline450과P나머지4회·최종보고서는진행대기/실행중이며완료아님. 구현·검수자료로컬커밋 a8d73e4,원격push없음.

- 최신 실행은 **research/marine_geollm_scie/runs/20261031_postfix_k5_v2/status.json**이다. 실제 supervisor8920/child34420 및 연구worker/proxy RUNNING을 확인했다. 첫stage graph_repeat_0, 이후baseline450→graph1..4→report. 아래v1 RUNNING/중단기록은이력이며현재실행과구분한다.
- v1은모델호출전 query_normalizer.py hash불일치로정상차단됐다. 별도파생생성기6tests passed 후 실제연구DB6관계를읽기전용재추출하여부모CSV와해시전부일치확인. outputs/scie_model_snapshot_20261031_execution_v1 LOADED_VERIFIED, 부모manifest불변·데이터재기준화없음·코드old/newhash lineage보존. 기존verify_files를그대로통과했다.
- 양쪽profiles_v2는새manifest경로/hash를동일참조하고246파일을동결했다. 실행중소스편집금지. v2stderr/stdout은outputs/scie_postfix_k5_v2_20261031.*.log, 전역lock과실제PID함께확인. automation geollm-k5도v2로갱신했다. 아직K5관측/보고서완료아님.
- 다음은첫graph완료gate→baseline450진행→나머지graph72→공통기계채점/반복변동성→독립검수결과별도반영. 실패원본은보존하고코드변경시다시새run을사용한다. 운영UI/feedback변경은이번커밋에서제외한다.

## 2026-10-31 공통 채점·구현 보완 완료 및 K5 반복 실행 시작

- **최신 상태 정정: K5 v1은 모델 호출 전 STOPPED_REQUIRES_REVIEW.** 기존 snapshot에 기록된 query_normalizer.py hash가 이번 수정과 달라 gate가 정상 차단했다. 원본 snapshot/run은 보존하며 동일 연구DB 데이터를 재추출·hash대조한 새 실행 snapshot과 새 profile/run을 준비 중이다. 완료 gate를 우회하거나 기존 manifest를 덮지 않는다. 아래 RUNNING은 최초시작 관측이며 현재 상태가 아니다.

- 최신 상세: research/marine_geollm_scie/protocol/postfix_execution_20261031_KR.md. P실제final_dict를공통계약에매핑했다. 사전재채점 runs/20261031_common_mapping_before_v3/report: P3통과/9실패/6미측정포함, B1 1/9/8, 나머지B군각0/10/8. 기계계약검사이며정답률아님; Q4세통과는동일공간군집.
- 구현: source-backed FC정의/속성·비정확문서RAG연결, AOI/지도범위필수계약, 복합대상/지도/설명산출물완결검사, AnchorageArea부분치환방지, 유효QEC enum. 문서발췌나0문서만으로설명COMPLETED 금지. 미지원교차실행·미완성등대설명은숨기지않는다.
- 실제영어지도복합parse251.6초(생성만의측정아님)/최종약268초문서-only완료를확인했다. 일반fallback은gemma2/SDK명시제한없음.15초/재시도0/외부await deadline과범위사전검증을추가했다. 운영prior기본llama3.1미설치404는기존Qwen shadow설정참조로보완; 연구명시Qwen고정은유지.
- 최종API runs/20261031_contract_routing_api_v4/verified_contracts.json 12/12: 실제FC·승인/미실행·정책·QEC스키마·부분완료확인. 지도복합4.062초추가입력, 전체1.250~22.344초; 전체SLO아님. v1준비전통신실패/v2지연및잘못된완료/v3설명누락모두보존.159회귀후최종관련100passed(중복합산금지). 기존사고필터오류코드2실패는HEAD에서도재현해별도P0로기록했다.
- **현재K5 RUNNING**: research/marine_geollm_scie/runs/20261031_postfix_k5_v1/status.json 및실제PID/로그를우선확인. P첫18→baseline450→P나머지72→report,총540관측. 245소스/계약/profile/snapshot동결,semanticprior180초/parser15초고정. 실행중동결파일변경/중복worker금지. 모델오류행은보존하고완료gate우회금지. 실패수정시새run사용. 아직반복결과완료아님.
- 프로세스첫관측supervisor11496/child37976, 이후변경가능. outputs/scie_repeat_active.lock과실제프로세스함께확인. stdout/stderr outputs/scie_postfix_k5_20261031.*.log. 즉시중단요청시supervisor/하위PID/연구worker·proxy모두중지하고원본보존. STOP_AFTER_STAGE는즉시중단아님.
- 독립GOLD검수자는사용자가선정했다고확인했지만결과미제공/완료0. 최신A/B/합의한글빈양식 research/marine_geollm_scie/review/20261031_independent_gold_v3. 초기양식은AI정답ID·객체별locator를제외하고원천판/경로/hash만제공한다. 합의결과는새참조버전으로재채점; 기존18은검수후에도holdout아님.
- 후속점검 automation geollm-k5 ACTIVE(30분). 상태변경없으면조용히종료,의미있는완료·실패·조치필요만알리고보고서완성후종료한다. 이전geollm삭제상태와혼동하지않는다. 운영UI/feedback사용자변경보존,이번요청원격push없음.
- 다음: 실제K5상태/gate확인→실패원인별도재현·수정또는540관측보고서→사례내/동등표현군집변동집계→독립검수결과수령후별도재채점. 잔여P0는등대다중매핑·설명완결, AOI교차도구/복합대상개별실행, 기존사고필터오류코드정합성. 독립holdout/ablation/recovery/전체SLO는미완료, Qwenshadow승격/QLoRA보류.

## 2026-10-31 사용자 재개 — Qwen timeout·정책 오류 수정 및 새 연구 검증 완료

- 아래 이전 인계의 “180초 미실행/정책 미검증”은 당시 관측이며 이 항목으로 갱신한다. 상세원인·검증·한계: research/marine_geollm_scie/protocol/timeout_policy_resolution_20261031_KR.md.
- Qwen 원인: CPU에서 stream=false 전체JSON생성에6~20초가필요하지만 semantic_prior 제한2.5초로 원본11회모두취소. 연구profile만180초로고정; 운영기본유지. 원본prompt timeout-only smoke2/2성공. 새graph는정책/FC/async수정도포함하여 단독ablation아님.
- 최종 runs/20261031_graph_timeout180_v2: graph18/18, 생성11/11 HTTP200/JSON객체(6.026~20.016초), warmup85/85성공, embedding22/22성공, 소스/profile/snapshot/registry동결검증. 상태 COMPLETED11/BLOCKED3/NEEDS_CLARIFICATION3/PARTIAL1은정답률아님. v1의warmup통신실패는보존하고 DEGRADED_WARMUP으로분리했다.
- 공개RestrictedArea코드오차단과 private_entry우회수정: parse최초정책검사, 명시비공개판별, 공개FC실제binding·출처hash·ExecutionValidator승인후29코드반환. 일반제한구역레이어명만으로차단하지않음. 실제API통합5/5 및 공개공간회귀4/4검증, 비공개선행실행없음.
- 동기cache/router/slot/retrieval을thread로분리. 최종관련76+기존계약33+proxy/embedding9=118tests passed. health연구병행10/10 HTTP200(6.78~203.73ms), 초기3초timeout1회도보존. 전체SLO검증은미완료.
- 새report는 같은snapshot의기존baseline90과새graph18을대조하며 모델/timeout/소스조건을명시한다: runs/20261031_graph_timeout180_v2/report/comparison_KR.md. P18평가매핑은미측정, 논문정답률/모델우열선언금지. 기존run불변.
- 다음실행순서/P0: 정의·속성fastpath오진입→AOI/복합대상완결계약→P공통평가매핑→새frozen run. 각원본보존/별도수정/실제API정상·부정검증. P1동시부하SLO/운영timeout예산, 독립GOLD·holdout/K5/recovery/ablation은별도. shadow후보실험은의미정확도검증전실행권한확대없음/QLoRA보류.
- 임베딩23,215/23,215(1024차원) 완료와snapshot검증은기존기록유지. 자동점검geollm은삭제상태이며 이번재실험은명시요청에따른수동실행. 운영UI/feedback등무관한변경은보존한다. 이번요청에는원격push가없다.

## 2026-10-31 K1 비교 산출물 완료·중대한 해석 제한

- 정책helper 수정15tests passed. 실제 after API5건: 공개ko OBSERVATION_TIMEOUT/RECEIVED, 공개en TRANSPORT_ERROR/TimeoutError, private_mixed/classified_en BLOCKED, private_entry NEEDS_CLARIFICATION 지속. 정책 정상화/최종답변 완료를 선언하지 않는다. 잔여우회경로·서비스지연은 별도 P0, 원본은 runs/20261031_restriction_policy_{before,after}/api_rows.jsonl. 신규추론180초조건은 아직 실행하지 않았다.
- supervisor v3 EXECUTION_COMPARISON_FINISHED/DONE,04:39:54KST. snapshot/graph18/baseline90/report 모두 exit0. 원본 research/marine_geollm_scie/runs/20261030_full_execution_v5 불변 보존. baseline90은 schema completed84/invalid_response6이며 실행·의미 정확도가 아니다.
- 보고서 report/comparison_KR.md 및 component_scores/common_output_observations/summary.csv 생성. baseline 구성요소 전체검사통과 B1만1행, 나머지0; P18행은 구조 매핑 미측정이라 0점으로 비교하면 안 된다. 전체 모델우열/논문정답률 주장 불가.
- 별도 graph감사: semantic_prior 기본2.5초 timeout 때문에 Qwen generate11회 모두 client_disconnected/timeout. 문항 embedding22회 성공과 구분. 이번 P는 정상Qwen 활용 효과의 근거가 아니다. 원본실패 포함 운영조건 결과로 보존하고 timeout 변경은 별도 연구조건/새run으로 해야 한다.
- 발견결함: 정의/속성의 공간fastpath 오진입, 제한구역 코드 설명 policy오차단, AOI없는 intersects를 문서COMPLETED, 복합 등대+Wreck 중 Wreck만 완료, AnchorageArea 부분치환. Q4세표현 11건은 정상관측. 연구snapshot 누락원천/coverage 부족은 구현오류와 구분한다.
- 비교실행 종료 후 별도 embedding_fix 에이전트에 연구timeout 조건·감사문서, validator 에이전트에 정책오차단 최소수정/정상부정검증을 맡겼다. 수정후재실험은 원본을 덮지 않는다. 나머지 결함 및 K5/독립holdout/recovery/ablation은 후속이며 본논문전체완료 아님.
- 한글 완료요약: research/marine_geollm_scie/protocol/execution_results_20261031_KR.md. 연구timeout 조건 준비18tests passed(신규추론 미실행), graph오류감사 및 별도run명령 문서화. 비교보고서 완료에 따라 매시간 automation geollm은 삭제했다. 추가실험은 자동 시작하지 않는다. 정책수정 실제API 관측은 별도 에이전트가 마무리하며 결과는 issues/restriction_policy_fix_20261031.md 확인.

## 2026-10-31 임베딩 완료·논문 K1 실제 실행 진입

- 03:32 KST 임베딩 worker 최종 검증 COMPLETED: 전체 document_chunks23,215/벡터23,215/NULL0/min=max1024/model_digest_unchanged=true. 대상 dataset_source_text6,362 청크의 미완료 해소. 기존8469벡터 생성 metadata 미확정은 별도 한계이며 소급 검증된 것이 아니다.
- supervisor v3가 새 scie_model_v3 snapshot을 생성하여 LOADED_VERIFIED. 문서23,215/벡터23,215, capability21/벡터21, 지명1146/항로표지314/섬1140/S10125300의6관계 확인. snapshot 경로 outputs/scie_model_snapshot_20261030_v3.
- graph18 원시 관측 완료(exit0,03:38KST), 상태 COMPLETED10/BLOCKED4/NEEDS_CLARIFICATION3/PARTIAL1. 이는 정답률이 아니다. runs/20261030_full_execution_v5/graph/production_rows.jsonl을 보존한다.
- 04:05 이후 확인시 BASELINES_90 실행중(로그43/90 관측), supervisor 오류없음. 결과 미완성. embedding_fix 별도 에이전트에 graph18 원인분류 읽기전용 감사를 맡겼다. 실행중 source freeze를 유지하고 수정은 비교완료 후 별도run으로 분리한다.
- 다음: baseline90 및 보고서완료 확인→실제 도구/모델/상태별 원인 검토→별도 수정/재현. 기존 K5/독립holdout/공간coverage/recovery/ablation 한계 유지. 자동점검 geollm 활성.

## 2026-10-30 세 번째 실행 — 사용자 명시 재개

- 사용자 재개 요청으로 두 번째 PAUSED_BY_USER를 해제했다. 원천DB 재조회 dataset6,362/임베딩2,612/잔여3,750, 고정Qwen/bge digest 일치, 관련6tests passed. Ollama 중지 상태에서 serve 기동, 연구DB 재기동. 기존 저장벡터 보존.
- 같은 임베딩 출력 폴더로 worker 재개, 새 supervisor 출력 outputs/scie_full_pipeline_20261030_v3를 사용한다. v1 실패/v2 중단을 덮지 않는다. snapshot DB scie_model_v3 및 snapshot/run 경로 미존재를 확인했다. 후속은 완료gate→snapshot→graph18→baseline90→report.
- 매시간 automation geollm을 ACTIVE로 복구했다. 실제 최신 progress/worker/supervisor v3 로그를 확인한다. 실패시 원인과 원본을 보존하고 별도 수정/검증하며, 사용자 중단시 worker/supervisor/automation 모두 다시 중지한다. 논문 전체 완료·독립holdout/K5/recovery/ablation 완료를 뜻하지 않는다.

## 2026-10-30 두 번째 사용자 중단 — 다음 접속 인계

- **PAUSED_BY_USER. 사용자가 다시 재개를 요청하기 전 임베딩·논문 실험을 실행하지 않는다.** 임베딩 worker 및 full_pipeline 프로세스 부재를 확인했고 매시간 후속 automation geollm도 PAUSED로 변경했다. 다른 웹/DB 서비스는 유지했다.
- 중지 후 실제 DB 재조회: dataset_source_text 총6,362 / 임베딩2,612 / 잔여3,750. 이미 commit된 청크는 보존했으며 미commit 배치는 완료에 포함하지 않는다. progress/manifest 및 supervisor v2 상태를 PAUSED_BY_USER로 갱신했다.
- HTTP400 원본과 동일입력 HTTP200 재현, 제한재시도·상태기록 수정 및6tests passed는 아래 기록을 따른다. 정확한 최초400 원인은 미상이다. supervisor v1 실패/v2 중단 산출물을 보존한다. snapshot/graph18/baseline90은 아직 시작하지 않았다.
- 재개 순서: 최신 인계/실제 프로세스/DB잔여/모델digest 확인 → 같은 임베딩 출력 경로로 NULL만 재개 → 새 supervisor v3 출력 경로 사용 → 완료/차원/digest gate → 새 snapshot→graph18→baseline90→보고서. 기존 supervisor.lock 삭제나 기존 실패 덮어쓰기 금지. 자동점검은 사용자 재개 요청 후에만 ACTIVE로 돌린다.
- 임베딩 명령: `.venv/Scripts/python.exe -u -m scripts.complete_dataset_embeddings --output outputs/dataset_embedding_completion_20261030_v1 --batch-size 8 --threads 12`
- 후속 명령: `.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.full_pipeline --execute --output outputs/scie_full_pipeline_20261030_v3 --embedding-dir outputs/dataset_embedding_completion_20261030_v1 --snapshot-dir outputs/scie_model_snapshot_20261030_v3 --run-dir research/marine_geollm_scie/runs/20261030_full_execution_v5` (경로/DB 미존재 재확인 후 사용).
- 소스 수정 및 이번 인계는 미커밋이며 기존 사용자 UI/feedback 변경과 분리한다. 현재 요청에는 GitHub 푸시가 포함되지 않는다.

## 2026-10-30 HTTP400 조사·제한 재시도 보완 후 재개

- 동일 실패8입력/모델/truncate=false 재현은 HTTP200, 8벡터/6,379토큰 성공. 원본400 상세응답 유실로 확정 원인은 미상이다. 입력길이 오류로 단정하지 않는다.
- 별도 수정 에이전트가 동일입력 최대1회 재시도(5초/digest재검증), errors.jsonl 상태/분류/입력 및 응답hash 기록, 재개RUNNING·실패FAILED 상태 갱신을 추가했다. 관련 테스트6 passed. 원문/모델/배치조건 및 기존 벡터는 보존했다.
- embedding worker를 같은 outputs/dataset_embedding_completion_20261030_v1에 재개했다. 새 supervisor는 outputs/scie_full_pipeline_20261030_v2/status.json을 사용한다. v1 실패는 보존한다. 아직 snapshot/graph/baseline 미실행이며 완료 gate 통과 후 순차 실행한다. 현재 코드 freeze 이후 관련 소스를 변경하면 새 실행 조건이 필요하다.
- 매시간 후속 점검 automation geollm 활성. 최신 v2 supervisor와 실제 worker/DB를 우선 확인한다. 다음: 재개 첫 commit→잔여0/차원/digest→새 snapshot→graph18/baseline90→오류 분석/보고서. 임베딩 일시 재시도는 논문 runtime recovery 측정과 별개다.

## 2026-10-30 임베딩 HTTP400 중단 및 후속 감시

- 사용자 재개 후1,296건 commit, dataset2,212/6,362, 잔여4,150에서 Ollama /api/embed HTTP400으로 worker가 종료했다. worker.log 실패 원본 보존. supervisor는 STOPPED_REQUIRES_REVIEW로 정상 차단했고 snapshot/graph/baseline은 시작하지 않았다.
- progress RUNNING 및 manifest PAUSED_BY_USER는 과거 표시이므로 실제 worker 생존과 혼동하지 않는다. 별도 embedding_fix 에이전트가 실패 입력/응답 원인 및 상태기록 수정을 담당한다. 원문 truncation·모델 변경·완료 gate 우회 금지. 수정 후 단위검증과 실제 실패 batch 재현을 통과한 뒤 NULL 잔여만 재개하고, 코드 freeze가 달라지면 새 supervisor 출력 폴더를 사용한다.
- 사용자 요청에 따라 매시간 이 채팅의 후속 점검(automation id: geollm)을 활성화했다. 최신 인계·실제 상태를 확인하고 의미 있는 완료/실패/사용자 조치 때 알리며, 비교 보고서 완성 후 종료한다. 중복 worker/supervisor를 띄우지 않는다.

## 2026-10-30 사용자 요청 작업 재개

- 사용자의 명시적 재개 요청으로 이전 PAUSED_BY_USER 지시를 해제했다. Docker 중지 및 오래된 Windows 소켓 접근 오류를 확인하여 run/docker-secrets-engine 소켓 폴더를 백업 이름으로 보존하고 기동했다. DB 볼륨은 변경하지 않았다. 연구 DB도 재기동했다.
- 원천 DB 재조회: 전체23,215/임베딩17,769/잔여5,446. 고정 Qwen/bge-m3 digest 일치 및 관련 테스트148 passed(32.39s). 기동 직후 DB starting up 실패는 준비 완료 후 재조회했다.
- 기존 출력 폴더의 NULL 임베딩 worker를 숨김 백그라운드로 재개했다. supervisor도 시작했으며 outputs/scie_full_pipeline_20261030_v1/status.json의 WAITING_FOR_EMBEDDINGS에서 실제 완료 검증을 기다린다. 단계 순서는 임베딩 → 새로운 scie_model_v3 snapshot → graph18 → baseline90 K1 → 보고서다. 코드/계약 변경·단계 실패 시 자동 중지하며 성공으로 우회하지 않는다.
- 재개 후 두 배치16건의 DB commit을 worker에서 확인했다. dataset 임베딩932/6,362, 잔여5,430(관측 시점). 백그라운드 실행 중이므로 이후 값은 진행 파일로 확인한다.
- 진행 상태는 outputs/dataset_embedding_completion_20261030_v1/progress.json 및 supervisor status.json을 함께 확인한다. 첫 배치 commit 전 과거 PAUSED progress는 worker 실행 여부와 구분한다. 완료 수치는 실제 배치/DB 확인 전 증가시키지 않는다. 전체 실행 비교와 논문 완료는 아직 아니다.
- 다음 점검: 신규 배치 DB commit/잔여0 → snapshot 해시/차원 → 실제 모델/도구 관측 → 오류 분류 및 별도 수정. 기존 운영 UI 변경과 연구 산출물은 분리 유지한다. K5/독립holdout/recovery/ablation·공간coverage 한계와 shadow/QLoRA 보류는 유지한다.

## 2026-10-30 사용자 요청 중단·GitHub 푸시 인계

- **PAUSED_BY_USER. 명시적인 재개 요청 전 실행을 다시 시작하지 않는다.** [중단 위치·실측·재개 명령](../../research/marine_geollm_scie/protocol/pause_20261030_KR.md)을 먼저 읽는다. 이후 사용자 요청으로 이번 준비 코드·테스트·문서를 커밋/푸시한다. 중단·커밋은 실험 완료가 아니다.
- 미완료5,622개 중 **176개 신규 임베딩 commit, 5,446개 잔여**를 실제 DB 재조회로 확인했다. 전체23,215/임베딩17,769; dataset_source_text6,362/임베딩916. 전용worker 중지·bge-m3 unload, 다른 웹/DB 서비스 유지. 로컬 progress/manifest는 PAUSED_BY_USER. 재개는 같은 폴더와 NULL 조건으로 저장 배치를 건너뛴다.
- frozen_v5 18문항 답안범위 확정(AGENT_FINALIZED_UNDER_USER_DIRECTION/독립human=false), 기존v3/v4불변. Qwen/bge digest고정·연구모델proxy·전체18 graph·B0–B4 90조건 실제도구 비교·사후보고서 및 순차supervisor 코드를 준비했다. **새 모델비교·supervisor는 실행하지 않았고 scie_model_v3도 아직 없다.** 임베딩 완료를 수동 flag로 우회하지 않는다.
- 새 snapshot은 capability_embeddings 원천21행/21벡터를 여섯 번째 관계로 포함하고 capability pgvector=true gate를 적용하도록 준비했다. 원천 존재는 확인했지만 실제 새 snapshot/graph 검증은 미수행. 기존8469벡터의 모델metadata 미확정, 공간coverage/AOI·독립holdout/K5/recovery/ablation 제한은 유지한다.
- 커밋 전 관련 단위 **148 passed (33.80s)**. 전체 임베딩·실행 비교 완료를 뜻하지 않는다. 런타임 outputs/logs와 기존 사용자 UI/feedback/place integration test 변경은 커밋에서 분리한다.
- 다음 재개: 원문 인계·Git/컨테이너/잔여COUNT 확인 → embedding worker 재개·0잔여/차원/hash 검증 → 새로운 모델 snapshot/profile → graph18 및 baseline90 K1 → 실제 산출물 검토·오류 별도 수정 → 후속K5/미노출 평가. Qwen shadow/QLoRA 정책은 변경하지 않는다.

## 2026-10-30 다음 우선 작업 — 평가계약·연구 원천 연결

- 사용자의 논문 우선 작업에 따라 [연결 결과](../../research/marine_geollm_scie/latest_binding/report_KR.md), [재현·제한](../../research/marine_geollm_scie/protocol/research_binding_v2_KR.md)을 작성했다. 운영 코드·운영 DB를 변경하지 않고 이전 연구 DB도 보존했다.
- 18개 task-obligation/capability/QEC/근거 계약과 9개 FC 정의·속성·출처 답안 후보를 만들었다. XML 2.0.0의 정의·기하·binding·다중도·허용코드·XPath/hash를 검증했다. 기존 approved_v3 18건은 불변; 새 해석은 DRAFT/미승인으로 분리한다. 초기 기하 파서 실패는 수정·검산하고 원본 실패 산출물을 보존했다.
- 별도 연구 DB `marine-scie-pilot-db/scie_binding_v2`: 문서23,215/해양지명1,146/항로표지314/섬지명1,140/부산권S-101 25,300행. 다섯 관계 원본 COPY와 적재 후 COPY의 SHA256 전부 일치. source는 REPEATABLE READ/READ ONLY. `outputs/scie_binding_snapshot_20261030_v1/snapshot_manifest.json`은 LOADED_VERIFIED, mounted graph/사전 등21파일 해시 포함. 문서 embedding17,593/미완료5,622, source ID/hash 누락0. 전체 Dataset 임베딩 완료가 아니다.
- 실제 READ ONLY probe5개에서 지명11개·Wreck 발췌3개·벡터 자기거리0·coverage를 확인했다. 원문 문서질의9개는 실제 bge-m3→연구DB에서 각3개 반환. 저장벡터 생성 profile 미확인 및 근거 적합도 미채점이며 유사도를 정확도로 해석하지 않는다. 원시 `outputs/scie_binding_probe_20261030_v1/`, `outputs/scie_binding_retrieval_20261030_v1/`.
- 새 noLLM graph6건: Q1/Q2/Q3 BLOCKED, Q4 COMPLETED11, Q5 PARTIAL0/속성설명누락, Q6 COMPLETED 문서3. relation binding은 해소됐지만 일부 경로의 임베딩 API 차단은 profile 제한이다. Q6 exact/lexical 원천 경로 성공과 구분한다. 최초 상대경로 Docker mount 실패125는 보존, launcher resolve 보완 후 `runs/20261030_binding_graph_v2_ready/` 실행0 및 snapshot 전후 불변 검증.
- 새 P0후보: selected AOI 없는 공간질의가 wreck 키워드로 document_search를 선택. P1후보: 정규화 age→재령의 부분치환이 AnchorageArea를 손상. Q6는 원문 기반 대체 경로로 성공했으므로 정규화오류를 답변 실패로 자동 집계하지 않는다. [독립 감사·재현](../../research/marine_geollm_scie/issues/research_data_binding_audit_20261030.md). 이번에는 운영 수정 대신 별도 backlog로 남겼다.
- 최종 연구 테스트 **117 passed**. preflight v2 193검사의 실제 원천/관계/로드/관측 연결은 확인했고 신규 계약 DRAFT·저장embedding profile·AOI/coverage 미확정은 NOT_READY로 유지한다. 결과는 research/marine_geollm_scie/latest_binding/에 보존하며 기존 Results/latest를 덮지 않았다.
- 다음: 새 계약/최소근거 범위 검수 → 연구 전용 embedding/model profile 고정·full graph 연결 → 위 운영결함 별도 수정·정상/부정 검증 → 필요한 공간 coverage/AOI/시설중복·경계 고정 → 실행형 baseline/full P·오류주입/recovery/ablation/미노출 평가. snapshot 새 DB가 이미 있으면 생성기가 거절하며 삭제·덮어쓰기로 재실행하지 않는다. shadow calibration UNFITTED/QLoRA DEFER 유지.

## 2026-10-30 RQ 병렬 실험·사용자 승인 v3·공간 정답 검산

- 사용자의 논문 실험 우선순위에 따라 승인/프로토콜, RQ 평가, 별도 운영 수정 에이전트로 병렬 수행했다. [최신 인계](../../research/marine_geollm_scie/protocol/rq_v2_execution_20261030_KR.md), [RQ 결과](../../research/marine_geollm_scie/results/latest/reports/final_results_summary.md), [18개 승인 현황](../../research/marine_geollm_scie/benchmark/approved_v3/승인현황_KR.md)을 먼저 확인한다. 아래 이전 DRAFT 0건 표기는 승인 이전 이력이다.
- 사용자 명시 승인에 따라 새 approved_v3 참조 18건에 human_approval=true/GOLD를 기록했다. 원본 AI DRAFT와 XLSX는 보존했다. 독립 전문가 검수 0·holdout 0이며 AI 기원과 사용자 승인 이력을 분리한다. QEC 부분 슬롯 8건, 전체 의미/근거 집합 미확정; 사용자 승인이 미확정 필드를 자동 완성하지 않는다.
- Q4는 승인받은 해양수산부 독도 동도 기준점·2022 해양지명 CSV·5000m 이하로 고정했다. 원본 1,146행을 파싱하고 Vincenty와 연구 PostGIS geography로 전 행 검산: 포함 집합 일치, 최대 거리 차이 0.000004477m. 원본 ID44–54의 11개 지명이 세 동등표현의 동일 정답이며 독립 공간 표본은 1그룹이다. 최초 파서 45행 실패 기록도 보존했다. 다른 공간 6사례는 AOI/coverage/경계 미확정이며 부산권 Wreck snapshot의 0건을 독도 정답으로 전용하지 않는다.
- 실제 격리 graph smoke 6건에서 5건은 원천/문서 binding 등의 차단, 1건은 공간 0건 완료였다. planning90행·semantic54행·fault42행·spatial18행과 서로 다른 실행 범위로 보존했다. 계획 JSON·GRAPH_RETURNED·SQL 정합성을 전체 의미/공간 정확도로 합치지 않는다. shadow calibration UNFITTED·QLoRA DEFER 정책은 그대로다.
- 실제 API에서 복합 조회의 속성 설명 누락을 COMPLETED로 반환하던 오류를 수정했다. 설명 근거가 없으면 PARTIAL이며 공간 SUCCESS_EMPTY는 별도 보존한다. 최종 정상/부정 API 7건에서 계약 상태 확인. S-101 FC 설명 생성기 자체는 아직 미구현이다. 영어 거리 뒤 기준점 추출은 실제 fast path와 공통 helper로 연결했고 전체 기준명을 exact 계약으로 전달하여 복수 기준점의 첫 지명만 실행하는 오류도 수정했다. 최종 API 8관측에서 독도/BUSAN HANG 완료, 모호·누락·미등록·범위 초과 확인 요청을 구분했다. 중간 실패 run은 삭제하지 않는다.
- 최종 연구 테스트 88 passed, JS 검수자료 테스트 2 passed, 운영 수정 단위 33 passed. Q4 원문 3질의의 수정 후 실제 API는 모두 11개 원본 ID 집합 일치, 최대 거리 오차 0.004921m 미만; 관측 전후 소스 hash 동일. 수정 전 2/3에서 수정 후 3/3으로 바뀌었지만 하나의 개발 지리조건이며 holdout/모델우열이 아니다. 최종 raw는 outputs/scie_q4_live_20261030_after_location_fix/, 채점은 outputs/scie_q4_score_20261030_after_fix/에 보존했다. runtime 원시 기록은 ignored runs/outputs에, 코드·승인 참조·요약 표/그림은 연구 디렉터리에 분리한다. 운영 코드에서 연구/GOLD import 없음.
- 다음 논문 순서: 최신 manifest·Q4 원시 기록 확인 → 남은 semantic/QEC/evidence와 공간 AOI·coverage 계약 확정 → 실행형 B3/full P/P0/P1/H와 bounded recovery/ablation → 미노출 holdout·독립 검수·K5/군집 통계. 코드 수정 후 재실행은 runtime recovery 실험이 아니다. 운영 P0 우선순위는 아래 기존 로드맵을 따른다.
- 재현: `.venv/Scripts/python.exe -m pytest research/marine_geollm_scie/tests -q`; `runners.q4_live_observation`, `runners.score_q4_observations`, `runners.rq_results`의 명령과 원시 run 위치는 최신 인계를 따른다. 기존 출력 덮어쓰기 금지.

## 2026-10-30 논문 검수자료 v2 반영

- 사용자 지정 A Dataset근거 v2/B v2/합의수정본 v2를 찾았고, 합의문 A/B SHA256·실제 파일 및 18개 원문/ID 일치를 검증했다. [반영 결과와 다음 순서](../../research/marine_geollm_scie/protocol/review_v2_integration_KR.md). 18개 모두 AI DRAFT/human_approval=false 유지, human GOLD 0. B의 요약 셀 대신 전체 필드도 보존했다.
- 완료된 B0–B4 planning run `20261030_comparison_v2b` 6문항×5방법×3반복=90행의 해시를 확인하고 v2 합의와 연결했다. 신규 모델 호출 없음. 제한된 사후 슬롯 진단에서 재검토 30출력/계획 미제공 1출력. 정확도·실행 성공률이 아니며 나머지 12문항/full P/실행형 B3/ablation/recovery는 미완료다.
- 원본 CSV 재확인: 해양지명 1,146행/독도 포함 14/정확 값 0, 부산청 항로표지 314행/등대 포함 50/독도 포함 0. 원천 coverage·geometry·spatial GOLD 승인 아님. 원본·통합 JSONL·90행 대조 보고서는 `outputs/scie_review_v2_20261030/`에 보존했다.
- 검증: 신규 XLSX 파서·원문/해시/승인 상태·누락 슬롯 진단과 기존 metrics 테스트 **13 passed**. 운영 서비스/DB/라우팅 변경 없음. Docker backend와 연구 DB 실행 상태만 확인했으며 이번 작업에서 API 재검증은 하지 않았다.
- 다음 논문 작업: v2 미확정 geometry/거리/경계/시설 중복 정책 검수 → 고정 Dataset 독립 spatial oracle·Q4 동등표현 비교 → 사전 고정 평가 기준으로 나머지 사례/holdout → 실행형 baseline/full P·ablation/recovery. 실제 운영 오류는 API 재현 후 별도 수정한다. P0 잔여·shadow calibration UNFITTED·QLoRA DEFER 유지.
- 재현: `.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.review_v2_diagnostics --input-dir outputs/scie_annotation_ai_prefill_20261030 --model-run research/marine_geollm_scie/runs/20261030_comparison_v2b --output outputs/scie_review_v2_<새이름>`; 동일 출력 덮어쓰기 금지.

## 2026-10-30 논문 실험 결과 문서 한글화

- 사용자 요청에 따라 연구 결과 요약(`latest/reports/results_summary.md`), 상세 분석·재현 방법(`protocol/pilot_findings_20261029.md`), 준비 상태(`RESULTS_READINESS.md`)를 한글로 바꿨다. 요약 생성 코드도 한글 출력으로 변경했다.
- 원시 기록·측정 수치·manifest·운영 코드는 변경하지 않았다. 31사례/114기록/GOLD 0, PILOT_ONLY 및 본실험 NOT_READY 상태를 유지한다. 오류 분류 문서는 기존 한글본을 사용한다. 다음 연구 작업과 운영 P0 우선순위는 아래 인계를 따른다.

## 2026-10-29 논문 병렬 파일럿과 독립 수정 에이전트

- 사용자 지정 `CODEX_Marine_GeoLLM_SCIE_Results_실험프레임워크_KR.md`에 따라 `research/marine_geollm_scie/`를 만들고 프로토콜·validator/Qwen·평가 에이전트를 병렬 수행했다. 운영 라우팅/QEC/Validator 소스 변경 없음. 운영 DB는 읽기 전용으로 원본을 추출하고 연구용 `marine-scie-pilot-db`에서 실제 공간조회를 수행했다.
- 최종 cohort는 DRAFT 31사례/114행: 언어 컴포넌트 18×3=54, 오류 fixture 7×3×2=42, 공간 6×3=18. 독립 전문가 GOLD 0. full P/B0–B3/완전한 B4·ablation·recovery·본실험 정확도는 **미완료**이며 현재는 PILOT_ONLY, 논문 결과 NOT_READY다. `research/marine_geollm_scie/RESULTS_READINESS.md`와 `protocol/pilot_findings_20261029.md`를 먼저 읽는다.
- Qwen1.5b reviewer는 실제 21회 요청 중 19회 응답/초기 timeout2. 정상 fixture 오차단1을 보존했다. 실제 Validator의 DRAFT 예상 일치는21/21이지만 synthetic schema 진단이므로 논문 정확도로 전용하지 않는다. 연구40초와 운영180초 timeout 정책을 혼동하지 않는다.
- S-101 원본25,300행 subset/digest/transaction 보존. 실제 radius component 정상12회(정상0건3회 포함)와 의도한 비실행6회. 정상12회 객체 집합이 독립 거리 SQL과 일치하고 실행승인 receipt 유효. 500m/0.5km 동등성 확인. 같은 원본의 SQL 정합성은 human spatial gold가 아니다. 기준점은 원본 Wreck 위 실험 좌표이며 부산항 입구라고 주장하지 않는다.
- 별도 수정 에이전트가7개 관측을 분류했다. 운영 버그는 확정되지 않았으며 host jsonschema 누락을 기존 lock 버전으로 복구했다. 관련 테스트 host27passed/2failed →29passed, 격리29passed. 연구테스트13passed. `issues/findings.json`/`issues/triage_20261029.md`에 재현/조치/향후수정 절차가 있다. 원본 실험을 덮어쓰지 않고 수정 후에는 새 run ID를 사용한다.
- `latest/reports/results_summary.md`, `latest/manifest.json`, R1–R7 CSV/MD, F1–F7 PNG/CSV와 실제 운영진단 D1을 생성했다. 미측정 정확도는 null/NOT_READY. 반복3회를 독립 통계표본으로 취급하지 않는다. 연구 raw·98MB 원본 snapshot은 ignored `runs/20261029_pilot/`에 유지하고 요약/코드/테스트/프로토콜만 커밋한다. 기존 사용자 UI/feedback/테스트 변경은 별도로 보존한다.
- 재현: `.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests -q`; `.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.finalize --run-dir research/marine_geollm_scie/runs/20261029_pilot`. 신규 추론/공간 실행 명령과 snapshot 재사용 제한은 `protocol/pilot_findings_20261029.md` 참조. Windows psycopg2 접속 UnicodeDecodeError는 원인 미확정이며 컨테이너 경로로 실험했다. host Kiwi 부족 관측은 격리 결과와 별도로 남겼다.
- 다음 논문 작업: 확정 운영오류만 독립 수정/정상·부정 API 재검증 → 입력예산 동일 B0–B3/완전한B4/full P adapter → 전문가 semantic/QEC/spatial/evidence gold 및 holdout 동결 → ablation·L1/L2/L3·bounded recovery → K5 본실험/paired 통계. 운영 P0·shadow calibration UNFITTED·QLoRA DEFER는 기존 상태를 유지한다.

## 2026-10-07 독도 부근 지명 검색 기본 반경과 위치 근거

- 사용자 요청으로 해양지명 단독 검색에 반경 미지정 시 10km 기본값을 적용하고 응답/해석/QEC provenance에 표시한다. 명시 반경은 지도 문맥보다 우선하며 0·음수·50km 초과를 기본값으로 덮지 않는다. 위험객체·복합 레이어에 대한 기존 반경 정책은 변경하지 않았다.
- `독도구근해저지명`은 지명 검색 대상과 source-backed 지명 앞부분 일치 조건에서 `독도 부근`으로 해석한다. 무조건 문자열 교정하지 않는다. 기준 지명 검색 원천에 독도가 없던 문제는 해양수산부 공개 동도 좌표와 출처를 별도 `data/public_place_anchors.json`으로 연결했다. 기존 seed_registry를 승인으로 승격하지 않는다. 이 점은 독도 전체 경계/항행 기준점이 아니다.
- 실제 API 5/5: 오타 질의 및 일반 부근 질의는 10km/11건, 명시 1km는 9건, 없는 지명과 60km는 검색 미실행·추가 확인. ExecutionValidator 승인 receipt 확인. 초기 backend 기동 중 연결종료 5건은 `outputs/nearby_names_20261007.jsonl`에 보존했고 준비 후 타임스탬프별 재검증 파일로 분리했다.
- Validator 회귀 20 passed, 신규 반경 우선순위/음수·0/제한적 오타 교정 2 passed. 실제 웹 오타 질의에서 11건 답변과 독도 지도 결과 확인, 화면 `outputs/dokdo-nearby-20261007.png`. 기존 UI의 결과 fitBounds가 이동을 수행한다. Qwen PLACE_LOOKUP 후보는 위치/출처 확인이며 그 자체가 지도 이동 권한을 의미하지 않는다. 일반 질의 전체의 조회/이동 분리 개편을 완료한 것은 아니다.
- 후속: 다른 누락 지명의 공공 원천 확장, 동명 지명·입구 등 세부 위치 해소, 0건 결과에서도 확인된 기준 위치를 표시하는 UI, 검색 한도와 전체 건수 분리. 기존 일반 P0/논문 실험/MDC 네트워크 미비는 유지한다.

## 2026-10-07 지도 분석 패널 크기 보완

- 조위 패널이 `.top-row` 안에 추가돼 지도와 가로 공간을 경쟁하던 구조를 수정하고, 해당 행 아래 별도 패널로 배치했다. 좁은 화면의 420px 고정 지도 높이를 화면 높이 기반으로 변경했다. 질의창과 지도 높이 및 질의창 내부 스크롤은 유지한다.
- 실제 브라우저에서 지도 패널 420→657px, 지도 본체 373→609px 확인. 1600×1000 반응형 점검은 지도 604×850px, 질의창 높이 850px, 조위 패널은 별도 행임을 확인했고 viewport override를 해제했다. Node JS 문법 및 diff 검사 통과. 화면 `outputs/map-layout-20261007.png`는 실행 산출물로 커밋 제외.
- 데이터·라우팅·실행 승인 정책 변경 없음. 남은 운영 P0/MDC 연결 및 논문 실험은 이전 인계를 따른다.

## 2026-10-06 논문 초안 분석과 실험 분리 제안

- 사용자 제공 `Marine_GeoLLM_SCIE_논문초안_v0.1_KR.docx`의 본문·표·수식과 현재 QEC/Validator/Evidence/benchmark/shadow 코드를 대조했다. 논문 및 운영 소스는 수정하지 않았다. 문서 렌더러는 bundled LibreOffice 미발견으로 실패해 페이지 배치 검증은 하지 않았다.
- 논문의 RQ1–RQ5는 semantic grounding, 실행 전 오류탐지, 실제 공간결과, recovery, evidence audit를 요구한다. 기존 shadow는 실행하지 않으며 기존 benchmark PASS는 기대 차단도 포함하므로 EVQSR/ESR로 전용할 수 없다. 기존 로그·AI 검토는 독립 human gold가 아니다.
- 제안(아직 구현 아님): `research/marine_geollm_paper/` 독립 runner/config/baseline/fault injection/result oracle/metrics, 별도 DB snapshot·권한·volume·결과 경로. 운영의 ExecutionValidator를 끄는 전역 옵션을 추가하지 않는다. 운영 코드 SHA를 고정한 참조 실험과 논문용 개선 구현을 구분한다.
- 우선 설계: Q1–Q6 정상·정상 빈 결과·추가 입력·원천 없음 구분, Q7 오류주입 별도 집합; 전문가 검수 및 위치/템플릿/원질의 family별 split. B0–B3/P 비교와 A3→P의 recovery 효과, A2→A3의 validator 효과를 분리한다. Evidence는 필드 존재뿐 아니라 원천 해소·주장 지지 여부를 평가한다.
- 다음 논문 작업: gold/정답 공간결과·지표 분모·baseline 입력예산 및 삭제실험 명세 고정 → 격리 환경 → 소규모 pilot → 프로토콜 동결 → 본실험/통계. 연구 제안 단계로서 새 실험값이나 완료 수치를 만들지 않았다. MDC 및 AIS/예보는 초안의 S-101 핵심 실험과 분리한다. 운영 우선순위와 shadow/QLoRA 승인 상태를 변경하지 않는다.

## 2026-10-06 MDC 접속 설정 복구·네트워크 차단 확인

- 사용자가 제공한 Oracle 접속 정보를 Git/Docker build 제외 `.env`의 `ORACLE_URL`로 저장했다. 비밀번호 특수문자는 URL 인코딩했다. `orcl`은 우선 service_name으로 설정했으며 TCP 연결 전 실패해 SID/service_name 정합성은 미검증이다. 비밀값은 소스·문서·로그에 기록하지 않는다.
- 사용자 지정 테이블: 조위관측소 `DT`, 해양관측부이 `T_WRN_TW_BUOY`. 테이블명 제공은 스키마·자료기간·단위·물때 컬럼 확인 완료를 뜻하지 않는다.
- 호스트에서 sandbox 밖 재시도를 포함해 Oracle 접속은 `DPY-6005`. 8초 TCP 점검은 호스트 결과 10035, backend 컨테이너 결과 11로 연결 미성립. 인증 이전 단계이며 비밀번호 오류나 DB 서비스명 오류로 단정하지 않는다. VPN/접근 허용 IP/서버 listener·방화벽 확인이 필요하다.
- Oracle thin 드라이버를 호스트 프로젝트 venv에 설치하고 pyproject/poetry.lock에 의존성을 추가했다. backend 이미지는 아직 재빌드하지 않았고 새 환경변수도 실행 중 컨테이너에는 미적용이다. 기존 웹 서비스는 유지한다.
- `scripts/check_mdc_connection.py`: 환경설정 로딩, 연결/호출 시간 제한, 읽기 전용 transaction, 지정 두 테이블 컬럼 및 최대 2행 조회, 오류 코드만 출력. 실패를 0행 성공으로 바꾸지 않는다. 기존 Oracle 초기화 로그도 원문 예외 대신 예외 종류만 남긴다.
- 검증: `.venv\Scripts\python.exe -m pytest tests/unit/test_mdc_connection.py -q` → 3 passed. 실제 테이블 조회·자연어 연동 성공은 미검증이며 실행 승인도 추가하지 않았다.
- 다음 첫 작업: MDC 네트워크 접근 복구 → `.venv\Scripts\python.exe -m scripts.check_mdc_connection` → 실제 컬럼/자료기간/관측소·시각·단위·기준면 확인 → 대조기/소조기 별도 테이블 또는 계산 근거 확인 → backend 재빌드/환경 적용 → QEC/ExecutionValidator 경유 LLM 조회 및 실제 API 정상·부정 검증. 실측·예측 조위는 KHOA API, 기타 과거 관측·물때는 MDC 원천 정책을 유지한다.

## 2026-10-06 MDC 연결 재탐색·데이터 소스 정책

- 사용자 지정 정책: 실측·예측 조위는 연동한 KHOA API, 기타 해양관측 과거치 및 대조기/소조기는 MDC DB를 근거로 조회한다. Qwen은 해석 보조이며 수치·물때의 사실 권위가 아니다. 자연어 연결은 아직 미완료다.
- 기존 연결은 `data/database.py`의 `ORACLE_URL`/`get_oracle_db`이며 `check_oracle.py`도 남아 있다. `scratch/results4.txt`의 2026-07-23 로그에는 `No module named 'oracledb'`로 Oracle 초기화 실패가 기록돼 있다. 과거 설정 또는 연결 시도 흔적이며 성공 증거는 아니다.
- 현재 `.env`, 프로세스 및 backend 컨테이너 환경에 Oracle/MDC 키가 없다. 이미지 `/app/.env`도 없다. `.env.example`의 전체 Git 변경 이력은 Oracle 값이 비어 있다. `D:\Hangman\GeoLLM` 복사본에도 실제 환경 파일은 없고 Oracle 기본값은 비어 있다. DBeaver 연결 목록은 gbenc PostgreSQL만 확인됐다. 비밀값은 출력·문서화하지 않았다.
- P0: 실제 MDC 접속 설정 위치 복구, Oracle 드라이버/접속 검증, 읽기 전용 테이블·컬럼 조사 미완료. 연결 완료나 대조기 조회 성공으로 표시하지 않는다. 기존 API 조위를 MDC 과거치나 대조기 정보로 대체하지 않는다.
- 다음: 과거 MDC 설정이 보관된 프로그램/파일 확인 → Oracle 읽기 전용 연결 → 관측소·시각·단위·수직기준면·물때 테이블 매핑 → registry/QEC/ExecutionValidator 경유 자연어 연결 → 실제 API에서 정상·결측·잘못된 기간 검증. 재현: `rg -n 'ORACLE_URL|get_oracle_db' data/database.py`, `rg -n 'Oracle engine' scratch/results4.txt` (접속 성공 검사가 아니라 기존 코드·실패 기록 확인).

## 2026-10-06 국립해양조사원 실측·예측 조위 API

- 사용자 제공 API/인증키로 공식 operation을 확인하고 서버 proxy 및 로컬 PostGIS 저장을 구현했다. [저장 위치·API·재현·제한](tide_observation_20261006.md). 키는 Git 제외 환경설정에만 보관한다.
- 최종 배포 API에서 인천 24건 조회·DB 저장·이력 24건 재조회, 잘못된 날짜 422 확인. 실제 웹 조회·저장과 두 스냅샷 이력 48건 확인. 실측 미제공은 예측 값으로 채우지 않는다. 현재 volume은 docker_postgis_data이다.
- 웹 별도 조위 조회·저장/이력 패널과 `serving.khoa_tide_observations`/`serving.khoa_tide_fetches`를 추가했다. 공식 API 응답 200 확인, 관련 6 tests 통과. 실제 배포 API·저장 이력 결과는 후속 검증 기록을 따른다.
- 다음: 단위·수직기준면 활용가이드 검수 → 관측소 registry/지명 매핑 → QEC를 통한 자연어 조회·지도 연결. 자동 정기 수집·만조/간조·대조기 계산은 미구현이며 기존 예보 전체를 READY로 표시하지 않는다.

## 2026-10-06 지도 portrayal 심볼 표시 통일

- 일반 GeoJSON 결과의 이모지·임의 좌표 jitter를 제거하고 반경 검색과 같은 portrayal SVG 렌더러를 사용한다. 심볼 색상 필터를 제거하고 SVG image 내부에 로컬 팔레트를 포함해 외부 CSS 미적용을 보완했다. 미해결 객체는 중립 위치 표시와 미해결 안내를 사용한다.
- Node radius UI 회귀 및 비동기 팔레트/좌표 보존/외부 asset 거부 검증 통과. 실제 웹 `부산항 3km 이내 침선을 찾아줘` 응답에서 DANGER01/WRECKS04/WRECKS05 109개 이미지 모두 로드, filter=none 확인. 화면은 `outputs/portrayal-map-20261006.png`(커밋 제외).
- 제한: 기존 Python 심볼 선택 후보를 표시하며 공식 PC 전체 실행은 아니다. 부표/등표 미해결 매핑, 선·면 portrayal, 수심 문자·안전수심 문맥 및 SVG pivot/실척 표현은 후속 검증이 필요하다. 해당 웹 질의가 `feature_search_by_area`/현재 지도 범위를 사용한 관측도 남긴다. 명시 3km 조건 정합성은 별도 P0이며 심볼 표시 성공을 검색 의미 정확도로 보지 않는다.

## 2026-10-06 웹 재기동·상태 확인

- Docker 엔진 중지 상태에서 Docker Desktop을 시작했고 기존 backend/DB가 기동했다. `/` HTTP 200, 일반 Dataset 근거 API 5/5 요청 정상(부산항 입구/해양공간관리계획/양식장/수로/없는 자료), 없는 자료 0건을 재확인했다. 이번에는 Qwen 재평가·벡터 전체 검증·브라우저 렌더링 검증을 하지 않았다.
- 실제 DB snapshot: 본문 23,215개, 임베딩 17,593개. 기존 16,853개 대비 신규 740/6,362개이며 5,622개 미완료다. 이전 진행 파일의 RUNNING은 현재 worker 생존 증거가 아니다. Docker 재기동으로 이전 detached worker는 자동 재개되지 않는다.
- 다음 작업: 신규 임베딩 worker 재개·완료 확인 → 벡터 및 실제 웹 질의 검증 → OCR/원천 완전성/수치조류 사양 → canonical 의미 관계 검수. Phase A 전체 완료, 독립 gold/calibration, QLoRA 승격은 계속 보류한다.

## 2026-10-02 Dataset 전체 원천 대조·본문/공간 연결 확대

- 종료 전 관측: 신규 임베딩 worker 재개 후 72/6,362개(6,290개 대기). 전체 완료가 아니다. 최종 API 검증과 별개로 브라우저 탭 새로고침은 CDP timeout으로 새 UI 결과 확인을 완료하지 못했다. 다음 세션에서 실제 웹 재질의 확인이 필요하다.
- 사용자 우선순위로 Dataset 전체 244개 파일의 SHA-256을 대조했다. [구현·실제 관측·재개 명령](dataset_pipeline_20261002.md). 기존 profile/partial hash/파일명 추정을 본문 완료로 보지 않는 원본별 audit를 추가했다.
- 기존 항로서지·소형선항만 8,440개는 DB에서 모두 1,024차원 임베딩 완료 확인. 이전 10월 1일의 이 항목은 해소됐다. 새 문서 32개에서 6,362개 본문을 추가 적재했으며 신규 벡터는 별도 worker 진행 중이다.
- 누락 정적 SHP 37개 member 209,952행, CSV 17개 고유 원본 1,128,824행을 추출했다. **추출 수와 최종 DB 적재 수는 구분한다.** `outputs/dataset_pipeline/finalize.log`, `spatial_loaded.json`, `live_snapshot.json`, `audit.json` 및 실제 DB를 대조한다. Windows 대용량 bind mount 읽기 병목으로 `/tmp` 사본을 사용한다.
- 원본 해시/본문/record collection을 연결하고 Dataset 근거·Qwen 인용 API를 웹 분석 아래와 SSE에 반영했다. ExecutionValidator의 read-only 승인만 사용하며 좌표·canonical/ontology 의미 관계를 자동 승인하지 않는다. CSV 좌표는 추론하지 않는다.
- 실제 `해양공간관리계획`은 적재 전 0건→적재 후 원문 5건, 해양사고심판 사례집도 검색됨. Qwen 원문 없는 설명은 일반론·길이 제한 잘림이 있었고, 근거 기반 인용과 분리 보존했다. 대량 적재 중 HTTP 500 관측 후 공간 조회 실패를 별도 PARTIAL로 격리했다. 최신 API 재검증 결과는 후속 기록을 따른다.
- P0: 신규 6,362개 임베딩 전체 완료·벡터 조회, 대량 적재 최종 행/geometry 검사, 빈 페이지 OCR 여부, 기존 본문 완전성 및 중첩 archive/바이너리·dump 검증. 수치조류의 grid/time/수치 인코딩 사양은 아직 없으며 전체 Dataset 완료가 아니다. P1: canonical 연결·원천 판 검수 및 독립 human gold. Qwen shadow/QLoRA DEFER.
- 다음 시작점: worker/DB 확인 → `dataset_pipeline snapshot`/`audit` → `check_dataset_pipeline --model`/`--semantic`. 컨테이너 restart는 worker를 중단한다. 재개 명령은 상세 문서에 있다. 런타임 산출물과 사용자/관리자 UI의 기존 미커밋 변경은 소스 커밋에서 제외한다.
- 최종 적재 확인: 정적 공간 209,952행(유효성·범위 통과 206,120, 제외 3,832), CSV 1,128,824행. 출처 그래프 23,418 노드/23,232 관계. Python 확장 31 passed, 후속 조회 실패 격리 관련 6 passed(중복), Node 5 passed. 검색 인덱스를 추가했다. 이 수치를 신규 임베딩 완료나 전체 Dataset 의미 연결 완료로 해석하지 않는다.
- 최종 재배포 API: lexical 5/5 요청 완료(0.319~5.262초), 실제 bge-m3/pgvector 5/5 완료(0.560~2.703초), HTTP 오류 0. 부산항/해양공간관리계획/양식장/수로와 없는 자료를 확인했고 negative는 문서·공간 기록 모두 0건이다. 벡터 조회는 현재 임베딩된 자료에 한정된다. 신규 6,362개 전체 벡터 완료가 아니다.

## 2026-10-01 항로서지·소형선항만 본문·공간·지식 연결

- 사용자 우선순위로 두 원천을 처리했다. [변경·검증·재개 방법](coastal_knowledge_20261001.md). PDF 30/HWP 28, PDF 1,644쪽, 본문 청크 8,440개를 추출·적재했다. 소형선항만 439건의 EPSG:5179→4326 변환·유효성을 확인했다. 전체 Dataset 완료가 아니다.
- 출처/hash/페이지·section을 유지한 지식 그래프 9,758 노드·10,327 관계. 원문 지명 언급 및 항만 원천 record 연결이며, 입구 geometry/방파제 관계를 자동 승인하지 않는다.
- 새 원문 조회 API와 웹 분석 근거, Qwen 원문 발췌 선택, 최종 SSE·저장 결과 근거 연결. ExecutionValidator는 문서 조회만 승인하며 기존 공간 clarification을 유지한다. 늦은 이전 질의 응답을 차단한다.
- Python 26 passed, Node 5 passed. 실제 원문 질의 부산항/다대포항/울릉도 각 발췌 5개, 없는 지명 0개. Qwen 자유 인용의 지명 혼합 실패를 기록하고 ID 선택 방식으로 수정해 원문 일치 인용 3개를 검증했다. 부분 벡터 검색도 실제 bge-m3/pgvector 결과 5개를 확인했다.
- **P0 미완료: 전체 8,440개 임베딩**. CPU worker는 배치별 DB 저장/재개 가능하며 `outputs/coastal_knowledge/embedding_progress.json`, worker 로그와 DB COUNT(embedding)을 반드시 대조한다. 컨테이너 재시작은 worker를 중단하므로 문서의 `--embed` 명령으로 재개한다. 문서 검색 가능과 전체 임베딩 완료를 구분한다.
- 추가 미비: 텍스트 없는 PDF 61쪽의 OCR 필요 여부, DBF 394개 기록의 잘린 필드 원천 보완, 문서 판·최신성, 동명 항만 식별, 실제 입구 geometry 및 의미 관계 검수. 상시 운영/Qwen 학습 승격은 하지 않았다. 다음 첫 작업은 worker 생존/DB 진행 확인 → 전체 임베딩 완료·벡터 검증 → 원천 품질 검수다.

## 2026-10-01 입구·근처의 해석 중심 답변

- 위치 확인 대기 응답의 첫 화면을 공간 표현 의미 → 실제 후보 관측 → 미확정 조건으로 보완했다. 입구/출구를 항만 전체·중심점으로 대체하지 않고, 근처/주변은 기준 위치와 반경/영역을 분리해 설명한다. 실제 반경 기록이 있으면 보존하고 임의 반경은 추가하지 않는다.
- 이는 표시 계층의 해석 설명이며 지형·좌표·실행 근거를 생성하거나 Qwen에 승인 권한을 주는 변경이 아니다. 검증된 좌표 원천 확보는 기존 P0로 남는다.
- 관련 Node 회귀 5 passed. 실제 웹 부산항 입구로 이동 재요청에서 상단 제목과 답변 본문이 공간 표현 해석, 후보 1개, 좌표 미확정, 미실행으로 표시됨을 확인했다.

## 2026-10-01 추가 확인 대기와 오류 표시 구분

- NEEDS_USER_INPUT을 실행 불가 오류로 표시하던 trace UI를 입력 확인 대기로 수정했다. place_navigation_action은 빠른 지명 해석 경로 선택일 뿐 실행 승인 아님을 명시한다.
- 위치 이름 추출을 좌표 확정처럼 보이게 하는 체크 표시를 제거했다. 빈 KG/RAG 필터·경로는 기록 없음으로 표시하고 검색 0건과 구분한다. 승인 권한이나 resolver 기준은 변경하지 않았다.
- Node 관련 UI 회귀 4 passed 및 inline JS 문법 확인. 실제 브라우저 부산항 입구로 이동 재요청에서 입력 확인 대기·공간쿼리 미실행·추출 위치 이름·KG/RAG 기록 없음 문구를 확인했다. 다음 P0는 아래의 검증된 기준 좌표·복합 출력·원천 연결이며 문구 수정으로 해결됐다고 보지 않는다.

## 2026-10-01 실행 상태 표시와 해석 기반 응답

- 최종 SSE에서 실행 상태 전체를 reset하던 UI와 빠른 지명 조회의 상태 누락을 수정했다. 완료 후 의도 처리, 후보 발견, 후보 확인 대기, 미승인, 미실행, 응답 완료를 유지한다. 응답 완료를 지도·보고서 도구 성공으로 표시하지 않는다.
- 질의 응답 안에 원문/정규화/규칙 순위/Qwen 원문 해석·슬롯/융합 순위/실제 실행 판단을 연결했다. 비교가 늦게 완료돼도 현재 질의만 갱신한다. 모델의 위치 표현이 원문 대상과 다르면 차이를 표시한다. 좌표 없는 외부 후보는 선택 불가와 좌표 보완 필요를 설명한다.
- Node UI 16 passed, 후속 핵심 4 passed. 브라우저에서 부산항 입구로 이동의 기존 reset 증상 재현 후, 수정본의 상태 지속 및 Qwen 완료 시 답변 갱신을 확인했다. Qwen은 부산항으로 슬롯을 축약했지만 실제 원문 부산항 입구를 유지하며 승인하지 않았다.
- 이전 중단된 최종 API 검증도 산출물로 확인: 일반 수로 품질 문서는 Standard RAG 실제 2건, 렌더링 규칙은 PARTIAL/OUTPUT_OBLIGATIONS_UNMET, 창원 정비불량 사고 59건 COMPLETED. 전체 데이터 품질/복합 분석 완성을 뜻하지 않는다.
- 남은 P0와 재현은 [100개 예제 검증](web_presets_processing_20261001.md)을 따른다. 실행 기록이 없는 legacy 전문 단계는 기록 확인 필요로 표시하며 완료를 추정하지 않는다.

## 2026-10-01 질의창 100개 검증과 단계별 응답 연결

- [실제 검증·100개 관측 표·남은 P0](web_presets_processing_20261001.md). 초기 예제 100개 SSE 완료, 수정 후 15개 모두 6단계 설명 확인. 의미 정확도 100%를 뜻하지 않는다.
- 이전 비교 근거 잔류/늦은 응답 혼입, 근거→근처 교정, 사건/예측/신항만예정지역 fast path, 주변 지명 추출, 사고 필터 Gate 안내를 수정했다. 실행 승인 권한은 ExecutionValidator로 유지한다.
- 테스트 배치 68/59/11/27/20/10 passed(중복 포함), Node 13 passed. 기존 비네트워크 graph fixture의 DB 접속 teardown 오류는 미해소이며 전체 테스트 통과를 뜻하지 않는다. 이전 사고 Gate 기대값 실패 2개도 이번 배치에서 해소했다.
- 다음 첫 P0: authoritative 위치 원천 및 복합 요청 양성 검증, 일반 문서/CSV 근거 관련성, AIS 셀 설명/S-101 portrayal의 실제 최종 산출물. 위치/원천 미비를 성공으로 우회하지 않는다. Phase A 전체 완료 및 학습 승격은 보류한다.


## 2026-10-01 사용자 우선순위 — 지명 해석과 실행 응답 연결

- [원인·변경·재현](place_query_linkage_20261001.md). Qwen은 울릉도를 추출했지만 실제 위치 원천에서 기준점을 해소하지 못했다. 해석한 지명·대상·반경을 보존하고 위치 미확인/반경 누락/검색 미실행을 답변에서 구분하도록 보완했다. 반경 누락 시 이미 확인된 위치와 출처도 유지한다.
- 대조 검색에서 DB layer_id=marine_gazetteer_mof와 registry key=marine_gazetteer의 불일치를 발견해 수정했다. 레이어 반경 tool binding도 dwithin으로 정합화했다. ExecutionValidator 권한과 Qwen shadow 정책은 유지한다.
- 관련 회귀 88 passed. 별도 기존 사고 조회 테스트 2개는 기대 오류 코드와 공통 Gate 반환 코드가 달라 실패했으며 이번 변경 대상 밖의 P0로 남긴다. 실제 API 최종 결과는 연결 보고서를 확인한다.
- 다음: 울릉도 자체의 authoritative 기준 geometry 확보 및 사용자 기준점 확인 후 재조회 검증 → 일반 문서 질의의 근거/근처 정규화·오경로 → 사고 Gate 상태 정합성. 원천 확보 전 울릉항이나 모델 좌표로 울릉도를 대체하지 않는다. Phase A 전체 완료와 QLoRA 승격은 보류한다.

## 2026-10-01 Phase A 운영 원천 및 실제 브라우저 검증

- [검증 결과·재현·미비점](phase_a_sources_ui_20261001.md). 운영 Agent 직접 호출 5/5: RAG 문서 2건, 사고 관계 5건, 미준비/fixture/미등록 시계열 차단. HTTP E2E와 구분한다. 시계열 binding에서 파일 존재·루트 경계·fixture 별칭·확장자를 검증하도록 수정했다.
- Python 관련 회귀 117 passed, Node UI 12 passed. backend 재시작 후 실제 API 승인/차단/재개 6/6 통과. 초기 들여쓰기 오류 및 UI 테스트 mock/문구 실패는 수정했으며 검증 문서에 기록했다.
- 실제 브라우저에서 Evidence 메뉴, 분석 아래 비교 영역, 미평가 점수, PARTIAL 안내, 미실행 단계 표시 및 질의창/지도 동일 높이와 내부 스크롤을 확인했다. 이전 browser helper 장애는 이번 세션에서는 해소됐다. 승인이나 human gold 변경은 하지 않았다.
- **다음 첫 P0:** `수로 측량 데이터 품질 관리 관련 근거 문서를 검색해줘`의 `근거`→`근처` 정규화 및 DATA_DISCOVERY 오경로를 조사·수정한다. 사고 데이터 중심 근거 반환을 일반 RAG 정상 답변으로 인정하지 않는다. 직접 RAG 실행 성공과 웹 의도 오류는 별개다.
- 이후 운영 원천 권한/열/Agent/슬롯 변경 검증과 실제 시계열 양성 원천 → Phase A 완료 판단 → B 실제 데이터/adapter → C/D/E/F 순서다. **Phase A 전체 완료는 보류**한다. Qwen/융합 shadow, calibration UNFITTED, QLoRA DEFER 유지.

## 2026-09-30 Phase A 후속 검증 및 일반 질의 재개 계약 보완

- [변경·검증·잔여 범위](phase_a_validation_20260930.md). 사용자 요청으로 Phase A를 재개했다. 일반 질의도 추가 입력 시 이전 계획/QEC/Agent 결과/승인을 폐기하고 revision을 올려 재계획한다. 메모리 checkpoint가 없으면 저장 snapshot을 사용하며, 모두 없으면 재개를 거절한다.
- RAG 사전 원천 검사에 실제 SQL이 사용하는 chunk_id/source_id/source_sha256을 추가했다. 누락 시 실행 전에 차단한다.
- 수정 전 관련 회귀 175 passed. 수정 후 179 passed(77 warnings), 별도 일반 재개·저장 snapshot 복원 route 테스트 2 passed(1 warning). 전체 저장소 테스트 통과나 의미 정확도를 뜻하지 않는다.
- 최신 코드로 backend 재시작 후 실제 API **6/6 통과**: 이동/정의/1km 검색 승인·완료, 반경 누락 추가 입력 요구·미승인, 60km 차단·미승인, 같은 작업에 1km 추가 입력 시 revision 2·새 승인·완료. 정적 UI 자산·검토 이력 API 확인. 원본 `outputs/web-intent-audit/20260930-phase-a-runtime-v1.jsonl`은 커밋 제외.
- 응답 시간은 20.894/40.295/15.802/32.658/41.161/68.390초였다. 계약은 통과했지만 지연 개선/SLO 충족을 뜻하지 않는다. 문법 검사 및 git diff --check 통과.
- **다음 실행 순서:** 일반 RAG·사고 관계·시계열의 실제 운영 원천별 end-to-end 및 권한/원천 변경 검증 → UI 렌더링/지도 문맥 E2E → Phase A 완료 판단 → B 실제 데이터/adapter → C 근거 품질 → D 독립 gold/holdout → E benchmark/CI/SLO → F 학습 판단. Phase A 전체 완료 선언은 보류한다.
- 아래 9월 28일 인계의 '최신 backend 미반영/전체 관련 회귀 미검증'은 이번 범위에서 해소했다. 그 외 미구현 adapter·UI·원천별 검증은 유지한다. 지도 API 연동은 아직 가능성 검토 상태다. 규칙/Qwen/융합 shadow, calibration UNFITTED, QLoRA DEFER.


## 2026-09-29 사용자 우선순위 — parser & Map_viewer 지도 API 연동 검토

- [가능성 판단·근거·연동 순서](map_viewer_api_feasibility_20260929.md): 기술적으로 가능하며 기존 Leaflet에 서버 proxy를 통한 PNG XYZ 레이어 연결을 우선 권장한다. 이번에는 구현하지 않았다.
- 내부 지도 API 3000 health는 DB/projection 정상, FC/PC 2.0.0. 공개 지도 API 3002는 연결 거부, GeoLLM 8000은 전송 오류로 정상 확인 불가. Stage 0~4 로컬 manifest complete=true는 확인했지만 전체 파일/화면/공개 API ready 검증은 아니다. Stage 5/6 완성으로 해석하지 않는다.
- 다음 연동 순서: 서비스 상태/이용권/대표 타일 확인 → 키를 서버에 두는 고정 경로 proxy → Leaflet XYZ 및 줌/좌표 정합성 → 클릭/객체 API·원천 ID/판 매핑. 공개 API는 타일만 제공하므로 객체 근거 연동은 추가 adapter가 필요하다.
- Phase A 전체 회귀와 최신 API 재검증은 여전히 미완료이며 아래 인계에 남는다. 규칙/Qwen/융합은 shadow, calibration UNFITTED, QLoRA DEFER다. 자동 서비스 시작·키 발급·연동 코드 변경은 하지 않았다.


## 2026-09-28 최종 인계 — 사용자 요청으로 Phase A 작업 중단·커밋·푸시

- **다음 세션은 이 절과 문서 전체를 먼저 읽는다. Phase A 완료 선언은 보류한다.** 아래 이전 기록은 당시 검증 범위이며 최신 변경 전체의 통과를 의미하지 않는다.
- 추가 구현: registry 10개 항목에 실행/조사/미지원 계약을 명시하고, 공통 Agent 진입 gate를 dispatch 및 직접 호출에 적용했다. 요청 ID·질의·Agent·권한·operation·원천 binding을 다시 검증한다. QEC 누락/재사용은 차단하고 슬롯 수정은 승인을 무효화한다.
- Standard RAG는 문서 relation/SELECT/필수 열과 embedding profile을 확인한다. Data Discovery는 본문 CSV fetch를 제거한 metadata 전용 조사 계약, Validation은 부모 실행 QEC를 승인하지 않는 별도 조사 계약을 쓴다. AIS/Drone의 미완성 실행 adapter와 미구현 Map Agent는 BLOCKED_CONFIG로 남는다. 이는 기능 완성이 아니다.
- 레거시 DSL 거리 제한을 공통 50km로 맞췄고 최근접 검색 기본 결과 수는 1이다. 화면의 실행 가능 표시는 단순 READY/boolean이 아니라 validator 기록을 확인한다. 사람의 결과 검토 승인 후에는 보고서로 진행하며 실행 승인으로 승격하지 않는다.
- 검증 기록: 최초 진입 gate 회귀 43 passed / 7 failed(변경된 상태명·QEC fixture), 이를 보완했다. 확장 회귀는 170 passed / 2 failed였으며 실행 중 수정 전 사고 Agent fixture를 로드한 결과다. 수정한 사고 Agent 및 신규 계약 테스트의 별도 재검증 결과는 아래 최종 검증 기록을 따른다. 겹치는 수치는 합산하지 않는다.
- 현재 API 5/5 통과 기록(v2)은 **이번 전체 Agent gate 추가 이전 버전**이다. 최신 변경의 컨테이너 재시작과 실제 API 재검증은 중단 요청에 따라 다음 작업으로 남긴다. 현재 실행 중 프로세스와 디스크 소스가 다를 수 있다. UI 브라우저 렌더링도 미검증이다.
- 최종 제한 회귀: `docker exec geollm_backend python -m pytest tests/unit/test_accident_risk_agent.py tests/unit/test_agent_execution_contracts.py -q --disable-warnings --maxfail=2` → **27 passed, 39 warnings (31.37s)**. 사고 Agent의 2개 실패는 수정 후 통과했다. 확장 172개 전체를 최종 소스로 다시 돌린 결과는 아직 없다. `git diff --check` 및 staged 형식 검사는 통과했다.

### 다음 실행 순서 / 재현

1. **P0 / Phase A 마무리**: 변경 파일과 컨테이너 버전 확인 → 최신 회귀 전체 재실행 → backend 재시작 → 정상/부정 실제 API 검증. `docker exec geollm_backend python -m pytest tests/unit/test_agent_execution_contracts.py tests/unit/test_execution_dispatch_gate.py tests/unit/test_execution_validator.py tests/unit/test_spatial_agent.py tests/unit/test_standard_rag.py tests/unit/test_accident_risk_agent.py tests/unit/test_data_discovery.py tests/unit/test_execution_authority.py tests/unit/test_execution_gate_regressions.py tests/unit/test_radius_stream_contract.py tests/unit/test_uport_execution.py -q`. API: `python -m scripts.check_execution_authority_runtime --output outputs/web-intent-audit/<새 파일>.jsonl`(기존 파일 덮어쓰기 금지).
2. 일반 RAG·사고 관계·시계열 직접 호출 및 수정/재개 계약을 실제 서비스에서 추가 검증한다. 원천 권한 변경, Agent 변경, 슬롯 변경 시 실행 전 차단을 확인한다. RAG SQL 전체 필수 열과 검증 열 목록의 일치도 후속 감사한다. 테스트 결과와 실제 실행 결과를 분리한다.
3. 브라우저에서 Evidence 메뉴·분석 아래 비교 근거·지도와 질의창 높이·긴 대화 내부 스크롤을 확인한다. Windows browser sandbox helper 실패로 남은 E2E다.
4. **Phase B**: AIS/V-PASS·수치조류·바다갈라짐·Observation 원천/기간/커버리지 및 실행 adapter. Data Discovery의 기존 예시 catalog 항목을 실제 원천으로 검증/교체한다. metadata 발견을 실제 데이터 검증으로 취급하지 않는다.
5. C KG/인용/lineage/S-101 portrayal → D 사람 승인 3→30→300+ 및 hard negative/대화/복합/실패/holdout → E strict benchmark/CI/CD/SLO/monitoring → F FastPath·retriever 학습 검토. Planner QLoRA는 조건 충족 후 판단한다.
6. **P1 shadow 실험**: 규칙/Qwen/융합은 동일 후보 비교 전용, 실행 권한 없음. calibration UNFITTED, human gold 미승인, QLoRA DEFER. 동점/후보 구분력/추가 확인 오류와 CPU 지연을 독립 gold로 평가한다.

- 공유 작업 보존: 별도 관리자 UI script 및 index의 해당 script 태그/관리자 인계 절, 런타임 피드백 JSONL은 이 커밋에서 제외한다. 자동 생성 출력과 로그도 제외한다. GitHub 푸시 후에도 이 파일들 때문에 작업 트리가 dirty일 수 있다.

## 2026-09-28 실행 권한 단일화 1차 및 Evidence 검토 메뉴

- 사용자 우선순위인 Phase A부터 진행했다. RoutePlanner의 자체 승인을 제거하고 지도 이동·정의·legacy 조회·반경/영역/최근접/레이어·통항·UPort의 승인 부여를 ExecutionValidator로 모았다. 입력/binding hash가 바뀌거나 READY 플래그만 있는 QEC는 승인으로 취급하지 않는다. [변경 범위·검증·A–F 순서](execution_authority_and_review_20260928.md).
- P0 기본 반경 불일치를 수정했다. 위험객체 3km·사고 10km의 암묵 기본값을 제거하고 명시 반경/지도 영역을 요구한다. 반경 상한은 공통 50km다.
- Evidence 검토·승인은 주요 메뉴로 이동했다. 분석 결과 아래의 접이식 비교 근거와 별도로, 검토 화면에서 저장된 최근 30개 요청의 원문→실제 정규화→규칙/Qwen/융합 순위→실행 검증/차단 사유를 확인한다. Evidence 승인과 human gold/실행 권한은 분리한다. 질의창은 지도와 같은 높이, 내역 내부 스크롤, 하단 입력 고정으로 변경했다.
- 단위 검증: 110 passed 및 관련 그래프 회귀 134 passed; 정책 수정 후 최종 반경/통항/승인 회귀 93 passed. 중복 포함이므로 합산하지 않는다. 첫 실제 API 검증에서 30초 관측 타임아웃 3건이 발생했고 원본 v1을 보존했다. 180초 제한 재검증 v2는 **5/5 통과**: 지도 이동·정의·1km 검색은 COMPLETED와 validator 승인 기록, 반경 누락은 NEEDS_CLARIFICATION, 60km는 BLOCKED. UI 자산·검토 이력 API 응답도 확인했다. 원본 `outputs/web-intent-audit/20260928-execution-authority-v2.jsonl`.
- 브라우저 자동화는 Windows sandbox helper 초기화 오류로 시작하지 못했다. 메뉴 클릭·스크롤의 실제 렌더링은 미검증이다. 관리자 메뉴는 별도 공유 작업의 변경을 보존한다.
- 다음 실행 순서: Phase A의 일반 Standard RAG/보조 Agent registry 진입점 전체 QEC 감사와 legacy 재개 계약 → B 실제 원천/커버리지 → C KG/인용/lineage/공식 portrayal → D 사람 승인 자료·hard negative·대화/복합/실패 → E benchmark/CI/SLO/monitoring → F 학습 여부 판단. **모든 Agent QEC 완료로 선언하지 않는다.** Qwen/융합은 shadow, calibration UNFITTED, human gold 미승인, QLoRA DEFER다.

## 2026-09-28 웹 요청의 실제 규칙/Qwen/융합 비교와 지도 이동 허용

- 사용자 지정 우선순위에 따라 웹 SSE 요청(빠른 지명 이동 포함)마다 실제 Qwen 후보 점수 비교를 실행하도록 연결했다. 단일 worker/대기열과 별도 comparison_id를 사용하며, 웹에서 규칙·Qwen·동일 가중치 융합 순위, 원문 슬롯, 모델 해석과 실제 실행 판단을 확인한다. [설계·실패 기록·최종 재현](live_web_intent_comparison_20260928.md).
- 같은 후보를 평가하고 규칙 기준선의 legacy Ollama 호출을 제외했다. prompt/model digest/registry/source hash, 실제 입력·출력·지연, 실행 관측을 SQLite에 기록한다. 모델과 융합은 shadow 전용이며 실행 권한은 없다. gold=null, calibration=UNFITTED, QLoRA DEFER다.
- `해운대구로 이동`은 단일 행정지명 정확 일치·유효 좌표·출처·명시적 이동 조건에서 map_view_only로 허용한다. 분석 권위/registry 승격은 false이며 일반 위치 resolver의 분석 승인 정책은 유지한다. 복합/분석/제외 조건과 모호한 후보는 자동 허용하지 않는다. 지명 마커를 선석으로 오표시하거나 좌표를 임의 이동시키지 않는다.
- 최종 관련 회귀 **114 passed**. 실제 API 비교 **2/2 계약 통과**: 이동 COMPLETED, 주변 위험객체 NEEDS_CLARIFICATION; 둘 다 Qwen 호출과 세 순위 기록 완료. 원본 `outputs/web-intent-audit/20260928-live-comparison-v4/`, 운영 기록 `geollm_results/web_intent_comparison.sqlite3`. 브라우저 도구는 Windows sandbox helper 오류로 시작되지 않아 실제 클릭/렌더링 E2E는 미검증이다.
- P1 제한: Qwen 3.5 4B는 CPU 100% 환경에서 원본/압축 요청 모두 180초 timeout. 웹 기본값을 설치된 Qwen 2.5 1.5B로 조정했다. 1.5B 최초 응답의 문자열 null·후보 중복/누락은 검증에서 거절했고 원문 enum/후보 필수 점수 스키마로 보완했다. 실패 원본은 v1–v3 및 DB에 남겼다.
- 최종 1.5B 비교 지연은 약 63초/59초다. 위험객체 요청에 모든 후보를 1점으로 평가하고 추가 확인 불필요라고 판단한 한계가 남는다. 실제 실행은 이 판단을 따르지 않는다. 웹은 상위 동점을 명시하며, 단순 순위 일치나 구조 검증 통과를 정확도로 취급하지 않는다.
- 다음 실행 순서: 실제 웹 추가 사례를 필수 작업/슬롯/금지 대체 결과 기준으로 human gold 검수 → 후보 구분력·추가 확인 판단 오류 및 4B 지연 분석 → 독립 holdout/calibration. P0의 사건/VTS/예측/신항만예정지역 오해석과 기본 반경 정책 불일치는 아직 미해결이며, 기존 우선순위로 이어간다. 피드백 JSONL과 런타임 출력은 소스 커밋에서 제외한다.

## 2026-09-28 사용자 우선순위: 웹 질의의 의도 오류와 실행 미지원 분리

- 사용자는 한국어 의도/슬롯과 Qwen(Ollama 실행)·규칙 융합 비교 흐름을 우선한다고 재확인했다. 이번에는 모델 비교 이전에 현재 웹 서비스의 해석 오류와 실행 미지원/원천 부족을 분리했다. [검수 보고서와 재현](web_intent_execution_audit_20260928.md).
- 실제 웹 샘플 100개를 같은 SSE API로 순차 실행했다. 완료 이벤트 100/100, 관측 오류 0, COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8. Browser 도구는 두 차례 Transport closed여서 클릭·지도·렌더링은 미검증이다. 기본 실험은 지도/대화 문맥 없이 수행했으며 상태 분포는 정확도가 아니다.
- 근거 기반 AI 검토에서 37(사건→지명), 51(바다갈라짐 시간→반경), 52(예측→지명), 56(VTS 축약→지명), 72/73(신항만예정지역→항만 기준점)의 의도/작업 해석 오류 6건을 확인했다. 전체 오류가 6건뿐이라는 의미나 human gold가 아니다. 대조 401은 사건을 사고로 바꾸면 실제 59건을 조회했다.
- 선택 객체 API 5/5, 속성/부정/복합 API 10/10 계약 통과. 객체 조회는 실행되지만 공식 portrayal은 PARTIAL, 부정/복합은 명시적 NOT_RUN이다. 31/32는 요청 월 미적재이며 대조 404의 최신 적재 월 AIS는 실제 2023-12 집계 6,847,473건을 반환해 의도 오류/연산 미지원과 구분했다.
- 새 P0: 72/73의 잘못된 COMPLETED와 S-101 위험객체 기본 반경 정책 불일치. 실제 DB geometry만 준 대조 402는 명시 반경 없이 3km/140건, 대조 403은 명시 1km/49건이다. `s101_radius_execution.parse_distance()`의 기본값이며 기존 문서의 근거 없는 반경 제거 완료 주장과 일치하지 않는다. API가 기본값을 고지한다는 점과 정책 정합성 문제를 함께 기록한다. 운영 수정은 이번 평가에 포함하지 않았다.
- 다음: 위 오류/대조쌍을 필수 작업·슬롯·금지 대체 결과 단위로 사람 검수 → fast path 후보 누락과 S3 완료 판정/반경 정책 정리 → 동일 후보 Qwen S4 원문 선택·지연 smoke → 전체 규칙/Qwen/융합 비교 → 독립 gold/calibration. 실행 미지원·원천 부족을 Qwen 의도 오류로 자동 집계하지 않는다. 신규 Qwen 추론/승격은 없고 QLoRA DEFER다.
- 원본은 `outputs/web-intent-audit/20260928-v1/`, `20260928-selected-feature.jsonl`, `20260928-marine-mapping.jsonl`, `20260928-probes.jsonl`에 분리했다. 4개 대조 질의 재현 스크립트는 `scripts/check_web_intent_disambiguation.py`다. 기존 사용자 피드백 JSONL은 소스 커밋에서 제외한다.

## 2026-09-28 다음 단계 점검

- 관련 공통 실행 계약 단위 테스트는 컨테이너에서 62 passed, 경고 1건으로 재확인했다.
- `python scripts/check_web_db_connection.py`는 9/11 통과했다. 웹 페이지·health는 200이나 부산/인천 선석 API가 모두 503이었다. 컨테이너 실행 상태만으로 원천 정상 여부를 판단하지 않는다. 이전 11/11은 과거 검증 결과다.
- 다음 최우선은 위 스크립트로 재현되는 선석 조회 503의 원천 연결/조회 경로 진단과 정상화 확인이다. 이후 사고·통항 경로의 공통 계획/실행/근거 계약 감사 → 공식 portrayal 규칙 trace → 전체 처리 lineage → 복합/부정 조건 실제 실행 순서를 유지한다.
- 이번 점검은 신규 Ollama 추론·calibration을 수행하지 않았다. 독립 human gold/holdout 및 지연 검증 전 shadow 실행 권한 승격과 QLoRA는 보류한다.
- 항행 API 회귀는 최종 7/7 통과했다. 부산 선석 API는 별도 재시도에서 실제 FeatureCollection을 반환했다. 최초 503 원인은 미확정이며 지속 장애로 단정하지 않는다. 전체 웹·DB 재검사와 병행 부하 안정성 검증은 남았다. 전체 저장소 테스트와 브라우저 E2E는 이번 점검 범위가 아니다.

## 2026-09-26 공통 오케스트레이터 계약을 속성 검색으로 확대

- [상세 설계·검증·재현 문서](orchestration_execution_contracts_20260926.md)를 추가했다. 사용자 최우선인 후보/문맥 → 계획 → QEC → 실행 검증 → 근거 연결을 S-101 속성 검색에 확장했다. 일반 semantic router/ContextResolver 전체 개편은 아니다.
- `source_attribute_search` operation을 등록하고 RoutePlanner, typed QueryExecutionContext, SchemaBindingAdapter, execution validator, EvidenceBuilder를 사용한다. 원문에서 다시 해석한 매핑과 Feature/속성 조건/registry·FC hash가 일치해야 실행한다.
- 계획 hash, SQL hash, 결과 hash와 query_execution_id를 남기며 슬롯·실행·공간 근거를 같은 실행으로 연결한다. 검증 준비 상태와 실제 실행 성공/실패를 분리하고 DB 장애를 0건 조회로 대체하지 않는다.
- 관련 단위 **62 passed**, 실제 속성 API **10/10**, 선택 객체 API **5/5**, 웹·DB **11/11** 통과. 원본: `outputs/marine-mapping/orchestration-v1.jsonl`, `outputs/selected-feature/orchestration-v1.jsonl`. 의미 정확도·브라우저 E2E·전체 테스트 통과를 의미하지 않는다.
- 마지막 항행 실제 회귀도 **7/7** 통과했다. 통항 분석 PARTIAL, 위치 부족 clarification, 정의 COMPLETED 상태를 유지한다.
- P1 shadow는 신규 모델 추론/승격 없이 유지하며 QLoRA DEFER다. 다음 P0는 사고·통항 등 다른 실행 경로의 동일 계약 감사 → 실제 portrayal 규칙 근거 → 처리 lineage·복합/부정 작업 실행이다.
- 사용자가 요청한 GitHub push에는 앞선 로컬 커밋 `da09b99`, `f845a96`과 이번 코드·테스트·registry·상세 문서를 함께 포함한다. 사용자 피드백 JSONL 및 outputs 실행 원본은 제외한다.

## 2026-09-26 사용자 우선순위: 공통 오케스트레이터와 선택 객체 근거

- 사용자 지정 최우선 축은 semantic router, context resolver, QueryExecutionContext, route planner, execution validator, Evidence builder의 연결이다. 개별 기능을 추가할 때 후보 해석 → 문맥/슬롯 → 계획 → 입력·원천 검증 → 실제 실행 → 근거 → 완료 판정의 일관성을 먼저 검증한다.
- 선택 객체 요청을 기존 후보/semantic slot 해석 뒤 `selected_feature_lookup` 계획으로 연결했다. RoutePlanner registry, typed QueryExecutionContext, SchemaBindingAdapter의 실제 원천 컬럼·SELECT 권한 확인, 공통 execution validator, EvidenceBuilder를 사용한다. 명시 선택 ID·원천은 request 문맥에서 해소하며 일반 ContextResolver/semantic router 전체를 개편한 것은 아니다.
- 선택 객체의 client 속성 대신 `projection.s101_feature_valid`에서 유일한 ID를 조회한다. 원천·ID 누락/오류, 미존재/중복, 원천 장애는 완료되지 않는다. 계획 hash, 실행 ID, 조회 행 hash와 EvidenceBundle 연결을 기록한다. 행 hash는 조회 시점 결과 식별자이며 원천 파일 전체 lineage가 아니다.
- 기존 Python portrayal 선택은 `CANDIDATE_NOT_VERIFIED`, `official_rule_executed=false`로 구분한다. 공식 PC 규칙 실행 trace가 없어 심볼 연결 요청은 PARTIAL/OUTPUT_OBLIGATIONS_UNMET를 유지한다. portrayal 완료를 위해 필요한 공식 rule/symbol binding은 여전히 P0다.
- 초기 직접 조회 버전은 실제 API 5/5 (`outputs/selected-feature/resume-v1.jsonl`), 초기 모듈 단위 9개 통과. 공통 오케스트레이터 연결 이후 최종 검증은 아래 후속 결과로 구분한다. 첫 관련 테스트 실행은 backend 재시작으로 중단되어 통과 집계에 포함하지 않는다.
- 공통 연결 후 선택 객체/완료 계약 **29 passed**, 선택 객체·execution validator·EvidenceBuilder 최종 회귀 **31 passed**(일부 중복). 실제 API `resume-v2.jsonl` **5/5**로 QEC readiness, 실행 ID와 근거 ID 일치까지 확인했다. 최초 공통 검증 회귀는 20 passed/1 failed였으며 바다갈라짐 미적재 테스트가 운영 executable registry에 의존한 fixture 문제를 수정했다. 운영 바다갈라짐 상태는 변경하지 않았다.
- 선택 객체 처리 flag 초기화까지 포함한 최종 코드 재기동 후 `outputs/selected-feature/resume-v3.jsonl` **5/5** 재확인. 정상 객체·portrayal 부분 완료·선택 없음·잘못된 원천·잘못된 ID를 검사했다. 브라우저 클릭과 전체 서비스 의미 정확도는 미측정이다.
- Qwen은 모델, Ollama는 실행 프로그램이다. 현재 융합 대상은 규칙/슬롯/registry와 모델 후보 평가이며 Qwen·Ollama 두 모델의 앙상블이 아니다. 신규 모델 추론·승격은 이번 작업에 포함하지 않는다.
- 다음: 공통 오케스트레이터의 계획/실행/근거 계약 회귀 확대 → 실제 portrayal 규칙 실행 근거 → 처리 lineage 및 복합 요구. 독립 gold/calibration, 일반 문맥 해소의 정확도·지연 검증과 QLoRA DEFER 조건은 유지한다.

## 2026-09-26 재개: S-101 속성 검색과 입력 계약 검증

- 기존 미커밋 FC 참조 파서·매핑 registry·속성 검색 구현을 이어 검증했다. 잠제/수중방파제는 `ShorelineConstruction`의 `categoryOfShorelineConstruction=1 AND waterLevelEffect=3`으로 제한된 검색이다. 누락 속성은 제외하며 전체 실세계 잠제의 완전한 매핑이나 human gold 승인을 의미하지 않는다. 물양장·예선·선유장의 미해결 매핑은 실행을 차단한다.
- 실제 API 초기 `outputs/marine-mapping/resume-v1.jsonl`은 **7/8**이었다. `잠제를 찾아줘`가 장소 이동 단축 경로로 들어가 지도 기준점 확인만으로 COMPLETED를 반환했다. 등록된 원문 용어의 실행 요청은 정식 매핑/슬롯 검사로 보내도록 수정했고 최종 반경 누락 결과는 `NEEDS_CLARIFICATION/RADIUS_REQUIRED`다.
- 속성 검색 실행 함수에서 지도 `exclusions` 및 불일치/복수 `target_features`를 검사하도록 보강했다. 직접 호출에서도 질의 부정 조건을 검사한다. 부정·복합 실행 지원을 완료한 것은 아니며 미지원 조건은 `NOT_RUN`으로 차단한다.
- 최종 실제 API **10/10** 계약 통과: `outputs/marine-mapping/resume-v2.jsonl`. DB의 실제 잠제 조건 객체에서 평가 기준점을 얻고 조회 행의 두 속성, execution ID, 미해결/부정/복합/반경 누락 응답을 확인했다. 의미 정확도나 F1 측정은 아니다.
- 컨테이너 최종 관련 단위 **102 passed**, shadow 계약·평가 **25 passed**. 앞선 graph 포함 회귀 **98 passed**는 일부 중복이며 최종 fast-path 수정 이전 결과다. 호스트 Python은 `structlog` 부재로 수집 실패했다. 재시작 직후 웹/항행 점검은 연결 거부로 실패했고 준비 완료 후 웹·DB **11/11** 통과했다. 전체 저장소 테스트/브라우저 조작 검증을 의미하지 않는다.
- 준비 완료 후 `check_navigation_runtime.py`도 **7/7** 통과했다. 부산/인천 통항 결과는 PARTIAL을 유지하며 위치 없음·먼 위치·미등록 항만과 정의 질의를 함께 확인했다.
- P1: 기존 원문 선택 schema 및 동일 실험 설정 검사 변경을 보존·회귀 검증했다. 신규 Ollama 추론이나 calibration을 수행하지 않았고 `used_for_execution=false`, QLoRA DEFER를 유지한다.
- 다음 P0: portrayal/선택 객체의 실제 근거 산출물 → 전체 처리 lineage → 복합 작업·부정 조건의 실제 실행 지원. 매핑의 의미 범위와 원문 판/human 검수, API 병행 부하 지연 및 readiness 대기는 남은 제한이다. 사용자 피드백 JSONL과 outputs 원본은 소스 커밋에서 제외한다.

## 2026-09-26 해수부 순화어 런타임 연결과 직접 근거 조회

- [구현·검증 문서](mof_terminology_runtime_20260926.md): 기존 4개 순화어 후보를 원문/hash/페이지를 포함한 보조 registry로 만들고 실제 질의 분석·슬롯 trace·검수 양식에 연결했다. 같은 번호 표 행 안에서만 관계를 추출하도록 다음 행 오연결 문제도 수정했다.
- 원문과 선택적 띄어쓰기를 보존하고 접두부·동음이의어·다중어 제외·인용을 구분한다. 미검수 순화어 관계로 Feature/KG/tool 입력을 자동 확정하지 않는다. 매핑 미해결 및 관련 capability 입력 계약을 trace에 남긴다.
- `잠제의 순화어는?`은 기존 일반 경로에서 30.204초 관측 timeout이 발생했다. 명시적 단일 순화어 질문을 원문 registry 직접 조회로 수정했다. 최종 실제 응답은 `terminology_relation_lookup`, 원문 인용·페이지·hash, LLM 미사용이며 1.012초였다. 일반 정의/복합 실행 질문을 이 경로로 대체하지 않는다.
- 관련 단위 45개와 별도 한국어/평가 회귀 48개, 합계 93개 통과. 실제 API `live-mof-terminology-v3.jsonl` 13/13 계약 통과. 초기 readiness 실패와 v2 12/13 결과를 기록했고 대기 시간 설정 및 readiness 별도 기록을 추가했다. 의미 정확도/F1을 측정한 결과는 아니다.
- 다음: 순화어의 의미 범위와 FC/DCEG 객체·속성 관계 검수 및 사전 확대 → 승인된 매핑의 실제 검색·도구 반영 → 독립 gold → Qwen 원문 선택·지연 개선과 동일 입력 비교. 이번에는 신규 Qwen 추론을 하지 않았고 shadow/QLoRA 승격은 보류한다. P0 portrayal·복합/부정 조건 실제 실행도 남아 있다.

## 2026-09-26 해양 근거 색인·공통 정규화 사전·혼합 평가 연결

- [후속 보고서](reference_linkage_and_mixed_evaluation_20260926.md): MOF 원문 12개 및 S-101 FC/DCEG의 6,090개 근거 단위에 원천·텍스트 hash와 페이지/문단/코드 locator를 부여했다. fonttools 평가용 설치로 PDF 경고 340개 단위를 해소했으며 빈 텍스트 22개·제어문자 4개와 판 보류 50쪽을 구분한다.
- query 원문을 유지하며 Kiwi와 semantic binding의 기존 해양/S-101 사전을 통합했다. 정박지→AnchorageArea→기존 KG seed 누락을 실제 API에서 수정 확인했다. 후보 다중성·제외 조건·미존재 Feature 필터는 유지한다.
- MOF 순화어 4개는 원문 구간과 연결된 AI_REVIEW_REQUIRED 후보다. 새 전체 ontology 구축이나 운영 query 자동 치환 완료가 아니다. 검수 양식 100개 중 18개에 근거 후보를 연결했고 gold 참조의 hash/locator/인용/판/검수 상태를 검사하도록 했다.
- 기존 1.5B/4B 동일 10문항 응답을 규칙/Qwen/혼합으로 재평가했다. 입력·문항·prompt·추론 설정 일치를 강제하며 실패를 제외하지 않는다. 독립 human gold와 calibration이 없어 의미 accuracy/F1은 null, 혼합 슬롯/계획 점수도 아직 null이다. 신규 Qwen 호출은 없었다.
- 최종 근거·혼합·사전 단위 테스트 22개와 별도 Kiwi 활성 테스트 1개가 통과했다. API 최초 readiness 실패 0/8을 보존하고 대기 기능을 추가했다. 준비 완료 뒤 실제 API 최종 9/9 통과(침선 실제 도구 실행 및 부정 사례 포함).
- 다음: 현행 법령/지침 최종본 검증 → MOF 용어·관계 검수와 승인된 정규화 반영 → 독립 gold → Qwen 원문 선택·지연 개선 후 동일 후보 실험 확대. P0 portrayal/복합 작업·부정 조건 실행 및 QLoRA 조건부 보류는 유지한다.

## 2026-09-26 GitHub push 및 해양수산부 공식 원문 확보

- 사용자 요청으로 기존 커밋을 `origin/main`에 push하고 원격 `453b58a`를 확인했다. 후속 자료 수집 코드·목록·문서는 별도 커밋으로 push한다.
- [수집 보고서](maritime_reference_acquisition_20260926.md): 해양수산부 공식 첨부 12개(PDF 4/HML 5/HWPX 3), 출처 페이지 7개를 `Dataset/authoritative_references/mof/20260926-v1/`에 보관했다. 실패 0, 19개 hash 재검증, 기존 S-101·사고자료 12개는 중복 다운로드 없이 목록화했다.
- PDF 페이지/일부 본문 및 HML/HWPX XML 확인 완료. 지침 PDF 표지 `2019-xx`와 동반 제정문 사이의 판 불일치는 GOLD_APPROVAL_BLOCKED로 기록했다. 지정 고시의 제외구역·지적경계 조건도 확인해 좌표만으로 자동 공간 적재하지 않았다.
- 원문은 로컬 Dataset에 보관하며 GitHub에는 재현 스크립트·출처/hash 목록·검수 상태를 보존한다. 기존 사용자 피드백 JSONL은 제외한다.
- 다음 참조 작업: 현행 통합법령·후속 개정 확인 → 불일치 자료 판 검수 → 조항/용어 locator 및 canonical ID 연결 → 독립 human gold. 자료 수집은 완료했으나 원천 전체 망라·RAG/DB 적재·gold 승인은 미완료다. 기존 P0 실제 작업 산출물 및 shadow 지연 개선도 남아 있다.

## 2026-09-26 최종 재검증 및 해양 정답 근거 기준

- `web-samples-v4/`: 실제 API 100/100 완료 이벤트, 도메인 FAILED 0, 관측 오류 0. COMPLETED 9 / PARTIAL 15 / NEEDS_CLARIFICATION 68 / BLOCKED 8. 상태 분포는 의미 정확도가 아니며 추가 질문 68건의 필요성은 독립 검수가 남았다.
- 45번은 빈 graph update 수정 후 SQLAlchemy 2.1의 기본 PostgreSQL 드라이버 변경으로 `No module named 'psycopg'`가 발생했다. 기존 psycopg2와 호환되는 SQLAlchemy `>=2.0.31,<2.1`로 고정하고 lock/image를 재생성했다. 실제 2.0.54·psycopg2 확인 후 v4에서 45번 COMPLETED와 오류 없음 확인. 실패 v2/v3 원본을 보존했다.
- `stage-matrix-v1.json`: 동일 원문·ID 100개를 S0와 대조했다. 상태/오류/route/분석유형/계획 도구 중 변화 사례 5개, 관측 오류 0. 슬롯·KG·입력 계약·실행 ID·근거 수를 함께 기록하며 정답 판정은 아니다.
- 기존 광범위 324개 회귀 통과에 더해 최종 이미지에서 평가 지표 테스트 11개 통과(중복 포함). accuracy, macro/micro-F1, 허용 도구 대안·raw 슬롯·clarification 지표를 구현했다. human gold 부재로 실제 의미 점수는 null이다.
- [해양 정답 근거 기준](maritime_evaluation_reference_standard.md)과 `configs/evaluation/maritime_reference_policy.yaml`을 추가했다. 공식 사전 위키와 일반 위키를 구분하고, FC/PC/DCEG·법령·고시·관측 데이터의 적용 범위와 검수 계약을 정했다. 검수 양식에 출처·최소 주장 필드를 추가했다. 정책은 설계 기준이며 원천 자동 수집·서명/진위 검증·런타임 강제 적용은 미완료다.

다음 실행 순서: P0 실제 portrayal/선택 객체 근거·처리 lineage·복합/부정 조건 실행 보강 → 해양 참조 원천 snapshot/locator와 독립 검수 gold 구축 → shadow 원문 선택·지연 문제 개선 → smoke 통과 후 전체 동일 후보 비교. 9B 및 QLoRA 승격 조건은 여전히 미충족이다. 웹 브라우저 조작은 미검증이며 이번 검증은 실제 SSE API/DB 경로다.

## 2026-09-26 한국어 슬롯·온톨로지/KG·도구 계약 구현

최신 구현과 판단 근거는 [구현·평가 보고서](korean_pipeline_implementation_20260926.md), 검수 방식은 [한국어 shadow 검수 지침](korean_shadow_annotation_guide.md)에 기록했다. 아래 9월 25일의 미설치·계획 상태는 당시 이력이며 현재 상태가 아니다.

- S0: 실제 API 100개 기준선과 모델 입력을 고정했다. 실제 후보 trace 85개, 없는 15개를 구분한다. 과거 기준 시각은 없으므로 생성하지 않았다.
- S1/S2: 원문 구간·출처·거리/기간 검증, Kiwi 0.23.2와 모델 0.23.0 고정, registry 사전·토큰 근거, 부정/문맥/수량 공통 검사를 구현했다. 원문/명시 지도 입력에 근거 없는 반경은 제거한다. 부정/제외는 현재 무시한 실행을 차단하는 단계이며 실행 지원 완료가 아니다.
- 온톨로지/KG/도구 연결: 사전 canonical ID→타입 검증 관계→KG seed→capability 입력/출력 계약을 연결했다. 원문·사전·ontology·KG hash와 unresolved 입력을 기록하고 실제 graph RAG seed와 거리 도구 입력에 반영한다. KG 관계를 사실·실행 권위로 승격하지 않는다.
- S3: 공통 종료 노드에서 필수 산출물을 감사한다. 46/47/48/76/84를 재검증했고 관련 없는 문서나 일반 사건 조회로 완료하지 않는다. portrayal 매핑·선택 객체 근거·전체 처리 lineage 자체의 완성은 남았다.
- 실제 API 100개: `web-samples-v1/`, COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8. 이후 76의 dispatch 수정은 `p0-followup-v2/`에 별도 보존했다. 상태 분포는 정확도가 아니다. 기존 API 계약 13/13, 신규 계약 7/7. 최종 수정 이후 재검증은 구현 보고서의 후속 기록을 따른다.
- S4: Qwen3.5:4b 설치·동일 후보 runner 구현. CPU 실행 대표 10개 시험에서 구조/인용/슬롯 근거 통과 3, 원문 인용 실패 5, 슬롯 거부 1, 120초 timeout 1. p50 95.835초. 의미 정답률이 아니며 전체 모델 100개 평가 완료가 아니다. 해당 설정은 smoke를 통과하지 못해 전체 확대/운영 채택을 보류한다.
- S5/S6/S7: 독립 human gold·calibration·holdout 미확보. 모델 출력 없는 개발 검수 양식 100개를 만들었다. 9B는 검증된 자원 여유와 무 timeout 조건 미충족으로 보류, QLoRA DEFER. shadow는 계속 `used_for_execution=false`다.
- 효율: 요청 내 참조 검증 16→10회, warm 한국어 분석 p50 1.218ms / p95 2.717ms, binding p50 0.239ms / p95 0.661ms를 관측했다. 단일 개발 환경 측정이며 전체 API 개선율을 주장하지 않는다.
- 배포 재현: Kiwi/model/jsonschema 고정과 poetry.lock 추가, Dockerfile packaging 호환 범위·pip check 보강, runtime 산출물을 이미지 context에서 제외했다. backend 새 이미지 재생성 후 관련 324개 테스트, 실제 API 계약 13/13 및 신규 8/8 통과. 실제 항만 후보 선택 후 1852m Wreck 검색 8건과 근거 8개를 확인했다.
- 후속 실패도 보존: `web-samples-v2/`의 45번 legacy 응답에서 빈 graph update가 SSE 종료를 일으켰다. 상태 update를 보존하도록 수정하고 회귀 테스트를 추가했다. 최종 재실행과 상세 근거는 구현 보고서에 기록한다.

다음 순서: 최종 회귀/런타임 확인 → P0의 실제 산출물·복합 작업·부정 조건 실행 보강 → 원문 span 선택 방식의 shadow adapter 개선과 자원 검증 → smoke 통과 후 전체 동일 후보 비교 → 독립 평가 후 승격/QLoRA 판단. 사용자 피드백 JSONL 및 outputs 원본은 소스 커밋에서 제외한다.

## 2026-09-25 한국어 슬롯·Kiwi·Qwen3.5 상세 작업계획

사용자 지정 후속 계획: [한국어 의도·슬롯 보강 및 Qwen3.5 shadow 평가](korean_intent_slot_shadow_plan.md). **계획 문서 작성 완료이며 신규 구현·모델 실험 완료가 아니다.** 원문 구간/단위/부정/문맥 근거 → Kiwi → 작업별 완료 계약 → 동일 후보 Qwen3.5 4B → 독립 평가와 조건부 9B → QLoRA go/defer 순서다.

- 왜: 무근거 반경·날짜, 부정 표현의 사건 필터 오인, 관련 문서만으로 분석 완료, shadow/API 병행 부하를 각각 해결해야 한다. 단일 intent 일치율로 성공을 판정하지 않는다.
- 어떻게: 기존 registry·KG·PostGIS·도구 실행은 유지하고 원문 근거 슬롯 및 필요한 작업 계약을 추가한다. 모델은 고정 후보의 해석과 점수만 제안하며 shadow 결과는 실행에 반영하지 않는다.
- 이번 재확인: backend 실행 및 `/health` 200, Kiwi 미설치, Qwen3.5 4B/9B 미설치. 기존 Ollama 목록은 qwen2.5:1.5b/bge-m3/gemma2다. 저장된 `live-presets-v5` 100개·오류 0 및 `contracts-v7` 13/13을 재확인했다. 이전 단위 177개는 이번 문서 작업에서 재실행하지 않았다.
- 평가: 계획상 필요 작업 충족과 실제 작업 완료를 분리하고, 슬롯 원문/정규화 정확도·무근거 슬롯·불필요 질문·필요 질문 누락·과잉 실행·p50/p95 지연을 측정한다. 웹 100개는 개발 회귀셋이며 독립 holdout으로 재사용하지 않는다.
- 남은 조건: 하드웨어 계측, Kiwi/모델 설치·버전 고정, 독립 human gold와 calibration, 자원 격리. QLoRA는 DEFER다. 문서의 자원·표본 수 기준은 계획값이며 검증된 성능이 아니다.
- 다음 시작점: 상세 계획 S0(snapshot·자원 기준선) → S1(슬롯 근거 schema·단위 검증) → S2(Kiwi·부정 범위·fast path 공통 검사). 기존 P0 46/47/48/76/84는 S2/S3의 필수 회귀로 유지한다.

## 2026-09-25 후속: 샘플 파이프라인 수정 및 실행 검증

최종 검증: 관련 단위 **177 passed**, 실행 중 API 계약 **13/13** (`contracts-v7.jsonl`). 웹 샘플 `live-presets-v5`는 100/100 완료 이벤트 수신, 관측 timeout 0; COMPLETED 13 / PARTIAL 13 / NEEDS_CLARIFICATION 66 / BLOCKED 8. 상태 분포는 의미 정확도가 아니다. 아래 이전 실행 수치는 중간 이력으로 보존한다.

최종 재현에서 남은 P0: 샘플 46의 portrayal 매칭 대신 정의 반환, 47/48의 지도 객체 문맥 없이 문서 완료, 76의 원천 좌표 처리 방식 질문을 공간 검색으로 분류, 84의 '위치 없이'를 사고 필터 '없, 부근'으로 조회. 이 사례와 불필요한 clarification을 다음 작업의 출력·문맥·부정 표현 회귀 기준으로 삼는다. 상세 전후 trace: `outputs/pipeline-comparison/final-review/stage_matrix.json`.

상세 판단 근거: [pipeline_repair_review_20260925.md](pipeline_repair_review_20260925.md). 사용자 우선순위는 공통 GeoLLM 샘플의 **의도→슬롯→후보→실행 계획→실제 도구→결과** 검증이다. 브라우저 미연결은 이 검증의 차단 사유가 아니다.

- 항만 catalogue 대표점 SQL의 불필요한 unary union을 제거했다. 실제 73개 항만 그룹 조회 8.54초→0.13초. 정상 지명 원천과 장애 원천을 분리하고 동일 이름 불량 행/후보 자체 원천 장애는 계속 차단한다.
- 실행 산출물과 관련 문서 주제를 구분하고, 검증된 기존 후보를 요청 산출물에 따라 재선택한다. 장소 후보가 1위여도 traffic aggregation을 후보에서 배제하지 않는다. 검색 행동만으로 사고 후보를 만드는 신호를 제한하고 nearest 공간 신호를 보완했다.
- 최근 N개월은 현재 월 기준 source별 월 coverage를 검사한다. 과거 적재 기간으로 묵시적 대체하지 않는다. 최신 적재 월은 별도 의미로 보존한다. 고정 V-PASS 우세·12개월 문구, 임의 3km layer 반경을 제거했다.
- S-101 단일 Feature 매핑, 실제 traffic coverage/pgvector 진단, 작업 trace 문맥 부족 처리, SSE 도메인 결과·근거 보존을 구현했다. 적재 관련 문서 청크 조회만 수행한 응답은 PARTIAL이며 전체 적재 완료로 표시하지 않는다.
- 격리 환경 관련 회귀 **173 passed**. 실제 API 계약 검사 **9/9 통과** (`outputs/web-sample-review/contracts-v4.jsonl`). 최신 적재 월 부산항 AIS 조회는 실제 2023-12 자료 6개 교차 격자, 집계 합 6,847,473을 반환했다. 고유 선박 수 또는 현재 통항량이 아니다.
- 최초 Ollama 100개 결과는 기본 형식/인용 통과 69, 인용 불일치 27, JSON 실패 4. 슬롯·설명 오류가 남아 있으므로 정확도로 해석하지 않는다. 최초 lexical 후보 재생과 실제 서비스 후보는 다른 실험이다. `--live-candidates`로 후자를 분리했으며 동일 후보의 rule/Ollama/혼합 순위를 저장한다. human gold와 calibration 없이 실행 권한을 승격하지 않는다.
- 원시 출력은 `outputs/web-sample-review/`, `outputs/pipeline-comparison/`에 분리한다. 기존 사용자 변경 `data/feedback/query_quality_issues.jsonl`은 소스 커밋에 포함하지 않는다.

남은 P0: portrayal symbol 연결 근거 완결성, raw→표준화→serving 전체 lineage 진단, 복합 요구의 작업별 실행/누락/완료 계약, 최신 외부 예측 및 실제 LiDAR 엔진. 지명 한정어·동명이칭 추가 입력을 자동 좌표로 치환하지 않는다. 남은 P1: 사람이 검수한 독립 gold/holdout, 동일 후보·모델·prompt의 calibration과 ablation. QLoRA 조건은 여전히 미충족이다.

동일 서비스 후보 후속 8개 실험은 구조/인용 5개 통과, 3개 인용 실패였다. 통과 응답에도 무근거 반경·날짜가 남는다. 82/46번에서 후보 부족에 따른 ABSTAIN은 유용했지만 슬롯까지 신뢰할 수는 없다. 병행 부하 실험은 API 계약 6/9로 저하했고 timeout·항만 원천 시간 제한을 관측했다. 원본 `contracts-v5.jsonl`과 `live-candidates-v2/`를 보존했다. 후보/DB 동기 조회를 이벤트 루프 밖으로 이동했으며 상시 shadow 승격 전 자원 격리와 동시 요청 검증이 필요하다.

후속으로 사고 조회 필터가 없는 질의의 clarification 경로, 실제 Dataset 경로별 embedding NULL 집계, resolver registry 선언 목록을 추가했다. 해당 후속 단위 18개와 이벤트 루프 수정 후 관련 46개 회귀가 통과했다(앞의 173개와 중복 포함). 새 진단도 source coverage와 runtime availability를 구분하며 문서/등록 정보만으로 완료를 주장하지 않는다.

기준일: 2026-09-25
재개 원칙: 명시적 새 우선순위가 없으면 아래 `P0 미비점`부터 처리한다. 이번 세션은 사용자 지시에 따라 GeoLLM 공통 P1 Ollama shadow 실험을 우선 수행했다.

## 2026-09-25 GeoLLM 공통 shadow 실험 및 근거 평가

### 후속: 실제 웹 샘플 100개 응답 평가

- [웹 샘플 평가 보고서](web_sample_review_20260925.md): 실제 HTTP 페이지의 100개 preset을 웹과 같은 SSE API로 실행했다. COMPLETED 29 / BLOCKED 63 / NEEDS_CLARIFICATION 5 / 관측 timeout 3. **상태값은 정답률이 아니다.**
- Browser 연결 목록이 비어 화면 클릭·렌더링은 미검증이다. 사용자에게 연결을 요청했으며 지도 문맥은 임의로 넣지 않았다. SSE/API 관측과 브라우저 E2E를 구분한다.
- 샘플 21의 Feature 식별, 25의 구역 지도 표시, 28/30/31/32의 통항 집계, 79의 pgvector 동작 확인, 80/82의 판단 근거 요청이 관련 문서 답변으로 종료되는 **필수 결과 누락**을 확인했다. 28/30/31/32/33의 `traffic_analysis`는 null이다.
- 원천 장애 55건의 공통 경로를 확인했다. 실제 catalog에는 후보 1,985개가 있지만 항만 projection 집계가 5초 statement timeout으로 실패하고 전체 지명 해소에 전파된다. 원천별 격리·조회 비용 개선이 필요하다.
- 43/44의 정의는 로컬 FC 정의와 일치했다. 97/98은 공식 예측 원천 부재를 명시하고 차단했다. 이 제한된 성공을 전체 서비스 정확도로 확장하지 않는다.
- 원본은 `outputs/web-sample-review/live-presets-v1/`. 40/41/42는 30초 관측 timeout 후 기존 task가 RECEIVED로 남아 있었다. 관측 클라이언트 연결 종료의 영향과 실제 브라우저 동작을 분리해 재현해야 한다.
- 평가 수집기 `scripts/check_geollm_web_samples.py` 추가. 이번 평가는 운영 코드 수정 전 기준 결과이며, 운영 라우팅을 변경하지 않았다.

- 오프라인 shadow runner, Pydantic 계약 검증, 규칙/Ollama/혼합 순위·보정·원본 요청/응답·실행 관측·모델/prompt/registry/source 버전 기록을 구현했다. 운영 상시 관측이나 실행 결정권 승격은 아직 아니다.
- gemma2 9B는 180초 timeout 2회, 축약 입력 1회 307.9초. qwen2.5:1.5b 실제 16문항은 계약 통과 9/16, 중앙값 55.62초, 기존 API 관측 15건/관측 timeout 1건이다.
- 라벨은 AI 작성 REVIEW_REQUIRED이다. 단일 라벨 불일치를 오분류로 단정하지 않도록 `provisional_label_agreement`, `reference_label_coverage`로 수정했다. 의미 정확도·task coverage는 미측정이다. 공간 분석과 위치 조회처럼 같은 기능을 공유하는 route는 대안일 수 있다.
- [실험 결과](intent_shadow_evaluation.md), [16문항 판단 근거](intent_shadow_review.md)에 필수 작업, 기능 조합, 원문 보존, 관측 근거와 유보 사유를 기록했다. AI 의견은 human gold가 아니다.
- v1 입력 축약에서 반경 검색 설명이 빠진 문제를 수정했다. v2는 원문 인용·capability ID·판단 근거·미충족 작업을 필수로 받는다. calibration 2문항에서 구조·참조 통과 1건, 다른 후보 capability 참조 거부 1건. 내용 해석 문제는 남았으며 v2 전체 evaluation은 미수행이다.
- shadow/broker 회귀검증 **20 passed**. **QLoRA DEFER**: 독립 human gold/holdout, 반복 오류 분석, 모델·GPU·라이선스·rollback 조건 미충족.
- 원본 산출물은 `outputs/intent-shadow/{pilot-probe-v1,pilot-v2,qwen-pilot-v1,qwen-rationale-v2}`에 보존한다. runtime 로그·피드백은 소스 커밋과 구분한다.

## 2026-09-25 재수정 및 실제 검증 결과

### 웹·DB·서비스 상태

- `/`, `/uport/`, `/vision/react_lidar/`, 최신 LiDAR JS 번들 및 `/health` HTTP 200. `/health`만으로 DB 정상 여부를 판단하지 않는다.
- `POSTGIS_URL`은 `marine_geo`, `S101_DB_URL`은 `gbhd_s101`. 부산 선석 169건, 인천 선석 128건을 `projection.s101_feature_valid`에서 실제 조회했다. 잘못된 bbox/과대 bbox는 422.
- `python scripts/check_web_db_connection.py`: **11개 점검 모두 통과**. 실제 LiDAR 미등록 ID의 preprocess/classify는 모두 404이며 가짜 job을 만들지 않는다.
- LiDAR `lidar_datasets` 테이블이 없음을 발견했다. `python -m scripts.initialize_lidar_registry`로 빈 테이블을 생성했고 실제 조회 결과 **0건**이다. 샘플 데이터를 삽입하지 않았다. 파일 크기·점 수는 BigInteger이며 실제 메타데이터를 저장한다.
- Compose backend를 `up -d --no-build backend`로 재생성했다. tests와 ui의 읽기 전용 마운트가 적용돼 재시작 후에도 최신 웹 번들을 사용한다. DB/타일/ETA 서비스는 유지했다.
- 항만 조회가 재기동 후 5초 제한을 넘기는 오류를 실제 API에서 발견했다. `scripts/sql/20260925_navigation_port_index.sql`의 항만 전용 인덱스를 DB에 적용했다. EXPLAIN ANALYZE에서 **Index Scan**, 항만명 73개, 실행시간 **193.193ms**를 확인했다. 이후 실제 질의 7개가 모두 통과했다. projection을 재생성하는 환경에서는 이 인덱스도 적용해야 한다.

### 제거·수정한 실행 경로

- mock registry/client/VDB/S-111 DB, fake embedding, 합성 공간결과, LiDAR pilot 산출물 생성 코드를 제거했다. 단위검증에 사용하는 격리 fixture는 테스트 폴더에만 둔다.
- RAG 원천 장애는 `BLOCKED/RAG_SOURCE_UNAVAILABLE`로 반환한다. LLM 실패 시 실제 검색 문서 발췌만 사용하며 임의 규정 답변을 만들지 않는다.
- 임의 위험등급, 기본 흘수 8m, 근거 없는 UKC 10% 법적 주장과 LLM 위험등급 fallback을 제거했다. 검증된 위험규칙 엔진이 없으면 `UNKNOWN/NOT_EVALUATED`이다.
- 고정 정확도·품질 점수와 의미 없는 100% 표시를 제거했다. 측정하지 않은 점수는 null/미평가이며 registry hit·문서 수·도구 실행 여부는 관측값으로 따로 남긴다.
- `navigation_risk.py`, `port_context.py`, `quality.py`로 복합 분석·위치 해소·미평가 계약을 분리했다. `parsed_intent`와 최종 route가 분석은 `ANALYSIS`, 정의는 `DEFINITION`으로 일치한다.
- 위치는 명시 항만명을 우선하며, 지도 문맥은 선택 feature → 클릭 → 명시 geometry → viewport → 중심 순으로 해소한다. S-101 HarbourAreaAdministrative 실제 geometry/ID를 사용하고, 지도 최근접 항만은 기본 25km 정책 밖이면 clarification이다. DB에 수록된 항만 범위이며 전국 항만의 완전성을 보증하지 않는다.
- 통항 검색은 지정 geometry 또는 사용자가 준 반경으로 제한한다. 누락된 실행 결과를 통항량 0으로 대체하지 않는다. 격자·월 합계는 고유 선박 수/실시간 위험도가 아니라고 명시한다.
- 실패·부분 결과를 report 단계에서 COMPLETED로 덮어쓰지 않는다. UI도 실행하지 않은 단계를 모두 완료 처리하지 않는다.
- LiDAR UI의 날짜/장비/CRS/좌표/점 수/밀도/RGB 고정값, 대시보드 목업 및 이전 배포 번들을 제거했다. 실제 파일 헤더를 표시하고 값이 없으면 미확인·미측정으로 표시한다.
- 전처리는 실제 PDAL 산출물과 LAS 헤더 점 수를 확인한 경우에만 성공한다. 정합·CRS 변환·RMSE는 미수행/미측정이다. 분류·DEM/S-111 의미검색 등 미구현 기능은 명시적으로 차단한다. **실행 컨테이너에 PDAL은 미설치**이며 실제 엔진 성공 검증은 미완료다.

### 검증 범위

- 관련 단위/그래프/스트림/공간/장소/RAG/UI API 회귀 **257 passed**. 이후 LiDAR DB 저장 수정에 대해 파일 헤더→실제 SQLite 저장→동일 경로 재등록 ID 유지와 실패 경로 **12 passed**를 별도 확인했다(11개 중복 실행, 총 고유 테스트 258개). 전체 저장소 테스트를 통과했다고 주장하지 않는다.
- `python scripts/check_navigation_runtime.py`: **7/7 통과**. 부산/인천 bbox와 부산 지도+명시 인천항은 실제 통항자료가 있는 `PARTIAL`; 위치 없음/먼 좌표/없는 항만은 `NEEDS_CLARIFICATION`; `조석예보란`은 `COMPLETED/DEFINITION`이다. 의도·최종 상태·항만 ID·통항자료·미평가 계약을 함께 검사한다.
- 실제 항만 source ID: 부산 지도 599613, 인천 지도 623953, 명시 인천항 집계 대표 548868. 고정 입력 ID가 아니라 해당 실행에서 조회한 결과다.
- `npm run build`, Compose `config --quiet`, `git diff --check` 통과. 최신 번들은 실제 HTTP로 확인했다.
- Browser 연결 목록이 비어 있어 실제 화면 렌더링·클릭·지도 조작은 미검증이다. HTTP/API 검증과 구분한다.
- 기존 훈련 데이터 확장 프레임워크는 유지했다. 웹·DB 검증 당시 P1은 dry-run이었고 이후 위 기록의 오프라인 후보 점수 결합·잠정 calibration 실험을 수행했다. 독립 human gold 평가·운영 승격·QLoRA는 미수행이다.
- 기존 사용자 변경 및 런타임 기록 `data/feedback/query_quality_issues.jsonl`, ignored scratch/outputs 로그는 소스 커밋에서 제외한다.

## P0 미비점 — 다음 접속에서 먼저 처리

1. **시공간 입력과 실행 범위의 잔여 계약**
   - 항만 대표점 조회 비용과 전체 원천 장애 전파는 이번 수정으로 개선했다. 실제 항만 면 union은 유지하며 병행 부하에서의 시간 제한·자원 격리는 아직 검증이 필요하다. 필수 분석 결과 없이 문서 검색만으로 COMPLETED 처리되는 잔여 경로, 특히 portrayal·지도 선택 객체·복합 요구를 작업별 출력 계약으로 검증한다.
   - 파일럿 API에서 C02/C03/E01/E03/E04는 `GAZETTEER_UNAVAILABLE`. 위치 문맥 없는 E04는 누락 위치 clarification과 원천 장애를 구분해야 한다. E06 `내일 인천항 만조 시각을 알려줘`는 `COMPLETED`와 `error_code=BLOCKED_DATA`가 함께 관측돼 상태 정합성을 재검증해야 한다. E07 관측 timeout은 작업 자체 실패와 구분한다. 재현 질의·관측은 공통 검토 문서와 qwen-pilot-v1 원본에 보존했다.
   - 최근 N개월과 source별 월 coverage 계약을 수정하고 부정 사례를 추가했다. 일 단위·지원하지 않는 명시 날짜 표현은 월 자료로 실행한 척하지 않고 clarification한다. 정확한 일 단위 집계와 다양한 명시 날짜 구간의 지원은 남은 작업이다.
   - 항만 입구/출구는 항만 전체 geometry로 치환하지 않고 clarification한다. 사용자가 확인한 세부 위치를 재제출하는 UI 흐름과 다중 항만·광역 viewport를 실제 브라우저에서 확인해야 한다.
   - 분류기 단위 테스트의 사전 fixture 통과를 실제 모든 용어의 정의 근거 확보로 간주하지 않는다. 등록되지 않은 복합 용어와 다중 의도를 추가 검증한다.

2. **위험 분석 근거 확장**
   - 사고이력, 수심/UKC, 기상·파고·조류를 동일 시공간으로 결합해야 한다. 현재 통항+고시 결과는 `PARTIAL`이며 종합 위험점수·사고확률을 산정하지 않는다.
   - 실시간 AIS provider 미설정 시 503 계약을 유지한다. 2023년 등 과거 집계가 실시간 관측을 대신하지 않는다.

3. **LiDAR와 S-111 실제 엔진 완성**
   - PDAL 설치·고정 버전·실제 LAS/LAZ 성공 실행과 출력 품질 검증이 필요하다. 분류/DEM/정합/변화탐지는 구현 전 성공을 반환하지 않는다.
   - S-111 실제 원천·관측 인덱스·검색 근거 계약을 연결해야 한다.
   - LiDAR 원본이 변경된 동일 경로의 재등록 시 메타데이터 갱신/버전 정책, 처리 산출물의 웹 제공과 영속 작업 상태를 보강한다.

4. **구조·운영 검증**
   - graph.py의 남은 중복 helper와 다른 legacy 분석 경로를 순차 감사한다. 이번 수정 범위를 전체 저장소의 모든 stub 구현 완료로 간주하지 않는다.
   - Browser 연결 후 지도/폼의 실제 상호작용 검증. 서비스 재기동 직후에는 준비 완료를 기다린 뒤 smoke를 실행한다.

## P1 Ollama 의도 보조와 QLoRA 보강

### 현재 확인된 한계

- 운영 `query_candidate_broker`는 Ollama 필요 여부만 계산하고 실제 호출·채택을 수행하지 않는다. 별도 `scripts/run_intent_shadow.py`에서는 실제 Ollama 재평가를 구현·실험했다.
- 현재 모드는 `dry_run_no_execution_change`여서 Ollama 판단이 실행 경로를 바꾸지 않는다.
- Ollama semantic prior는 장소 유형 후보에 치우쳐 있고, route vector 초기화도 비활성화돼 있다.
- 기존 LLM fallback은 위치·거리·대상 슬롯 추출 중심이며 복합 분석과 필요 근거를 판단하지 않는다.

### 1단계: 기반 Ollama 보완

1. Pydantic `IntentAmbiguityJudgement` 계약을 만든다. 출력은 후보 의도, 선택 의도, 분석 유형, 문맥 참조, 필요 근거, 누락 슬롯, reason code, confidence로 제한한다.
2. 상위 route 점수 차이가 작거나, 지시어가 있거나, 정의·실행 표현이 섞이거나, 복수 근거 결합이 필요하거나, 규칙과 registry/KG가 충돌할 때만 호출한다.
3. trace에 `needed`, `called`, `used`, `accepted`, `rejected_reason`, `latency_ms`, `model_version`, `prompt_version`을 기록한다.
4. Ollama 출력은 후보일 뿐이며 registry ID, capability, 필수 슬롯 검증 후에만 최종 경로로 승격한다.
5. 타임아웃·JSON 오류·검증 실패 시 결정론 경로 또는 clarification으로 복귀한다.
6. 먼저 shadow mode로 gold-label과 비교하고 기준 통과 후 실행 경로에 반영한다.

### Shadow-mode 후보 점수 결합 실험

Ollama에는 자유 의도 생성을 맡기지 않고 규칙·슬롯·registry가 생성한 동일 후보 2~4개를 전달한다. 각 후보의 의도·문맥 적합도, 필요 근거, 누락 슬롯, reason code를 구조화해 반환받는다.

```text
combined_score =
    w_rule      * deterministic_route_score
  + w_ollama   * calibrated_ollama_score
  + w_registry * registry_readiness
  + w_context  * context_completeness
```

- 초기에는 `w_ollama`를 낮게 제한하고 어떤 가중치도 고정된 정답으로 간주하지 않는다.
- Ollama 점수는 validation set에서 calibration한 뒤 규칙 점수와 비교한다.
- 실제 실행은 기존 안전 경로를 유지하고 shadow 결과만 trace와 평가 저장소에 기록한다.
- 규칙·Ollama·혼합 순위, 최종 실행 순위, disagreement type을 보존한다.
- 필수 슬롯·권위 근거가 없거나 점수원이 크게 충돌하면 실행에 반영하지 않는다.
- 규칙 단독, Ollama 단독, 단순 가중합, calibration 결합, registry/context gate 결합을 비교한다.
- 오류는 정의↔실행, 검색↔분석, 지시어 해소, 복합 근거 선택, 불필요 clarification, 위험한 과잉 실행으로 분류한다.

### 연구 가설과 논문화 조건

연구 가설은 "도메인 규칙, authoritative registry readiness, 공간·대화 문맥, 로컬 LLM 후보 재평가를 결합하면 단일 규칙 또는 단일 LLM보다 해양 GeoLLM의 모호·복합 의도 라우팅을 더 안전하고 정확하게 수행할 수 있다"이다.

논문 기여로 성립하려면 다음이 필요하다.

- 재현 가능한 marine geospatial ambiguity benchmark와 annotation guideline
- 규칙, embedding router, Ollama, 결합 방식의 공정한 baseline 비교
- 각 점수원과 gate를 제거하는 ablation study
- calibration error, selective prediction, clarification 품질, 심각 오류율 평가
- 미관측 항만·용어에 대한 domain generalization 평가
- latency, 로컬 배포 비용, privacy, failure-safe 동작 분석
- QLoRA 전후 비교와 사실 권위 분리 검증
- seed, prompt, model, registry snapshot, lineage를 포함한 재현성 패키지

논문 작업명은 `Authority-Grounded Hybrid Intent Routing for Maritime GeoLLM`으로 두며, 실제 제목과 기여 주장은 benchmark 결과 후 확정한다.

### 2단계: 평가 데이터 축적

- 정의/실행 경계, 지시어와 대화 문맥, 복합 분석·근거 선택, 근거 부족, 유사 용어·부정·다중 의도를 hard case로 확대한다.
- 규칙 결과, Ollama 결과, 최종 채택 결과, 사용자 피드백을 함께 저장한다.
- 학습/검증/holdout을 lineage로 분리하고 합성 데이터 near-duplicate 오염을 차단한다.

### 3단계: QLoRA 적용 조건

QLoRA는 즉시 적용하지 않고 다음 조건을 모두 만족할 때 진행한다.

- prompt와 few-shot 보완 후에도 반복 오류가 남는다.
- 사람이 검수한 충분한 gold-label과 독립 holdout이 확보된다.
- 오류가 지식 부족이 아니라 의도·슬롯·근거 선택 패턴의 일관된 실패다.
- 기반 모델·라이선스·GPU·양자화·adapter 배포 및 rollback 절차가 확정된다.

학습 목표는 자유 답변이 아니라 intent/analysis type, 문맥 참조, 슬롯, EvidenceBundle 종류, clarification 판정으로 제한한다. 법령 내용, 좌표, 실제 통항량은 adapter가 생성하지 않고 registry·PostGIS·도구 결과로만 확정한다.

### QLoRA 평가·승격 기준

- 규칙 단독, 기반 Ollama, prompt 개선 Ollama, QLoRA adapter를 동일 holdout에서 비교한다.
- intent macro-F1, slot exact match/F1, evidence-selection F1, clarification precision/recall, schema validity, latency, fallback rate를 측정한다.
- 정의형→실행형, 분석형→문서검색형 같은 중대 오류를 별도 집계한다.
- 전체 점수뿐 아니라 중대 오류 감소와 미관측 도메인 일반화를 확인한다.
- adapter의 base model, dataset snapshot, prompt/schema version, 평가 보고서를 registry에 등록하고 즉시 rollback 가능하게 한다.

## 다음 실행 순서

**최신 사용자 지정 우선순위:** [상세 계획](korean_intent_slot_shadow_plan.md)의 S0–S4 구현·검증 현황은 문서 상단과 [구현 보고서](korean_pipeline_implementation_20260926.md)를 따른다. 남은 실제 작업별 산출물과 shadow 원문/자원 문제를 보완하고 smoke를 통과한 뒤 전체 비교를 확대한다. S5 독립 평가 후 조건부 9B/자원 격리, S7 QLoRA 판단으로 이어간다. 아래 기존 순서는 운영 점검 및 잔여 P0 목록으로 유지한다.

사용자 지정 P1 후속: AI 사후 검토를 사람이 확인해 **필수 작업·허용 capability 조합·슬롯·근거·clarification** 단위의 독립 평가셋을 만든다. route 이름을 정답으로 고정하지 않는다. 후보 설명 누락·공유 기능을 정비하고 고정한 prompt/model로 전체 calibration/evaluation을 재실험한다. 지연·실패 격리 확인 전 상시 shadow나 실행 권한을 승격하지 않는다. 별도 우선순위가 없으면 아래 P0 순서를 따른다.

1. 웹 준비 후 `python scripts/check_web_db_connection.py`와 `python scripts/check_navigation_runtime.py` 실행.
2. 새 DB에는 `docker exec geollm_backend python -m scripts.initialize_lidar_registry` 적용. S-101 projection에는 `scripts/sql/20260925_navigation_port_index.sql`을 S101 DB에 적용.
3. P0-1의 복합 요구·portrayal·선택 객체 출력 계약과 shadow/API 자원 격리를 우선 검증한다. 항만 세부위치 확인 흐름과 미지원 날짜 표현을 보강하고 관련 단위 테스트+실제 API 부정 사례를 검증한다.
4. 사고·수심·기상 근거 결합 및 LiDAR 실제 엔진을 각각 원천·산출물 검증과 함께 확장.
5. Browser 연결 후 화면·지도 조작 검증.
6. 구현된 오프라인 shadow를 근거·복수 기능 조합 기준의 독립 human gold/calibration 평가로 확장한다. v2 전체 평가와 상시 관측 연동은 미완료다. 승격 조건 충족 전 실행 결정권을 주지 않는다.
7. prompt 보완 후에도 반복 오류가 남고 holdout·rollback 조건이 충족될 때만 QLoRA 실험.

## 검증 시 주의사항

- 2023년 통항자료를 현재 실시간 위험도라고 표현하지 않는다.
- `estimated_accuracy`는 측정 전 null이다. registry exact match를 답변 정확도 100%라고 표현하지 않는다.
- 고시 polygon이 `pending_geometry_ingest`이면 적용 공간을 확정했다고 표현하지 않는다.
- 지도 문맥과 명시 항만명이 모두 없으면 특정 항만을 임의 선택하지 않는다.
