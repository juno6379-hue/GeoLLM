# 신뢰성 판단 행렬

이 문서는 연구 평가계약과 운영 감사 요구를 정의한다. 운영 코드에서 이 registry를 import하거나 자동 활성화하지 않는다. 정책 규격 완성은 운영 구현 완료나 논문 실험 완료가 아니다.

- `production_status: null`은 미감사이며 미구현으로 단정하지 않는다. 감사 후 코드·검증 근거가 있을 때만 네 구현상태 중 하나로 분류한다.
- Primary detector는 검증할 가설이며 검출 우월성이 입증된 결과가 아니다.
- 1km는 원문 예시일 뿐 채택한 기본값이 아니다. 연구 GOLD의 특정 부산항 polygon은 운영 전체 항계 정책이 아니다.
- 원시 trace 없는 실행 필드는 null이다. 비실행 false는 완전한 관측으로 확인한다. 문서/metadata SQL은 GIS SQL과 구분한다.
- 기존 GOLD·결과는 불변 유지하며 이 30개 대표 명세를 추가할 경우 별도 benchmark/fault-set 버전과 독립 Oracle 검증이 필요하다.
- PlanStatus에는 PARTIAL이 없고 AgentStatus.PARTIAL, TaskResultStatus.SUCCESS_EMPTY가 각각 결과 계층이다(shared/schemas/agent.py). 이 enum 존재만으로 종단 전파 완료를 주장하지 않는다.

| 사례 | 요구 판단 | 검출 가설 | RQ | 운영 검증 |
|---|---|---|---|---|
| R-A1 잘못된 Feature | 의미 불일치 해결 전 실행 금지 | HYBRID | RQ1, RQ2 | NOT_AUDITED |
| R-A2 의미 과잉 확장 | 대상 범위 불일치 검토 및 실행 보류 | LLM_REVIEW_PRIMARY | RQ1, RQ2 | NOT_AUDITED |
| R-A3 다의적 해양 용어 | 집합·시설 중복 정책 해소 또는 NEEDS_USER_INPUT | HYBRID | RQ1, RQ2 | NOT_AUDITED |
| R-B1 최근접의 반경 오해 | nearest/top_k=1 유지; coverage 별도 판단 | HYBRID | RQ1, RQ2, RQ3 | NOT_AUDITED |
| R-B2 모호한 근접 표현 | 승인된 일반 정책과 provenance 또는 NEEDS_USER_INPUT | HYBRID | RQ1, RQ2, RQ5 | NOT_AUDITED |
| R-B3 선택 영역 누락 | NEEDS_USER_INPUT/MISSING_REFERENCE_GEOMETRY; GIS 미실행 | DETERMINISTIC_PRIMARY | RQ1, RQ2, RQ3 | NOT_AUDITED |
| R-B4 잘못된 기준기하 | 출처·버전·hash를 갖는 확정 polygon 사용 | HYBRID | RQ2, RQ3 | NOT_AUDITED |
| R-B5 경계 술어 미확정 | BLOCKED_CONFIG 또는 연구 UNRESOLVED_POLICY | DETERMINISTIC_PRIMARY | RQ2, RQ3 | NOT_AUDITED |
| R-B6 면 거리 계산 오류 | polygon 대 geometry 최소 지오데식 거리 | POST_EXECUTION_PRIMARY | RQ3 | NOT_AUDITED |
| R-C1 자료 공간범위 밖 | BLOCKED_DATA; result_count=null | DETERMINISTIC_PRIMARY | RQ1, RQ2, RQ3, RQ5 | NOT_AUDITED |
| R-C2 부분 자료범위 | 범위 공개 PARTIAL 또는 완전성 필수면 BLOCKED_DATA | DETERMINISTIC_PRIMARY | RQ1, RQ2, RQ3 | NOT_AUDITED |
| R-C3 오래된 snapshot | BLOCKED_DATA 또는 허용된 과거 범위만 명시 | DETERMINISTIC_PRIMARY | RQ1, RQ2, RQ5 | NOT_AUDITED |
| R-D1 FC에 없는 Feature | FEATURE_NOT_IN_CATALOGUE; 재해소 또는 BLOCKED_CONFIG | DETERMINISTIC_PRIMARY | RQ2 | NOT_AUDITED |
| R-D2 Feature에 없는 속성 | ATTRIBUTE_NOT_IN_FEATURE 차단 | DETERMINISTIC_PRIMARY | RQ2 | NOT_AUDITED |
| R-D3 CodeList 혼동 | 원천 FC identity 및 permitted_values 확인 | DETERMINISTIC_PRIMARY | RQ2 | NOT_AUDITED |
| R-D4 스키마와 실제 값 혼동 | 실제 object 값과 FC 정의/코드/locator 연결 | POST_EXECUTION_PRIMARY | RQ1, RQ3 | NOT_AUDITED |
| R-E1 단위 정규화 | 5000m 등가 변환 및 원문·변환 provenance | DETERMINISTIC_PRIMARY | RQ2, RQ4 | NOT_AUDITED |
| R-E2 잘못된 거리 | 현재 명시된 거리정책 위반 차단 | DETERMINISTIC_PRIMARY | RQ2, RQ5 | NOT_AUDITED |
| R-E3 CRS 불일치 | 승인 변환 없으면 BLOCKED_CONFIG | DETERMINISTIC_PRIMARY | RQ2, RQ4 | NOT_AUDITED |
| R-F1 도구 불가 | BLOCKED_CONFIG; 등가 fallback만 별도 검증 | DETERMINISTIC_PRIMARY | RQ2, RQ4, RQ5 | NOT_AUDITED |
| R-F2 템플릿 누락 | BLOCKED_CONFIG | DETERMINISTIC_PRIMARY | RQ2 | NOT_AUDITED |
| R-F3 스키마 변경 | SCHEMA_CHANGED/BLOCKED_CONFIG | DETERMINISTIC_PRIMARY | RQ2, RQ3 | NOT_AUDITED |
| R-F4 권한 부족 | BLOCKED_POLICY | DETERMINISTIC_PRIMARY | RQ2, RQ4 | NOT_AUDITED |
| R-G1 승인 후 계획 변경 | 승인 무효; 재검증 전 미실행 | DETERMINISTIC_PRIMARY | RQ2, RQ3 | NOT_AUDITED |
| R-H1 복합 과업 부분 완료 | 필수 네 산출물 모두 충족 전 PARTIAL | POST_EXECUTION_PRIMARY | RQ1, RQ3 | NOT_AUDITED |
| R-H2 비교 산출물 누락 | 비교 기준·결과·source scope 포함 전 PARTIAL | POST_EXECUTION_PRIMARY | RQ1, RQ3 | NOT_AUDITED |
| R-H3 하위작업 범위 불일치 | comparison_scope_compatible=false와 한계 공개 | POST_EXECUTION_PRIMARY | RQ1, RQ3 | NOT_AUDITED |
| R-I1 시설 중복 | 사전 시설 식별·dedup 정책 적용 | POST_EXECUTION_PRIMARY | RQ2, RQ3 | NOT_AUDITED |
| R-J1 객체와 근거 불일치 | 객체별 근거 별도 실패 판정 | POST_EXECUTION_PRIMARY | RQ3 | NOT_AUDITED |
| R-J2 KG를 공식 정의로 대체 | 공식 원문 edition/locator 필요 | HYBRID | RQ1, RQ3 | NOT_AUDITED |
| R-J3 근거 판 불일치 | WRONG_VERSION; 판 불일치 공개 | DETERMINISTIC_PRIMARY | RQ2, RQ3 | NOT_AUDITED |
| R-K1 의미 보존 복구 | 실행 성공과 의미 보존 모두 별도 확인 | HYBRID | RQ4, RQ5 | NOT_AUDITED |
| R-K2 복구 중 의미 변형 | semantic_preserved=false; full recovery success 아님 | HYBRID | RQ4, RQ5 | NOT_AUDITED |
| R-K3 복구로 자료 부재 우회 | BLOCKED_DATA 유지 | DETERMINISTIC_PRIMARY | RQ4 | NOT_AUDITED |
| R-K4 복구로 권한 우회 | BLOCKED_POLICY 유지 | DETERMINISTIC_PRIMARY | RQ4 | NOT_AUDITED |
| R-L1 과거를 현재로 표현 | BLOCKED_DATA 또는 과거 한계 명시 | DETERMINISTIC_PRIMARY | RQ1, RQ2, RQ3 | NOT_AUDITED |
| R-L2 필수 시간 누락 | NEEDS_USER_INPUT | DETERMINISTIC_PRIMARY | RQ1, RQ2 | NOT_AUDITED |
| R-M1 빈 결과와 실패 혼동 | SUCCESS_EMPTY; 범위와 실행 근거 공개 | POST_EXECUTION_PRIMARY | RQ3 | NOT_AUDITED |
| R-M2 결과 잘림 | total_count/returned_count/truncated/page 구분 | POST_EXECUTION_PRIMARY | RQ3, RQ5 | NOT_AUDITED |
| R-M3 숨은 기본값 | 명시조건 우선; field/value/source/policy/version 기록 | HYBRID | RQ1, RQ2, RQ5 | NOT_AUDITED |

## 적용 순서

평가계약과 production 개선은 별도 변경으로 관리한다. 연구 fault 주입은 격리 runtime에서만 수행한다. 운영 변경은 원인 재현 → 일반 정책 구현 → 정상·부정 단위검증 → 실제 API 검증 → 사용자 영향/잔여 한계 기록 순서로 승격한다. 변경 후 소스·정책·모델·snapshot hash를 새로 동결하고 8방법 전체를 재실행한다. 기존 raw를 바꿔 새 구현 결과로 사용하지 않는다.

RQ3의 spatial correctness는 독립 SQL/GIS object GOLD가 있는 범위에서만 계산한다. 범위 밖은 abstention으로 별도 평가한다. RQ4는 실행 복구와 의미 보존의 두 값 모두 참일 때만 full recovery success다. 분모·누락·미측정·오류유형·질의조건을 함께 공개한다.
