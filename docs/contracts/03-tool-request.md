# Tool Request Contract

## 1. Pydantic Model
```python
class ToolRequest(BaseModel):
    task_id: str
    trace_id: str
    agent_name: str
    tool_name: str
    tool_version: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_references: List[str] = Field(default_factory=list)
    security_context: SecurityContext
    timeout: int = 60
    idempotency_key: Optional[str] = None
```

## 2. JSON Schema
```json
{
  "$defs": {
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
    "tool_name": {
      "title": "Tool Name",
      "type": "string"
    },
    "tool_version": {
      "title": "Tool Version",
      "type": "string"
    },
    "operation": {
      "title": "Operation",
      "type": "string"
    },
    "parameters": {
      "additionalProperties": true,
      "title": "Parameters",
      "type": "object"
    },
    "input_references": {
      "items": {
        "type": "string"
      },
      "title": "Input References",
      "type": "array"
    },
    "security_context": {
      "$ref": "#/$defs/SecurityContext"
    },
    "timeout": {
      "default": 60,
      "title": "Timeout",
      "type": "integer"
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
    }
  },
  "required": [
    "task_id",
    "trace_id",
    "agent_name",
    "tool_name",
    "tool_version",
    "operation",
    "security_context"
  ],
  "title": "ToolRequest",
  "type": "object"
}
```

## 3. 예제 Request
```json
{
  "task_id": "string_value",
  "trace_id": "string_value",
  "agent_name": "string_value",
  "tool_name": "string_value",
  "tool_version": "string_value",
  "operation": "string_value",
  "parameters": {},
  "input_references": [],
  "security_context": null,
  "timeout": 123,
  "idempotency_key": null
}
```

## 4. 필드 설명 및 필수 여부
| 필드명 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `task_id` | string | ✅ | - |
| `trace_id` | string | ✅ | - |
| `agent_name` | string | ✅ | - |
| `tool_name` | string | ✅ | - |
| `tool_version` | string | ✅ | - |
| `operation` | string | ✅ | - |
| `parameters` | object | ❌ | - |
| `input_references` | array | ❌ | - |
| `security_context` | object (ref) | ✅ | - |
| `timeout` | integer | ❌ | - |
| `idempotency_key` | any | ❌ | - |

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
