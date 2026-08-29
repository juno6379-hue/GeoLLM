# QueryPlan 및 SQL Template Compiler 규칙

## 1. QueryPlan JSON

```json
{
  "query_id": "Q-20260731-001",
  "intent": "spatial_feature_proximity_search",
  "analysis_type": "feature_dwithin",
  "target": {
    "original_term": "선석",
    "concept_id": "MARINE_BERTH",
    "nftc_codes": [153],
    "feature_names": ["Berth"],
    "geometry_types": [],
    "resolution_status": "RESOLVED",
    "confidence": 0.96
  },
  "location": {
    "original_text": "부산항",
    "place_id": "BUSAN_PORT",
    "geometry_source": "GAZETTEER",
    "reference_mode": "CENTROID",
    "resolution_status": "RESOLVED",
    "confidence": 0.95
  },
  "spatial": {
    "relation": "dwithin",
    "distance_m": 1000,
    "map_bounds_required": false
  },
  "output": {
    "format": "geojson",
    "limit": 100,
    "include_attributes": true
  },
  "target_agent": "SpatialQueryAgent",
  "required_tools": [
    "SRIDGuard",
    "SQLTemplateCompiler",
    "PostGISExecutor"
  ],
  "unresolved_slots": [],
  "execution_status": "READY"
}
```

## 2. SQL 템플릿 목록

```text
feature_by_code
feature_by_name
feature_within_area
feature_dwithin
nearest_feature
feature_count
feature_intersection
geometry_length
geometry_area
feature_detail
dataset_metadata
```

## 3. `feature_dwithin` 템플릿

```sql
WITH location AS (
    SELECT
        geom,
        COALESCE(centroid, ST_PointOnSurface(geom)) AS reference_point
    FROM public.place_gazetteer
    WHERE place_id = :place_id
      AND enabled = true
)
SELECT
    vf.seq AS id,
    vf.meta_seq_id,
    vf.dataset_name,
    vf.nftc_code,
    vf.feature_name,
    GeometryType(vf.geom) AS geometry_type,
    ST_AsGeoJSON(vf.geom) AS geojson,
    ST_Distance(
        vf.geom::geography,
        l.reference_point::geography
    ) AS distance_m,
    vf.attr
FROM public.v_feature_readable AS vf
CROSS JOIN location AS l
WHERE vf.nftc_code = ANY(:nftc_codes)
  AND ST_DWithin(
      vf.geom::geography,
      l.reference_point::geography,
      :distance_m
  )
ORDER BY distance_m, vf.seq
LIMIT :result_limit;
```

## 4. `feature_within_area` 템플릿

```sql
WITH location AS (
    SELECT geom
    FROM public.place_gazetteer
    WHERE place_id = :place_id
      AND enabled = true
)
SELECT
    vf.seq AS id,
    vf.nftc_code,
    vf.feature_name,
    GeometryType(vf.geom) AS geometry_type,
    ST_AsGeoJSON(vf.geom) AS geojson,
    vf.attr
FROM public.v_feature_readable AS vf
CROSS JOIN location AS l
WHERE vf.nftc_code = ANY(:nftc_codes)
  AND vf.geom && l.geom
  AND ST_Intersects(vf.geom, l.geom)
ORDER BY vf.seq
LIMIT :result_limit;
```

## 5. `nearest_feature` 템플릿

```sql
WITH location AS (
    SELECT COALESCE(centroid, ST_PointOnSurface(geom)) AS reference_point
    FROM public.place_gazetteer
    WHERE place_id = :place_id
      AND enabled = true
)
SELECT
    vf.seq AS id,
    vf.nftc_code,
    vf.feature_name,
    GeometryType(vf.geom) AS geometry_type,
    ST_AsGeoJSON(vf.geom) AS geojson,
    ST_Distance(
        vf.geom::geography,
        l.reference_point::geography
    ) AS distance_m
FROM public.v_feature_readable AS vf
CROSS JOIN location AS l
WHERE vf.nftc_code = ANY(:nftc_codes)
ORDER BY vf.geom <-> l.reference_point
LIMIT :result_limit;
```

## 6. SQL 안전 규칙

허용:

- `SELECT`
- 허용 목록의 테이블·뷰·컬럼
- bind parameter
- 사전 승인된 PostGIS 함수

금지:

- 문자열 연결로 사용자 입력 삽입
- 임의 식별자 생성
- `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`
- SRID 미확인 상태의 geography 캐스팅
- 무제한 전체 조회

허용 PostGIS 함수 예시:

```text
ST_AsGeoJSON
ST_DWithin
ST_Distance
ST_Intersects
ST_Contains
ST_Within
ST_Touches
ST_Centroid
ST_PointOnSurface
ST_Transform
ST_SRID
GeometryType
ST_IsValid
```

## 7. SQL 컴파일 절차

```text
1. QueryPlan Schema 검증
2. execution_status == READY 확인
3. template_id 선택
4. Schema Registry 검사
5. SRID Guard 실행
6. bind parameter 생성
7. SELECT-only 검사
8. LIMIT 검사
9. SQL 실행
10. 결과 Schema 검증
```
