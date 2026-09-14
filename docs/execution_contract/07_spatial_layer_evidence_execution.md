# Phase 7 공간 레이어 근거 실행

## 범위

Phase 7은 `Dataset` 폴더의 공간성 자료를 실행 가능한 근거 레이어로 전환하기 위한 단계다. 사고-S101 relation은 이미 DB에 올라와 있고, Phase 7.2에서 shapefile 기반의 정적 레이어 4종을 PostGIS serving table로 적재했다. 수치조류도, 바다갈라짐, AIS/V-PASS 등 별도 포맷 또는 대용량 동적 레이어는 registry에는 등록하되 ingestion 전에는 실행을 차단한다.

핵심 원칙은 다음과 같다.

```text
QueryExecutionContext
-> ExecutionValidator PASS
-> 등록된 ToolBinding 실행
-> EvidenceBundle 반환
```

이 경로를 통과하지 않은 agent 실행은 허용하지 않는다.

## 실행계약 적용 대상

오케스트레이터 dispatch 단계에서 다음 agent는 `QueryExecutionContext` 검증을 반드시 통과해야 한다.

- `Spatial Analysis Agent`
- `Accident/Risk Agent`
- `AIS Analysis Agent`

## 공간 레이어 registry

`data/spatial_layer_registry.yaml`에 다음 레이어를 등록했다.

- `accident_s101_relation`
  - 실행 상태: `executable`
  - 테이블: `serving.accident_s101_relation_current`
  - 역할: 사고와 S-101 객체의 거리·관계 조회
- `tidal_current_surface`
  - 원천: `Dataset/수치조류도_국내연안2025.zip`
  - 실행 상태: `needs_ingestion`
- `eddy_hazard_area`
  - 원천: `Dataset/와류.zip`
  - 실행 상태: `executable`
  - 테이블: `serving.eddy_hazard_area_current`
- `planned_port_area`
  - 원천: `Dataset/신항만예정지역.zip`
  - 실행 상태: `executable`
  - 테이블: `serving.planned_port_area_current`
- `island_gazetteer`
  - 원천: `Dataset/도서지명.zip`
  - 실행 상태: `executable`
  - 테이블: `serving.island_gazetteer_current`
- `sea_parting_prediction`
  - 원천: `Dataset/바다갈라짐예측정보_*.ZIP`
  - 실행 상태: `needs_ingestion`
- `vessel_traffic_control_area`
  - 원천: `Dataset/선박안전교통관제구역.zip`
  - 실행 상태: `executable`
  - 테이블: `serving.vessel_traffic_control_area_current`

## Phase 7.2 적재 결과

`scripts/ingest_spatial_layer_archives.py`가 zip 내부 shapefile을 파싱하고, 원천 CRS를 WGS84 좌표계로 변환해 serving table에 적재한다. 원천 archive 해시와 zip 내부 member 경로는 각 row의 `provenance`에 보존한다.

- `island_gazetteer`: 1,140건
- `planned_port_area`: 12건
- `eddy_hazard_area`: 620건
- `vessel_traffic_control_area`: 40건

적재 후 registry의 `execution_status`는 `executable`로 승격했고, `expected_physical_table` 대신 실제 `physical_table`을 사용한다.

## 동적 교통 레이어

AIS/V-PASS는 S-101 정적 객체가 아니라 `DynamicTrafficLayer`로 분리한다.

`data/traffic_layer_registry.yaml`에 다음 레이어를 등록했다.

- `ais_route_analysis`
  - 원천: `Dataset/AIS항로분석.zip`
- `ais_major_route`
  - 원천: `Dataset/AIS주요통항로분석.zip`
- `vpass_route_analysis`
  - 원천: `Dataset/V-PASS항로분석.zip`
- `vpass_major_route`
  - 원천: `Dataset/V-PASS주요통항로분석.zip`

현재 이 레이어들은 serving table로 적재되지 않았으므로 `BLOCKED_DATA`로 차단한다.

## mock 금지 정책

ingestion이 끝나지 않은 레이어는 가짜 결과를 반환하지 않는다.

```text
미적재 레이어
-> registry에는 존재
-> schema binding 시도
-> serving table 없음
-> ExecutionValidator가 BLOCKED_DATA 반환
```

이 정책은 “있는 척” 결과를 만드는 문제를 막기 위한 것이다.

## EvidenceBundle partition

Phase 7 이후 결과 근거는 다음 partition으로 나뉜다.

- `spatial_feature_evidence`: S-101 feature query 근거
- `spatial_layer_evidence`: 수치조류, 와류, 신항만, 도서지명, 바다갈라짐 등 공간 레이어 근거
- `accident_relation_evidence`: 사고-S101 relation 근거
- `regulatory_evidence`: 법령, 고시, 행정규칙, 공식자료 근거
- `rag_evidence`: 문서/RAG 인용 근거
- `kg_provenance`: KG 경로 근거

## 사고 relation 실행기

`services.accident_risk_agent.agent.execute_accident_risk`는 다음 테이블을 읽기 전용으로 조회한다.

```text
serving.accident_s101_relation_current
```

필수 slot:

- `feature_instance_id`

선택 filter:

- `distance_m`
- `filters.limit`
- `filters.k`

반환 결과:

- `accident_spatial_geojson`
- `accident_relation_evidence`
- 실행 SQL provenance
- `EvidenceBundle`

## 남은 작업

- 수치조류도 `.data` 포맷을 해석하는 raster/vector adapter가 필요하다.
- 바다갈라짐 예측정보는 시간표 기반 자료와 도서/지점 좌표를 연결하는 위치 binding이 필요하다.
- AIS/V-PASS는 대용량 동적 교통 레이어이므로 샘플 적재 정책, 시간 컬럼 해석, 증분 적재 전략이 필요하다.
- 각 레이어의 속성 스키마, CRS, 시간 컬럼, geometry 유효성 검증 규칙을 dataset별로 계속 보강해야 한다.
