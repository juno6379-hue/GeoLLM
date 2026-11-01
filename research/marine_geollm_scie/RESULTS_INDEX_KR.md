# 논문 실험 결과 위치

기준일: 2026-11-01. 논문 연구 루트는 `D:\An_GeoLLM\research\marine_geollm_scie`이다.

| 구분 | 폴더/파일 | 현재 해석 |
|---|---|---|
| 최신 완료 v5 | [결과·한계](protocol/eight_results_v5_20261101_KR.md), [통합 보고서](runs/20261101_gold_v2_eight_k1_v5/report_with_faults/comparison_KR.md) | 144+27관측·무결성 검증 완료. LLM 의미 오류/범위 차단·독립GOLD 미완료 |
| 중단 원본 v4 | [실행 상태](runs/20261101_gold_v2_eight_k1_v4/status.json) | 144수집 후 공유 검토 gate 실패. 17문항 검토 미호출·fault미실행, 완성된 비교로 인용 금지 |
| 최신 재실행 v3 | [결과 해설](protocol/eight_results_v3_20261101_KR.md), [통합 보고서](runs/20261101_gold_v2_eight_k1_v3/report_with_faults/comparison_KR.md) | 144+27관측 완료·무결성 검증. 공통 실행 성공 v3 적용. 독립 GOLD/전체 논문 결론 미완료 |
| 최신 8방법 v2 실행 | [runs/20261101_gold_v2_eight_k1_v2](runs/20261101_gold_v2_eight_k1_v2) | 관측144+fault27 완료. 독립 GOLD/RQ 전체 결론은 미완료 |
| 보존된 v1 실패 | [runs/20261101_gold_v2_eight_k1_v1](runs/20261101_gold_v2_eight_k1_v1) | P1 18건 후 comparison10행에서 harness TypeError 중단. 완성 비교 아님 |
| 기존 K5 비교 보고서 | [runs/20261031_postfix_k5_v2/report/comparison_KR.md](runs/20261031_postfix_k5_v2/report/comparison_KR.md) | 기존 6방법, 540관측 완료. 새 8방법 GOLD v2 결과가 아님 |
| 기존 K5 원시 실행 | [runs/20261031_postfix_k5_v2](runs/20261031_postfix_k5_v2) | baselines 450행, graph_repeat_0~4 각18행. 오류·미측정 포함 원본 |
| 기존 K5 한글 해설 | [protocol/k5_results_20261031_KR.md](protocol/k5_results_20261031_KR.md) | 조건·오류·반복 해석 제한 |
| GOLD v2 동결 묶음 | [benchmark/gold_v2_immutable_20261101_v1](benchmark/gold_v2_immutable_20261101_v1) | 질문/답안계약/독립 검산/manifest. 동결은 실험 완료가 아님 |
| GOLD v2 Oracle 상세 | [protocol/gold_v2_oracle_and_paired_design_20261101_KR.md](protocol/gold_v2_oracle_and_paired_design_20261101_KR.md) | 승인된 범위·부산 polygon·독립 GIS 검산 및 한계 |
| Oracle 원시 출력 | `D:\An_GeoLLM\outputs\gold_v2_oracle_audit_20261031_v3` | 실제 연구DB SQL/GIS 검산. v1/v2 실패·차이 원본 별도 보존 |
| 신뢰성 정책·감사 | [reliability](reliability) | 운영 gap과 RQ1~RQ5 연결. 실측 점수와 구분 |
| 독립 검수 양식 | [review/20261031_independent_gold_v3](review/20261031_independent_gold_v3) | 검수자 선정됨. 독립 결과 수령·완료는 아직 확인되지 않음 |

**새 GOLD v2 8방법 관측 보고서가 생성됐다.** [결과와 제한](protocol/eight_results_20261101_KR.md), [통합 보고서](runs/20261101_gold_v2_eight_k1_v2/report_with_faults/comparison_KR.md)를 먼저 확인한다. 관측 수집 완료와 논문 검증 완료는 구분한다. 이전 K5 결과를 이름만 변경하거나 재사용하지 않는다. `results/latest` 등 과거 파일럿 폴더를 최신 8방법 결과로 읽지 않는다.

운영 수정은 [운영·연구 분리 정책](../../docs/geollm/reliability_delivery_policy.md)에 따라 별도 검증한다. 운영 버그 수정 이후 비교에는 새 source hash와 전체 재실행이 필요하다. 독립 GOLD 미수령 항목은 의미 정확도를 만들지 않고 미측정으로 남긴다.
