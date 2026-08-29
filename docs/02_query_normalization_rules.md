# 자연어 질의 정규화 규칙

## 1. 목적

자연어 질문을 실행 가능한 구조화 슬롯으로 변환한다. 정규화 단계는 SQL을 생성하지 않는다.

## 2. 필수 슬롯

```json
{
  "original_query": "부산항 반경 1km 내 선석을 찾아줘",
  "location_text": "부산항",
  "target_term": "선석",
  "distance_m": 1000,
  "spatial_relation_text": "반경 내",
  "aggregate": null,
  "sort": null,
  "limit": null,
  "output_format": "geojson"
}
```

## 3. 거리 정규화

| 표현 | 결과 |
|---|---:|
| `1km` | `1000` m |
| `500m` | `500` m |
| `2.5킬로미터` | `2500` m |
| 거리 미지정 주변검색 | 정책 기본값 사용 |

기본 거리값은 설정 파일에서 관리한다.

```yaml
spatial_defaults:
  proximity_distance_m: 50
  query_limit: 100
```

## 4. 공간관계 정규화

| 자연어 표현 | 정규화 값 |
|---|---|
| 주변, 근처, 반경 내, 이내 | `dwithin` |
| 안에, 내부, 포함된 | `within_area` |
| 겹치는, 교차하는 | `intersects` |
| 가장 가까운 | `nearest` |
| 접하는 | `touches` |
| 포함하는 | `contains` |

## 5. 집계 표현

| 표현 | 값 |
|---|---|
| 몇 개, 개수, 수량 | `count` |
| 총 길이 | `sum_length` |
| 총 면적 | `sum_area` |
| 평균 거리 | `avg_distance` |

## 6. 정규화 완료 조건

정규화 단계는 슬롯 추출 여부만 판정한다.

```text
NORMALIZED
```

다음 값이 아직 없어도 정상이다.

- `concept_id`
- `nftc_codes`
- `place_id`
- `target_agent`

단, 이 상태에서 `execution_ready=true`를 반환하면 안 된다.

## 7. 출력 Schema

```json
{
  "original_query": "string",
  "location_text": "string|null",
  "target_term": "string|null",
  "distance_m": "number|null",
  "spatial_relation": "dwithin|within_area|intersects|nearest|touches|contains|null",
  "aggregate": "count|sum_length|sum_area|avg_distance|null",
  "requested_limit": "integer|null",
  "output_format": "geojson|table|map|report",
  "normalization_status": "NORMALIZED|INCOMPLETE",
  "missing_slots": []
}
```
