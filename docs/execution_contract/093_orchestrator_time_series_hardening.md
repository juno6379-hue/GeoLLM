# Orchestrator Time-Series/Forecast Hardening

## Purpose

This update strengthens the orchestrator after Phase 9 and Phase 10 without adding external data integration.

## Changes

- Added deterministic result-family detection in `services/orchestrator/graph.py`.
- Added time-series result validation:
  - metrics must be present
  - `missing_rate` must be numeric
  - `missing_rate > 0.30` triggers review
- Added forecast result validation:
  - forecast rows must be present
  - each row must include forecast value, lower bound, and upper bound
  - confidence interval ordering must be valid
- Adjusted data-discovery validation status for non-spatial time-series agents.
- Added final result packaging:
  - `time_series_result`
  - `forecast_result`

## Validation Baseline

Container checks passed:

- `python -m py_compile services/orchestrator/graph.py`
- Direct `validate_node` + `map_report_node` invocation for `Time-Series Agent`
- Direct `validate_node` + `map_report_node` invocation for `Time-Series Forecast Agent`

Expected final result fields:

- Time-series analysis:
  - `time_series_result.metrics`
  - `time_series_result.anomalies`
  - `validation_payload.time_series_validation`
- Forecast analysis:
  - `forecast_result.forecast`
  - `forecast_result.confidence_level`
  - `validation_payload.forecast_validation`

## Deferred

External datasets and model endpoints remain deferred. `tidal_current_surface` is still not promoted to executable value lookup until a real parser or API adapter is implemented.
