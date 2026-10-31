# K5 반복 비교 결과 — 2026-10-31

**20:44:50 KST(11:44:50 UTC)**에 전체 관측이 완료됐다. 실제 run은 runs/20261031_postfix_k5_v2이며 raw와 보고서를 보존한다.

## 완료 검증

B0–B4 450행(18문항×5방법×5반복), P90행(18문항×5반복), 총540행. 기대 case/method/repeat 집합, 원시hash, 고정 소스246파일·snapshot/profile·모델digest, P각회 초기화85호출 성공을 재검증했다. 부모·자식 프로세스 및 연구worker/proxy 종료를 확인했다. 전체 의미 실험 완료를 뜻하지 않는다.

P Qwen 생성50/50 HTTP200, 호출3.237~23.038초. 사례 embedding100/100 반환 및 초기화embedding420회 반환. P 상태는 COMPLETED50/PARTIAL20/NEEDS_CLARIFICATION20이며 정확도가 아니다. Baseline 응답은 schema completed420/invalid_response28/HTTP500 error2다.

## 공통 기계 계약 검사

| 방법 | 90관측 중 통과 | 미충족 | 미측정 포함 | 16군집 중 완전측정군집 | 측정군집 평균 |
|---|---:|---:|---:|---:|---:|
| B0 |2|48|40|10|0.04|
| B1 |3|47|40|10|0.06|
| B2 |4|46|40|10|0.08|
| B3 |2|48|40|10|0.04|
| B4 |4|46|40|10|0.08|
| P |35|25|30|10|0.50|

각문항5회부터 집계하고 독도 동등표현3개는 하나의 군집으로 묶었다. 540행은 독립540사례가 아니다. 표의 값은 출력 필드·근거binding 등 기계계약 검사이며 전체 의미 정답률/승률이 아니다. 군집별 측정·결측 대상을 고려해야 하며 단순 모델 우열로 해석하지 않는다.

P는 매회7통과/5미충족/6미측정포함으로 12측정 문항의 통과 여부가 바뀌지 않았다. B0/B1/B2/B3/B4는 각각1/3/2/1/1문항에서 검사 통과 여부가 바뀌었다. 결과가 반복돼도 옳다는 증거는 아니다. P 미충족5문항은 등대 정의, 등대 색상 속성, 제한구역 코드, 영어 Wreck 속성, 등대와 부표 구분이다. 요구 객체/기하/정의/원천binding 또는 attribute_binding_contract가 미충족이다. 실제 답변의 의미 오류와 기계 필드 미충족은 별도 원문 검토로 구분해야 한다.

사례별 지연 평균·표준편차·최소최대는 report/case_repeats.jsonl에 있다. P의 PILOT_Q2_01은6.63~74.05초로 큰 변동이 남는다. 서비스전체 SLO가 아니다.

## 오류와 해석 제한

- B1 row157/repeat1 및 row433/repeat4 HTTP500은 서버 로그와 일치. 내부 원인 미상이며 원본 입력·옵션으로 별도 재현한다. 성공한 재현으로 실패 원본을 대체하지 않는다.
- 20:07~20:19 KST 전후 운영 Dataset 원본hash/DB/lexical 감사가 병행됐다. 추가모델호출은 없지만 CPU/IO영향과 두번째500의 인과관계는 미확정이다. 지연 비교의 교란요인으로 남긴다.
- baseline seed42~46, P기존옵션/fresh process이며 동일계산예산·순서무작위 조건이 아니다. 운영 기본prior2.5초가 아니라 연구180초 조건이므로 운영 SLA로 전용하지 않는다.
- 독립GOLD 검수 결과 미수령, semantic_accuracy=null. 기존18은 노출된 개발사례이고 검수후에도 holdout이 아니다. 독립holdout/통제ablation/recovery 실험은 미완료다.

## 후속

운영 Dataset의 SSE 최종답변·Qwen인용·semantic 검색 및 공간오류를 연구와 분리한 outputs/dataset_live_followup_20261031_v1에서 점검한다. 독립GOLD가 오면 새 참조버전으로 별도재채점한다. 연구 원시run과 이번보고서를 소급수정하여 좋은 결과로 만들지 않는다.

원시 비교보고서: research/marine_geollm_scie/runs/20261031_postfix_k5_v2/report/comparison_KR.md
검증기록: 같은run/completion_gate_audit.json

## 별도 오류 재현

outputs/k5_http500_reproduction_20261031: 원본 두 입력/옵션 각1회, 고정digest, timeout240초/재시도0. 두건 HTTP200/계획스키마 통과(74.831/87.474초). 최초500 원인미상 유지, 원본450행hash불변. 재현성 없는 일시실패를 해결완료로 표현하지 않는다.
