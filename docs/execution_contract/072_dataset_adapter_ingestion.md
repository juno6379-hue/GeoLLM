# Phase 7.2 Dataset Adapter / Ingestion

## 목적

Phase 7.2는 `Dataset` 폴더의 실제 공간자료를 PostGIS serving table로 적재해, `QueryExecutionContext -> ExecutionValidator PASS -> Tool 실행 -> EvidenceBundle 반환` 경로에서 사용할 수 있게 만드는 단계다.

## 구현 내용

- `scripts/ingest_spatial_layer_archives.py`를 추가했다.
- zip 내부 shapefile을 탐색해 geometry와 속성을 읽는다.
- EPSG:5179 계열 원천 좌표계를 감지하고 EPSG:4326으로 변환한다.
- 원천 archive SHA-256, zip member 경로, 적재 스크립트 정보를 row provenance로 저장한다.
- 적재 성공 시 `data/spatial_layer_registry.yaml`의 `execution_status`를 `executable`로 승격하고 실제 `physical_table`을 기록한다.

## 적재 완료 레이어

- `island_gazetteer`
  - 원천: `Dataset/도서지명.zip`
  - 테이블: `serving.island_gazetteer_current`
  - 건수: 1,140
- `planned_port_area`
  - 원천: `Dataset/신항만예정지역.zip`
  - 테이블: `serving.planned_port_area_current`
  - 건수: 12
- `eddy_hazard_area`
  - 원천: `Dataset/와류.zip`
  - 테이블: `serving.eddy_hazard_area_current`
  - 건수: 620
- `vessel_traffic_control_area`
  - 원천: `Dataset/선박안전교통관제구역.zip`
  - 테이블: `serving.vessel_traffic_control_area_current`
  - 건수: 40

## 보류 레이어

- `tidal_current_surface`: `수치조류도_국내연안2025.zip`의 `.data` 구조 해석이 필요하다.
- `sea_parting_prediction`: CSV/XML/JSON 예측 시간표에 geometry가 없어 도서지명 또는 기준 지점 좌표와 연결해야 한다.
- `ais_route_analysis`, `vpass_route_analysis`: 대용량 동적 교통 레이어라 기본 적재 대상에서 제외했다. 스크립트는 `--include-dynamic-traffic` 옵션을 제공하지만 운영 적용 전 시간 컬럼과 샘플/증분 정책을 확정해야 한다.

## 실행 예

```bash
python scripts/ingest_spatial_layer_archives.py --replace --update-registry
```

대용량 교통 레이어를 시험 적재할 때는 다음처럼 제한 건수를 두고 실행한다.

```bash
python scripts/ingest_spatial_layer_archives.py --include-dynamic-traffic --layers ais_route_analysis --max-records 10000
```
