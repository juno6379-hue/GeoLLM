# 다섯 질문에 대한 현재 답변

- RQ1: 전체 의미 효과 차이 미측정. 제공된 확정 QEC 필드는 내부 승인 참조와 부분 비교할 수 있으나 전체 실행계약 정확도가 아니다. 부분 QEC 필드 측정 행수=34.
- RQ2: 승인 fault GOLD 및 H 동일오류셋 실험 없음. DRAFT 진단은 별도 표.
- RQ3: 실제 반환 ID와 일치하는 승인 snapshot/oracle이 있는 범위만 평가한다. 계획 출력에는 공간 정답률을 부여하지 않는다.

| 실행군 | 실행 / 대상 | 공간일치 / 대상 | ESR | SCR | CGE | SSFR | 동등질의군 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIVE_Q4_AFTER_LOCATION_FIX | 3/3 | 3/3 | 100.0% | 100.0% | 100.0% | 0.0% | 1 |
| LIVE_Q4_BEFORE_LOCATION_FIX | 2/3 | 2/3 | 66.7% | 66.7% | 100.0% | 0.0% | 1 |

사용자 승인 고정 원천에 대한 내부 대조이며 독립 전문가 GOLD나 holdout 결과가 아니다.
- RQ4: 독립 recovery/GOLD 측정 없음: SPR/SDR/RSC 모두 null.
- RQ5: 실측 비용만 산출. 신뢰성 향상의 추가 비용은 미측정.

숫자로 확인된 제한: 사용자 승인 AI보조 참조 18건 / 독립 전문가 승인 참조 0건, holdout 0, 계획 K=3/요구5, 원시행 216.

# final_results_summary

**진행 상태: NOT_READY — 논문 Results 완료 아님**

## 1. 무엇을 비교했는가

RQ1–RQ5, ablation, holdout 및 재현성 요구를 대조한다.

## 2. 실제 결과

원시행 216개: {"PLAN_ONLY": 90, "SEMANTIC_COMPONENT": 54, "FAULT_FIXTURE": 42, "SPATIAL_COMPONENT": 18, "GRAPH_SMOKE": 6, "LIVE_Q4_BEFORE_LOCATION_FIX": 3, "LIVE_Q4_AFTER_LOCATION_FIX": 3}. 사용자 승인 AI보조 참조 18건 / 독립 전문가 승인 참조 0건, holdout 0건, 계획반복 K=3(요구5).

- RQ1: 전체 의미 효과 차이 미측정. 제공된 확정 QEC 필드는 내부 승인 참조와 부분 비교할 수 있으나 전체 실행계약 정확도가 아니다. 부분 QEC 필드 측정 행수=34.
- RQ2: 승인 fault GOLD 및 H 동일오류셋 실험 없음. DRAFT 진단은 별도 표.
- RQ3: 실제 반환 ID와 일치하는 승인 snapshot/oracle이 있는 범위만 평가한다. 계획 출력에는 공간 정답률을 부여하지 않는다.

| 실행군 | 실행 / 대상 | 공간일치 / 대상 | ESR | SCR | CGE | SSFR | 동등질의군 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIVE_Q4_AFTER_LOCATION_FIX | 3/3 | 3/3 | 100.0% | 100.0% | 100.0% | 0.0% | 1 |
| LIVE_Q4_BEFORE_LOCATION_FIX | 2/3 | 2/3 | 66.7% | 66.7% | 100.0% | 0.0% | 1 |

사용자 승인 고정 원천에 대한 내부 대조이며 독립 전문가 GOLD나 holdout 결과가 아니다.
- RQ4: 독립 recovery/GOLD 측정 없음: SPR/SDR/RSC 모두 null.
- RQ5: 실측 비용만 산출. 신뢰성 향상의 추가 비용은 미측정.

## 3. 가장 큰 차이

성능 차이 미확정. 비용 차이는 위 RQ5 관측값만 사용하며 동일한 신뢰성을 확보했다는 가정을 하지 않는다.

## 4. 예상과 다른 결과

예상 방향을 고정하지 않았다. 정답 미확정 때문에 예상 대비 성능을 판정하지 않는다.

## 5. 오류 사례

오류 행과 timeout을 삭제하지 않고 source record에 보존했다.

## 6. 통계검정

독립 정답과 표본을 이용한 확증적 검정은 NOT_READY이다.

## 7. 논문에 쓸 수 있는 결론

현재 관측한 실행범위·비용·결측과 확보된 사용자 승인 참조 범위의 내부 대조를 기술할 수 있다. component 결과를 합쳐 full pipeline 결과로 쓰지 않는다.

## 8. 아직 주장하면 안 되는 것

P1 우월성, 한글 의도분류 전체 정확도, silent failure 감소, recovery 의미보존 및 holdout 일반화는 주장할 수 없다.
