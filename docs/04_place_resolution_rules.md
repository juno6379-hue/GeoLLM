# 장소명 및 공간범위 해석 규칙

## 1. 목적

`부산항`, `북항`, `부산항 신항`과 같은 장소명을 검색 기준 geometry로 변환한다.

## 2. 장소 사전 테이블

```sql
CREATE TABLE public.place_gazetteer (
    place_id varchar(100) PRIMARY KEY,
    place_name_ko varchar(200) NOT NULL,
    place_name_en varchar(200),
    place_type varchar(50),
    aliases jsonb,
    geom geometry(Geometry, 4326) NOT NULL,
    centroid geometry(Point, 4326),
    source varchar(200),
    enabled boolean NOT NULL DEFAULT true
);

CREATE INDEX idx_place_gazetteer_geom
ON public.place_gazetteer
USING gist (geom);
```

## 3. 위치 해석 우선순위

1. UI에서 전달된 `map_bounds_geom`
2. `place_gazetteer.geom`
3. `place_gazetteer.centroid`
4. 외부 지오코딩 또는 관리자가 승인한 장소 후보
5. 사용자 명확화

## 4. 장소명 후보 조회

```sql
SELECT
    place_id,
    place_name_ko,
    place_name_en,
    place_type,
    geom,
    centroid
FROM public.place_gazetteer
WHERE enabled = true
  AND (
      place_name_ko = :location_text
      OR place_name_en ILIKE :location_text
      OR aliases @> to_jsonb(ARRAY[:location_text]::text[])
  )
ORDER BY
    CASE WHEN place_name_ko = :location_text THEN 1 ELSE 2 END,
    place_id;
```

## 5. 부산항 해석 규칙

`부산항`을 단일 고정 좌표로만 취급하지 않는다.

가능한 후보:

- 부산항 전체 항계
- 부산항 북항
- 부산항 신항
- 현재 지도화면 내 부산항 영역

질문이 `부산항 선석`처럼 일반적이면 전체 항계 geometry를 우선 사용한다.

질문이 `부산항 주변 1km`이면 다음 정책 중 하나를 명시적으로 선택한다.

```text
A. 항계 전체의 외곽으로부터 1km
B. 항계 대표점으로부터 1km
C. 현재 지도 중심점으로부터 1km
```

기본 권장:

- `부산항에 있는 선석` → `ST_Intersects(feature.geom, port.geom)`
- `부산항 중심 반경 1km` → centroid/대표점과 `ST_DWithin`
- `부산항 경계 주변 1km` → 항계 geometry와 geography 거리 계산

## 6. 출력 예시

```json
{
  "original_text": "부산항",
  "place_id": "BUSAN_PORT",
  "resolved_name": "부산항",
  "place_type": "PORT_AREA",
  "geometry_source": "GAZETTEER",
  "reference_mode": "AREA",
  "resolution_status": "RESOLVED",
  "confidence": 0.95,
  "candidate_count": 1
}
```

## 7. 모호성 처리

```text
부산항 → 전체/북항/신항 후보가 동일 점수
→ MULTIPLE_LOCATION_CANDIDATES
→ 후보 목록 표시
→ 사용자 선택 또는 지도범위로 자동 축소
```

## 8. 해양/도서 지명사전 통합 현황 (`maritime_gazetteer`)

현재 시스템은 위 설계(`place_gazetteer`)를 구체화하여, 국립해양조사원 등의 공식 데이터를 바탕으로 한 **해양/도서 지명사전(`maritime_gazetteer`)**을 실제 PostGIS 데이터베이스에 구축 및 통합하여 사용 중입니다.

*   **통합 데이터 소스**: 
    *   도서지명 (`TB_AREA_NAME_LAND.shp`) - 약 1,140건
    *   해양지명 (`TB_AREA_NAME_OCEAN.shp`) - 약 1,194건
*   **좌표계**: 원본 `EPSG:5179`에서 시스템 표준인 `EPSG:4326`으로 변환하여 저장
*   **실제 테이블 스키마**:
    ```sql
    CREATE TABLE maritime_gazetteer (
        id SERIAL PRIMARY KEY,
        name_kor VARCHAR(255),
        name_eng VARCHAR(255),
        source_type VARCHAR(50),  -- 'LAND' 또는 'OCEAN'
        geom GEOMETRY(Point, 4326)
    );
    CREATE INDEX idx_gazetteer_name_kor ON maritime_gazetteer (name_kor);
    CREATE INDEX idx_gazetteer_geom ON maritime_gazetteer USING GIST (geom);
    ```
*   **지오코딩 처리 우선순위 (`geocoding_tool.py` 적용 사항)**:
    1.  사용자 질의어를 `maritime_gazetteer` 테이블의 `name_kor`, `name_eng` 컬럼과 대조(ILIKE 검색).
    2.  정확히 일치(Exact Match)하는 건을 1순위, 포함(Starts with)하는 건을 2순위로 정렬하여 WKT(Point) 공간 좌표 반환.
    3.  `maritime_gazetteer`에 데이터가 없을 경우에 한해, 외부 OpenStreetMap (OSM Nominatim API)으로 Fallback 하여 육상 랜드마크 검색 후 자체 캐시(`osm_geocoding_cache`)에 저장.
