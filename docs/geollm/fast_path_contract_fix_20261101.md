# 운영 fast path 계약 보완 및 실제 API 검증

2026-11-01. 논문 원본 run/GOLD를 수정하지 않은 운영 수정이다. 전체 기능 구현 완료를 뜻하지 않는다.

## 수정 범위

`services/orchestrator/graph.py`의 hazard radius, generic Dataset radius, S-101 nearest fast path가 실행 전에 연산·대상 의무를 확인한다.

- 명시 nearest/closest/최근접/가장 가까운 요청을 radius로 처리하지 않는다. radius 전용 경로는 `UNSUPPORTED_OPERATOR`로 차단하며 불필요한 반경 입력을 요구하지 않는다.
- 복수 객체 family 요청에서 실제 선택된 대상에 누락된 family가 있으면 `UNSUPPORTED_COMPOSITE_TASK`로 차단한다. 비교 산출물을 지원하지 않는 fast path 역시 이 사유로 차단한다.
- 대상 수가 많다는 이유만으로 차단하지 않는다. 기존 `select_targets`와 동일 profile의 실제 선택 집합을 사용한다. Wreck+Obstruction 등 지원되는 복수 대상 실행은 유지한다.
- 거절은 기존 ExecutionValidator 검증을 거친다. READY 권한을 새로 부여하거나 feature/source/reference geometry를 보정하지 않는다.

## 실제 SSE 결과

원본 `outputs/reliability_fast_path_contract_20261101_v2/`에 요청, SSE 전체, 최종 답변을 보존했다. v1은 backend 초기화 도중 RemoteDisconnected가 발생한 관측 원본이며 덮어쓰지 않았다. `/health` 200 확인 후 v2를 실행했다.

| 요청 | 실제 결과 | 확인 |
|---|---|---|
| 독도 부근에서 가장 가까운 등대 | BLOCKED / UNSUPPORTED_OPERATOR, 26.750초 | DISTANCE_REQUIRED로 바꾸지 않음, count=null |
| 부산항 주변 2km 정박지+제한구역 비교 | BLOCKED / UNSUPPORTED_COMPOSITE_TASK, 7.468초 | 일부 대상만 실행하지 않음, count=null |
| POINT(129.075 35.075) 1km Wreck | PARTIAL / DATA_COVERAGE_UNVERIFIED, 14.203초 | spatial_select 실행 완료, observed_count=0, total_count=null. 실세계 0건 확정 아님 |
| 동일 POINT 1km Wreck+Obstruction | COMPLETED, 9.828초 | 두 target 유지, total_count=returned_count=18, 실제 실행 receipt 생성 |

두 거절 결과의 `search_execution`은 NOT_RUN이며 execution_attempted/execution_started/tool_called/sql_executed=false다. 이는 guard의 실행 전 반환 위치와 응답을 확인한 결과이다. 별도 DB 서버 SQL 감사 계측으로 모든 명령의 부재를 증명한 것은 아니며, 의도 분석의 metadata 조회와 실제 공간 실행을 구분해야 한다.

두 radius 결과 모두 QEC provenance에 execution_validation, feature_code_verification, spatial_select, snapshot_receipt 완료가 기록됐다. feature code 검증은 각각 10.436ms / 15.361ms, spatial_select는 78.242ms / 61.402ms였다. 콜드 캐시 SLO나 전체 정확도 수치로 해석하지 않는다.

실행 종료 후 별도 비동기 규칙/Qwen 비교 상태도 `/api/v1/intent-comparisons/{id}`로 확인했다. nearest/composite/radius는 COMPLETED, multi는 `FAILED: ValueError: selection/score mismatch`로 종료됐다. 네 작업 모두 terminal 상태이며 각 `*_comparison.json`을 보존했다. multi 공간 실행 성공과 shadow 비교 실패는 구분한다. 모델 비교의 실패를 정상 Qwen 결과로 바꾸지 않았다.

## 테스트와 잔여 오류

- 전용 `test_spatial_fast_path_contract.py`, catalogue/spatial contracts, coverage gate: **66 passed**.
- 기존 `test_place_graph_integration.py`: **28 passed, 1 failed**. 단순 위치조회 `test_place_query_revision_is_preserved`는 execution_revision=3을 주어도 QEC revision=1이다.
- 새 guard를 런타임 monkeypatch로 항상 None 반환하게 한 별도 단일 테스트에서도 revision 실패가 재현됐다. 새 guard를 비활성화해도 남는 오류이며, 과거 commit 전체를 재생한 결과는 아니다. 기존 dirty 테스트 파일은 수정하지 않았다.
- nearest 등대 executor, canonical polygon reference 선택·해소, 공인 source coverage 계약, 복합 비교 및 target별 완료 증빙은 여전히 별도 작업이다. 지원되지 않는 요청을 정확히 거절하도록 보완했을 뿐 이를 구현 완료로 표시하지 않는다.

검증 graph SHA256: `5c19179721f2ce5635c9a4f5d3eb6ab82568b9d8788b570805d7892deb6bc148`.
