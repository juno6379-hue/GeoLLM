# 22. S-101 2.0 Spatial Reliability and Accident Relations

## 목적

`gbhd_s101`의 S-101 2.0 공간 데이터를 신뢰 가능한 serving layer로 고정하고, 표준화된 사고 위치와 S-101 feature 간 관계 조인을 검증한다.

## 기준

- DB: `gbhd_s101`
- Product specification: `INT.IHO.S-101.2.0`
- Source projection: `projection.s101_feature_current`
- Valid serving layer: `projection.s101_feature_valid`
- Anchor layer: `projection.s101_feature_valid_anchor`
- Accident table: `serving.accident_events`
- Relation layer: `serving.accident_s101_relation_current`

## Geometry 품질 결과

현재 `gbhd_s101` 기준 S-101 2.0 projection은 과거 handoff에 남아 있던 invalid MULTIPOLYGON 약 2.9만 건 상태가 아니다.

검증 결과:

```text
projection.s101_feature_current | 787102 rows | invalid 0
projection.s101_feature_valid   | 787102 rows | invalid 0
MULTIPOLYGON                    | 433 rows    | invalid 0
SRID 4326                       | 787102 rows
```

`projection.s101_feature_valid`는 `ST_MakeValid`, `ST_CollectionExtract`, `ST_Force2D`를 적용할 수 있는 재생성 가능한 materialized view다. 현재는 원본 projection이 모두 valid라 `was_geometry_repaired = false`다.

## Accident 데이터 적재

입력 CSV:

```text
outputs/standardized/accident_events_coastguard_2025.csv
```

적재 결과:

```text
serving.accident_events | 4636 rows | geocoded 4636 | invalid 0
```

## 관계 조인 방식

복잡한 polygon/line geometry에 직접 KNN을 수행하면 느리다. 따라서 다음 2단계 구조를 사용한다.

1. `projection.s101_feature_valid_anchor`
   - 각 valid S-101 feature에 대해 `ST_PointOnSurface(geometry)` anchor point를 materialize
   - anchor point에 GiST index 생성
2. `serving.accident_s101_relation_current`
   - 사고점별 anchor 최근접 후보 20개 산출
   - 후보에 대해 실제 S-101 geometry와 `ST_DistanceSphere`, `ST_Intersects` 계산
   - 사고점별 최종 상위 5개 관계 저장

이 관계 layer는 운영용 nearest relation 검증 layer다. 전체 exhaustive 1km 교차/거리 관계가 필요하면 `ST_Subdivide` 기반의 별도 geometry tile layer를 만들어야 한다.

## 관계 조인 결과

```text
relation_rows           | 23180
accidents_with_relation | 4636
accidents_without_relation | 0
average_distance_meters | 501.558
max_distance_meters     | 61881.126
```

Relation type 분포:

```text
INTERSECTS         | 5844 rows | 2469 accidents
WITHIN_50M         | 5245 rows | 1799 accidents
WITHIN_100M        | 2682 rows | 1220 accidents
WITHIN_500M        | 5876 rows | 2017 accidents
WITHIN_1000M       | 1432 rows | 632 accidents
NEAREST_OVER_1000M | 2101 rows | 651 accidents
```

상위 연결 feature type:

```text
DepthArea                | 5325 relations | 3113 accidents
DepthContour             | 4239 relations | 2572 accidents
SeabedArea               | 2442 relations | 1520 accidents
QualityOfBathymetricData | 1584 relations | 1015 accidents
ShorelineConstruction    | 1471 relations | 631 accidents
Obstruction              | 1353 relations | 803 accidents
Sounding                 | 448 relations  | 261 accidents
Coastline                | 360 relations  | 223 accidents
Wreck                    | 327 relations  | 171 accidents
Pontoon                  | 312 relations  | 181 accidents
FishingFacility          | 311 relations  | 130 accidents
UnsurveyedArea           | 309 relations  | 215 accidents
```

## Smoke Test

사고 100건 샘플에 대해 exact `ST_Intersects`를 수행했다.

```text
exact_intersections  | 5489
accidents_intersecting | 100
```

## 실행 순서

```powershell
docker cp outputs\standardized\accident_events_coastguard_2025.csv an_geollm_postgis:/tmp/accident_events_coastguard_2025.csv
docker cp scripts\load_accident_events_postgis.sql an_geollm_postgis:/tmp/load_accident_events_postgis.sql
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -v ON_ERROR_STOP=1 -f /tmp/load_accident_events_postgis.sql

docker cp scripts\ensure_s101_valid_geometry_and_accident_relations.sql an_geollm_postgis:/tmp/ensure_s101_valid_geometry_and_accident_relations.sql
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -v ON_ERROR_STOP=1 -f /tmp/ensure_s101_valid_geometry_and_accident_relations.sql
```

이미 `projection.s101_feature_valid`가 존재하면 더 빠르게 아래 두 단계만 실행할 수 있다.

```powershell
docker cp scripts\ensure_s101_valid_geometry_anchor.sql an_geollm_postgis:/tmp/ensure_s101_valid_geometry_anchor.sql
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -v ON_ERROR_STOP=1 -f /tmp/ensure_s101_valid_geometry_anchor.sql

docker cp scripts\ensure_accident_s101_relations.sql an_geollm_postgis:/tmp/ensure_accident_s101_relations.sql
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -v ON_ERROR_STOP=1 -f /tmp/ensure_accident_s101_relations.sql
```

## 다음 작업

1. `ST_Subdivide` 기반 exhaustive exact relation layer 추가
2. 사고 유형별 위험 feature type whitelist/weight 정의
3. `serving.accident_s101_relation_current`를 accident risk agent에서 직접 사용
4. relation 결과를 지도 overlay와 API 응답 provenance에 연결
