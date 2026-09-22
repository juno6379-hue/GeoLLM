"""Validate registry declarations and live PostGIS spatial layer contracts."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = (ROOT / "data/spatial_layer_registry.yaml", ROOT / "data/traffic_layer_registry.yaml")
DEFAULT_REPORT = ROOT / "outputs/reports/spatial_layer_quality.json"
SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def load_layers(paths: tuple[Path, ...] = REGISTRIES) -> dict[str, dict[str, Any]]:
    layers: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for layer_id, layer in (payload.get("layers") or {}).items():
            layers[f"{path.stem}:{layer_id}"] = dict(layer or {})
    return layers


def validate_registry(layers: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for layer_id, layer in layers.items():
        status = layer.get("execution_status")
        if status not in {"executable", "metadata_only", "blocked"}:
            issues.append({"layer": layer_id, "code": "INVALID_EXECUTION_STATUS"})
        if status == "executable":
            for key in ("physical_table", "supported_operations"):
                if not layer.get(key):
                    issues.append({"layer": layer_id, "code": f"MISSING_{key.upper()}"})
            relation = str(layer.get("physical_table") or "")
            parts = relation.split(".")
            if len(parts) != 2 or not all(SAFE_IDENTIFIER.fullmatch(part) for part in parts):
                issues.append({"layer": layer_id, "code": "INVALID_PHYSICAL_TABLE"})
            if layer.get("layer_type") != "dynamic_traffic_tile" and not layer.get("geometry_column"):
                issues.append({"layer": layer_id, "code": "MISSING_GEOMETRY_COLUMN"})
            if layer.get("geometry_column") and not layer.get("srid"):
                issues.append({"layer": layer_id, "code": "MISSING_SRID"})
            if "time_space_lookup" in (layer.get("supported_operations") or []) and not (layer.get("time_column") or layer.get("temporal_column")):
                issues.append({"layer": layer_id, "code": "MISSING_TIME_COLUMN"})
        if status == "metadata_only" and not (layer.get("metadata_table") or layer.get("source_asset")):
            issues.append({"layer": layer_id, "code": "MISSING_METADATA_SOURCE"})
    return issues


def _geometry_stats(connection, relation: str, geometry_column: str, mode: str, sample_size: int) -> dict[str, Any]:
    schema, table_name = relation.split(".", 1)
    qualified = f'"{schema}"."{table_name}"'
    quoted = f'"{geometry_column}"'
    source = qualified if mode == "full" else f"(SELECT {quoted} FROM {qualified} WHERE {quoted} IS NOT NULL LIMIT {sample_size}) sampled"
    return dict(connection.execute(text(
        f"SELECT count(*) FILTER (WHERE {quoted} IS NOT NULL) non_null, "
        f"count(*) FILTER (WHERE {quoted} IS NOT NULL AND NOT ST_IsValid({quoted})) invalid, "
        f"array_remove(array_agg(DISTINCT ST_SRID({quoted})), NULL) srids FROM {source}"
    )).mappings().one())


def validate_database(layers: dict[str, dict[str, Any]], database_url: str, *, mode: str = "sample", sample_size: int = 10000, timeout_ms: int = 30000) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    engine = create_engine(database_url, pool_pre_ping=True)
    geometry_cache: dict[tuple[str, str], dict[str, Any]] = {}
    with engine.connect() as connection:
        connection.execute(text("SET statement_timeout = :timeout"), {"timeout": timeout_ms})
        for layer_id, layer in layers.items():
            if layer.get("execution_status") != "executable" or not layer.get("physical_table"):
                continue
            relation = str(layer["physical_table"])
            print(f"[spatial-quality] checking {layer_id} -> {relation}", file=sys.stderr, flush=True)
            exists = connection.scalar(text("SELECT to_regclass(:relation) IS NOT NULL"), {"relation": relation})
            if not exists:
                issues.append({"layer": layer_id, "code": "TABLE_NOT_FOUND", "relation": relation})
                continue
            columns = set(connection.scalars(text("""
                SELECT attribute.attname FROM pg_attribute attribute
                WHERE attribute.attrelid = to_regclass(:relation)
                  AND attribute.attnum > 0 AND NOT attribute.attisdropped
            """), {"relation": relation}))
            declared = [value for key, value in layer.items() if key.endswith("_column") and isinstance(value, str)]
            missing = sorted(set(declared) - columns)
            for column in missing:
                issues.append({"layer": layer_id, "code": "COLUMN_NOT_FOUND", "column": column})
            geometry_column = layer.get("geometry_column")
            if not geometry_column or geometry_column not in columns:
                continue
            cache_key = (relation, geometry_column)
            if cache_key not in geometry_cache:
                try:
                    geometry_cache[cache_key] = _geometry_stats(connection, relation, geometry_column, mode, sample_size)
                except Exception as exc:
                    issues.append({"layer": layer_id, "code": "GEOMETRY_SCAN_FAILED", "error": type(exc).__name__})
                    connection.rollback()
                    connection.execute(text("SET statement_timeout = :timeout"), {"timeout": timeout_ms})
                    continue
            stats = geometry_cache[cache_key]
            expected = int(layer.get("srid") or 0)
            observed = sorted(int(value) for value in (stats.get("srids") or []))
            if int(stats.get("invalid") or 0) > 0:
                issues.append({"layer": layer_id, "code": "INVALID_GEOMETRY", "count": int(stats["invalid"]), "mode": mode})
            if expected and observed and observed != [expected]:
                issues.append({"layer": layer_id, "code": "SRID_MISMATCH", "expected": expected, "observed": observed})
            schema, table_name = relation.split(".", 1)
            has_index = connection.scalar(text("""
                SELECT EXISTS (SELECT 1 FROM pg_indexes
                  WHERE schemaname=:schema AND tablename=:table AND indexdef ILIKE :needle)
            """), {"schema": schema, "table": table_name, "needle": f"%{geometry_column}%"})
            if not has_index:
                issues.append({"layer": layer_id, "code": "SPATIAL_INDEX_NOT_FOUND"})
            checks.append({"layer": layer_id, "relation": relation, "geometry_column": geometry_column,
                           "mode": mode, "checked_rows": int(stats.get("non_null") or 0),
                           "invalid": int(stats.get("invalid") or 0), "srids": observed,
                           "spatial_index": bool(has_index), "cache_reused": list(geometry_cache).index(cache_key) < len(checks)})
    return issues, checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-only", action="store_true")
    parser.add_argument("--database-url", default=os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL"))
    parser.add_argument("--mode", choices=("sample", "full"), default="sample")
    parser.add_argument("--sample-size", type=int, default=10000)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    layers = load_layers()
    issues = validate_registry(layers)
    checks: list[dict[str, Any]] = []
    if not args.registry_only:
        if not args.database_url:
            issues.append({"layer": "*", "code": "DATABASE_URL_NOT_CONFIGURED"})
        else:
            db_issues, checks = validate_database(layers, args.database_url, mode=args.mode, sample_size=args.sample_size, timeout_ms=args.timeout_ms)
            issues.extend(db_issues)
    report = {"status": "PASS" if not issues else "FAIL", "generated_at": datetime.now(timezone.utc).isoformat(),
              "mode": "registry" if args.registry_only else args.mode, "checked_layers": len(layers),
              "unique_geometry_scans": len({(item["relation"], item["geometry_column"]) for item in checks}),
              "checks": checks, "issues": issues}
    rendered = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered, flush=True)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())