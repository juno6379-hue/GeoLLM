# Agent Request Contract

## 1. Pydantic Model
```python
class AgentRequest(BaseModel):
    task_id: str
    trace_id: str
    session_id: Optional[str] = None
    user_id: str
    organization_id: str
    agent_name: str
    original_query: str
    parsed_intent: Optional[Intent] = None
    spatial_context: Optional[SpatialContext] = None
    temporal_context: Optional[TemporalContext] = None
    available_datasets: List[DatasetVersion] = Field(default_factory=list)
    security_context: SecurityContext
    orchestrator_context: OrchestratorContext = Field(default_factory=OrchestratorContext)
    previous_agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    requested_outputs: List[str] = Field(default_factory=list)
    callback: Optional[str] = None
    idempotency_key: Optional[str] = None
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
    },
    "Intent": {
      "properties": {
        "intent_type": {
          "title": "Intent Type",
          "type": "string"
        },
        "target_objects": {
          "items": {
            "type": "string"
          },
          "title": "Target Objects",
          "type": "array"
        }
      },
      "required": [
        "intent_type"
      ],
      "title": "Intent",
      "type": "object"
    },
    "OrchestratorContext": {
      "properties": {
        "priority": {
          "default": "NORMAL",
          "title": "Priority",
          "type": "string"
        },
        "timeout_seconds": {
          "default": 300,
          "title": "Timeout Seconds",
          "type": "integer"
        }
      },
      "title": "OrchestratorContext",
      "type": "object"
    },
    "SecurityContext": {
      "properties": {
        "clearance_level": {
          "title": "Clearance Level",
          "type": "string"
        },
        "allowed_tool_scopes": {
          "items": {
            "type": "string"
          },
          "title": "Allowed Tool Scopes",
          "type": "array"
        }
      },
      "required": [
        "clearance_level"
      ],
      "title": "SecurityContext",
      "type": "object"
    },
    "SpatialContext": {
      "properties": {
        "base_location": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Base Location"
        },
        "geometry": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Geometry"
        },
        "buffer_distance": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Buffer Distance"
        },
        "crs": {
          "default": "EPSG:4326",
          "title": "Crs",
          "type": "string"
        }
      },
      "title": "SpatialContext",
      "type": "object"
    },
    "TemporalContext": {
      "properties": {
        "start_time": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Start Time"
        },
        "end_time": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "End Time"
        },
        "target_time": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Target Time"
        }
      },
      "title": "TemporalContext",
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
    "session_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Session Id"
    },
    "user_id": {
      "title": "User Id",
      "type": "string"
    },
    "organization_id": {
      "title": "Organization Id",
      "type": "string"
    },
    "agent_name": {
      "title": "Agent Name",
      "type": "string"
    },
    "original_query": {
      "title": "Original Query",
      "type": "string"
    },
    "parsed_intent": {
      "anyOf": [
        {
          "$ref": "#/$defs/Intent"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "spatial_context": {
      "anyOf": [
        {
          "$ref": "#/$defs/SpatialContext"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "temporal_context": {
      "anyOf": [
        {
          "$ref": "#/$defs/TemporalContext"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "available_datasets": {
      "items": {
        "$ref": "#/$defs/DatasetVersion"
      },
      "title": "Available Datasets",
      "type": "array"
    },
    "security_context": {
      "$ref": "#/$defs/SecurityContext"
    },
    "orchestrator_context": {
      "$ref": "#/$defs/OrchestratorContext"
    },
    "previous_agent_outputs": {
      "additionalProperties": true,
      "title": "Previous Agent Outputs",
      "type": "object"
    },
    "requested_outputs": {
      "items": {
        "type": "string"
      },
      "title": "Requested Outputs",
      "type": "array"
    },
    "callback": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Callback"
    },
    "idempotency_key": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Idempotency Key"
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
    "user_id",
    "organization_id",
    "agent_name",
    "original_query",
    "security_context"
  ],
  "title": "AgentRequest",
  "type": "object"
}
```

## 3. 예제 Request
```json
{
  "task_id": "string_value",
  "trace_id": "string_value",
  "session_id": null,
  "user_id": "string_value",
  "organization_id": "string_value",
  "agent_name": "string_value",
  "original_query": "string_value",
  "parsed_intent": null,
  "spatial_context": null,
  "temporal_context": null,
  "available_datasets": [],
  "security_context": null,
  "orchestrator_context": null,
  "previous_agent_outputs": {},
  "requested_outputs": [],
  "callback": null,
  "idempotency_key": null,
  "created_at": "string_value"
}
```

## 4. 필드 설명 및 필수 여부
| 필드명 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `task_id` | string | ✅ | - |
| `trace_id` | string | ✅ | - |
| `session_id` | any | ❌ | - |
| `user_id` | string | ✅ | - |
| `organization_id` | string | ✅ | - |
| `agent_name` | string | ✅ | - |
| `original_query` | string | ✅ | - |
| `parsed_intent` | any | ❌ | - |
| `spatial_context` | any | ❌ | - |
| `temporal_context` | any | ❌ | - |
| `available_datasets` | array | ❌ | - |
| `security_context` | object (ref) | ✅ | - |
| `orchestrator_context` | object (ref) | ❌ | - |
| `previous_agent_outputs` | object | ❌ | - |
| `requested_outputs` | array | ❌ | - |
| `callback` | any | ❌ | - |
| `idempotency_key` | any | ❌ | - |
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
