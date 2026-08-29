# Agent Result Contract

## 1. Pydantic Model
```python
class AgentResult(BaseModel):
    task_id: str
    trace_id: str
    agent_name: str
    agent_version: str
    status: AgentStatus
    summary: Optional[str] = None
    structured_result: Dict[str, Any] = Field(default_factory=dict)
    features: Optional[str] = None  # URI to GeoJSON etc.
    metrics: Dict[str, Any] = Field(default_factory=dict)
    output_layers: List[MapOutputLayer] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    tool_calls: List[ToolCallLog] = Field(default_factory=list)
    source_dataset_versions: List[DatasetVersion] = Field(default_factory=list)
    validation_payload: Dict[str, Any] = Field(default_factory=dict)
    recommended_next_actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## 2. JSON Schema
```json
{
  "$defs": {
    "AgentStatus": {
      "enum": [
        "RECEIVED",
        "PARSING",
        "PLANNING",
        "WAITING_FOR_DATA",
        "EXECUTING",
        "PARTIAL",
        "VALIDATING",
        "WAITING_FOR_REVIEW",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "BLOCKED_BY_PERMISSION",
        "BLOCKED_BY_DATA_QUALITY"
      ],
      "title": "AgentStatus",
      "type": "string"
    },
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
    },
    "MapOutputLayer": {
      "properties": {
        "layer_id": {
          "title": "Layer Id",
          "type": "string"
        },
        "type": {
          "title": "Type",
          "type": "string"
        }
      },
      "required": [
        "layer_id",
        "type"
      ],
      "title": "MapOutputLayer",
      "type": "object"
    },
    "ToolCallLog": {
      "properties": {
        "tool_name": {
          "title": "Tool Name",
          "type": "string"
        },
        "status": {
          "title": "Status",
          "type": "string"
        },
        "execution_time_ms": {
          "title": "Execution Time Ms",
          "type": "integer"
        }
      },
      "required": [
        "tool_name",
        "status",
        "execution_time_ms"
      ],
      "title": "ToolCallLog",
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
    "agent_name": {
      "title": "Agent Name",
      "type": "string"
    },
    "agent_version": {
      "title": "Agent Version",
      "type": "string"
    },
    "status": {
      "$ref": "#/$defs/AgentStatus"
    },
    "summary": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Summary"
    },
    "structured_result": {
      "additionalProperties": true,
      "title": "Structured Result",
      "type": "object"
    },
    "features": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Features"
    },
    "metrics": {
      "additionalProperties": true,
      "title": "Metrics",
      "type": "object"
    },
    "output_layers": {
      "items": {
        "$ref": "#/$defs/MapOutputLayer"
      },
      "title": "Output Layers",
      "type": "array"
    },
    "evidence": {
      "items": {
        "type": "string"
      },
      "title": "Evidence",
      "type": "array"
    },
    "provenance": {
      "additionalProperties": true,
      "title": "Provenance",
      "type": "object"
    },
    "confidence": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Confidence"
    },
    "uncertainty": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Uncertainty"
    },
    "warnings": {
      "items": {
        "type": "string"
      },
      "title": "Warnings",
      "type": "array"
    },
    "tool_calls": {
      "items": {
        "$ref": "#/$defs/ToolCallLog"
      },
      "title": "Tool Calls",
      "type": "array"
    },
    "source_dataset_versions": {
      "items": {
        "$ref": "#/$defs/DatasetVersion"
      },
      "title": "Source Dataset Versions",
      "type": "array"
    },
    "validation_payload": {
      "additionalProperties": true,
      "title": "Validation Payload",
      "type": "object"
    },
    "recommended_next_actions": {
      "items": {
        "type": "string"
      },
      "title": "Recommended Next Actions",
      "type": "array"
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
    "agent_name",
    "agent_version",
    "status"
  ],
  "title": "AgentResult",
  "type": "object"
}
```

## 3. 예제 Response
```json
{
  "task_id": "string_value",
  "trace_id": "string_value",
  "agent_name": "string_value",
  "agent_version": "string_value",
  "status": null,
  "summary": null,
  "structured_result": {},
  "features": null,
  "metrics": {},
  "output_layers": [],
  "evidence": [],
  "provenance": {},
  "confidence": null,
  "uncertainty": null,
  "warnings": [],
  "tool_calls": [],
  "source_dataset_versions": [],
  "validation_payload": {},
  "recommended_next_actions": [],
  "created_at": "string_value"
}
```

## 4. 필드 설명 및 필수 여부
| 필드명 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `task_id` | string | ✅ | - |
| `trace_id` | string | ✅ | - |
| `agent_name` | string | ✅ | - |
| `agent_version` | string | ✅ | - |
| `status` | object (ref) | ✅ | - |
| `summary` | any | ❌ | - |
| `structured_result` | object | ❌ | - |
| `features` | any | ❌ | - |
| `metrics` | object | ❌ | - |
| `output_layers` | array | ❌ | - |
| `evidence` | array | ❌ | - |
| `provenance` | object | ❌ | - |
| `confidence` | any | ❌ | - |
| `uncertainty` | any | ❌ | - |
| `warnings` | array | ❌ | - |
| `tool_calls` | array | ❌ | - |
| `source_dataset_versions` | array | ❌ | - |
| `validation_payload` | object | ❌ | - |
| `recommended_next_actions` | array | ❌ | - |
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
