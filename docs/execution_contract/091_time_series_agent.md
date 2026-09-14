# Phase 9 Time-Series Agent

## Purpose

Phase 9 adds a deterministic, read-only Time-Series Agent for observation data. It returns statistical metrics, missing-value checks, and anomaly candidates without fabricating unavailable ocean-current values.

## Added Components

- `services/time_series_agent/tools.py`
- `services/time_series_agent/agent.py`
- `data/time_series_registry.yaml`
- `data/fixtures/time_series_observation_sample.csv`
- Agent registry entry: `Time-Series Agent`
- Tool registry entry: `timeseries.observation_analyze`
- Query template: `observed_time_series_analysis`
- Capability route: `observed_time_series_analysis`

## Execution Policy

- `tidal_current_surface` remains `metadata_only`.
- The agent does not infer or synthesize tidal current speed/direction from `Dataset/수치조류도_국내연안2025.zip`.
- Executable analysis requires either:
  - a registry dataset with a file path, timestamp column, and value column, or
  - explicit request filters such as `source_path`, `timestamp_column`, and `value_column`.
- Missing executable data returns `BLOCKED_DATA`.

## Metrics

The analyzer returns:

- row count and filtered row count
- value count
- missing count and missing rate
- invalid timestamp count
- mean, median, min, max
- population standard deviation
- Q1, Q3, IQR lower/upper bounds
- anomaly count
- anomaly rows from z-score and IQR checks

## Validation Commands

```powershell
docker exec geollm_backend python -m py_compile services/time_series_agent/agent.py services/time_series_agent/tools.py services/orchestrator/graph.py services/orchestrator/schema_binding_adapter.py services/orchestrator/execution_validator.py
docker exec geollm_backend python -c "from services.time_series_agent.tools import analyze_time_series; import json; r=analyze_time_series(dataset_id='sample_observation_timeseries', station_id='ST-001'); print(json.dumps({'status': r['status'], 'missing_rate': r['metrics']['missing_rate'], 'anomaly_count': r['metrics']['anomaly_count']}, ensure_ascii=False))"
```

## Current Baseline

Fixture validation:

- status: `PASS`
- station: `ST-001`
- filtered rows: `6`
- missing rate: `0.166667`
- anomaly count: `1`

Agent validation:

- status: `COMPLETED`
- summary: `Analyzed 6 time-series rows with missing_rate=0.166667 and anomalies=1.`

## Next Step

Implement a real observation ingestion adapter or parser for an authoritative time-series source. For `tidal_current_surface`, this still requires the binary grid specification before value lookup can become executable.
