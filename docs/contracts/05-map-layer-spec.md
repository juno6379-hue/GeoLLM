# Map Layer Specification

## 1. Pydantic Model
```python
class MapLayerSpecification(BaseModel):
    layer_id: str
    task_id: str
    title: str
    description: str
    geometry_type: str
    source_type: str
    source_uri: Optional[str] = None
    inline_geojson: Optional[Dict[str, Any]] = None
    source_crs: str = "EPSG:4326"
    display_crs: str = "EPSG:4326"
    style: Dict[str, Any] = Field(default_factory=dict)
    legend: Dict[str, Any] = Field(default_factory=dict)
    popup_fields: List[str] = Field(default_factory=list)
    label_field: Optional[str] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    visibility: bool = True
    z_index: int = 0
    valid_time: Optional[str] = None
    dataset_version: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
    feature_count: Optional[int] = None
```

## 2. JSON Schema
```json
{
  "properties": {
    "layer_id": {
      "title": "Layer Id",
      "type": "string"
    },
    "task_id": {
      "title": "Task Id",
      "type": "string"
    },
    "title": {
      "title": "Title",
      "type": "string"
    },
    "description": {
      "title": "Description",
      "type": "string"
    },
    "geometry_type": {
      "title": "Geometry Type",
      "type": "string"
    },
    "source_type": {
      "title": "Source Type",
      "type": "string"
    },
    "source_uri": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Uri"
    },
    "inline_geojson": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Inline Geojson"
    },
    "source_crs": {
      "default": "EPSG:4326",
      "title": "Source Crs",
      "type": "string"
    },
    "display_crs": {
      "default": "EPSG:4326",
      "title": "Display Crs",
      "type": "string"
    },
    "style": {
      "additionalProperties": true,
      "title": "Style",
      "type": "object"
    },
    "legend": {
      "additionalProperties": true,
      "title": "Legend",
      "type": "object"
    },
    "popup_fields": {
      "items": {
        "type": "string"
      },
      "title": "Popup Fields",
      "type": "array"
    },
    "label_field": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Label Field"
    },
    "min_zoom": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Min Zoom"
    },
    "max_zoom": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Max Zoom"
    },
    "visibility": {
      "default": true,
      "title": "Visibility",
      "type": "boolean"
    },
    "z_index": {
      "default": 0,
      "title": "Z Index",
      "type": "integer"
    },
    "valid_time": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Valid Time"
    },
    "dataset_version": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Dataset Version"
    },
    "provenance": {
      "additionalProperties": true,
      "title": "Provenance",
      "type": "object"
    },
    "feature_count": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Feature Count"
    }
  },
  "required": [
    "layer_id",
    "task_id",
    "title",
    "description",
    "geometry_type",
    "source_type"
  ],
  "title": "MapLayerSpecification",
  "type": "object"
}
```

## 3. 예제 Response
```json
{
  "layer_id": "string_value",
  "task_id": "string_value",
  "title": "string_value",
  "description": "string_value",
  "geometry_type": "string_value",
  "source_type": "string_value",
  "source_uri": null,
  "inline_geojson": null,
  "source_crs": "string_value",
  "display_crs": "string_value",
  "style": {},
  "legend": {},
  "popup_fields": [],
  "label_field": null,
  "min_zoom": null,
  "max_zoom": null,
  "visibility": true,
  "z_index": 123,
  "valid_time": null,
  "dataset_version": null,
  "provenance": {},
  "feature_count": null
}
```

## 4. 필드 설명 및 필수 여부
| 필드명 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `layer_id` | string | ✅ | - |
| `task_id` | string | ✅ | - |
| `title` | string | ✅ | - |
| `description` | string | ✅ | - |
| `geometry_type` | string | ✅ | - |
| `source_type` | string | ✅ | - |
| `source_uri` | any | ❌ | - |
| `inline_geojson` | any | ❌ | - |
| `source_crs` | string | ❌ | - |
| `display_crs` | string | ❌ | - |
| `style` | object | ❌ | - |
| `legend` | object | ❌ | - |
| `popup_fields` | array | ❌ | - |
| `label_field` | any | ❌ | - |
| `min_zoom` | any | ❌ | - |
| `max_zoom` | any | ❌ | - |
| `visibility` | boolean | ❌ | - |
| `z_index` | integer | ❌ | - |
| `valid_time` | any | ❌ | - |
| `dataset_version` | any | ❌ | - |
| `provenance` | object | ❌ | - |
| `feature_count` | any | ❌ | - |

## 5. Validation Rule
- 모든 필수 필드는 누락되어서는 안 됩니다.
- Pydantic의 기본 타입 체킹을 통과해야 합니다.

## 6. 오류 예제
```json
{
  "detail": [
    {
      "loc": ["body", "task_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 7. 버전관리 정책
- 유의적 버전(Semantic Versioning) 원칙을 따릅니다.
- 하위 호환성이 깨지는 변경 발생 시 새로운 API 버전(v2)으로 라우팅합니다.
