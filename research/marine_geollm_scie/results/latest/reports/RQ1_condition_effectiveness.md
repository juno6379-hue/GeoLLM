# RQ1_condition_effectiveness

**진행 상태: NOT_READY — 논문 Results 완료 아님**

## 1. 무엇을 비교했는가

RQ1_condition_effectiveness: 원시기록을 cohort·방법별로 분리해 비교한다. scope가 다른 component를 P0/P1로 대체하지 않았다.

## 2. 실제 결과

표 RQ1_condition_effectiveness.csv 참조. 사용자 승인 AI보조 참조 18건 / 독립 전문가 승인 참조 0건. 미확정 성분은 null/NOT_READY. 사용자 승인 AI보조 참조는 독립 전문가 GOLD와 구분한다.

## 3. 가장 큰 차이

확정된 내부 대조 범위 밖의 기술 효과 차이는 아직 산출할 수 없다.

## 4. 예상과 다른 결과

예상 방향을 고정하지 않았다. 정답 미확정 때문에 예상 대비 성능을 판정하지 않는다.

## 5. 오류 사례

[{"cohort": "FAULT_FIXTURE", "method": "B4_LLM_Self_Reviewer", "case_id": "valid_control", "source_record": 2, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\validator\\validator_rows.jsonl", "status": "error", "graph_status": null, "execution_success": null, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "FAULT_FIXTURE", "method": "B4_LLM_Self_Reviewer", "case_id": "valid_control", "source_record": 4, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\validator\\validator_rows.jsonl", "status": "error", "graph_status": null, "execution_success": null, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_zero", "source_record": 13, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "NEEDS_CLARIFICATION", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_zero", "source_record": 14, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "NEEDS_CLARIFICATION", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_zero", "source_record": 15, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "NEEDS_CLARIFICATION", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_over_limit", "source_record": 16, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "BLOCKED", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_over_limit", "source_record": 17, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "BLOCKED", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}, {"cohort": "SPATIAL_COMPONENT", "method": "P_radius_component", "case_id": "spatial_over_limit", "source_record": 18, "source_file": "research\\marine_geollm_scie\\runs\\20261029_pilot\\spatial\\spatial_rows.jsonl", "status": "BLOCKED", "graph_status": null, "execution_success": false, "expected_behavior": null, "classification": "NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT"}]

모든 오류 행의 원본 포인터는 metrics/error_examples.json에 보존했다.

## 6. 통계검정

paired_diagnostic_statistics.json에 계획 출력 JSON schema 및 latency의 관측 검정을 기록했다. 과학적 정답 검정은 NOT_READY. 반복을 사례로 중복 계산하지 않았고 equivalence group을 bootstrap 단위로 사용했다. K=3이며 요구 K=5와 다르다. 표본군이 작고 사후 조건 라벨이므로 확증적 검정이 아니다.

## 7. 논문에 쓸 수 있는 결론

현재 관측한 실행범위·비용·결측과 확보된 사용자 승인 참조 범위의 내부 대조를 기술할 수 있다. component 결과를 합쳐 full pipeline 결과로 쓰지 않는다.

## 8. 아직 주장하면 안 되는 것

P1 우월성, 한글 의도분류 전체 정확도, silent failure 감소, recovery 의미보존 및 holdout 일반화는 주장할 수 없다.
