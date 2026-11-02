# RQ2·RQ4 확장 개발 계약 — 모델 실행 전 고정

## 분리 원칙

기존 GOLD v2, 기존 8-fault cohort와 원본 실험은 변경하지 않는다. 새 개발 계약은 `fixtures/rq2_rq4_expanded_20261103_v3`이며 v1/v2 준비 원본도 보존한다. 홀드아웃을 읽거나 개발에 이용하지 않는다. 새 코드·입력·Oracle·모델을 함께 동결한 Development K1에서 실행한다. 실제 모델 호출 전까지 정확도·모델 복구율은 미측정이다.

## RQ2 입력과 분모

서로 다른 원천 Wreck 기준점 3개에서 11종 오류를 각각 구성했다. 기존 unit/geometry/crs/source/numeric/wrong_feature/semantic_expansion/semantic_distance에 **wrong valid attribute**, **evidence mismatch**, **unselected-reference ambiguity**를 추가했다. 각 fault의 정상 입력을 함께 보존한다. 총 fault 33, clean 36, case 69이며 B4/P0/H 207행이다.

`expected_fault_codes`, `fault_subtype`, `initial_plan_sha256`, `clean_plan_sha256`, `changed_paths`, query/context를 호출 전에 고정한다. 두 정상 S-101 attribute `valueOfSounding`과 `waterLevelEffect`의 치환을 검사한다. 지명 의미 모호성 전체를 검증한 것이 아니라 두 명시 기준점 미선택이라는 모호성 사례다. 부정 계획에서 geometry를 제거한 경우 정상 counterpart는 clarification이며 SQL을 실행하지 않는다.

같은 base의 변형과 반복된 정상 입력은 독립 표본이 아니다. 유형별 N=3은 개발 진단 수준이다. paired clean 결과, exact query/context/plan 중복을 제거한 정상 오차단 분모, 중복 clean verdict 불일치를 별도로 공개한다. 중복 입력의 verdict가 다르면 마지막 행을 임의 선택하지 않고 그 unique-control 결과를 null로 남긴다. 통계 bootstrap은 base scenario로 묶어야 하며 3개 cluster로 강한 일반화를 하지 않는다.

`expected_behavior`, `execution_eligible`, `binary_diagnosis_eligible`, `false_block_eligible`를 사전에 고정한다. 정상 clarification 6사례는 실행 불가가 올바른 입력이므로 binary·False Block 분모에 넣지 않는다. 정상 실행 가능 clean30사례만 paired False Block 분모다. 원시 native readiness/invalid 판정은 보존하지만 이 값만으로 의도 오류나 올바른 추가입력 행동을 증명할 수 없으므로 별도 Safe Abstention은 null이다. 원시207관측 중 진단대상189행, 행동 미측정18행을 구분한다.

Binary Recall과 Target-fault-code Recall을 분리한다. 정상/이상 verdict만 맞고 다른 원인으로 차단한 경우 목표 코드 검출은 실패다. 명시 false verdict는 목표 검출 false이고, 호출/코드 관측 누락은 null이다. B4는 새 구조화 응답의 `detected_fault_codes`, P0는 compiler/native blocker의 원문 코드, H는 두 최초 진단을 사용한다. 복구 결과에서 최초 코드를 역추론하지 않는다. 예상 코드는 reviewer prompt나 native validator 입력에 넣지 않는다. 전체 코드 어휘와 공개 계약 설명만 제공한다.

새 review schema는 `expanded_fault_review_v1`, 모델 호출 1회/오류 입력, 기존 768 output tokens·180초·temperature0.2·8192 context·재시도0 조건을 유지한다. JSON 절단·초기 verdict 모순은 실패/미관측으로 보존한다. 모든 base 및 정상 대조에 같은 reviewer 조건을 적용한다. P0는 기존 lossless compiler/native Validator를 사용하며 새로운 정답 기반 검사기를 넣지 않는다. 현재 native 경로의 attribute/evidence 슬롯 검사가 미지원이면 실제 미검출로 남는다.

## RQ4 non-empty Oracle

실제 연구 DB `scie_model_v3`의 고정 S-101 관계를 READ ONLY REPEATABLE READ와 source hash guard로 조회했다. 독립 Oracle는 executor의 `ST_DWithin` 템플릿 대신 `ST_Distance <= radius`를 사용하며 모든 객체 ID·geometry·geometry SHA·거리·속성을 저장한다. 같은 PostGIS 엔진의 독립 SQL이며 독립 GIS 엔진이나 인간 검수는 아니다.

|Base|기준 원천 ID|반경|Oracle 객체 수|
|---|---|---:|---:|
|WRECK_A|524189|250m|4|
|WRECK_B|560060|750m|5|
|WRECK_C|560063|1500m|4|

3개 정상 native 승인과 실제 executor 반환 ID가 Oracle에 일치했다. typed unit fault의 초기 거절→사전 명시된 clean fixture→실제 object set 복원도 개발 계약으로 확인했다. 이 clean fixture는 **모델 recovery 성능이 아니다**. 모델 실행에서는 공유 LLM repair를 B4가 실행하고 H가 native 재검증 후 실행한다. 회복 가능한 fault 24개/방법이며 P0에는 복구 추론을 추가하지 않는다. geometry/source/ambiguity는 자동 보완 금지, 복구 분모 제외다.

Recovery Success, Spatial restoration, Semantic preservation, Joint success를 별도로 기록한다. 보존 판정은 source/feature/CRS/reference/distance/relation 및 top-level attributes/evidence refs의 고정 task tuple이다. 자유 자연어의 전체 의미 보존으로 주장하지 않는다. 실제 객체 속성 내용의 올바른 설명이나 근거 본문 entailment를 이 tuple 검사로 대체하지 않는다. Oracle empty는 제외, 누락은 미측정이며 성공률을 만들지 않는다.

## 실행과 검증

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.expanded_fault_runner --contract-dir research/marine_geollm_scie/fixtures/rq2_rq4_expanded_20261103_v3 --profile <new_frozen_profile> --benchmark <frozen_gold_v2> --output <new_run>/expanded_faults --execute
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.expanded_fault_runner --contract-dir research/marine_geollm_scie/fixtures/rq2_rq4_expanded_20261103_v3 --report-run <new_run>/expanded_faults --output <new_run>/expanded_fault_report
```

`--execute` 없이는 모델을 호출하지 않는다. 계약 manifest와 raw 각 행/shared review 해시를 보고 단계에서도 검증한다. 새 snapshot manifest가 생기면 6관계 SHA/rows/columns 전부 동일한 데이터 lineage bridge를 명시하고, 새 코드/모델 동결 gate는 별도로 유지한다. 정상 대조 실패나 원본 hash 차이가 있으면 실행·완료 주장을 중단한다. 이 확장 계약을 전체 RQ1~RQ5·ablation 또는 최종 holdout 완료와 혼동하지 않는다.

## 동결 전 v3 교정

UNIT_TYPED는 각 base의 원래 반경과 동일한 0.25 km/0.75 km/1.5 km 문자열을 숫자 필드에 주입한다. 거리값 변경 오류를 섞지 않는다. v2의 고정 1 km 문자열은 여러 오류를 동시에 주입하므로 모델 실행에 사용하지 않고 준비 원본으로만 보존한다.

Native 코드 정규화 `native_fault_message_alias_v1`은 `reference geometry is unresolved`→`MISSING_REFERENCE_GEOMETRY`, `distance_m must be positive`→`DISTANCE_NOT_POSITIVE`, `explicit research source required`→`EXPLICIT_SOURCE_REQUIRED` 3개 원문 메시지를 사전 exact dictionary로 대응한다. 상태 prefix 제거 외에 substring/expected label 기반 추론은 하지 않는다. 원문 메시지와 native receipt는 보존하며 알 수 없는 코드는 그대로 둔다.

## 추가 측정·누락 정책 고정

`expanded_fault_metrics_v1`은 복구가 금지된 geometry/source/ambiguity 입력의 B4/H 검토안에서 search action 또는 nonempty tool_calls를 실제 관측했을 때만 `forbidden_recovery_proposed`를 판정한다. 검토 실패/미관측은 null, P0의 해당 제안 분모는 0이다. 보고서에는 관측된 양성 수·측정 수·누락 수·전체 분모를 분리하며 전체 제안 수는 모두 측정됐을 때만 숫자로 공개한다. 이를 실제 금지 SQL 실행으로 해석하지 않는다.

복구는 한 번으로 제한한다. First-repair Execution Success와 First-repair Joint Success를 분리하며 Joint는 실행·객체집합 복원·명시 task 의미 보존의 동시 충족이다. Semantic Drift는 관측된 preservation boolean의 반대값이며 미관측은 null이다. 인간 검토 dispatch 이벤트를 이 runner가 관측하지 않으므로 escalation은 null이다. 추가입력 제안이 곧 사람 검토 요청이라는 가정은 하지 않는다.

RQ2 paired comparison은 B4 대비 P0/H의 binary Recall 및 target-code Recall 차이다. case를 짝짓고 3개 source-base cluster를 복원추출한다. bootstrap 2,000회, seed 20261103, linear percentile 2.5%/97.5%로 고정한다. 누락 pair는 분모에 남기며 하나라도 있으면 전체 차이/CI는 null이다. 반복 행을 마지막 값으로 덮어쓰거나 독립 case로 세지 않고 명시 계약 없이 중복된 case는 거부한다. 이 CI는 3개 지리적 base의 개발 기술통계이며 일반 오류모집단의 확정적 우위를 뜻하지 않는다.
