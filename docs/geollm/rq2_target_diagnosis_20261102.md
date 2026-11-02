# RQ2 주입 오류 원인 코드 대조 — v6 원본의 사후 진단

원본 실험: 20261102_gold_v2_eight_k1_v6. 새 모델 실행·운영 수정·기존 결과 덮어쓰기를 하지 않았다. 이 결과는 기존 binary verdict를 실제 원문 원인과 대조한 별도 파생 분석이다.

## 방법별 결과

| 방법 | Binary Recall | 주입 오류 관련 코드 대조 Recall | 정상 CONTROL 오차단 | compiler / native target hit |
|---|---:|---:|---:|---:|
| B4 | 0/8 | 0/8 | 0/1 | 0 / 0 |
| P0 | 8/8 | 8/8 | 1/1 | 1 / 7 |
| H | 8/8 | 8/8 | 1/1 | 1 / 7 |

**사후 원문 매핑 결과다.** 최초 fault_contract에는 expected_fault_codes가 없었다. 따라서 표의 코드 Recall을 당시 사전등록된 유형별 정확도라고 표현하지 않는다.

B4는 8개 초기 오류 모두 invalid=false였다. 검출을 주장하지 않았으므로 target hit=false다. 전용 코드 출력은 미계측이며 initial_checks/reason/raw만 노출한다. B4 행에도 저장된 validator_detection을 LLM 검출로 합산하지 않았다.

P0/H는 단순히 coverage가 없어 모두 막았던 것만은 아니다. 8개 주입 오류 각각의 해당 원인도 원문 trace에 존재했다. 그러나 정상 CONTROL에도 DATA_COVERAGE_UNVERIFIED가 발생해 오차단했다. 이 정상 가용성 문제는 별도로 유지한다. H의 코드 성공은 이 관측에서 Validator 쪽 근거이며 LLM이 추가로 검출했다는 증거가 아니다.

## 오류별 실제 원인

| 주입 사례 | 사후 기대 코드 | P0/H 실제 관련 원문 | 단계 |
|---|---|---|---|
| FAULT_V2_CONTROL | 정상 | BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED | NATIVE_VALIDATOR |
| FAULT_V2_UNIT_TYPED | DISTANCE_VALUE_TYPE_INVALID | DISTANCE_VALUE_TYPE_INVALID | LOSSLESS_COMPILER |
| FAULT_V2_MISSING_GEOMETRY | MISSING_REFERENCE_GEOMETRY | NEEDS_USER_INPUT: reference geometry is unresolved | NATIVE_VALIDATOR |
| FAULT_V2_WRONG_CRS | REQUEST_CRS_MISMATCH | BLOCKED_CONFIG: REQUEST_CRS_MISMATCH | NATIVE_VALIDATOR |
| FAULT_V2_UNKNOWN_SOURCE | EXPLICIT_SOURCE_REQUIRED | BLOCKED_CONFIG: explicit research source required | NATIVE_VALIDATOR |
| FAULT_V2_NEGATIVE_RADIUS | DISTANCE_NOT_POSITIVE | NEEDS_USER_INPUT: distance_m must be positive | NATIVE_VALIDATOR |
| FAULT_V2_WRONG_FEATURE | REQUEST_TARGET_MISMATCH | BLOCKED_CONFIG: REQUEST_TARGET_MISMATCH | NATIVE_VALIDATOR |
| FAULT_V2_SEMANTIC_EXPANSION | REQUEST_TARGET_MISMATCH | BLOCKED_CONFIG: REQUEST_TARGET_MISMATCH | NATIVE_VALIDATOR |
| FAULT_V2_WRONG_RADIUS | REQUEST_DISTANCE_MISMATCH | BLOCKED_CONFIG: REQUEST_DISTANCE_MISMATCH | NATIVE_VALIDATOR |

## 엄격히 구분할 한계

- expected fault code는 기존 fault_contract의 사전 정의 필드가 아니라, 고정 주입 사례와 원문 blocker를 대조한 사후 매핑입니다.
- B4 행에 함께 저장된 validator_detection은 공통 비교 계측입니다. LLM Review 검출 성과로 합산하지 않습니다.
- B4의 initial_checks/reason/raw verdict를 그대로 공개합니다. 기존 reviewer에 전용 fault-code 출력 계약이 없어 true 판정만으로 정확한 코드 검출을 추정하지 않습니다.
- wrong_feature와 semantic_expansion은 같은 REQUEST_TARGET_MISMATCH로 검출됩니다. 두 세부 오류를 독립적으로 정확히 분류했다는 뜻이 아닙니다.
- 8개 오류 각각 N=1, 정상 CONTROL N=1입니다. 일반화 성능이나 신뢰구간을 만들지 않습니다.
- typed unit 1건은 lossless compiler의 형식 거절이며 native Validator 7건과 분리합니다.
- 기존 v6의 coverage 정상 오차단은 보존합니다. 사후 진단이 운영 수정·새 전체 비교 실행을 대체하지 않습니다.

typed unit은 DISTANCE_VALUE_TYPE_INVALID compiler 거절 1건이다. native Validator 8건이라고 쓰지 않는다. REQUEST_TARGET_MISMATCH는 wrong_feature와 semantic_expansion의 공유 상위 신호이며 세부 유형 독립 진단(strict_subtype_recall)은 null이다.

## 무결성 검증

원본 49파일 SHA를 보존했다. manifest의 rows/contract/oracle 해시, 27 branch JSON과 rows 일치, 9 initial plan canonical hash, 공유 review hash, method별 verdict 귀속을 확인했다. 진단 후 다시 읽어 원본 불변을 재확인했다. 하나라도 실패하면 UI는 INTEGRITY_FAILED로 반환하고 수치를 숨긴다.

diagnosis.json 각 행은 raw_path/raw_sha256, review_path/review_sha256, initial_plan_sha256과 원인 JSON pointer를 제공한다. 홀드아웃 자료를 읽지 않았다.

사후 매핑은 v6 fault_contract SHA256 `3802aca3949fda1abff4f12e66a86c5048e82012246f2e2a377c0811707052b1`에 고정했다. 다른 동결계약이 동일 case ID를 재사용해도 매핑하지 않고 MAPPING_NOT_DEFINED_FOR_COHORT로 반환한다.

## 연동·검증

연구 UI RQ2에 binary/목표코드 사후대응/정상 오차단과 사례별 예상·실제 코드를 분리 표시한다. `rq2_diagnosis.py`는 v6 fault contract SHA를 고정하고 원시행/공유review/초기plan 해시 검증에 실패하면 수치를 반환하지 않는다. UI Python76 및 추가대응회귀12, Node22 통과(중복합산하지 않음). 최종 HTTP·기존GOLD/v6 506파일 보존 확인은 `outputs/rq2_parent_20261102/final_verification.json`이다. 브라우저 렌더링 검증과 구분한다.

[다음 동결의 지표·표본 확장 계약](../../research/marine_geollm_scie/protocol/rq2_target_fault_contract_20261102_KR.md). 모델/운영 API 호출·운영 소스 변경·홀드아웃 사용·새 전체실험은 수행하지 않았다.
