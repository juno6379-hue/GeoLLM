# RQ2 이진 검출·목표 오류 코드 검출 분리

## 기존 v6 결과의 의미

통제 오류8 + 정상1의 단일 계획 변형 집합을 B4/P0/H로 관측했다. 오류유형당 N=1이며 같은 seed를 반복한다고 독립 오류 사례 수가 늘어나지 않는다. “이번 CRS 통제 사례 1건을 검출했다”라고 보고하며 CRS 오류 일반 Recall 100%라고 쓰지 않는다.

- Binary Recall = invalid 사례에서 predicted_invalid=true인 비율.
- Target-fault-code Recall = invalid 사례에서 predicted_invalid=true이고 미리 지정한 목표 오류 코드가 실제 검출 코드에 포함된 비율.
- 정상 False Block은 별도 정상 사례 분모로 계산한다. 오류유형에 정상 사례가 없으면 그 유형의 False Block은 0%가 아니라 분모0이다.
- 목표 코드 포함과 오류 코드 집합 전체 정확 일치는 다른 지표다. 불필요한 coverage 차단 등 추가 사유를 별도 공개한다.
- 코드/응답이 관측되지 않은 경우는 null과 missing 수를 남기고 분모에서 제외하지 않는다. invalid=false로 명시된 경우 목표 오류 검출 성공은 false다.

## 기존 원문 사후 대응

v6에는 expected_fault_codes가 사전 동결되어 있지 않다. 따라서 기존 compiler 오류와 native blockers를 고정된 표로 정규화한 결과는 **POST_HOC_CODE_MAPPING**이다. 원본 점수나 새로운 사전등록 실험 결과로 덮어쓰지 않는다.

| fault 유형 | 목표 진단 코드 | 해석 범위 |
|---|---|---|
| unit | DISTANCE_VALUE_TYPE_INVALID | radius 숫자 필드에 문자열이 들어간 형식 오류; 모든 단위 오류 진단 아님 |
| geometry | MISSING_REFERENCE_GEOMETRY | 기준 geometry 누락 |
| crs | REQUEST_CRS_MISMATCH | 명시 요청 CRS와 실행 계획 CRS 불일치 |
| source | EXPLICIT_SOURCE_REQUIRED | 등록된 명시 원천 필요 |
| numeric | DISTANCE_NOT_POSITIVE | 양수 거리 조건 위반 |
| wrong_feature | REQUEST_TARGET_MISMATCH | 요청 대상과 실행 대상 불일치 |
| semantic_expansion | REQUEST_TARGET_MISMATCH | 같은 상위 코드; 대상 추가와 치환을 구별했다고 주장하지 않음 |
| semantic_distance | REQUEST_DISTANCE_MISMATCH | 요청 거리와 실행 거리 불일치 |

B4 행에 비교용 validator_detection이 있어도 B4의 코드 검출로 합산하지 않는다. B4는 초기 LLM review 원문과 initial_checks만, P0는 초기 compiler/native Validator, H는 초기 LLM 검토와 Validator를 구분해 집계한다. 복구 후 결과에서 원래 오류를 진단했다고 역추론하지 않는다. 단위 오류의 compiler 거절1건과 native Validator 검출7건은 별도 기록한다.

## 다음 동결의 실행계약

원본 fault 주입 전에 expected_fault_codes 및 세부 fault_subtype을 부여한다. 진단기는 `detected_fault_codes`, `detector_stage`, `input_plan_sha256`, `evidence_pointer`, `raw_sha256`를 기록한다. coverage 같은 비목표 사유만 있을 때 binary는 성공해도 target-code는 실패여야 한다. 세부 치환/추가 원인 평가를 한다면 코드 체계를 별도로 설계하고 사전 고정한다. 과거 generic 코드에 새 subtype을 소급 주입하지 않는다.

유형별 여러 독립 입력을 준비할 때 대상 Feature·명시 거리·좌표 표현·원천·복합성 조합을 다양화하고, 각 변경 전 정상 계획이 같은 연구 snapshot/권위 경로에서 실제 유효함을 먼저 확인한다. clean→단일fault diff와 Oracle를 보존한다. 정상 대조도 함께 확장한다. 개발 사례 확장과 모델 seed 반복 수는 별도로 보고하고, 동일 base scenario를 단위로 paired 분석한다. 최종 표본 수는 예상 오차·분석계획으로 정하며 임의의 소수 사례를 충분한 통계적 검증이라고 부르지 않는다.

운영 coverage/연구 scope 연결 등 다음 동결의 선행 gate를 완료한 뒤 새 8방법 전체 비교와 fault 평가를 실행한다. 홀드아웃은 개발 오류 확장에 사용하지 않는다. 이번 작업에서는 새 모델 실험·운영 수정·홀드아웃 평가를 하지 않는다.
