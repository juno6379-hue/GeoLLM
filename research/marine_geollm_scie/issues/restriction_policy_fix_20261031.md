# 공개 S-101 제한코드 질의의 정책 오차단 수정

## 재현과 원인

원본 연구 run `20261030_full_execution_v5/graph/production_rows.jsonl`의 PILOT_Q2_02 `제한구역의 제한 종류는 어떤 코드로 표현해?`는 BLOCKED_POLICY였다. 이는 비공개 원천 요청이 아니라 공개 S-101 RestrictedArea/restriction의 코드 설명 요구다. `services/orchestrator/graph.py:_looks_like_policy_block_query`가 제한구역/restricted 단어만으로 비공개 요청을 분류했다.

실제 API 수정 전5건은 `runs/20261031_restriction_policy_before/api_rows.jsonl`에 보존했다. 공개 한국어/영어 코드설명 모두 BLOCKED, 비공개혼합/군사영어 BLOCKED였다. `비공개 진입제한 구역 좌표를 보여줘`는 NEEDS_CLARIFICATION이었다. 기존 public_restriction_terms 예외가 비공개 검사보다 먼저여서 보안정책 우선 검사에서 빠졌다. 좌표가 실제 노출됐다는 관측은 아니다.

## 최소 변경

운영 수정은 graph.py의 정책 predicate 한 곳이다. 명시 비공개·권한없음·classified/military/private/confidential·restricted data 요청을 우선 차단한다. 공개예외는 RestrictedArea/제한구역이라는 대상과 restriction/속성+코드/허용값 설명 요구가 함께 있고 좌표·geometry·download/export 등 실제자료 추출 요구가 없는 경우로 제한했다. 광범위한 단일키워드 bypass나 특정 benchmark 원문 예외는 추가하지 않았다. 일반 진입/속도제한 공공 공간조회 예외는 유지하지만 명시 비공개 요청보다 우선하지 않는다.

신규 tests/unit/test_restriction_policy_scope.py는 실제 운영 predicate AST를 읽어 DB/모델 graph초기화 없이 검사한다. 양성6·부정9 **15 passed**. 첫 검사에서 영문 feature ID 뒤 한국어 조사의 Unicode word boundary 문제가 발견되어 ASCII identifier 경계로 보완했다. 실제 API 검증은 별도로 수행하여 AST 검사만으로 완료를 주장하지 않는다.

원본 연구 run/GOLD를 변경하지 않았다. DB쓰기·보안권한 승격·후보 승인·UI 수정·커밋은 수행하지 않았다. backend는 services bind mount에 있는 graph모듈을 다시 로드하도록 geollm_backend만 재시작했다. 문서검색의 근거품질/코드 답변 완전성은 이 정책 predicate 수정의 완료범위와 분리한다.


## 실제 API 수정 후 결과와 미완료 범위

`runs/20261031_restriction_policy_after/api_rows.jsonl` 5건을 원본대로 보존했다. 공개 한국어는 120초 관측범위에서 RECEIVED/OBSERVATION_TIMEOUT, 공개 영어는 TRANSPORT_ERROR였다. 이는 성공이나 새 정책경로 통과 증거가 아니다. 공개 질의에 대한 실제 최종 코드설명·근거 완성은 검증하지 못했다.

비공개 혼합 요청과 classified military 영어는 BLOCKED였다. 그러나 `비공개 진입제한 구역 좌표를 보여줘`는 수정 후에도 NEEDS_CLARIFICATION이었다. helper 단위에서는 true이지만 실제 graph 전체의 정책 우선 적용은 미해소다. 실제 데이터가 공개됐다는 관측은 없으나 기대 BLOCKED 상태는 충족하지 못했다. check_intent_parsed의 query_contract/source_mapping/selected_feature 조기종료 및 공간 fastpath가 일반 정책차단보다 먼저 처리되는 점을 후속 감사 후보로 기록한다. 정확한 해당 경로 원인은 최종trace 대조가 필요하며 이번에 추가 수정하지 않았다.

종합 상태는 **PARTIALLY_VERIFIED_NOT_SERVICE_COMPLETE**. 단위15개와 before/after 원시기록, validation_summary.json을 함께 남긴다. 공개 답변 timeout은 관측환경/모델 지연 등 원인이 미확정이며 정답 실패로 채점하지 않는다. 재시도 폭을 늘리거나 원본을 덮어쓰지 않았다. 다음 담당자는 두 공개질의의 실제 완료 상태와 private_entry의 첫 종료경로를 각각 확인하고 운영수정 후 새run에서 정상/부정 검증을 마쳐야 한다.

부모 확인에 따르면 논문 비교보고서가 생성되어 자동감시는 삭제됐다. 원본 K1 결과는 수정 전 조건의 자료로 유지하고 이 정책 helper 변경의 연구 효과로 재계산하지 않는다. 이후 운영 검증과 연구 재실행은 새 source hash/run ID를 사용한다.


## 사용자 재개 후 정책 우회 경로 확정

이전 after 원시 private_entry의 history는 INTENT_PARSED→NEEDS_CLARIFICATION, actor=DatasetPlaceResolver였다. target_layers=[entry_restricted_area]이며 비공개 문구가 location_text로 전달됐다. 이는 helper가 false였기 때문이 아니라 check_intent_parsed에서 requested spatial layer 분기가 일반 policy block 분기보다 먼저 선택됐기 때문이다.

수정은 check_intent_parsed의 기존 query contract stop 검사 직후 원문 policy predicate를 먼저 적용하는4줄이다. private 요청을 기존 fast_spatial_or_traffic_block 경로로 보내고 새 데이터승인/우회는 만들지 않는다. 공개 RestrictedArea 코드설명의 예외는 앞선 predicate에서 유지된다. 기존 계약에서 이미 종료된 query_contract/source_mapping/selected_feature 결과는 기존 stop 처리로 보존한다. 이 범위를 모든 parse단계 보안경로의 전면 감사로 확대해 주장하지 않는다.

정상6/부정9 predicate 검사와 실제 conditional-edge의 우선 선택3건·기존contract stop1건을 합쳐 **19 passed**(6.48초). edge검사는 실제 함수 AST를 실행해 뒤의 레이어 helper 없이 정책분기에서 반환되는지 확인한다. 2026-10-31 부모의 공개FC 코드설명 통합 작업과 충돌을 피하려 graph 소유권을 넘겼고, 통합 후 재시작 한번 및 실제API5건을 함께 검증할 예정이다. 아래 최종관측 전에는 서비스전체완료로 승격하지 않는다.


## 통합 수정 후 최종 실제 API 검증

부모의 parse 최초 정책검사·공개 FC 응답 통합·동기 IO 분리, 별도 에이전트의 source-backed FC 설명모듈, 본 에이전트의 ExecutionValidator/registry gate를 통합한 후 backend를 한 번 재시작했다. 최종 raw는 **runs/20261031_restriction_policy_integrated/**이며 앞선 before/after 실패는 그대로 보존했다.

| 실제 질의 | 최종상태 | 검증 내용 |
|---|---|---|
| 공개 한국어 제한코드 | COMPLETED | PublicCatalogueAttribute, QEC EXECUTION_READY, receipt 재계산 authorized=true, 공간검색 NOT_RUN |
| 공개 영어 제한코드 | COMPLETED | 위와 동일, 한국어와 같은 FC 원천 |
| 비공개+코드 혼합 | BLOCKED | FastSpatialTrafficBlock, QEC BLOCKED_POLICY, authorized=false |
| 비공개 진입제한 좌표 | BLOCKED | 이전 DatasetPlaceResolver 우회 해소; QEC BLOCKED_POLICY, authorized=false |
| classified military 영어 | BLOCKED | QEC BLOCKED_POLICY, authorized=false |

공개2응답의 allowed_values29개와 parsedFC source_sha256은 실제 resolver/파일 결과와 정확히 일치했다. Validator가 원문을 다시 해소하고 고정 source_ref·실제 파일digest·필수 definition/feature/attribute/locator와 등록tool의 operation/source를 검증한다. DataBinding.snapshot_version에 digest를 넣고 builder가 승인받은 digest와 응답자료 digest를 대조한다. 최종 JSON을 다시 QueryExecutionContext로 역직렬화해 receipt 유효성까지 검사했다. 허용값과 source hash대조, 모든 승인/차단 관측은 verified_contracts.json에 보존했다.

정책/공개모듈/게이트 통합 단위 **45 passed**, 이후 직렬화 receipt 재검사 추가한 gate10 tests도 통과했다. 실행 권위는 ExecutionValidator이며 코드 설명자료가 공간 객체조회 권한으로 전용되지 않았다. 비공개3건의 count는 null이고 공간 성공으로 표시하지 않았다. 이는 대표5건의 계약 검증 완료이며 모든 보안경로/모든질의에 대한 포괄 검증은 아니다.

**남은 별도 운영 한계:** 같은 관측기간 /health 3회 중 HTTP200(76.12ms),3초 TimeoutError,HTTP200(2093.74ms)가 관측됐다. 공개 코드질의의 완료 문제는 해결했으나 서비스 응답성 전체가 안정됐다고 주장하지 않는다. 헬스/동시부하·임베딩/모델경로 지연은 별도 성능 후속으로 남기며 health_during_observation.json에 보존했다. API5 검증 후 추가 모델호출/재시도는 하지 않았다.

이 통합검증은 수정 전 논문 K1과 분리한다. 새로운 연구 실행은 최종 source해시를 고정한 별도run으로 수행해야 한다. 커밋하지 않았다.


## 공개 공간질의 회귀 발견과 수정

후속 연구 `20261031_graph_timeout180_v1/graph/production_rows.jsonl`의 Q5_02 `부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘`가 BLOCKED_POLICY로 끝났다. 정책 검사의 우선순위를 앞당긴 뒤에도 helper 마지막의 제한구역/restricted 레이블 단독차단이 남아 공개 항행제한 구역까지 기밀자료처럼 취급한 회귀다.

최종 helper는 명시적인 비공개/권한없는/군사·classified·private·confidential/restricted data 문구만 이 정책게이트에서 차단한다. RestrictedArea 공간표현 그 자체는 비공개 자료라는 증거가 아니므로 단독 레이블 차단과 불필요해진 공개코드 예외분기를 제거했다. 이후 공간조회는 기존 지명모호성·원천존재·실행권한·ExecutionValidator를 그대로 거친다. 확인 요청/원천차단을 0건 성공으로 바꾸지 않는다.

기존 일반좌표/geometry2개 사례는 policy predicate false로 기대를 바로잡았고 Q5_02 회귀를 추가했다. 공개FC·validator·정책 최신통합 **48 passed**(7.97초). 비공개 우선순위는 유지한다. graph수정완료 뒤 소스편집을 중단했고 부모가 같은 final source로 backend를 재시작했다. 새 실제4질의 검증은 `20261031_restriction_policy_spatial_regression`에 분리한다.


최종 회귀 API4건 모두 CAPTURED/terminal 확인: Q5공개공간 NEEDS_CLARIFICATION, 공개FC COMPLETED, private_entry와 restricted_data BLOCKED. 원시/역직렬화QEC 검증값은 새 run의 verified_contracts.json에 보존했다. Q5를 성공으로 승격하지 않았고 공개FC는 공간조회가 아니다. 명시비공개는 계속 정책차단하며 sourcehash 고정 후 추가 운영변경을 하지 않았다. 이 결과와 별도 연구v2 재실험을 구분한다.
