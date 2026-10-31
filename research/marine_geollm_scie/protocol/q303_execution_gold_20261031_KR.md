# Q3-03 입력 누락 GOLD와 실제 실행 관측

사용자 지시에 따라 Q3-03을 공간 객체 정답 집합이 아니라 필수 입력 누락 시 올바른 비실행 행동으로 평가한다. 별도 계약은 `benchmark/q303_behavior_v1.json`이다. 기존 frozen_v5와 K5 원본·점수는 변경하지 않았다. 사용자 승인 계약이며 독립 전문가 검수 완료를 뜻하지 않는다.

- semantic GOLD: Wreck / intersects. QEC: selected_geometry REQUIRED.
- 기대 행동: NEEDS_USER_INPUT / MISSING_REFERENCE_GEOMETRY / 영역 지정 요청.
- 운영의 NEEDS_CLARIFICATION과 AOI_REQUIRED는 평가 어댑터에서 위 상태·사유로 명시적으로 매핑한다. 운영 enum 자체는 바꾸지 않는다.
- execution_attempted, execution_started, tool_called, sql_executed 모두 false가 기대값이다. 요청 문구만으로 false를 채우지 않는다.

## 관측 구현과 범위

연구용 ExecutionObserver를 model_graph_session의 실제 ainvoke 전후에 설치했다. 전용 순차 worker에서 공간 Agent 진입, 공간 도구 함수 진입과 SQLAlchemy DBAPI 제출을 수동 변경 없이 관측한다. Python 프로파일과 SQLAlchemy 이벤트를 사용하며 모든 스레드를 포함한다. SQL 본문·파라미터는 저장하지 않는다.

- execution_attempted: 공간 Agent/도구 진입 또는 SQL 제출이 있었음.
- tool_called: execute_spatial_tool 함수에 진입했음. 입력 검증에서 차단되더라도 호출 자체는 true.
- execution_started: DB 실행 제출 단계에 도달했음. 결과 성공을 의미하지 않는다.
- sql_executed: SQLAlchemy before_cursor_execute 이벤트 발생. 실패한 SQL도 true. 공간 SQL에 한정하지 않은 보수적인 전체 SQL 관측이다.
- 요청 ID, 시작·종료 이벤트와 monotonic timestamp, observation_complete를 보존한다. 중단·예외에서는 관측된 true만 유지하고 나머지는 null이다. 기존 기록에 필드가 없으면 null이다.

범위 제한: 직접 DBAPI·외부 GIS 서비스·자식 프로세스는 이 관측기의 지원 대상이 아니다. 그런 실행 경로를 도입한 경우 별도 계측과 동결 범위 검증이 필요하다. 이 관측기만으로 임의의 모든 GIS 구현에 대한 비실행을 보증하지 않는다. 이번 진단은 네트워크가 차단된 전용 컨테이너의 기존 그래프 조기 입력 gate 경로다.

## 실제 검증

- 연구 단위/기존 평가/모델 profile 회귀: **31 passed**. 빈 관측과 누락 기록 구분, 스레드 내 실패 SQL 포착, 도구 진입 후 미실행, 중단 시 null, 기존 행 소급 false 금지를 확인했다.
- 실제 production graph를 별도 `docker-backend` 컨테이너에서 실행했다. 네트워크 none, 모델 비활성, .env 마스킹, 소스 읽기 전용, feedback/log tmpfs. 웹 프로세스·운영 코드는 변경하지 않았다.
- 원본: `outputs/q303_execution_audit_20261031_v1/observation.json`, stdout.log, stderr.log. 요청 ID `6f236c1d-3a51-44fc-84a6-e3c7fae74d57`.
- 실제 결과 NEEDS_CLARIFICATION / AOI_REQUIRED / 영역 요청. 관측 완료, 네 실행 필드 모두 false. 시작·종료 외 도구/SQL 이벤트 0. 행동 진단 **7/7 통과**. 전체 의미 정확도나 모델 비교 점수가 아니다.
- 초기 graph import의 embedding 연결 거부는 네트워크 차단 조건에 따른 제한이며 로그에 보존했다. 요청 관측 구간과 import 구간을 구분한다. 모델 활성 조건과 동등한 실험이 아니다.
- 실제 gate 응답은 Wreck/intersects 의미 필드를 완전하게 구조화하지 않으므로 semantic GOLD 채점은 완료로 선언하지 않는다. 이번 검증은 행동·실행 로그에 한정된다.

## 다음 실행

새 계약과 관측 코드로 새 동결 profile/run을 만든 뒤 모델 활성 조건에서 재검증한다. 현재 model_graph_session은 18문항 전체 원시 행에 execution_observation을 기록한다. 새 Q3-03 계약은 별도 제공하며 기존 18문항 frozen 계약을 자동 교체하지 않는다. 재채점은 새 출력 경로에서 수행한다. B0–B4의 실행 관측도 동일한 정의·계측 범위로 맞춘 뒤 비교하며, 기존 receipt만으로 새 관측 필드를 생성하지 않는다.

Q3-01의 전체 등대 최근접과 Q3-02의 부산항 포함 집합은 별도 공간 원본·시설 중복·경계 정책 확정 및 정답 계산이 필요하다. Q3-03 행동 GOLD 확정으로 이 두 문항까지 완료된 것은 아니다.
