# Intent 판별 및 Agent 라우팅 규칙

## 1. 허용 Intent

```text
spatial_feature_search
spatial_feature_proximity_search
spatial_feature_within_area
spatial_feature_count
nearest_feature_search
spatial_intersection
spatial_buffer_analysis
geometry_measurement
feature_detail_search
map_report_generation
clarification_required
```

## 2. 슬롯 기반 fallback

LLM 결과가 `N/A`, `null`, `unknown`이어도 슬롯으로 의도를 복구한다.

| 조건 | Intent |
|---|---|
| location + target + distance | `spatial_feature_proximity_search` |
| location + target | `spatial_feature_within_area` |
| location + target + count | `spatial_feature_count` |
| target + nearest | `nearest_feature_search` |
| target A + target B + 교차 | `spatial_intersection` |
| target + 길이/면적 | `geometry_measurement` |

```python
def infer_intent(slots: dict) -> str:
    location = slots.get("location_text")
    target = slots.get("target_term")
    distance = slots.get("distance_m")
    aggregate = slots.get("aggregate")
    relation = slots.get("spatial_relation")

    if location and target and aggregate == "count":
        return "spatial_feature_count"

    if location and target and distance is not None:
        return "spatial_feature_proximity_search"

    if location and target:
        return "spatial_feature_within_area"

    if target and relation == "nearest":
        return "nearest_feature_search"

    return "clarification_required"
```

## 3. Agent 라우팅

| Intent | Agent |
|---|---|
| spatial_feature_search | `SpatialQueryAgent` |
| spatial_feature_proximity_search | `SpatialQueryAgent` |
| spatial_feature_within_area | `SpatialQueryAgent` |
| nearest_feature_search | `SpatialQueryAgent` |
| spatial_feature_count | `SpatialStatisticsAgent` |
| spatial_intersection | `SpatialAnalysisAgent` |
| spatial_buffer_analysis | `SpatialAnalysisAgent` |
| geometry_measurement | `SpatialAnalysisAgent` |
| map_report_generation | `MapReportAgent` |
| clarification_required | `ClarificationAgent` |

`MapReportAgent`는 최초 검색 에이전트가 아니다. 공간조회 또는 분석 결과가 생성된 이후 출력 표현 단계에서 호출한다.

## 4. Required Tools 결정

```text
ConceptResolver
PlaceResolver
SchemaRegistry
SRIDGuard
SQLTemplateCompiler
PostGISExecutor
GeoJSONFormatter
MapRenderer
```

예시:

```json
{
  "intent": "spatial_feature_proximity_search",
  "target_agent": "SpatialQueryAgent",
  "required_tools": [
    "ConceptResolver",
    "PlaceResolver",
    "SchemaRegistry",
    "SRIDGuard",
    "SQLTemplateCompiler",
    "PostGISExecutor"
  ]
}
```

## 5. 실행 준비 조건

```python
def is_execution_ready(state: dict) -> bool:
    return (
        state.get("intent") not in (None, "clarification_required")
        and state.get("target_agent") is not None
        and state.get("target", {}).get("resolution_status") == "RESOLVED"
        and state.get("location", {}).get("resolution_status") == "RESOLVED"
        and not state.get("unresolved_slots")
    )
```

상태 enum:

```text
NORMALIZED
NEEDS_CONCEPT_RESOLUTION
NEEDS_LOCATION_RESOLUTION
NEEDS_CLARIFICATION
READY
EXECUTING
COMPLETED
FAILED
```
