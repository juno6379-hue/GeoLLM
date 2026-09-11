"""Validate the S-101 v2 projection database connection and spatial layer.

The validator is intentionally read-only. It checks that the serving
projection exists, can be queried, has PostGIS and spatial indexes, and reports
geometry quality for projection.s101_feature_current.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "outputs/reports/s101_v2_db_validation.json"
DEFAULT_REPORT = ROOT / "outputs/reports/20_s101_v2_db_validation.md"


def connect(database_url: str):
    import psycopg2

    return psycopg2.connect(database_url, connect_timeout=5, options="-c client_min_messages=warning")


def fetch_one(cur, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
    cur.execute(sql, params or ())
    columns = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    return dict(zip(columns, row)) if row else {}


def fetch_all(cur, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    cur.execute(sql, params or ())
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def validate(database_url: str, max_invalid_samples: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projection": "projection.s101_feature_current",
        "connected": False,
    }

    with connect(database_url) as conn:
        with conn.cursor() as cur:
            result["connected"] = True
            result["database"] = fetch_one(cur, """
                SELECT current_database() AS database_name,
                       current_user AS database_user,
                       current_setting('server_version') AS server_version
            """)
            result["extensions"] = fetch_one(cur, """
                SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') AS postgis_enabled,
                       EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') AS pgvector_enabled
            """)
            result["tables"] = fetch_one(cur, """
                SELECT to_regclass('projection.s101_dataset_current') IS NOT NULL AS dataset_current,
                       to_regclass('projection.s101_feature_current') IS NOT NULL AS feature_current,
                       to_regclass('projection.s101_feature_geojson') IS NOT NULL AS feature_geojson
            """)

            if not result["tables"]["feature_current"]:
                result["ready"] = False
                result["issues"] = ["projection.s101_feature_current is missing"]
                return result

            result["indexes"] = fetch_all(cur, """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'projection'
                  AND tablename = 's101_feature_current'
                ORDER BY indexname
            """)
            result["summary"] = fetch_one(cur, """
                SELECT COUNT(*) AS feature_count,
                       COUNT(DISTINCT dataset_id) AS dataset_count,
                       COUNT(DISTINCT dataset_version_id) AS dataset_version_count,
                       COUNT(DISTINCT feature_type_code) AS feature_type_count,
                       COUNT(geometry) AS geometry_count,
                       COUNT(*) FILTER (WHERE geometry IS NULL) AS null_geometry_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL AND ST_IsEmpty(geometry)) AS empty_geometry_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL AND ST_SRID(geometry) = 4326) AS srid_4326_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL AND ST_SRID(geometry) <> 4326) AS srid_mismatch_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL AND ST_IsValid(geometry)) AS valid_geometry_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL AND NOT ST_IsValid(geometry)) AS invalid_geometry_count
                FROM projection.s101_feature_current
            """)
            result["bbox"] = fetch_one(cur, """
                SELECT ST_XMin(e)::numeric(12,6) AS xmin,
                       ST_YMin(e)::numeric(12,6) AS ymin,
                       ST_XMax(e)::numeric(12,6) AS xmax,
                       ST_YMax(e)::numeric(12,6) AS ymax
                FROM (
                    SELECT ST_Extent(geometry)::box2d AS e
                    FROM projection.s101_feature_current
                    WHERE geometry IS NOT NULL
                ) s
            """)
            if result["summary"]["invalid_geometry_count"]:
                result["geometry_types"] = fetch_all(cur, """
                    SELECT GeometryType(geometry) AS geometry_type,
                           COUNT(*) AS feature_count,
                           NULL::bigint AS invalid_geometry_count
                    FROM projection.s101_feature_current
                    WHERE geometry IS NOT NULL
                    GROUP BY 1
                    ORDER BY feature_count DESC
                """)
                result.setdefault("warnings", []).append(
                    "Skipped geometry-type invalid counts; use invalid sample query for detailed repair triage."
                )
            else:
                result["geometry_types"] = fetch_all(cur, """
                    SELECT GeometryType(geometry) AS geometry_type,
                           COUNT(*) AS feature_count,
                           0::bigint AS invalid_geometry_count
                    FROM projection.s101_feature_current
                    WHERE geometry IS NOT NULL
                    GROUP BY 1
                    ORDER BY feature_count DESC
                """)
            result["feature_type_top10"] = fetch_all(cur, """
                SELECT feature_type_code,
                       COUNT(*) AS feature_count,
                       COUNT(*) FILTER (WHERE geometry IS NOT NULL) AS geometry_count
                FROM projection.s101_feature_current
                GROUP BY feature_type_code
                ORDER BY feature_count DESC
                LIMIT 10
            """)
            if result["summary"]["invalid_geometry_count"]:
                result["invalid_geometry_samples"] = fetch_all(cur, """
                    SELECT feature_instance_id,
                           dataset_id,
                           feature_type_code,
                           GeometryType(geometry) AS geometry_type,
                           ST_IsValidReason(geometry) AS invalid_reason
                    FROM projection.s101_feature_current
                    WHERE geometry IS NOT NULL
                      AND NOT ST_IsValid(geometry)
                    ORDER BY feature_instance_id
                    LIMIT %s
                """, (max_invalid_samples,))
            else:
                result["invalid_geometry_samples"] = []
            result["geojson_projection"] = fetch_one(cur, """
                SELECT COUNT(*) AS feature_geojson_count
                FROM projection.s101_feature_geojson
            """) if result["tables"]["feature_geojson"] else {"feature_geojson_count": 0}

    indexes = result.get("indexes", [])
    has_gist = any("using gist" in row["indexdef"].lower() for row in indexes)
    summary = result["summary"]
    issues = []
    if not result["extensions"]["postgis_enabled"]:
        issues.append("PostGIS extension is not enabled")
    if not result["tables"]["feature_geojson"]:
        issues.append("projection.s101_feature_geojson is missing")
    if not has_gist:
        issues.append("GiST geometry index is missing on projection.s101_feature_current.geometry")
    if not summary["feature_count"]:
        issues.append("projection.s101_feature_current has no rows")
    if summary["null_geometry_count"]:
        issues.append(f"{summary['null_geometry_count']} features have NULL geometry")
    if summary["empty_geometry_count"]:
        issues.append(f"{summary['empty_geometry_count']} features have empty geometry")
    if summary["srid_mismatch_count"]:
        issues.append(f"{summary['srid_mismatch_count']} features are not SRID 4326")
    if summary["invalid_geometry_count"]:
        issues.append(f"{summary['invalid_geometry_count']} geometries are invalid")

    result["has_geometry_gist_index"] = has_gist
    result["ready"] = not issues
    result["issues"] = issues
    return result


def write_outputs(result: dict[str, Any], json_output: Path, report_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    summary = result.get("summary", {})
    bbox = result.get("bbox", {})
    lines = [
        "# S-101 v2 DB Connection and Spatial Validation",
        "",
        f"- generated_at: `{result['generated_at']}`",
        f"- projection: `{result['projection']}`",
        f"- connected: `{result['connected']}`",
        f"- ready: `{result.get('ready', False)}`",
        f"- feature_count: `{summary.get('feature_count', 0)}`",
        f"- geometry_count: `{summary.get('geometry_count', 0)}`",
        f"- invalid_geometry_count: `{summary.get('invalid_geometry_count', 0)}`",
        f"- srid_4326_count: `{summary.get('srid_4326_count', 0)}`",
        f"- bbox: `{bbox.get('xmin')}, {bbox.get('ymin')}, {bbox.get('xmax')}, {bbox.get('ymax')}`",
        "",
        "## Issues",
        "",
    ]
    issues = result.get("issues", [])
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("- none")
    lines += ["", "## Geometry Types", ""]
    lines.extend(
        f"- `{row['geometry_type']}`: `{row['feature_count']}` rows, invalid `{row['invalid_geometry_count']}`"
        for row in result.get("geometry_types", [])
    )
    lines += ["", "## Invalid Geometry Samples", ""]
    samples = result.get("invalid_geometry_samples", [])
    if samples:
        lines.extend(
            f"- feature_instance_id `{row['feature_instance_id']}`, feature_type_code `{row['feature_type_code']}`: {row['invalid_reason']}"
            for row in samples
        )
    else:
        lines.append("- none")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("S101_DB_URL"))
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-invalid-samples", type=int, default=10)
    parser.add_argument("--fail-on-issues", action="store_true")
    args = parser.parse_args()

    if not args.database_url:
        raise RuntimeError("S101_DB_URL or --database-url is required")

    result = validate(args.database_url, args.max_invalid_samples)
    write_outputs(result, args.json_output, args.report_output)
    print(json.dumps({
        "connected": result["connected"],
        "ready": result["ready"],
        "feature_count": result.get("summary", {}).get("feature_count", 0),
        "invalid_geometry_count": result.get("summary", {}).get("invalid_geometry_count", 0),
        "issues": result["issues"],
        "json_output": str(args.json_output),
        "report_output": str(args.report_output),
    }, ensure_ascii=False))
    if args.fail_on_issues and result["issues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
