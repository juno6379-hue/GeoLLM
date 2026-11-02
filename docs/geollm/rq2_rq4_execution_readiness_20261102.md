# RQ2·RQ4 실측 확인과 다음 동결 실행 준비

2026-11-02. 현재 실행은 하지 않았다. 운영 Dataset 재임베딩이 진행 중이며 추가 Ollama 호출·연구 DB 변경·홀드아웃 사용을 금지한다. 아래는 기존 **20261102_gold_v2_eight_k1_v6** 원본을 읽어 확인한 사실과 다음 실행에서 보완해야 할 계약이다. 기존 raw 결과·GOLD·점수를 바꾸지 않는다.

> 후속: [목표 오류 코드 사후 진단](rq2_target_diagnosis_20261102.md)을 추가했다. Binary와 사후 target-code hit를 분리하며 전자는0/8·8/8·8/8, 후자도같다. 이는 기존에 사전등록한 지표가 아니며 세부 오류유형 정확도는 미측정이다. 아래 계약 부족 설명은 당시 상태로 보존한다.

## 현재 비교 단위와 원본 검증

- `runs/20261102_gold_v2_eight_k1_v6/faults/rows.jsonl`: 통제 오류 8종 + 정상 control 1개 × B4/P0/H = **27관측**.
- 9개 case마다 3방법이 하나의 `initial_plan_sha256`, 동일 `expected_invalid`, 동일 `fault_contract_sha256`를 사용했다. B4/H의 `review_artifact_sha256`도 각 case에서 같았다. 실제 9개 그룹 전부 확인했다.
- B4=LLM Review, P0=Deterministic Validator, H=Hybrid. `predicted_invalid`는 common execution floor 이전의 이진 검출이다.
- Table 10/12 집계 180개 값·분모를 기존 `report_with_faults/summary.json`과 대조했다. 모두 같았다. 별도 원래 `evaluation/rq_metrics.py::fault_detection(diagnostic=True)`의 Recall/FR/FB 9개 값과도 일치했다.
- `tools/scie_results_ui/paper_tables.py`는 선택된 run의 summary/faults/manifest만 읽는다. 과거 pilot 결과를 대체 입력으로 사용하지 않는다. `rq_metrics.py`와 `paper_metric_definitions.md`는 정의·해시 참조용이며 그 파일의 과거 점수를 읽지 않는다.

## RQ2 현재 실측

| 방법 | 오류 invalid 검출 Recall | False Ready | 정상 control False Block |
|---|---:|---:|---:|
| B4 | 0/8 | 8/8 | 0/1 |
| P0 | 8/8 | 0/8 | 1/1 |
| H | 8/8 | 0/8 | 1/1 |

오류 유형은 unit, geometry, crs, source, numeric, wrong_feature, semantic_expansion, semantic_distance다. 유형별로 각 방법 1관측뿐이다. 정상 control은 별도 집합이므로 각 오류 유형의 False Block 분모는 0이며 0%라고 표시하지 않는다.

이 Recall은 **invalid/ready 이진 판정**이다. 올바른 오류 원인을 찾아냈다는 다중 클래스 Recall은 아니다. 특히 운영 coverage 미승인 때문에 정상 control도 차단된 P0/H를 두고 모든 개별 오류 원인 진단이 완벽하다고 해석하지 않는다. 현재 known fault별 정답 사유와 detector의 실제 사유를 대응시키는 별도 계약이 부족하다.

다음 동결의 RQ2 원시 필드:

- `case_id`, `repeat_id`, `seed`, `fault_family`, `fault_id`, `expected_invalid`, `expected_fault_codes`, `severity`, `recoverable`, `authorization_context`.
- 공유 입력 `plan_sha256`, `source_snapshot_sha256`, `coverage_contract_sha256`, `benchmark_sha256`, 모델 digest·prompt·budget·code hash.
- `predicted_invalid`, `detected_fault_codes`, `detector_scope`, 검출 원시 응답 및 parser 오류, 검출기 latency/token, 공통 floor 적용 전후 판정 각각.
- 정상 control은 동일한 범위·권한 원천에서 실제 실행 가능한 정상 계약으로 검증한다. 연구 scope 선언을 운영 APPROVED로 강제 승격하지 않는다. 운영 승인 부재로 차단된 control은 환경 범위 제한과 False Block을 모두 공개한다.
- 이진 Recall과 **target-fault-code Recall**을 별도 측정한다. 누락 예측을 분모에서 제외하지 않는다.

## RQ4 현재 실측

| 방법 | 기존 계약 적격 N | 실제 시도 N | 실행 복구 성공 | Task tuple 보존 | Task tuple drift | 실행·보존·공간 공동 성공 |
|---|---:|---:|---:|---:|---:|---:|
| B4 | 6 | 6 | 5/6 | 4/6 | 2/6 | 3/6 |
| P0 | 0 | 0 | 산출 불가 | 산출 불가 | 산출 불가 | 산출 불가 |
| H | 6 | 6 | 0/6 | 4/6 | 2/6 | 0/6 |

P0는 현재 계약에서 복구 기능이 없어 `recovery_eligible=false`다. 같은 6개의 복구 가능 오류를 P0에 새 분모로 적용해 기존 결과를 재채점하지 않는다. 다음 계약에서는 **GOLD의 공통 복구 가능 집합**과 **방법의 복구 기능 가용성/시도 여부**를 분리해야 한다.

복구 가능 6유형: unit, crs, numeric, wrong_feature, semantic_expansion, semantic_distance. geometry/source는 명시 필수 입력·원천이 없으므로 자동 복구 대상이 아니다. 정상 control도 복구 성공 분모에서 제외한다. 현재 fault set에는 별도의 권한 거부 사례가 없으므로 권한 안전 중단 성능을 주장하지 않는다.

B4의 복구 후 공간 correctness는 6시도 중 5측정/1미측정, H는 0측정/6미측정이다. 따라서 공간 correctness 자체는 null이며 미측정 값을 false로 바꿔 평균하지 않는다. 실행 실패를 명시하는 **joint recovery 0/6**과 공간 correctness 미측정을 혼동하지 않는다. `semantic_preservation`은 명시 task tuple 비교이며 독립 인간 자연어 의미 검수가 아니다.

다음 동결의 RQ4 원시 필드·계약:

- `gold_recovery_eligible`, `method_recovery_supported`, `recovery_attempted`, `repair_attempt_index`, `max_repair_attempts`, `repair_policy_version`.
- 현재 한 번의 bounded review 흐름을 유지한다면 `max_repair_attempts=1`을 명시하고 첫 시도를 `repair_attempt_index=1`로 기록한다. 다회 복구가 필요하면 예산·재시도 규칙을 새 프로토콜로 사전 고정한다.
- 각 시도 전후 `plan_hash`, 원래 task tuple, `reference_geometry_hash`, feature/operator/distance/CRS/source/output 계약, **필드별 변화 목록**, LLM 원문·결정론 수정 기록.
- `execution_attempted`, `execution_started`, `tool_called`, `sql_executed`, `execution_success`, 반환 object IDs·geometry/source hash·oracle hash, post-validation 결과.
- `semantic_preservation`/`semantic_drift`의 판정 범위와 판정 근거. Task tuple 기계 판정과 인간 자연어 의미 판정을 별도 필드로 둔다.
- `first_repair_success`, `recovery_success_all_eligible`, `recovery_success_given_attempt`, `joint_recovery`, `recovered_spatial_correctness`의 분모를 각각 고정한다.
- `escalated`, `escalation_reason`, `escalation_target`, 사용자 추가입력 요청/권한 차단/자료 부재/전문가 검토를 구분한다. 단순 BLOCKED를 escalation이나 안전 중단 성공으로 추정하지 않는다.
- **Safe Abstention 별도 집합**: 자료·권한·필수 geometry 부족이면 공간 실행 4필드 false, 요청한 한계 설명, 결과 0건으로 오인시키지 않음, 허용된 문서 부분응답 여부까지 판정한다. 안전 중단을 자동 복구 성공에 합산하지 않는다.

## Table 10–14 표시와 미측정

- Table 10: 오류 유형별 binary Recall/False Ready/False Block. 오류별 N=1, control 분모를 공개한다.
- Table 11: 원본 ESR, 관측 Spatial Correctness, 실행·공간 공동 성공, CGE, SSFR, 원본 gap을 분리한다. **CGE=P(Spatial correct | Execution success)**로 `rq_metrics.spatial_gap` 정의를 따른다. 완전한 성공 집합에서만 1−SSFR이며 성공 분모 0이면 산출 불가다. 원본 gap은 ESR−joint_execution_spatial_success다.
- **EVQSR=S∧P∧X∧G∧E**는 기존 공식 정의가 있으나 동일 적격 사례의 5개 boolean 관측이 완비되지 않아 null이다. machine contract pass나 인간 의미 점수만으로 대체하지 않는다.
- Table 12: 위 실제 복구 관측. First-repair·escalation·최종 safe-abstention 전용 판정은 미계측 null이다.
- Table 13: 실제 P1 모듈 제거 실험이 없어 5개 제거 조건은 미실행이다. B0–H 방법 비교를 ablation으로 전용하지 않는다. Semantic/Schema/Spatial/Runtime/Evidence 5종 오류 매핑도 사전 계약 없이 임의 분류하지 않는다.
- Table 14: 18개 주 질의 비용과 별도 fault FR/FB의 모집단을 분리한다. 원본 파일 SHA를 답변 provenance completeness로 대체하지 않는다. B4/H 공유 review 비용을 독립 호출 비용으로 더하지 않는다.
- K1·동일 의미 반복 표현이라는 제약을 유지한다. paired Δ/CI는 동일 case/동등군·seed 짝을 고정한 반복 관측과 사전 통계 계약을 갖춘 뒤 계산한다.

## 실행 준비와 명령

현 시점에는 다음 중 **읽기 전용 검사만 실행했다**.

```powershell
.venv/Scripts/python.exe -m pytest tools/scie_results_ui/tests/test_paper_tables.py -q -p no:cacheprovider
```

10개 테스트 통과: 오류/정상 분모 분리, 누락 포함, 공동 복구 vs 실행만 성공 구분, 미측정 공간 결과, CGE 의미, unrun ablation, 원본 불변, 경로 이탈·중복 관측 차단. UI는 기존 원본을 읽는 파생 표시이며 새 논문 실험이 아니다.

추가 원시 필드 구현·회귀검증·운영 임베딩 및 API 보완이 끝나고, 모델/소스/데이터/계약을 새로 동결한 뒤 전체 8방법을 다시 실행한다. 다음은 **미실행 명령 템플릿**이며 이름만 바꾸어 현재 상태에서 실행하면 신규 RQ 필드가 자동 생기는 것이 아니다.

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.supervise_eight --output research/marine_geollm_scie/runs/<새_전체_run_id> --snapshot-output outputs/<새_snapshot_id> --include-faults
```

supervisor의 새 경로·단일 worker·모델 digest·DB snapshot·공유 plan/review·lossless QEC·완료 gate를 유지한다. v6나 과거 run에 덮어쓰지 않는다. 홀드아웃은 개발·계약 조정에 사용하지 않고 최종 시스템 동결 후 별도 평가로만 실행한다.
