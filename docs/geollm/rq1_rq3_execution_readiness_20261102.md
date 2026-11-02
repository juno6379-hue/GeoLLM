# RQ1·RQ3 측정 준비와 새 동결 실행 조건 — 2026-11-02

> 2026-11-02 후속: 실제 개발18문항 GOLD 원자172개(선택5개 별도)의 작성·원천 연결 검증을 완료했다. `benchmark/grounding_atoms_20261102_v1` 참조. 아래의 미작성 문구는 이전 준비 상태이며, 예측 원자 전체 연결과 RQ1 수치는 여전히 미측정이다. 상세: docs/geollm/rq1_annotation_completion_20261102.md.

상태: **DRAFT / PROPOSED**. 이 문서는 기존 논문 원본·GOLD·점수를 변경하지 않는 준비 계약이다. 새 모델 실험이나 홀드아웃 평가를 실행하지 않았다. 운영 Dataset 검증·재임베딩과 논문 평가를 분리하며, 운영 자료 전환과 검증이 끝난 뒤 새 snapshot에서 전체 비교해야 한다.

## 1. 확인한 현재 근거

- `research/marine_geollm_scie/protocol/paper_metric_definitions.md`
- `research/marine_geollm_scie/evaluation/rq_metrics.py`
- 현재 완료 실행 `20261102_gold_v2_eight_k1_v6`의 `report_with_faults/summary.json`
  - SHA256 `2c9123dcd4689391b2ce7b6369fc5be84284bf05b4de0869527f61bc237fa005`
- 운영 UI 전용 `tools/scie_results_ui/rq1_grounding.py`
- 사후 조건 파일 `outputs/scie_rq_v2_audit_20261030/condition_metadata.jsonl`
  - SHA256 `19a9cfa0f025265c07bd1c57cabdf1624650727a212d2cd656bb1c0e69caddfd`

조건 라벨은 현재 GOLD 질의 18개의 query SHA와 모두 일치했다. 그러나 **AI 사후 설명 분류·DRAFT·human_approval=false**다. GOLD 내용 승인과 조건 라벨의 사전등록·독립 검수는 별개다. 기존 144답변의 AI 보조 인간 확인 이진 채점은 Semantic Grounding F1의 정답 atom 집합이 아니다.

## 2. RQ1 Table 9 — 현재 표시 가능한 것

Table 9의 열은 `Terminology condition / B1 Text-RAG Semantic F1 / B2 Ontology·KG Semantic F1 / Δ(B2−B1) / 95% CI / Strict Match 해석`으로 구성한다. 기계계약 통과율은 보조 진단으로만 별도 표시한다.

| 조건 | query hash 일치 문항 N | 현재 동등 질의군 | 라벨 상태 |
|---|---:|---:|---|
| OFFICIAL_TERM | 6 | 6 | 사후·미승인 |
| DOMAIN_KOREAN | 11 | 10 | 사후·미승인 |
| COLLOQUIAL | 2 | 2 | 사후·미승인 |
| UNSEEN_SYNONYM | 0 | 0 | 훈련·검색 사전 노출 증거 미확인 |
| MIXED — 복합 요청 | 4 | 4 | COMPOSITE_MULTI_TASK에서 파생, 사후·미승인 |

조건은 중첩되므로 N을 합산하지 않는다. `MIXED_KO_EN` 언어 혼합은 복합 작업과 다르다. 해당 라벨만 있는 `PILOT_Q4_03`은 위 다섯 조건에 임의로 넣지 않고 분류 미설정으로 공개한다. Q4 동등 표현은 같은 지리 문제이므로 독립 표본으로 합산하지 않는다.

**현재 v6에 Table 9의 Semantic F1·Strict Match·CI 계약/산출물이 없다.** 따라서 점수·차이·CI는 모두 null이다. 과거 pilot F1, Feature F1, 기계계약 통과율, AI 보조 인간 확인 이진 점수로 빈칸을 채우지 않는다. N=0 조건은 정확도 0%가 아니다.

## 3. 제안하는 grounding atom 평가계약

아래 설계는 아직 동결·실행되지 않았다. 적용 전 계약 version/hash와 예외 정책을 정해야 한다.

1. **정답 단위**: 질의별 필수 grounding atom을 `kind + canonical target/value + source/version + task_id`로 둔다. 종류는 feature, attribute, relation/operator, reference, distance/unit, evidence binding 등이며 실제 질의에 필요한 종류만 포함한다. 모든 문항에 동일 개수 슬롯을 강제로 만들지 않는다.
2. **허용 대안**: 같은 필수 atom의 대체 표현·공식 별칭·허용 capability는 미리 명시한다. 모델 결과를 본 뒤 정답을 넓히지 않는다. 하나의 필수 atom에 여러 대안이 있어도 정답 수는 하나다.
3. **예측 단위**: B1/B2의 실제 저장 답안에서 명시적으로 확인되는 주장·ID·필드만 추출한다. 평가기가 새로운 reasoning으로 숨은 의도·CRS·객체·dataset을 보충하지 않는다. 해석 불가능한 출력과 평가기 미지원은 각각 모델 실패/계측 미완료로 분리한다.
4. **매칭**: 승인된 정규화·단위변환만 적용한 일대일 매칭이다. 한 예측을 여러 정답 atom의 TP로 중복 계산하지 않는다. 과잉 확장·잘못된 source binding은 FP/FN 정책을 계약에 명시한다.
5. **누락 처리**: 실제 답안에 필요한 atom이 없는 경우는 FN이다. 정답 atom 미작성 또는 평가기 미구현은 missing이며 오답이나 정답으로 세지 않는다. 통신 실패·시간초과·JSON 실패를 분석에서 제외하지 않는다. 이들에 대한 answer-empty 판정도 동결 계약에 명시하고 원본 실패 상태를 보존한다.
6. **Strict Match**: 필수 grounding 전체 일치 및 금지된 추가 작업 없음의 이진 판정이다. 부분 F1이 높더라도 필수 작업이 빠지면 strict 성공이 아니다. grounding strict와 실행·공간·근거를 모두 포함한 EVQSR를 구분한다.

### F1 및 CI 제안

- Table 9 주 지표 후보: 조건별 atom의 TP/FP/FN을 합한 **micro F1 = 2TP/(2TP+FP+FN)**. 사례별 macro F1은 보조로 분리한다. micro/macro 선택은 새 실행 전에 확정해야 한다.
- B1/B2는 같은 case/query/GOLD/snapshot/repeat의 쌍이어야 한다. Δ는 동일 조건의 B2−B1이다.
- 95% CI는 **equivalence group을 단위로 paired cluster bootstrap**한다. 같은 그룹의 두 방법과 반복을 함께 재표집하며, micro F1은 재표집마다 TP/FP/FN으로 다시 계산한다.
- 현재 `rq_metrics.cluster_bootstrap`은 사례별 수치 차이를 평균하는 함수다. 이를 그대로 적용하면 atom micro F1의 CI가 되지 않는다. micro용 재집계 함수와 회귀검증이 필요하다. 사례별 macro F1을 택한다면 그에 맞는 분모/가중치 계약을 별도 고정한다.
- 반복은 먼저 동일 사례 안에서 집계하고 독립 표본 수를 늘리는 것으로 취급하지 않는다. bootstrap 횟수·seed·가중 방식·실패/누락·최소 그룹 수를 사전 고정한다. 기존 helper의 2,000회/seed 20261030은 참고 구현값이며 새 계약 승인으로 간주하지 않는다.
- 현재 조건은 그룹 수가 매우 작고 사후 분류이므로, 추후 산출하더라도 개발·탐색용 CI와 확인적 결론을 구분한다. UNSEEN 조건의 표본이나 CI를 합성하지 않는다.

## 4. RQ3 — 분모와 기호를 고정해야 하는 이유

`rq_metrics.spatial_gap`의 정의와 현행 v6 보고서 키를 혼동하지 않는다. 아래는 실제 구현에서 확인한 의미다.

| 지표 | 평가 의미 | 주요 분모·결측 규칙 |
|---|---|---|
| ESR | 실제 공간 실행 성공 E | 승인된 EXECUTE 적격 사례. 미시도/차단으로 확인된 실행 실패는 false, 미관측은 null |
| SCR (`rq_metrics`) | 실행과 공간 정답의 공동 성공 E∧S | 같은 EXECUTE 적격 집합. 실행 실패는 false, 성공 후 공간 미측정은 null |
| CGE (`rq_metrics`) | 실행 성공 조건부 공간 정답 P(S\|E) | 실제 성공한 실행만. 성공 0건이면 null |
| SSFR | 성공했지만 공간적으로 틀린 비율 P(¬S\|E) | CGE와 같은 성공 집합. 공간 판정 누락이 있으면 null |
| execution_correctness_gap | ESR−SCR | 같은 적격 집합·정의·완전 측정일 때만 계산 |
| EVQSR | semantic_correct ∧ plan_valid ∧ execution_success ∧ spatial_correct ∧ evidence_correct | EXECUTE 집합의 다섯 구성요소. 필수 항목 미측정이 있으면 집계 null |

**CGE는 ESR−SCR가 아니다.** CGE와 SSFR의 분모·대상·관측이 완전히 같을 때만 CGE=1−SSFR이다. 안전중단 및 입력 요청은 GIS 실행 적격 집합에 섞지 않고 별도 평가한다. HTTP 200, API COMPLETED, Validator 승인, 문서 SELECT는 공간 실행 성공의 대용값이 아니다.

### 현재 v6에서 실제 확인한 값과 한계

B3/B4/P0/H/P1 각각의 원본 보고서는 다음과 같다.

- `execution_success_all_eligible`: **0/5**, 측정 5/5.
- `joint_execution_spatial_success`: **0/5**, 측정 5/5.
- `spatial_correctness`: **null**, 측정 2/5, 미측정 3.
- `silent_spatial_failure_given_success`: **null**, 성공 실행 분모 0.
- `safe_abstention`: **0/3**, 해당 행동 계약 전체 기준.
- `execution_correctness_gap`: **0**. 두 공동 지표가 모두 0인 결과이며 신뢰성이 높다는 뜻이 아니다.

v6의 `spatial_correctness`는 원천 객체 정답 판정의 누락을 보존하는 별도 키다. 이를 `rq_metrics`의 joint SCR와 이름만으로 동일시하지 않는다. 새 계약에는 `spatial_oracle_correctness`, `joint_execution_spatial_success`, `conditional_spatial_correctness`처럼 의미를 구분한 키와 분모를 명시해야 한다. 과거 보고서는 그대로 둔다.

현재 원본만으로 새 EVQSR를 만들 수 없다. 완전한 semantic contract 및 주장별 근거 지지 검증이 없으며, 근거 문자열 존재나 source hash만으로 evidence_correct를 확정할 수 없다. 분모 0의 CGE/SSFR는 0%도 100%도 아니다.

## 5. 다음 새 동결 실행의 필수 관측

| 구간 | 필요한 실제 기록 |
|---|---|
| 입력/GOLD | case/query hash, GOLD/허용 대안 hash, 조건 라벨 version·승인/사후 여부, equivalence group |
| 의미 | 원본 답안 hash, 추출한 atom 및 원문 위치, TP/FP/FN 매칭 근거, strict 판정, 미측정 이유 |
| 계획/승인 | B3 공유 초기 계획 hash, B4/H 공유 검토 hash, P0 lossless QEC, Validator 입력/결정/사유 |
| 실행 | execution_attempted/started/tool_called/sql_executed, 도구·공간 SQL 성공/오류, 종료·timeout, 문서 조회와 GIS 구분 |
| 공간 | source-bound 객체 ID·기하/거리/관계·CRS, snapshot 및 독립 Oracle hash, 객체 중복 정책, coverage·empty/unknown 구분 |
| 근거 | 답안 claim→원문/DB 필드·버전·인용의 연결, 실제 주장 지지 검증 결과와 artifact hash |
| 비용 | 동일 repeat의 시간·토큰·도구·SQL·복구 호출 및 누락 상태 |

현재 문서의 수록 범위 밖 응답, 입력 누락 응답, 복합 부분 응답은 각자의 행동/근거 계약으로 평가한다. 전체 차단을 안전성 개선으로만 보고하지 않고 정상 요청 오차단·가용성 비용을 함께 제시한다.

## 6. 실행 순서와 완료 gate

1. 운영 추출/재임베딩·현재 receipt 게시·실제 대표/부정 질의 검증을 완료한다. 임베딩 worker가 사용하는 Ollama와 새 모델 비교를 경쟁 실행하지 않는다.
2. grounding atom·Strict Match·실패/누락·micro/macro·조건 및 cluster CI 계약을 DRAFT에서 명시 동결 가능한 상태로 확정한다. 기존 GOLD v2를 변경해야 하면 별도 version과 검증이 필요하다.
3. 운영 코드·모델 digest·예산·데이터·평가 코드·평가기준을 새 run에 동결하고, 독립 SQL/GIS Oracle 및 실제 적재 hash를 재검증한다. 현재 출력/UI 진단을 평가 입력으로 역주입하지 않는다.
4. 동일 benchmark에 B0/B1/B2/B3/B4/P0/H/P1을 새로 실행한다. B3 초기 계획/B4-H 검토 공유와 P0 무손실 컴파일을 유지한다. 운영 변경 전 v6 답안을 새 실행 결과로 재사용하지 않는다.
5. TP/FP/FN 및 E/S/근거/전체계약을 사례별로 재검산하고 미측정 수를 보존한다. 코드 결함이 있으면 원본 run을 보존하고 수정 후 새 동결 run을 사용한다.
6. 조건별 Table 9 및 RQ3 동일 분모 표·오류 유형별 분석을 생성한다. 반복·CI는 실제 관측 수와 독립 질의군 수를 함께 공개한다.
7. 홀드아웃은 이 개발 작업에 사용하지 않는다. 최종 시스템 동결 후 별도 승인·평가 gate에서만 실행한다. 현재 자료로 홀드아웃 성능이나 독립 인간 의미 정확도를 만들지 않는다.

이 문서 작성 중 실제 모델 호출·DB 갱신·기존 연구 결과 재채점은 없었다. 어댑터의 null은 구현 누락을 숨기는 표시가 아니라, 현재 해당 측정계약과 결과가 없음을 나타낸다.

## RQ3 후속 실제 개발 검증

[2026-11-02 wrong-but-executable 검증](rq3_wrong_executable_20261102.md)에서 정상minimumgeometry24/GOLD일치 대비 centroid0/24누락을 확인했다. 기존v6모델분모에합산하지 않는다. 성공0인v6 CGE/SSFR는 여전히null이며 측정불가다.
