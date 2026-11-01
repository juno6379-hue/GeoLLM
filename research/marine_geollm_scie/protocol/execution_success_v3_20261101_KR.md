# 실행 성공 공통 평가계약 v3

평가 버전은 `spatial_execution_semantics_v3`이다. 기존 v2 원본·보고서를 덮어쓰지 않고, 새 동결 조건에서 8개 방법 전체를 재실행한다. 이 문서는 정의와 검증 계획이며 신규 실험 결과가 아니다.

## 관측과 성공의 정의

모든 방법은 동일한 `execution_semantics.canonical_trace`를 사용한다. 실제 공간 도구 호출 또는 공간 SQL 제출은 execution_attempted=true이고, SQL 제출은 execution_started/sql_executed=true이다. 문서·metadata·coverage 확인 SQL은 공간 실행이 아니다. 성공한 공간 SQL도 객체·거리·공간 관계의 정답을 증명하지 않는다.

- 관측 창이 완료되고 네 실행 플래그가 명시되며 공간 SQL 제출이 없으면 execution_succeeded=false이다. Validator 사전 차단, 도구 없는 방법, 도구 호출 후 SQL 이전 차단도 같은 정의를 적용한다.
- 완료된 관측에서 실제 공간 SQL 성공·실패는 각각 true/false이다. 모든 제출의 종료 결과가 확인되어야 성공을 확정한다.
- 관측 중단, 전송 실패로 서버 실행 여부 불명, 필드 누락, 미지원 계측 범위는 null이다. 부분 로그의 실제 호출 사실 true는 보존하되 완료 성공으로 승격하지 않는다.
- 실행 성공=true이면서 SQL 제출=false이거나 도구 호출=true이면서 시도=false인 모순은 원본과 telemetry_errors를 보존하고 해당 관측을 미확정으로 처리한다. 잘못된 형식을 자동 수정하지 않는다.

P1 계측 범위는 격리 프로세스의 알려진 공간 도구·SQLAlchemy·psycopg2이다. 외부 GIS, 사전 import한 직접 connect 별칭, 미계측 드라이버는 범위 밖이다. baseline subprocess가 서버 실행을 확인하지 못하면 null이다. 범위 밖 작업이 있었다면 관측 완료로 인증하지 않는다.

## 분모와 정답 행동

전체 적격 ESR은 GOLD의 IN_SNAPSHOT_SPATIAL 및 source_bound_set_equality 문항을 모든 방법에 똑같이 적용한다. 출력 누락·형식 오류도 분모에서 제외하지 않는다. 현재 18문항 계약에서는 공간 5문항이며, 원본 답안의 형태나 실행 여부로 평가 대상 문항을 선택하지 않는다.

조건부 ESR은 위 문항 중 실제 execution_attempted=true인 경우만 분모에 넣는다. 시도 여부가 불명인 문항의 수를 별도로 공개하고 하나라도 있으면 조건부 비율도 미확정이다. 두 ESR 모두 denominator/measured/missing을 함께 보고한다. 시도 0건은 조건부 성공률 0%가 아니라 미측정이다.

영역 미입력 Q3-03의 정상 행동은 NEEDS_USER_INPUT 및 실제 미실행이다. 그 경우 실행 성공=false여도 행동 계약은 통과할 수 있다. coverage 밖 문항 역시 별도 Safe Abstention 계약으로 평가하며 공간 실행 ESR 분모에 넣지 않는다.

Spatial Correctness는 별도 객체·원천·거리 계약으로 평가한다. Silent Spatial Failure의 분모는 실제 실행 성공 문항이며, 실행 또는 공간 정답 관측이 불완전하면 비율을 확정하지 않는다. 전체 적격 ESR과 실행·공간 정답 공동 성공률의 차이를 별도로 보고한다.

Q4_01~03은 같은 `dokdo_radius_5km` 동등 질의군이다. 성공 3행을 독립 공간 문제 3종으로 해석하지 않는다. 보고서에는 공간 적격 case ID와 equivalence_group을 함께 기록한다. K1만으로 변동성이나 독립 전문가 의미 정확도를 주장하지 않는다.

## 회귀 검증

`test_execution_semantics_v3.py`는 동일 trace의 8방법 동일 점수, 관측 완료 비실행, SQL 전 차단, 누락·중단·모순, 출력 누락 시 분모 유지, 정상 clarification의 행동 통과를 확인한다. 기존 runtime·직접 DBAPI observer·보고서 테스트와 함께 실행한다. 모델 호출 및 신규 동결 실행은 이 구현 단계에서 수행하지 않는다.
