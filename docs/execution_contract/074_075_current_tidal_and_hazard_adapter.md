# Phase 7.4/7.5 수치조류·위험해역 Adapter

## Phase 7.4 수치조류도

`Dataset/수치조류도_국내연안2025.zip`은 `header.data`, `dataset.data`, `2025_tide.data`로 구성된 대용량 바이너리 grid 자료다. 현재 단계에서는 조류 속도/방향 값을 임의 해석하지 않고 metadata adapter만 구현했다.

- metadata table: `serving.tidal_current_surface_metadata`
- registry 상태: `metadata_only`
- parser 상태: `NEEDS_BINARY_GRID_SPEC`
- 검증 정책: `current_tidal_lookup`은 여전히 `BLOCKED_DATA`로 차단한다.

이 정책은 수치조류 값을 모르는 상태에서 가짜 속도/방향을 만들지 않기 위한 것이다.

## Phase 7.5 위험·규제·보호 해역

와류 외에 국내 해양 공간자료의 위험·제한·주의성 레이어를 `serving.hazard_area_current`로 통합 적재했다. 각 row는 `layer_id`, 원천 archive, zip member, 원천 속성, source hash provenance를 보존한다.

- `caution_warning_area`: 주의경계해역, 5건
- `speed_restriction_area`: 속도제한구역, 94건
- `entry_restricted_area`: 진입제한, 6건
- `anchoring_prohibited_area`: 정박금지/투묘금지, 38건
- `fishing_prohibited_area`: 낚시금지구역, 236건
- `fishing_restricted_area`: 낚시제한구역, 1건
- `dumping_ground_area`: 투기장, 55건

보호수역은 항행 위험 자체가 아니므로 `hazard_area`가 아니라 `protected_area`로 분리한다.

- `protected_sea_area`: 보호수역, 1건, `serving.protected_area_current`
- 법령 근거 후보: `해양생태계의 보전 및 관리에 관한 법률` 제25조 해양보호구역의 지정·관리, 제27조 해양보호구역에서의 행위제한 등

`hazard_area_lookup` analysis type은 다음 레이어를 하나의 위험해역 묶음으로 조회한다.

- 와류
- 주의경계해역
- 속도제한구역
- 진입제한
- 정박금지/투묘금지
- 낚시금지/제한구역
- 투기장

`protected_area_lookup` analysis type은 보호·보전 목적의 공간 레이어를 별도로 조회한다.

- 보호수역

## 실행계약

위험해역 조회는 반드시 다음 경로를 통과한다.

```text
QueryExecutionContext
-> ExecutionValidator PASS
-> hazard.area_lookup ToolBinding
-> DataBinding 기반 PostGIS SQL
-> spatial_layer_evidence
```

수치조류도는 metadata provenance만 등록되었으며, 속도/방향 grid parser가 완성되기 전에는 실행 결과로 사용하지 않는다.
