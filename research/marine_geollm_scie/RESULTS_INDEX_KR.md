# 논문 실험 결과 위치

기준일: 2026-11-02. 논문 연구 루트는 `D:\An_GeoLLM\research\marine_geollm_scie`이다.

| 구분 | 폴더/파일 | 현재 해석 |
|---|---|---|
| 최신 완료 v6 | [결과·한계](protocol/eight_results_v6_20261102_KR.md), [통합 보고서](runs/20261102_gold_v2_eight_k1_v6/report_with_faults/comparison_KR.md) | 144+27·무결성/교차검증 완료. Q5-03 미실행 개선, P0/H 정상 오차단1/1·P1 ESR0/5·공간정답3미측정. 전체 신뢰성 개선 주장 불가 |
| 이전 완료 v5 | [결과·한계](protocol/eight_results_v5_20261101_KR.md), [통합 보고서](runs/20261101_gold_v2_eight_k1_v5/report_with_faults/comparison_KR.md) | 144+27관측·무결성 검증 완료. LLM 의미 오류/범위 차단·독립GOLD 미완료 |
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
| AI 사전검토 A/B·합의 제안 | [검토 안내](review/20261102_gold_v2_ai_prereview_v1/검토안내_KR.md) | GOLD v2·원본 근거 연결 18사례. 사용자 검토 대기, 독립 인간 검수 미완료 유지 |

**최신 GOLD v2 8방법 v6 관측 보고서를 검증했다.** [결과와 제한](protocol/eight_results_v6_20261102_KR.md), [통합 보고서](runs/20261102_gold_v2_eight_k1_v6/report_with_faults/comparison_KR.md)를 먼저 확인한다. 관측 수집 완료와 논문 검증 완료는 구분한다. 이전 K5 결과를 이름만 변경하거나 재사용하지 않는다. `results/latest` 등 과거 파일럿 폴더를 최신 8방법 결과로 읽지 않는다.

운영 수정은 [운영·연구 분리 정책](../../docs/geollm/reliability_delivery_policy.md)에 따라 별도 검증한다. 운영 버그 수정 이후 비교에는 새 source hash와 전체 재실행이 필요하다. 독립 GOLD 미수령 항목은 의미 정확도를 만들지 않고 미측정으로 남긴다.

## 2026-11-02 승인 GOLD 파생 재채점

- AAA·BBB 검수 완료: 사용자 확인, 합의/승인일 2026-11-02. 기존 동결 manifest는 원본 이력으로 보존.
- [144답변 재채점](review/20261102_approved_gold_rescore_v1/재채점_결과_KR.md): 승인 GOLD 과업 충족 13/144, 미충족131, 신규 판정29. 인간 의미 정확도가 아닌 별도 과업 지표.
- [승인 기록](review/20261102_approved_gold_rescore_v1/approval.json), [조건별 집계](review/20261102_approved_gold_rescore_v1/summary.json). 기존 v6 실행 결과와 별도이며 새 모델 실행이 아님.

## 홀드아웃·인간 답변 채점 준비 (2026-11-02)

- [최종 동결 후 평가 계획](protocol/holdout_and_human_scoring_20261102_KR.md): 홀드아웃18/RQ2 12/RQ4 8 준비, 평가 미실행.
- [인간 답변 채점 안내](review/20261102_answer_semantic_review_v1/채점안내_KR.md): AAA·BBB 각144 입력양식, 실제 채점0/144. GOLD 승인은 기존 기록 유지.
- 연구 UI의 독립 홀드아웃·인간 답변 채점 메뉴에서 준비 상태와 양식을 확인한다. 운영·개발 자료와 별도이며 새 성능 결과가 아니다.

## 제출 답변 판정 반영 (2026-11-02)

- [사람이 확인한 AI 보조 채점 결과](review/20261102_human_confirmed_assisted_results_v1/결과_KR.md): 각144건 완료, 의미27/144·공동16/144. 독립 두 인간 검수는 확인되지 않았으며 원본 v6 지표와 별도.

## RQ1 GOLD 원자 주석 — 2026-11-02

[18문항 사례별 주석표](benchmark/grounding_atoms_20261102_v1/annotation_KR.md): 필수172·선택5원자 작성/원천 연결 검증 완료. 새 인간 검수 완료 주장은 하지 않는다. B1/B2 원문36개 사전주석과 실제 Semantic F1·CI 측정은 구분한다. [현재 완료와 남은 측정 단계](../../docs/geollm/rq1_annotation_completion_20261102.md).

## RQ2 목표 오류 코드 사후 진단 — 2026-11-02

[원시 사유 대조](../../docs/geollm/rq2_target_diagnosis_20261102.md): B4 0/8, P0/H 8/8의 binary 결과와 목표 코드 대응을 분리. 같은 수치이나 subtype진단/일반화 성능이 아니다. 각오류N1·정상control1, compiler1/native7·정상오차단1/1을 공개한다. [새 동결 지표계약](protocol/rq2_target_fault_contract_20261102_KR.md).
