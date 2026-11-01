# 원요청 제약과 실행계획의 불일치 검사

2026-11-01. 운영 Validator 수정이며 논문 v2의 원본 관측·GOLD·점수를 변경하지 않는다.

## 원인과 수정

기존 Validator는 실제 source/tool binding, geometry 존재, 거리의 양수·상한 등을 확인했다. 그러나 유효한 CRS/feature/거리 값이 **사용자가 요청한 값과 같은지** 대조하지 않았다. 따라서 4326→3857, Wreck→Obstruction, Wreck에 Obstruction 추가, 1000m→5000m 변경은 범위 검사만 통과할 수 있었다. 이는 Compiler의 변환 문제가 아니라 Validator의 요청 보존 검사 누락이다.

`services/orchestrator/request_constraints.py`가 명시적·단일 제약만 추출하며 `ExecutionValidator`가 불일치를 차단한다. QEC slot, geometry, feature, source, 거리 값을 수정하지 않는다. 결정론적 제약 검사와 QEC 무손실 컴파일은 분리된다.

- `capture_request_constraints(query, spatial_context)`는 서버가 받은 원요청을 frozen object/JSON snapshot으로 보존한다. 호출자는 모델 계획이 아닌 동일 public query/context를 전달해야 한다.
- `validate_execution_context(..., request_constraints=trusted)`가 snapshot과 QEC 원질의를 대조한다. 파라미터가 없으면 QEC original_query만 검사하며 원context 검증 미수행을 기록한다.
- QEC provenance/context에 모델이 붙인 approved/trusted/constraint 주장은 근거로 사용하지 않는다.
- request hash, 실제 검사 항목, dictionary hash 및 한계를 receipt로 기록하고 authorization input hash에 포함한다. 검증 이후 receipt/slot/원질의 변경은 승인 무효다.
- 명시 거리 단위는 동등한 m/km를 허용하고 feature 순서 차이는 허용한다. 복합 child task는 원요청 feature 집합의 부분집합일 수 있다. 전체 child union 누락은 이 검사만으로 완료 판정하지 않는다.
- 모호한 다중거리·대안·제외·generic hazard 확장 및 참조 객체 언급을 임의로 하나의 target/radius로 만들지 않는다. feature와 layer namespace도 자동 교정하지 않는다.

## 실제 연구 DB 무모델 재검증

`outputs/request_constraint_native_replay_20261101_v3/rows.json`과 `summary.json`: 이전 frozen v2의 9 initial plan을 그대로 읽어 현재 native Validator에 재입력했다. 추가 동등단위/순서 2건을 별도로 검사했다. 실제 `scie_model_v3` metadata SELECT만 수행했고 모델 호출·공간 SQL 실행은 하지 않았다. 개발 중 v1/v2 replay도 별도 보존했다.

| 사례 | 새 검사 결과 |
|---|---|
| CONTROL | 승인 |
| WRONG_CRS | REQUEST_CRS_MISMATCH, native Validator 차단 |
| WRONG_FEATURE / SEMANTIC_EXPANSION | REQUEST_TARGET_MISMATCH, native Validator 차단 |
| WRONG_RADIUS | REQUEST_DISTANCE_MISMATCH, native Validator 차단 |
| MISSING_GEOMETRY / UNKNOWN_SOURCE / NEGATIVE_RADIUS | 차단 유지 |
| UNIT_TYPED | compiler 거절 유지, native Validator 미호출 |
| 1000m와 1km 동등표현 / 대상 순서변경 | 승인 |

11건의 계획 및 slot hash 불변을 확인했다. native 검출 7건과 compiler 거절 1건을 혼동하지 않는다. source-backed 메타데이터 점검을 포함한 개발 진단이며 새로운 8방법 논문 실험 결과나 독립 인간 정확도가 아니다.

## 단위 검증과 제한

최종 관련 Validator/coverage/radius/authority/새 검사 **156 passed**. 이전 개발 중 실행 횟수와 합산하지 않는다. 한국어 후접 `EPSG:4326이다`의 정규식 경계 누락을 테스트에서 발견해 수정했다. 독립 코드 감사에서 영어 depth/height/draft 및 `10m deep` 길이를 검색 반경으로 오인하는 문제도 발견해 수정했다. 새 검사만 명시 공간범위 문맥을 요구하며 전역 quantity parser는 변경하지 않았다. 참조 객체 이름을 검색 대상으로 오인하지 않는 회귀도 포함한다.

실제 API v1에서 새 검사가 차단했지만 기존 radius 예외 wrapper가 이유를 EXECUTION_GATE로 바꾸는 문제를 발견했다. `s101_radius_execution.py`를 보완해 REQUEST_CRS/TARGET/DISTANCE_MISMATCH와 원래 native blockers·decision input hash를 보존한다. 원본 v1 응답을 덮지 않고 backend 재시작·health200 후 v2에서 검증한다.

일반 자연어 의미 동등성, 모든 source namespace 매핑, 복합 union·geometry 선택·복구의 완전한 의미 보존은 미완료다. 모호한 입력을 임의 추론하거나 계획을 수리하지 않는다. 운영 실제 API 결과는 아래에 별도 기록한다.

## 운영 실제 API v2

원본: `outputs/request_constraint_runtime_20261101_v2/`. 최종 소스 재시작 및 `/health` 200 확인 후 동일 질의/문맥으로 실행했다. `source_verification.json`에 운영 3파일의 전후 hash 일치를 기록했다. 관측 클라이언트는 SSE이며 브라우저 렌더링 검증은 아니다.

| 요청/통제 | 최종 결과 | 실제 공간 실행 |
|---|---|---|
| POINT(129.075 35.075), Wreck+Obstruction 1km | COMPLETED, 18건, 30.719초 | feature code 검증·spatial_select·snapshot receipt 완료 |
| 원질의 CRS3857, 입력점 CRS4326 | BLOCKED / REQUEST_CRS_MISMATCH, 10.516초 | execution_validation 이후 공간 SELECT 단계 진입 없음 |
| 원질의 Wreck, 입력 target Obstruction | BLOCKED / REQUEST_TARGET_MISMATCH, 9.625초 | 동일 |
| 원질의 Wreck, 입력 target Wreck+Obstruction | BLOCKED / REQUEST_TARGET_MISMATCH, 9.781초 | 동일 |
| 원질의 1km, 입력 반경 5000m | NEEDS_CLARIFICATION / CONFLICTING_RADIUS, 10.016초 | 기존 입력 parser에서 거절, 새 native Validator의 검출로 세지 않음 |

거리 의미변경 자체의 새 native Validator 검출은 위 연구 DB 무모델 replay의 WRONG_RADIUS로 확인했다. API는 raw 모델 계획을 받는 endpoint가 아니므로 입력문맥 충돌을 같은 종류의 모델 fault로 포장하지 않는다. metadata SQL과 공간 SELECT도 구분한다. 서버 전체 DB SQL 감사 로그를 추가 수집한 것은 아니며, 여기서의 실행 근거는 실제 실행 stage 계측과 native gate receipt이다.

비동기 shadow 비교는 공간 실행과 별도다. v1은 control의 `selection/score mismatch` 실패와 나머지4건 COMPLETED를 보존한 뒤 재시작했다. v2도 control은 동일 실패, 나머지4건 COMPLETED로 모두 종료했음을 각 `/api/v1/intent-comparisons/{id}`로 확인했다. `*_comparison.json` 원본을 보존했고 QUEUED/RUNNING 작업이 없는 상태에서 연구 모델 실행 자원을 넘긴다. 이 보완이 shadow 비교 오류를 수정했다고 주장하지 않는다.
