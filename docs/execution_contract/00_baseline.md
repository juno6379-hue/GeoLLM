# Execution Contract Baseline

Status: PARTIAL
Run ID: 20260914-132336

## Runtime

- Workspace: `D:\An_GeoLLM`
- Backend container checked: `geollm_backend`
- Active chat model setting: `LLM_MODEL=gemma2`
- Active embedding model setting: `EMBEDDING_MODEL=bge-m3`
- Ollama endpoint is configured through `host.docker.internal:11434`.
- Backend DB routing uses Docker DNS `db`.

## Read-only DB Observations

Checked from backend container with read-only `SELECT` statements.

| Logical target | DB env | Exists | Count | Notes |
|---|---:|---:|---:|---|
| `projection.s101_feature_valid` | `S101_DB_URL` | yes | 787102 | relation is in `gbhd_s101`, not `marine_geo` |
| `serving.accident_s101_relation_current` | `S101_DB_URL` | yes | 23180 | relation row count, not unique accident count |
| `projection.s101_feature_valid` | `POSTGIS_URL` | no | n/a | not present in `marine_geo` |
| `serving.accident_s101_relation_current` | `POSTGIS_URL` | no | n/a | not present in `marine_geo` |

Confirmed columns:

- `projection.s101_feature_valid.geometry`: `geometry(Geometry,4326)`
- `projection.s101_feature_valid.feature_instance_id`: `bigint`
- `projection.s101_feature_valid.feature_type_name`: `text`
- `serving.accident_s101_relation_current.distance_meters`: `numeric`
- `serving.accident_s101_relation_current.accident_geometry`: `geometry(Point,4326)`
- `serving.accident_s101_relation_current.anchor_geometry`: `geometry(Point,4326)`

Lightweight geometry checks:

- `original_geometry_valid is false`: 0
- `geometry is null`: 0

`ST_IsValid(geometry)` full scan was started but manually interrupted after exceeding the baseline budget. It is recorded as `NOT_RUN` for this session.

## Existing Implementation Baseline

- `ExecutionSlots` and `QueryExecutionContext` already existed in `shared.schemas.agent`.
- Orchestrator already carries `query_execution_context` into `AgentRequest`.
- Spatial agent already consumes `query_execution_context`, but the contract was missing version, request identity, revision, readiness, plan hash, binding and evidence fields.
- UI was already adjusted to show natural-language `answer_text`/`summary` rather than SQL in the user-facing result panel.

## Test Baseline

- Host pytest: `NOT_RUN`; host Python lacks project dependencies such as `pydantic` and `fastapi`.
- Container pytest: `NOT_RUN`; backend container lacks `pytest`.
- Container py_compile: `DONE` for modified runtime modules.
- Container contract smoke test: `DONE`.

