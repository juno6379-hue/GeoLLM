# Tool Result Contract

## 1. Pydantic Model
```python
class ToolResult(BaseModel):
    task_id: str
    trace_id: str
    tool_name: str
    tool_version: str
    status: str
    structured_result: Dict[str, Any] = Field(default_factory=dict)
    output_references: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time: float
    source_dataset_versions: List[DatasetVersion] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## 2. JSON Schema
```json
{
  "$defs": {
    "DatasetVersion": {
      "properties": {
        "dataset_id": {
          "title": "Dataset Id",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "string"
        }
      },
      "required": [
        "dataset_id",
        "version"
      ],
      "title": "DatasetVersion",
      "type": "object"
    }
  },
  "properties": {
    "task_id": {
      "title": "Task Id",
      "type": "string"
    },
    "trace_id": {
      "title": "Trace Id",
      "type": "string"
    },
    "tool_name": {
      "title": "Tool Name",
      "type": "string"
    },
    "tool_version": {
      "title": "Tool Version",
      "type": "string"
    },
    "status": {
      "title": "Status",
      "type": "string"
    },
    "structured_result": {
      "additionalProperties": true,
      "title": "Structured Result",
      "type": "object"
    },
    "output_references": {
      "items": {
        "type": "string"
      },
      "title": "Output References",
      "type": "array"
    },
    "metrics": {
      "additionalProperties": true,
      "title": "Metrics",
      "type": "object"
    },
    "warnings": {
      "items": {
        "type": "string"
      },
      "title": "Warnings",
      "type": "array"
    },
    "errors": {
      "items": {
        "type": "string"
      },
      "title": "Errors",
      "type": "array"
    },
    "execution_time": {
      "title": "Execution Time",
      "type": "number"
    },
    "source_dataset_versions": {
      "items": {
        "$ref": "#/$defs/DatasetVersion"
      },
      "title": "Source Dataset Versions",
      "type": "array"
    },
    "provenance": {
      "additionalProperties": true,
      "title": "Provenance",
      "type": "object"
    },
    "created_at": {
      "format": "date-time",
      "title": "Created At",
      "type": "string"
    }
  },
  "required": [
    "task_id",
    "trace_id",
    "tool_name",
    "tool_version",
    "status",
    "execution_time"
  ],
  "title": "ToolResult",
  "type": "object"
}
```

## 3. 예제 Response
```json
{
  "task_id": "string_value",
  "trace_id": "string_value",
  "tool_name": "string_value",
  "tool_version": "string_value",
  "status": "string_value",
  "structured_result": {},
  "output_references": [],
  "metrics": {},
  "warnings": [],
  "errors": [],
  "execution_time": 1.23,
  "source_dataset_versions": [],
  "provenance": {},
  "created_at": "string_value"
}
```

## 4. 필드 설명 및 필수 여부
| 필드명 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `task_id` | string | ✅ | - |
| `trace_id` | string | ✅ | - |
| `tool_name` | string | ✅ | - |
| `tool_version` | string | ✅ | - |
| `status` | string | ✅ | - |
| `structured_result` | object | ❌ | - |
| `output_references` | array | ❌ | - |
| `metrics` | object | ❌ | - |
| `warnings` | array | ❌ | - |
| `errors` | array | ❌ | - |
| `execution_time` | number | ✅ | - |
| `source_dataset_versions` | array | ❌ | - |
| `provenance` | object | ❌ | - |
| `created_at` | string | ❌ | - |

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
