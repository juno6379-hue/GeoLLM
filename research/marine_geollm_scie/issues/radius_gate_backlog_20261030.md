# 반경 전처리와 독립 실행검증기의 차이 및 수정 후보

이 진단은 실제 `select_targets`·`prepare_radius_request`와 generic `ExecutionValidator`를 직접 비교한다. 기준점은 **합성 explicit point** `POINT(129.05 35.1)`이며 부산항 등의 검증된 지명 좌표라고 주장하지 않는다. DB/socket 연결은 즉시 오류가 나도록 차단했고 GIS 실행·LLM·live graph는 호출하지 않았다. 운영 unsafe 실행을 입증한 것이 아니다.

신규 단위검증3개가 통과했다(27.42초). 원시 결과는 `runs/20261030_radius_preprocessing/preprocessing_rows.jsonl`에 별도 저장한다. 기존19개 coverage 행은 변경하지 않았다.

|동일 변형|실제 반경 전처리|generic validator 직접 입력|해석|
|---|---|---|---|
|없는 S-101 feature 문자열|select_targets와prepare_radius_request가 거절|통과|해당 radius 경로에는 상위 목록 검사가 있다. 독립 gate에 같은 검사 근거가 있는 것은 아님|
|잘못된 CRS 문자열|prepare_radius_request에서 거절|통과|좌표계 보장은 이 경로에서 전처리에 의존함|
|spatial_relation=within, route=radius|radius QEC는 생성되지만 spatial_relation을 보존하지 않음|충돌 필드를 가진 QEC도 통과|radius 전용 builder의 고정 operation과 입력 필드 무시를 구분해야 함|

operator 변형은 자연어를 polygon-within 질의로 바꾼 실험이 아니다. 자연어 원문은 `침선 반경 3000m`로 유지하고 spatial_context의 relation만 충돌시켰다. 따라서 '사용자의 within 질의를 radius로 오해했다'고 해석하지 않는다. conflicting context를 명시적으로 거절할지, radius 전용 요청에서 사용하지 않는 필드로 취급할지는 계약 정의가 필요하다.

## 별도 수정 담당 backlog

### P1 — 실행검증기 단독 호출 시 feature·CRS 검사 범위

- 재현: `fault_injection/radius_preprocessing_audit.py`, `tests/test_radius_preprocessing_audit.py` 및 원시4행.
- 확인된 사실: radius 전처리는 거절하고 같은 결함을 직접 담은 generic QEC는 승인한다.
- 미확인: 다른 실제 caller가 전처리를 거치지 않고 이 QEC를 만들 수 있는지, 하위 SQL 실행기가 이를 막는지.
- 수정 후보 계층: `ExecutionValidator`의 radius 계약과 caller의 전처리 보장. 먼저 caller 경로를 감사하고, 공통 검증 강화가 필요한 경우 기존 승인된 비-WGS84/feature 사용 사례의 계약과 호환성을 확인한다.
- 완료 조건: 격리 end-to-end 정상/부정 재현, provenance 및 권한 결정 일관성, 의도적으로 지원하는 경로의 회귀 확인. 본 진단만으로 운영수정하지 않는다.

### P1 — 충돌하는 spatial_relation의 의미 계약

- 재현: `operator_mismatch` raw와 단위검증.
- 수정 후보 계층: typed input 정규화/반경 builder에서 충돌 필드 처리 정책을 정의하고 generic gate에서도 route와 relation 일관성을 보장할지 결정한다.
- 미확인: 실제 router가 해당 충돌 조합을 전달하는지. 사용하지 않는 context 필드인지 의미 조건인지부터 구분한다.
- 완료 조건: 동일한 사용자 질의·지도 문맥에서 왜 거절/정규화했는지 설명 가능하고 실제 capability 실행의 의미가 보존되는지 확인한다.

### P1 — 외부 상태 freshness와 실행 직전 재검증

- 재현: 기존 `coverage_pilot.py`의 L3 external registry/schema/permission 변형.
- 확인된 사실: receipt는 QEC input hash를 검증하며 외부 상태 변경을 조회하지 않는다. 다시 validator를 호출하면 주입한 외부 결함을 차단한다.
- 수정 후보 계층: 실제 실행기 transaction/snapshot 및 직전 재검증 계약. 아직 TOCTOU 취약점 확정이 아니다.
- 완료 조건: 별도 격리 DB에서 승인 이후 변경과 실제 실행 간 순서를 추적한다. 운영 DB 변경 금지.

## 재현 명령

```powershell
.\.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests/test_radius_preprocessing_audit.py -q
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.fault_injection.radius_preprocessing_audit --output-dir <새 결과 경로>
```

모든 라벨은 DRAFT이고 GOLD는0이다. 논문의 독립 검증기 완전성 주장에는 이 범위 차이를 공개해야 한다. 실제 production 전체의 위험 실행 증거로 확대 해석하지 않는다.
