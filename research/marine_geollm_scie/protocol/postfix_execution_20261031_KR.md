# 공통 채점·구현 보완·반복 실험 인계

사용자 요청은 P 실제 답변의 공통 채점, 구현 오류 수정 후 새 동결 실행, 반복 변동성과 독립 GOLD 검수다. 기존 연구 원본과 운영 UI 변경은 보존한다. 독립 검수자는 선정됐으나 검수 결과는 아직 제공되지 않았다.

## 실제 답변의 공통 채점

`execution_report.py`는 P의 `final_state.final_dict`에서 실제 document_answer, 실행 상태, 반환 객체 ID·원천 hash를 읽는다. 검색 excerpt나 GOLD를 답변으로 재작성하지 않는다. 구조 필드 누락은 기계 계약 미충족이며 서술 의미 오답과 다르다. 공간 실행·원천이 확인되지 않으면 공간 정답은 미측정이다. 운영 응답에 연구용 oracle 선언을 요구하지 않는다.

수정 전 원본 baseline90과 graph_timeout180_v2를 새 평가기로 재채점한 자료는 `runs/20261031_common_mapping_before_v3/report/`다.

| 방법 | 기계 검사 전체 통과 | 실패 | 미측정 포함 |
|---|---:|---:|---:|
| B0 | 0 | 10 | 8 |
| B1 | 1 | 9 | 8 |
| B2 | 0 | 10 | 8 |
| B3 | 0 | 10 | 8 |
| B4 | 0 | 10 | 8 |
| P | 3 | 9 | 6 |

P의 세 통과는 같은 독도 5km 지명 검색의 동등표현이다. 세 독립 공간 사례나 전체 의미 정확도로 해석하지 않는다. 새 실험과 구분되는 사전 결과다.

## 발견 원인과 수정 범위

- 문서형 정의·속성 요청이 공간 fast path에 들어가던 오류: 요청 형태/실행 슬롯을 구분하고 실제 FC 문서 조회를 연결했다. XML과 parsed 원천 hash, 기하·binding·locator 및 ExecutionValidator 승인을 확인한다.
- 정확 일치 문서가 없으면 FAILED/null로 끝나던 경로: 기존 Standard RAG로 이어지며 직접 exact 호출 실패도 검색 범위를 명시한 구조화 응답으로 반환한다.
- AOI 누락과 미지원 교차 실행, 복합 대상의 일부만 실행된 결과를 완료로 표현하던 문제: 실제 산출물 의무를 검사하고 clarification/차단/부분완료로 구분한다. 지원하지 않는 기능을 새로 구현한 것으로 표현하지 않는다.
- `AnchorageArea` 안의 age를 치환하던 문제: ASCII 토큰 경계를 적용한다.
- 영어 지도 복합 요청은 150초 관측 후에도 RECEIVED였고 약268초 뒤 문서2건만으로 COMPLETED였다. parse 구간은251.6초였으나 개별 생성 시간이 따로 기록되지 않아 전부 생성 시간으로 단정하지 않는다. 운영 fallback은 CPU gemma2와 명시 timeout/retry 없는 SDK를 사용했다. 누락 지도 범위를 먼저 확인하고, 선택적 parser fallback에15초/재시도0/전체 await deadline을 적용했다. 문서만으로 지도 요청 완료를 허용하지 않는다.
- 운영 semantic prior의 기본 llama3.1은 설치돼 있지 않아 HTTP404였다. 전용 모델 설정이 없으면 기존 GEOLLM_WEB_SHADOW_MODEL의 Qwen을 참조한다. 일반 LLM_MODEL=gemma2와 결합하지 않으며 연구의 명시 Qwen 설정은 유지한다.
- QEC guard가 NEEDS_CLARIFICATION/BLOCKED를 readiness에 쓰던 스키마 오류: 유효한 NEEDS_USER_INPUT/BLOCKED_CONFIG로 기록하며 실행 권한은 발급하지 않는다.

실패 원본 API v1(서버 준비 전 통신 오류), v2(문서 실패/지도 지연/QEC 오류), v3(실행경계12검사 통과)을 모두 보존했다. v3 내용을 사후 대조하니 등대 질문은 등선 발췌만 있고 연산자 질문은 문서0건인데도 COMPLETED였다. 실행경계 검사와 의미 완결성은 다른 검사다. 이 추가 발견에 따라 설명 출력의 완료 판정도 보완하고 다음 API 관측으로 검증한다.

## 반복 및 검수 조건

새 profile은 `runs/20261031_postfix_profiles_v1/`이다. 기존 snapshot과 frozen_v5 계약은 동일하고 코드/라우팅 timeout 조건은 새로 기록한다. semantic prior180초와 일반 parser fallback15초를 연구 환경과 profile에서 일치 검사한다. 정책·검색·완료 판정도 변경됐으므로 timeout 단독 효과나 Qwen 단독 효과의 실험이 아니다.

K5는 P18문항×5회와 B0–B4의18문항×5방법×5회, 총540행이다. 사례 내 반복을 먼저 집계하고 동등표현 군집을 고려한다. 결측을0점으로 바꾸지 않으며 독립 검수 전 의미 정확도·p-value·신뢰구간은 생성하지 않는다. 과거 baseline90의3691초 기준 전체5~7시간 이상 추정이다.

독립 검수용 최신 자료는 `review/20261031_independent_gold_v3/`다. 초기 A/B 양식에는 원천 판·경로·hash와 사용자 고정 공간 입력만 제공한다. AI 후보가 선택한 객체 ID·locator는 별도 파일에 두어 초기 판단을 유도하지 않는다. 사용자가 검수자를 선정했지만 완료0건이다. 합의 결과는 새 참조 버전으로 받아 재채점하며 기존 AI 참조를 소급 인간 GOLD로 변경하지 않는다. 이18개는 이미 노출된 개발 사례이므로 검수 후에도 holdout이 아니다.

## 남는 미비점

- 등대의 구조물·등화 다중 매핑과 설명 완결성, 실제 AOI 교차 도구, 복합 대상별 실행 완성.
- 사고 필터 누락의 기존 오류코드2건: 기대 ACCIDENT_FILTERS_REQUIRED 대비 EXECUTION_GATE. HEAD 모듈을 메모리에 복원한 동일 시험에서도 실패해 기존 문제로 확인했고, 무제한 DB 조회는 실행되지 않았다.
- 전체 서비스 부하 SLO, 독립 GOLD 결과, 미노출 holdout, 통제된 ablation/recovery 및 전체 RQ 확정.

새 실행의 실제 시작·검증·완료 상태는 아래 후속 기록과 해당 status.json을 함께 확인한다. 준비 코드와 테스트 통과를 반복 실험 완료로 간주하지 않는다.

## 2026-10-31 실제 검증 및 K5 시작

- 최종 API v4: `runs/20261031_contract_routing_api_v4/verified_contracts.json` 12/12 실행경계·원천정합성 통과. 정박지2/침선속성은 실제 FC정의·기하·XMLhash·유효승인 확인, 공개제한코드29개완료, AOI/지도누락은유효QEC추가입력, 비공개는정책차단. 등대/연산자설명은PARTIAL로미충족을드러내며 의미정답으로세지않는다. source_unchanged_after=true.
- 영어지도복합: v2에서150초관측timeout 후약268초에문서-only완료 → v4 MAP_SCOPE_REQUIRED/NEEDS_CLARIFICATION4.062초. 최종 API전체1.250~22.344초. 이는고정12요청의관측이며전체SLO가아니다.
- 광범위159tests passed 후 설명완결성추가를포함한최종관련100tests passed. 서로중복하므로합산하지않는다. 실제실행전연구환경timeout15초고정검증을추가했고해당모델profile시험19passed는최종100에포함된다. 잘못된시험파일명1회호출은수집실패후정확한파일로재실행했다.
- 운영runtime 확인: semanticprior qwen2.5:1.5b/GEOLLM_WEB_SHADOW_MODEL, 기본2.5초; generalparser gemma2는유지하되15초/재시도0. API조건은runtime_conditions.json에분리했다. 연구는명시Qwen+180초prior/15초parser로동결한다. API검증종료후미사용gemma2를unload한기록은outputs/scie_postfix_k5_resource_preflight.json이다.
- `runs/20261031_postfix_k5_v1` RUNNING, 첫stage graph_repeat_0. 최초실제supervisor PID11496/child37976 및245동결파일을확인했다. 이후PID/단계는status.json과실제프로세스로확인한다. parentstdout/stderr는outputs/scie_postfix_k5_20261031.{stdout,stderr}.log.
- 후속점검 automation `geollm-k5` ACTIVE,30분간격. 변경없음은조용히종료하고의미있는단계완료/실패/검수자료필요시에알린다. 보고서완성후점검종료. 이전geollm과별개다. 아직K5완료/보고서완성아님.

## 첫 K5 실행의 초기 gate 중단

05:55UTC v1은 실제 모델 호출 전 STOPPED_REQUIRES_REVIEW. 기존 snapshot.files의 query_normalizer.py만변경됐고나머지원천파일20개hash동일. 정상검증차단이며기존snapshot을수정하지않는다. 별도에이전트가원본CSV와현재연구DB를재대조한파생실행snapshot/lineage를준비한다. 새코드조건은새profile/run으로측정하며이번실패는보존한다.

## K5 v2 실제 재개

`derive_execution_snapshot`의6tests통과후 실제DB6관계를읽기전용으로새CSV에재추출했다. 모든전체CSVhash가부모와일치, 부모manifest불변, 코드query_normalizer변경전후hash만명시해새실행snapshot을만들었다. outputs/scie_model_snapshot_20261031_execution_v1 LOADED_VERIFIED 및기존verify_files통과. 관계별REPEATABLE READ이며단일교차관계transaction으로주장하지않는다. 데이터동일성은각관계전체CSV일치로검증했다.

새 profiles_v2의baseline/P가같은새snapshot을참조한다. `runs/20261031_postfix_k5_v2`에서supervisor8920/child34420 및연구worker/proxy실제실행을확인했다.246파일동결,첫graph18실행중. 현재status/PID는항상최신파일과실제프로세스로대조한다. 후속automation geollm-k5는v2를30분마다확인한다. 아직540관측·반복보고서완료가아니다.

## 첫 P 반복 완료·baseline K5 진입

graph_repeat_0 18/18, EXECUTION_OBSERVED, source_unchanged_after=true, 초기화85/85오류없음. 생성10/10 HTTP200/JSON객체 및 문항embedding20/20성공. 상태COMPLETED10/PARTIAL4/NEEDS_CLARIFICATION4. 같은평가기로기계검사7통과/5실패/6미측정포함이며첫회잠정결과다. interim_graph_repeat0_audit.json에원본/평가기/계약hash와문항별검사요약을저장했다. 현재baselines_k5 RUNNING이고전체K5완료가아니다. 관련소스·검수자료커밋 a8d73e4,원격push없음.
