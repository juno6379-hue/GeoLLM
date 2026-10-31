# GOLD v2 연결 matched fault·bounded recovery 진단

이 cohort는 원래 18문항 GOLD를 변경하지 않는 별도 연구 명세다. clean plan은 연구 snapshot의 S-101 Wreck, 명시 POINT(129.05 35.1), EPSG:4326, 1000m, dwithin, source=s101이다. 입력 좌표는 통제된 시험 입력이며 특정 항만 입구라고 주장하지 않는다. source 범위 검증·독립 SQL 결과와 실제 도구 실행을 모두 확인한 후 모델을 호출한다.

## 고정 조건

9개 입력: clean control, radius_m 문자열 `1 km`의 typed tool contract 위반, 기준기하 누락, 잘못된 CRS, 미등록 source, 음수 반경, 잘못된 Feature(Obstruction), 대상 과잉 확장(Wreck+Obstruction), 명시 1000m를 5000m로 변경. 총 3검출방법 × 9조건 = 27관측이다. 단위 오류는 의미 1km 자체가 잘못된 것이 아니라 숫자형 필드에 문자열이 들어간 계약 오류다. 기존 18개 질문의 기준을 바꾸지 않는다.

- 라벨: CONTROLLED_PROTOCOL_NOT_INDEPENDENT_EXPERT. 독립 인간 GOLD 정확도라고 표현하지 않는다.
- permission fault: 권한이 다른 실제 격리 원천/역할이 없으므로 NOT_ELIGIBLE. 가짜 permission 실패를 만들지 않는다.
- 모델 budget: 각 입력당 reviewer 1회, 최대 출력768token, retry0. B4/H가 그 결과를 공유한다.
- P0: 동일 초기 plan을 lossless compile한 후 실제 native Validator만 수행. 별도 복구 추론 없음.
- missing geometry: reviewer 입력에도 geometry를 주지 않으며 복구 실행 금지. source unknown도 대체 원천을 추측해 실행하지 않는다.
- 복구 가능한 항목: typed unit, CRS, 음수거리, 잘못된 Feature, 대상 과잉 확장, 거리 변경. 원문1000m/4326/Wreck 및 원래 explicit task tuple 보존 여부를 사후 평가한다. 새 필터·추가 tool 인자·상위 target/속성/연산/CRS/거리의 불일치도 의미 보존 실패로 판정한다.

## RQ2 관측

공통 executor safety floor 이전의 initial-plan 검출을 비교한다. B4는 `invalid`라는 명시 reviewer verdict, P0는 compilation rejection 또는 native Validator의 실제 승인/차단이다. compiler_rejected와 native_validator_called를 별도 보존한다. native Validator 연결 실패는 검출 성공이 아니라 null이다.

H의 **초기 오류 검출**은 두 component verdict의 OR로 정의하고 둘 다 저장한다. 이는 전체 H 시스템의 최종 실행 결정이나 복구 성공률을 의미하지 않는다. H 복구는 별도로 동일 reviewer 수정 plan을 native Validator에 다시 통과시킨다. common executor에서 차단된 것을 Validator가 검출한 것으로 계산하지 않는다.

## RQ4 관측

같은 reviewer의 수정안 1개만 허용한다. B4는 공통 read-only executor로, H는 추가 native Validator 이후 실행한다. 원래 tool/source/Feature/연산/기준기하/CRS/거리/analysis_type의 고정 tuple과 대조한다. 명시 단위 등가는 허용하되 대상 확장·원천 교체·거리 변경은 의미 보존 실패다. 이는 제한된 machine semantic preservation이며 자연어 전체 의미 검수의 대체가 아니다.

독립 SQL은 executor의 ST_DWithin 대신 ST_Distance<=1000 조건으로 Wreck ID를 계산한다. 같은 PostGIS·source를 사용하므로 독립 수치 엔진 검산이라고 표현하지 않는다. 결과 ID는 reviewer prompt에 주지 않는다. clean 실제 실행이 이 oracle과 다르면 모델 실행 전에 중단한다.

`joint_success`는 실제 실행 성공 AND fixed tuple 보존 AND oracle 객체 집합 일치다. 미측정은 null로 남긴다. P0는 복구를 수행하지 않으므로 복구율 분모에 억지로 포함하지 않는다. 모든 실패 raw, 원본 plan/hash, reviewer raw, validation receipts, 실제 SQL/tool 관측을 보존한다.

## 실행

`runners/eight_fault_recovery.py`는 기본적으로 준비만 수행한다. 부모가 새 source/profile/model/snapshot/GOLD hash를 동결한 후 `--execute`로 실행한다. 출력 폴더는 반드시 새 이름을 사용한다. 실행 중 source hash 변화는 중단 조건이다. 현재 구현/단위테스트는 모델 실험 결과가 아니다.

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.eight_fault_recovery --profile <새동결baseline_profile.json> --benchmark research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1 --output <새fault_run> --execute
```
