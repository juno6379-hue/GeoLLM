# 09. Map Agent 연계 설계 (Map Agent Integration)

## 1. 개요
플랫폼은 지도 UI를 직접 렌더링하지 않고, 기 구축된 "Map Agent"를 재사용합니다. 이를 위해 플랫폼의 분석 결과를 기존 Map Agent가 이해할 수 있는 표준 규격으로 변환하는 `Map Agent Adapter`를 설계합니다.

## 2. MapLayerSpecification 설계
각 전문 Agent(Spatial, AIS, Vision 등)가 산출한 공간 결과는 Orchestrator를 거쳐 Adapter로 전달되며, Adapter는 다음 스키마를 생성합니다.

```json
{
  "layer_id": "layer-uuid-v4",
  "task_id": "task-uuid-v4",
  "title": "부산항 3km 이내 위험객체",
  "description": "국립해양조사원 2026.06 데이터를 기반으로 한 공간 교차 분석 결과",
  "geometry_type": "POINT",
  "source_type": "GEOJSON",
  "source_uri": "s3://results/task-uuid/hazards.geojson",
  "inline_geojson": null, 
  "source_crs": "EPSG:4326",
  "display_crs": "EPSG:3857",
  "style": {
    "fill_color": "#FF0000",
    "stroke_color": "#8B0000",
    "marker_symbol": "hazard-icon",
    "opacity": 0.8
  },
  "legend": {
    "title": "위험객체 유형",
    "items": [{"label": "침선", "color": "#FF0000"}]
  },
  "popup_fields": ["object_name", "depth", "report_date"],
  "label_field": "object_name",
  "min_zoom": 10,
  "max_zoom": 18,
  "visibility": true,
  "z_index": 100,
  "valid_time": "2026-07-15T00:00:00Z",
  "dataset_version": "enc-v2026.06",
  "provenance": "Spatial Analysis Agent (postgis.intersection)"
}
```

## 3. Map Agent Adapter 로직
1. **변환**: AgentResult 내의 `features`(GeoJSON 경로 또는 인라인 데이터)를 파싱하여 `MapLayerSpecification`으로 매핑.
2. **스타일링 자동화**: 객체 유형(침선, 항로, 예측 등)에 따라 기본 스타일(Style) 및 범례(Legend) 자동 생성.
3. **Session 연결**: 클라이언트가 지도 화면을 보고 있는 `map_session_id`를 유지하여, Adapter가 기존 Map Agent API(예: `POST /api/map/layers`)를 호출하면 클라이언트 화면에 즉시 레이어가 추가되도록 연동.
4. **검증**: 지도에 표시될 객체 수(`feature count`)와 Agent가 반환한 수치(`structured_result.count`)가 일치하는지 대조(Map-Data Sync).

## 4. 프론트엔드 (UI) 통합 구현체 (MVP)
현재 플랫폼은 독자적인 Leaflet 기반의 통합 시각화 UI(`services/orchestrator/static/index.html`)를 제공하며, 다음과 같이 연동되어 있습니다.

### 4.1. 베이스맵 연동 (S-101 전자해도)
운영 환경에 존재하는 기존 **S-101 전자해도 WMS 서버**(`http://localhost:8657/encService`)를 Leaflet의 `L.tileLayer.wms`를 통해 Base Layer로 호출합니다.
- 동적 파라미터 연동: `displayMode`, `colorPalette`, `simplifiedPoint` 등의 S-101 맵 서버 고유의 시각화 파라미터를 그대로 주입하여 종이해도(Paper) 및 주/야간 테마를 완벽히 지원합니다.

### 4.2. 공간 분석 결과 오버레이 (GeoJSON)
- 클라이언트 UI는 Orchestrator의 API(`GET /api/v1/tasks/{task_id}`)를 지속적으로 Polling합니다.
- 분석이 완료(`COMPLETED`)되면 반환된 `MapLayerSpecification`을 파싱합니다.
  - 데이터가 소규모(`vector_embedded`)인 경우 즉시 렌더링
  - 대용량(`vector_file`)인 경우 `FastAPI /data` 라우터를 통해 GeoJSON 파일을 비동기 Fetch 후 렌더링
- Leaflet `L.geoJSON` 객체를 통해 S-101 배경 지도 위에 붉은색 폴리곤(위험구역 등)을 오버레이로 덧씌웁니다.

## 5. 기존 Map Agent와의 계약
- 독립적인 별도 Map Agent 시스템을 유지할 경우, RESTful API 또는 Message Queue를 통해 `MapLayerSpecification` 페이로드를 수신해야 합니다.
- 대용량 데이터의 경우, GeoJSON을 직접 보내지 않고 `source_uri` (S3 Pre-signed URL 또는 FastAPI 정적 경로)를 보내어 Map Agent가 Vector Tile(MVT)로 변환하거나 클라이언트에서 직접 로드하도록 위임합니다.
