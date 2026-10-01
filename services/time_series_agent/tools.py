from __future__ import annotations

import csv
import json
import math
import os
import urllib.error
import urllib.request
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DEFAULT_REGISTRY = DATA / "time_series_registry.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _resolve_under_root(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    try:
        path = path.resolve()
        path.relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError(f"time-series source must stay under project root: {value}")
    return path


def _dataset_from_registry(dataset_id: str | None) -> dict[str, Any]:
    if not dataset_id:
        return {}
    registry = _load_yaml(DEFAULT_REGISTRY)
    return (registry.get("datasets") or {}).get(dataset_id, {})


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    for suffix in ("Z", "z"):
        if text.endswith(suffix):
            text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def _read_csv(path: Path, *, encoding: str = "utf-8-sig") -> list[dict[str, Any]]:
    with path.open("r", encoding=encoding, newline="") as fh:
        return list(csv.DictReader(fh))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _read_rows(path: Path, *, encoding: str = "utf-8-sig") -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path, encoding=encoding)
    if suffix in {".jsonl", ".ndjson"}:
        return _read_jsonl(path)
    raise ValueError(f"unsupported time-series source format: {path.suffix}")


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _z_value(confidence_level: float) -> float:
    if confidence_level >= 0.99:
        return 2.576
    if confidence_level >= 0.95:
        return 1.96
    if confidence_level >= 0.90:
        return 1.645
    return 1.282


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return ordered[int(pos)]
    return ordered[lower] * (upper - pos) + ordered[upper] * (pos - lower)


def analyze_time_series(
    *,
    dataset_id: str | None = None,
    source_path: str | None = None,
    timestamp_column: str | None = None,
    value_column: str | None = None,
    station_column: str | None = None,
    station_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    z_threshold: float = 3.0,
) -> dict[str, Any]:
    dataset = _dataset_from_registry(dataset_id)
    source = source_path or dataset.get("path")
    path = _resolve_under_root(source)
    if not path:
        return {
            "status": "BLOCKED_DATA",
            "blockers": ["BLOCKED_DATA: time-series source_path is required"],
            "dataset_id": dataset_id,
        }
    if not path.exists():
        return {
            "status": "BLOCKED_DATA",
            "blockers": [f"BLOCKED_DATA: time-series source not found: {path}"],
            "dataset_id": dataset_id,
            "source_path": str(path),
        }

    timestamp_column = timestamp_column or dataset.get("timestamp_column") or "observed_at"
    value_column = value_column or dataset.get("value_column") or "value"
    station_column = station_column or dataset.get("station_column") or "station_id"
    rows = _read_rows(path, encoding=dataset.get("encoding", "utf-8-sig"))
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)

    filtered: list[dict[str, Any]] = []
    values: list[float] = []
    missing = 0
    invalid_time = 0
    for row in rows:
        if station_id and str(row.get(station_column, "")).strip() != str(station_id):
            continue
        observed_at = _parse_time(row.get(timestamp_column))
        if row.get(timestamp_column) and not observed_at:
            invalid_time += 1
        if start_dt and observed_at and observed_at < start_dt:
            continue
        if end_dt and observed_at and observed_at > end_dt:
            continue
        value = _to_float(row.get(value_column))
        if value is None:
            missing += 1
        else:
            values.append(value)
        filtered.append({"observed_at": observed_at, "value": value, "raw": row})

    if not filtered:
        return {
            "status": "NO_DATA",
            "dataset_id": dataset_id,
            "source_path": str(path),
            "row_count": len(rows),
            "filtered_count": 0,
            "blockers": [],
        }

    value_count = len(values)
    avg = mean(values) if values else None
    stddev = pstdev(values) if len(values) > 1 else 0.0
    q1 = _quantile(values, 0.25)
    q3 = _quantile(values, 0.75)
    anomalies: list[dict[str, Any]] = []
    iqr_lower = None
    iqr_upper = None
    if q1 is not None and q3 is not None and q3 >= q1:
        iqr = q3 - q1
        iqr_lower = q1 - 1.5 * iqr
        iqr_upper = q3 + 1.5 * iqr
    if values and stddev and stddev > 0:
        for item in filtered:
            value = item["value"]
            if value is None:
                continue
            z_score = (value - avg) / stddev
            if abs(z_score) >= z_threshold:
                anomalies.append({
                    "observed_at": item["observed_at"].isoformat() if item["observed_at"] else None,
                    "value": value,
                    "z_score": round(z_score, 4),
                    "method": "z_score",
                })
    if iqr_lower is not None and iqr_upper is not None:
        existing = {(item.get("observed_at"), item.get("value")) for item in anomalies}
        for item in filtered:
            value = item["value"]
            if value is None:
                continue
            key = (item["observed_at"].isoformat() if item["observed_at"] else None, value)
            if key in existing:
                continue
            if value < iqr_lower or value > iqr_upper:
                anomalies.append({
                    "observed_at": key[0],
                    "value": value,
                    "method": "iqr",
                    "iqr_lower": iqr_lower,
                    "iqr_upper": iqr_upper,
                })

    observed_times = [item["observed_at"] for item in filtered if item["observed_at"]]
    metrics = {
        "row_count": len(rows),
        "filtered_count": len(filtered),
        "value_count": value_count,
        "missing_count": missing,
        "missing_rate": round(missing / len(filtered), 6),
        "invalid_time_count": invalid_time,
        "mean": avg,
        "median": median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "stddev_population": stddev,
        "q1": q1,
        "q3": q3,
        "iqr_lower": iqr_lower,
        "iqr_upper": iqr_upper,
        "anomaly_count": len(anomalies),
        "z_threshold": z_threshold,
    }
    return {
        "status": "PASS",
        "dataset_id": dataset_id,
        "source_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "timestamp_column": timestamp_column,
        "value_column": value_column,
        "station_column": station_column,
        "station_id": station_id,
        "time_range": {
            "start": min(observed_times).isoformat() if observed_times else None,
            "end": max(observed_times).isoformat() if observed_times else None,
        },
        "metrics": metrics,
        "anomalies": anomalies[:100],
        "sample": [
            {
                "observed_at": item["observed_at"].isoformat() if item["observed_at"] else None,
                "value": item["value"],
            }
            for item in filtered[:10]
        ],
    }


def _load_filtered_points(
    *,
    dataset_id: str | None = None,
    source_path: str | None = None,
    timestamp_column: str | None = None,
    value_column: str | None = None,
    station_column: str | None = None,
    station_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    dataset = _dataset_from_registry(dataset_id)
    source = source_path or dataset.get("path")
    path = _resolve_under_root(source)
    if not path or not path.exists():
        return {
            "status": "BLOCKED_DATA",
            "blockers": [f"BLOCKED_DATA: time-series source not found: {source}"],
            "points": [],
        }
    timestamp_column = timestamp_column or dataset.get("timestamp_column") or "observed_at"
    value_column = value_column or dataset.get("value_column") or "value"
    station_column = station_column or dataset.get("station_column") or "station_id"
    rows = _read_rows(path, encoding=dataset.get("encoding", "utf-8-sig"))
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    points: list[tuple[datetime, float]] = []
    for row in rows:
        if station_id and str(row.get(station_column, "")).strip() != str(station_id):
            continue
        observed_at = _parse_time(row.get(timestamp_column))
        value = _to_float(row.get(value_column))
        if not observed_at or value is None:
            continue
        if start_dt and observed_at < start_dt:
            continue
        if end_dt and observed_at > end_dt:
            continue
        points.append((observed_at, value))
    points.sort(key=lambda item: item[0])
    return {
        "status": "PASS",
        "points": points,
        "source_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "timestamp_column": timestamp_column,
        "value_column": value_column,
        "station_column": station_column,
    }


def _call_forecast_endpoint(endpoint: str, payload: dict[str, Any], timeout_sec: int = 20) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "BLOCKED_CONFIG", "blockers": [f"BLOCKED_CONFIG: forecast endpoint failed: {type(exc).__name__}: {exc}"]}


def forecast_time_series(
    *,
    dataset_id: str | None = None,
    source_path: str | None = None,
    timestamp_column: str | None = None,
    value_column: str | None = None,
    station_column: str | None = None,
    station_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    horizon_steps: int = 3,
    confidence_level: float = 0.95,
    model_endpoint: str | None = None,
) -> dict[str, Any]:
    loaded = _load_filtered_points(
        dataset_id=dataset_id,
        source_path=source_path,
        timestamp_column=timestamp_column,
        value_column=value_column,
        station_column=station_column,
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
    )
    if loaded.get("status") != "PASS":
        return loaded
    points: list[tuple[datetime, float]] = loaded["points"]
    if len(points) < 2:
        return {
            "status": "BLOCKED_DATA",
            "blockers": ["BLOCKED_DATA: at least two valid observations are required for forecasting"],
            "point_count": len(points),
        }
    horizon_steps = max(1, min(int(horizon_steps), 168))
    confidence_level = max(0.5, min(float(confidence_level), 0.99))
    endpoint = model_endpoint or os.getenv("FORECAST_MODEL_ENDPOINT")
    endpoint_payload = {
        "dataset_id": dataset_id,
        "station_id": station_id,
        "horizon_steps": horizon_steps,
        "confidence_level": confidence_level,
        "observations": [{"observed_at": t.isoformat(), "value": v} for t, v in points],
    }
    if endpoint:
        endpoint_result = _call_forecast_endpoint(endpoint, endpoint_payload)
        if endpoint_result.get("status") in {"PASS", "COMPLETED"}:
            endpoint_result.setdefault("method", "model_endpoint")
            endpoint_result.setdefault("model_endpoint", endpoint)
            return endpoint_result
        return endpoint_result

    xs = list(range(len(points)))
    ys = [value for _, value in points]
    x_bar = mean(xs)
    y_bar = mean(ys)
    denom = sum((x - x_bar) ** 2 for x in xs)
    slope = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys)) / denom if denom else 0.0
    intercept = y_bar - slope * x_bar
    fitted = [intercept + slope * x for x in xs]
    residuals = [y - y_hat for y, y_hat in zip(ys, fitted)]
    residual_std = pstdev(residuals) if len(residuals) > 1 else 0.0
    if residual_std == 0:
        residual_std = pstdev(ys) if len(ys) > 1 else 0.0
    deltas = [
        (points[idx][0] - points[idx - 1][0]).total_seconds()
        for idx in range(1, len(points))
        if (points[idx][0] - points[idx - 1][0]).total_seconds() > 0
    ]
    cadence_seconds = median(deltas) if deltas else 3600.0
    last_time = points[-1][0]
    z = _z_value(confidence_level)
    forecasts = []
    for step in range(1, horizon_steps + 1):
        x = len(points) - 1 + step
        y_hat = intercept + slope * x
        interval = z * residual_std * math.sqrt(1.0 + step / max(len(points), 1))
        forecasts.append({
            "step": step,
            "forecast_time": (last_time + timedelta(seconds=cadence_seconds * step)).isoformat(),
            "forecast_value": y_hat,
            "lower_bound": y_hat - interval,
            "upper_bound": y_hat + interval,
        })
    return {
        "status": "PASS",
        "method": "deterministic_linear_baseline",
        "dataset_id": dataset_id,
        "station_id": station_id,
        "source_path": loaded.get("source_path"),
        "timestamp_column": loaded.get("timestamp_column"),
        "value_column": loaded.get("value_column"),
        "point_count": len(points),
        "horizon_steps": horizon_steps,
        "confidence_level": confidence_level,
        "cadence_seconds": cadence_seconds,
        "model": {
            "intercept": intercept,
            "slope_per_step": slope,
            "residual_std": residual_std,
        },
        "forecast": forecasts,
        "provenance": {
            "model_endpoint": None,
            "fallback_reason": "FORECAST_MODEL_ENDPOINT not configured",
        },
    }
