# GOLD v2 8방법 v5 결과와 한계

2026-11-01 22:58:01 KST에 관측 완료. 21:42:32 시작 후 약75분29초이며 모든 단계exit0이다. 8방법 각18건=144관측과 별도 오류27관측을 새로 실행했다. v4는 검토 호출 전 코드 결함으로 중단된 원본이며 결과를 재사용하지 않았다.

[통합 보고서](../runs/20261101_gold_v2_eight_k1_v5/report_with_faults/comparison_KR.md)와 [통제 오류·복구 보고서](../runs/20261101_gold_v2_eight_k1_v5/fault_report/comparison_KR.md), 각 summary.json의 조건·오류별 분모를 참조한다. 이는 기계 계약·실제 실행 평가이며 독립 인간 의미 정확도가 아니다.

## 코드 결함 수정 확인

v4의 구문 분리 IndexError가 재발하지 않았다. 주 비교17개 검토 원본과 통제9개 검토 원본이 실제 생성됐고 모두 schema 오류가 없었다. 나머지 주 비교1건은 최초 계획 오류로 검토하지 않았다. B4/H 공유 기록과 완료 gate를 통과했다. 형식과 호출 연결의 해결을 모델 의미 판단 해결로 표현하지 않는다.

## 실제 성능과 남은 오류

| 항목 | v5 결과 | 해석 제한 |
|---|---|---|
| LLM 검토 B4 오류 검출 | 오류8건 모두 정상 판정, False Ready8/8 | 형식 통과에도 의미 판정 실패 |
| P0·H 오류 차단 | 각각8/8, 정상 오차단0/1 | 작은 개발 통제집합이며 전체 일반 정확도 아님 |
| P0 차단 구성 | native Validator7건+compiler 타입 거절1건 | 모두를 native 검출로 귀속하지 않음 |
| B4·H 복구 공동 성공 | 각6시도 중3 | 명시 의미 계약과 공간 결과를 함께 만족한 비율 |
| P1 공간 실행/정답 | 각각3/5 | 성공3건은 같은 Q4 표현변형군 |
| P1 Silent Spatial Failure | 실행성공3건 중0 | 전체 시스템 무오류 주장이 아님 |
| 다른7방법 공간 실행 | 각각0/5 | B0~B2는 도구 없는 설계; 전체 답변 품질과 구분 |

P1 기계 계약 통과는8/18, B3/B4/P0/H는각2/14측정(전체18), B0/B1은0/15측정, B2는0/14측정이다. 출력 누락과 미측정은 제거하지 않았다. B0/B1/B2의 INVALID_RESPONSE는각7/6/5건이며, 초기 계획 오류1건은네분기에동일하게보존했다.

typed schema로 인자 형식을 제한해도 도구 선택·clarification·답변 의미 오류가 남았다. 공통 공간 평가5문항에서 B3/B4/P0/H는 공간 시도 자체가 없었다. 따라서 실행기 반환 상태를 공간 실행 성공으로 읽어서는 안 된다. 공통 ESR v3는 모든 방법에 같은 공간 문항·분모5를 적용하고 실제 SQL 성공과 공간 정답을 분리한다.

복구의 공동 성공3건은 고정 snapshot에서 빈 Oracle 결과와 일치한 사례라는 제한을 유지한다. 별도 개발의 비어 있지 않은3feature 엔진 통제는 모델 생성 성공이나 이 논문 cohort 점수에 포함하지 않는다. 금지된 복구 제안은 B4/H각2건이다.

**범위 차단의 잔여 실패:** P1의 전체 실제 SQL 성공 관측은4건이며, 위 ESR 대상 성공3건 외에 Q5-03도 포함된다. Q5-03은 독도 기준점으로 공간 SQL1회를 실행하고 PARTIAL/NO_EVIDENCE·returned_count0/count=null을 반환했다. 실세계0건으로 확정하지는 않았지만 범위 부족에서 실행 전에 차단해야 하는 행동은 충족하지 못했다. 이 문항은 out-of-coverage GOLD여서 공간ESR분모에서 제외되므로, ESR3/5만으로 안전중단 능력을 주장할 수 없다.

Q5-03 원본은 coverage UNKNOWN/required=false 상태에서 EXECUTION_READY를 부여했다. P1 Safe Abstention 계약은0/3이며, Q3-01/Q5-01도 미실행만으로는 요구된 coverage 사유·고지를 충족하지 못했다. 단순히 차단 건수를 늘리는 대신 서버 원천 범위의 근거와 정확한 설명을 함께 보완해야 한다.

## 검증·후속 작업

주검증은144raw receipt,27fault 계약/Oracle,281동결소스, v4보존418파일, 공통ESR·완료 gate 및 모델digest사후검사를 통과했다. `outputs/gold_v2_eight_v5_final_verification_20261101.json`에 요약했다. 원본run은 변경하지 않았으며 운영UI/feedback/dirty test를 보존했다.

별도 읽기전용 에이전트가18군 공유 초기계획·B4/H검토hash 일치, P0 lossless17/초기무효1, 검토17+9건의stop/schema, 공통분모와 위Q5-03의 실제SQL실행을 교차 확인했다.

해결된 것은 운영 revision 전달·shadow 표시 계약과 연구 검토 호출 결함이다. LLM 의미 오류, 운영coverage/canonical polygon/nearest/복합완결성, 비어 있지 않은 복구 평가, 독립 인간GOLD와 반복 검증은 남아 있다. 같은18문항의 반복 개발이므로 독립 holdout이나 일반화 성능을 주장하지 않는다. 7B후보 개발의 시간초과/부분 검출은 별도 결과이며 공식1.5b 비교에 합치지 않았다. scientific_completion·production_release_approved·rq1_to_rq5_complete는false다.
