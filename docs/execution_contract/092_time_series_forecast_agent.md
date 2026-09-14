# Phase 10 Time-Series Forecast Agent

## Purpose

Phase 10 adds a read-only Time-Series Forecast Agent that returns future values with confidence intervals. It can call a configured model endpoint, but it never fabricates unavailable source observations.

## Added Components

- `services/time_series_agent/forecast_agent.py`
- `services.time_series_agent.tools.forecast_time_series`
- Agent registry entry: `Time-Series Forecast Agent`
- Tool registry entry: `timeseries.forecast`
- Query template: `observed_time_series_forecast`
- Capability route: `observed_time_series_forecast`

## Forecast Policy

- If `FORECAST_MODEL_ENDPOINT` or request `model_endpoint` is configured, the forecast tool POSTs observations to that endpoint.
- If no endpoint is configured, the tool uses `deterministic_linear_baseline`.
- The baseline is computed from valid observed rows only:
  - linear trend over observation index
  - median observation cadence for future timestamps
  - residual standard deviation for confidence intervals
- Forecast horizon is capped at `168` steps by the execution validator.
- `tidal_current_surface` remains blocked for value lookup until its binary grid parser is implemented.

## Output

The agent returns:

- forecast time
- forecast value
- lower bound
- upper bound
- confidence level
- method and model provenance
- point count and residual standard deviation

## Validation Commands

```powershell
docker exec geollm_backend python -m py_compile services/time_series_agent/forecast_agent.py services/time_series_agent/tools.py services/orchestrator/graph.py services/orchestrator/schema_binding_adapter.py services/orchestrator/execution_validator.py
docker exec geollm_backend python -c "from services.time_series_agent.tools import forecast_time_series; import json; r=forecast_time_series(dataset_id='sample_observation_timeseries', station_id='ST-001', horizon_steps=3, confidence_level=0.95); print(json.dumps({'status': r['status'], 'method': r.get('method'), 'steps': len(r.get('forecast', [])), 'first': r.get('forecast', [None])[0]}, ensure_ascii=False, indent=2))"
```

## Current Baseline

Fixture forecast validation:

- status: `PASS`
- method: `deterministic_linear_baseline`
- forecast steps: `3`
- first forecast time: `2026-01-01T06:00:00`
- confidence level: `0.95`

Agent validation:

- execution contract: `EXECUTION_READY`
- agent status: `COMPLETED`
- point count: `5`
- residual std: `3.201843219147371`

## Next Step

For operational forecasting, connect an approved model endpoint and register its version, training window, intended variables, and confidence interval semantics. The deterministic baseline is only a contract-complete fallback for file-backed observations.
