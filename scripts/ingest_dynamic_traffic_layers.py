"""Ingest AIS/V-PASS monthly route-density grids into raw, standardized, and serving PostGIS tables."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import warnings
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import psycopg2
import psycopg2.extras
import shapefile
import yaml
from shapely.geometry import shape as geojson_to_shape


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
DATA = ROOT / "data"
REPORTS = ROOT / "outputs" / "reports"


@dataclass(frozen=True)
class TrafficSource:
    layer_id: str
    layer_source: str
    source_asset: str
    count_prefix: str


SOURCES = {
    "ais_route_analysis": TrafficSource("ais_route_analysis", "AIS", "AIS항로분석.zip", "AIS"),
    "vpass_route_analysis": TrafficSource("vpass_route_analysis", "V-PASS", "V-PASS항로분석.zip", "VPASS"),
}


def db_url() -> str:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL or POSTGIS_URL is required")
    return url


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_cpg(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="ascii", errors="ignore").strip().lower()
    if raw in {"949", "cp949"}:
        return "cp949"
    if raw in {"utf_8", "utf-8"}:
        return "utf-8"
    return raw or None


def srid_from_prj(text: str | None) -> int:
    if not text:
        return 4326
    lowered = text.lower()
    if "false_easting" in lowered and "1000000" in lowered and "central_meridian" in lowered and "127.5" in lowered:
        return 5179
    if "kgd2002_unified" in lowered or "korea_2000_unified" in lowered:
        return 5179
    if "wgs_1984" in lowered or "wgs 84" in lowered:
        return 4326
    return 4326


def open_shapefile(path: Path) -> shapefile.Reader:
    encodings = [read_cpg(path.with_suffix(".cpg")), "utf-8", "cp949", "euc-kr"]
    last_error: Exception | None = None
    for encoding in [item for item in dict.fromkeys(encodings) if item]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                reader = shapefile.Reader(str(path), encoding=encoding, encodingErrors="replace")
            _ = [field[0] for field in reader.fields[1:]]
            if len(reader):
                _ = reader.record(0)
            return reader
        except Exception as exc:
            last_error = exc
            try:
                reader.close()  # type: ignore[name-defined]
            except Exception:
                pass
    raise RuntimeError(f"failed to open shapefile {path.name}: {last_error}")


def parse_member_time(member_name: str) -> tuple[date, int] | None:
    match = re.search(r"_(20\d{4})_lv(\d+)\.shp$", member_name, re.I)
    if not match:
        return None
    yyyymm = match.group(1)
    return date(int(yyyymm[:4]), int(yyyymm[4:]), 1), int(match.group(2))


def source_id(source: TrafficSource, source_asset: str, member: str, idx: int, properties: dict[str, Any]) -> str:
    natural = properties.get("OG_ID") or idx
    raw = f"{source.layer_id}|{source_asset}|{member}|{natural}|{idx}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def iter_rows(source: TrafficSource, levels: set[int], months: set[str] | None, max_records: int | None) -> Iterable[dict[str, Any]]:
    archive = DATASET / source.source_asset
    if not archive.exists():
        raise FileNotFoundError(f"source archive not found: {archive}")
    archive_hash = sha256_file(archive)
    yielded = 0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmpdir)
        for shp_path in sorted(Path(tmpdir).rglob("*.shp")):
            parsed = parse_member_time(shp_path.name)
            if not parsed:
                continue
            observed_month, grid_level = parsed
            month_key = f"{observed_month:%Y%m}"
            if grid_level not in levels or (months and month_key not in months):
                continue
            prj_path = shp_path.with_suffix(".prj")
            native_srid = srid_from_prj(prj_path.read_text(encoding="utf-8", errors="ignore") if prj_path.exists() else None)
            reader = open_shapefile(shp_path)
            field_names = [field[0] for field in reader.fields[1:]]
            try:
                for idx, shape_record in enumerate(reader.iterShapeRecords(), start=1):
                    props = dict(zip(field_names, shape_record.record))
                    geom = geojson_to_shape(shape_record.shape.__geo_interface__)
                    if geom.is_empty:
                        continue
                    total = props.get(f"{source.count_prefix}_AT")
                    day = props.get(f"{source.count_prefix}_DT")
                    night = props.get(f"{source.count_prefix}_NT")
                    row_id = source_id(source, source.source_asset, shp_path.name, idx, props)
                    yield {
                        "source_id": row_id,
                        "layer_id": source.layer_id,
                        "layer_source": source.layer_source,
                        "source_asset": f"Dataset/{source.source_asset}",
                        "source_member": shp_path.name,
                        "source_sha256": archive_hash,
                        "record_index": idx,
                        "grid_id": str(props.get("OG_ID") or row_id),
                        "grid_level": grid_level,
                        "observed_month": observed_month,
                        "observed_at": datetime(observed_month.year, observed_month.month, 1, tzinfo=timezone.utc),
                        "vessel_count_total": int(total or 0),
                        "vessel_count_day": int(day or 0),
                        "vessel_count_night": int(night or 0),
                        "native_srid": native_srid,
                        "properties": props,
                        "provenance": {
                            "source_asset": f"Dataset/{source.source_asset}",
                            "source_member": shp_path.name,
                            "source_sha256": archive_hash,
                            "ingestion_script": "scripts/ingest_dynamic_traffic_layers.py",
                        },
                        "wkt": geom.wkt,
                    }
                    yielded += 1
                    if max_records and yielded >= max_records:
                        return
            finally:
                reader.close()


def ensure_tables(cur) -> None:
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
    cur.execute("CREATE SCHEMA IF NOT EXISTS standardized")
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.dynamic_traffic_archive_feature (
            raw_id text PRIMARY KEY,
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            source_asset text NOT NULL,
            source_member text NOT NULL,
            source_sha256 text NOT NULL,
            record_index integer NOT NULL,
            raw_properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            native_srid integer NOT NULL,
            raw_wkt text NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS standardized.dynamic_traffic_observation (
            observation_id text PRIMARY KEY,
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            grid_id text NOT NULL,
            grid_level integer NOT NULL,
            observed_month date NOT NULL,
            observed_at timestamptz NOT NULL,
            time_bucket text NOT NULL,
            vessel_identifier text,
            vessel_count_total integer NOT NULL,
            vessel_count_day integer NOT NULL,
            vessel_count_night integer NOT NULL,
            source_asset text NOT NULL,
            source_member text NOT NULL,
            native_srid integer NOT NULL,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            geom geometry(Geometry,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS serving.dynamic_traffic_layer (
            source_id text PRIMARY KEY,
            observed_at timestamptz NOT NULL,
            observed_month date NOT NULL,
            time_bucket text NOT NULL,
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            grid_id text NOT NULL,
            grid_level integer NOT NULL,
            vessel_identifier text,
            vessel_count_total integer NOT NULL,
            vessel_count_day integer NOT NULL,
            vessel_count_night integer NOT NULL,
            reference_place_id text,
            reference_place_name text,
            reference_distance_m double precision,
            source_asset text NOT NULL,
            source_member text NOT NULL,
            native_srid integer NOT NULL,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            geom geometry(Geometry,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute("CREATE TABLE IF NOT EXISTS serving.dynamic_traffic_reference_place (place_id text PRIMARY KEY, name text NOT NULL, geom geometry(Point,4326) NOT NULL)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_archive_feature_layer ON raw.dynamic_traffic_archive_feature (layer_id, layer_source)")
    for table in ["standardized.dynamic_traffic_observation", "serving.dynamic_traffic_layer"]:
        schema, name = table.split(".")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{name}_layer_time ON {schema}.{name} (layer_source, observed_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_observation_geom ON standardized.dynamic_traffic_observation USING gist (geom)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_layer_geom ON serving.dynamic_traffic_layer USING gist (geom)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_layer_month ON serving.dynamic_traffic_layer (observed_month, layer_source, grid_level)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_layer_place ON serving.dynamic_traffic_layer (reference_place_id)")


def insert_places(cur) -> None:
    registry_path = DATA / "place_geometry_registry.yaml"
    if not registry_path.exists():
        return
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    values = []
    for place_id, place in (data.get("places") or {}).items():
        wkt = place.get("geometry_wkt")
        if wkt:
            values.append((place_id, place.get("canonical_name") or place_id, wkt))
    if not values:
        return
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.dynamic_traffic_reference_place (place_id, name, geom)
        VALUES %s
        ON CONFLICT (place_id) DO UPDATE SET name = EXCLUDED.name, geom = EXCLUDED.geom
        """,
        values,
        template="(%s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326))",
    )


def insert_rows(cur, rows: list[dict[str, Any]], replace_layers: set[str]) -> int:
    ensure_tables(cur)
    insert_places(cur)
    if replace_layers:
        for layer_id in replace_layers:
            cur.execute("DELETE FROM raw.dynamic_traffic_archive_feature WHERE layer_id = %s", (layer_id,))
            cur.execute("DELETE FROM standardized.dynamic_traffic_observation WHERE layer_id = %s", (layer_id,))
            cur.execute("DELETE FROM serving.dynamic_traffic_layer WHERE layer_id = %s", (layer_id,))
    if not rows:
        return 0
    raw_values = [
        (
            r["source_id"], r["layer_id"], r["layer_source"], r["source_asset"], r["source_member"], r["source_sha256"],
            r["record_index"], json.dumps(r["properties"], ensure_ascii=False, default=str), r["native_srid"], r["wkt"],
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO raw.dynamic_traffic_archive_feature
          (raw_id, layer_id, layer_source, source_asset, source_member, source_sha256, record_index, raw_properties, native_srid, raw_wkt)
        VALUES %s
        ON CONFLICT (raw_id) DO UPDATE SET raw_properties = EXCLUDED.raw_properties, raw_wkt = EXCLUDED.raw_wkt, ingested_at = now()
        """,
        raw_values,
        template="(%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)",
    )
    common_values = [
        (
            r["source_id"], r["layer_id"], r["layer_source"], r["grid_id"], r["grid_level"], r["observed_month"],
            r["observed_at"], "month", None, r["vessel_count_total"], r["vessel_count_day"], r["vessel_count_night"],
            r["source_asset"], r["source_member"], r["native_srid"],
            json.dumps(r["properties"], ensure_ascii=False, default=str),
            json.dumps(r["provenance"], ensure_ascii=False, default=str),
            r["wkt"], r["native_srid"],
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO standardized.dynamic_traffic_observation
          (observation_id, layer_id, layer_source, grid_id, grid_level, observed_month, observed_at, time_bucket,
           vessel_identifier, vessel_count_total, vessel_count_day, vessel_count_night, source_asset, source_member,
           native_srid, properties, provenance, geom)
        VALUES %s
        ON CONFLICT (observation_id) DO UPDATE SET
          vessel_count_total = EXCLUDED.vessel_count_total,
          vessel_count_day = EXCLUDED.vessel_count_day,
          vessel_count_night = EXCLUDED.vessel_count_night,
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          geom = EXCLUDED.geom,
          ingested_at = now()
        """,
        common_values,
        template="""(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
            ST_Force2D(ST_MakeValid(ST_Transform(ST_SetSRID(ST_GeomFromText(%s), %s), 4326)))
        )""",
    )
    serving_values = [
        (
            r["source_id"], r["observed_at"], r["observed_month"], "month", r["layer_id"], r["layer_source"],
            r["grid_id"], r["grid_level"], None, r["vessel_count_total"], r["vessel_count_day"], r["vessel_count_night"],
            r["source_asset"], r["source_member"], r["native_srid"],
            json.dumps(r["properties"], ensure_ascii=False, default=str),
            json.dumps(r["provenance"], ensure_ascii=False, default=str),
            r["wkt"], r["native_srid"],
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.dynamic_traffic_layer
          (source_id, observed_at, observed_month, time_bucket, layer_id, layer_source, grid_id, grid_level,
           vessel_identifier, vessel_count_total, vessel_count_day, vessel_count_night, source_asset, source_member,
           native_srid, properties, provenance, geom)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          vessel_count_total = EXCLUDED.vessel_count_total,
          vessel_count_day = EXCLUDED.vessel_count_day,
          vessel_count_night = EXCLUDED.vessel_count_night,
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          geom = EXCLUDED.geom,
          ingested_at = now()
        """,
        serving_values,
        template="""(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
            ST_Force2D(ST_MakeValid(ST_Transform(ST_SetSRID(ST_GeomFromText(%s), %s), 4326)))
        )""",
    )
    layer_ids = sorted({r["layer_id"] for r in rows})
    cur.execute(
        """
        WITH nearest AS (
            SELECT DISTINCT ON (t.source_id)
                t.source_id,
                p.place_id,
                p.name,
                ST_Distance(t.geom::geography, p.geom::geography) AS distance_m
            FROM serving.dynamic_traffic_layer AS t
            CROSS JOIN serving.dynamic_traffic_reference_place AS p
            WHERE t.layer_id = ANY(%s)
            ORDER BY t.source_id, t.geom <-> p.geom
        )
        UPDATE serving.dynamic_traffic_layer AS t
        SET reference_place_id = nearest.place_id,
            reference_place_name = nearest.name,
            reference_distance_m = nearest.distance_m
        FROM nearest
        WHERE t.source_id = nearest.source_id
        """,
        (layer_ids,),
    )
    cur.execute("ANALYZE raw.dynamic_traffic_archive_feature")
    cur.execute("ANALYZE standardized.dynamic_traffic_observation")
    cur.execute("ANALYZE serving.dynamic_traffic_layer")
    return len(rows)


def update_registry(results: list[dict[str, Any]]) -> None:
    path = DATA / "traffic_layer_registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    layers = data.setdefault("layers", {})
    for result in results:
        if result["rows"] <= 0:
            continue
        layer = layers.setdefault(result["layer_id"], {})
        layer["execution_status"] = "executable"
        layer["physical_table"] = "serving.dynamic_traffic_layer"
        layer["raw_table"] = "raw.dynamic_traffic_archive_feature"
        layer["standardized_table"] = "standardized.dynamic_traffic_observation"
        layer["geometry_column"] = "geom"
        layer["temporal_column"] = "observed_at"
        layer["time_bucket_column"] = "observed_month"
        layer["count_column"] = "vessel_count_total"
        layer["grid_id_column"] = "grid_id"
        layer["grid_level_column"] = "grid_level"
        layer["reference_place_columns"] = ["reference_place_id", "reference_place_name", "reference_distance_m"]
        layer["srid"] = 4326
        layer["available_months"] = result["available_months"]
        layer["ingested_rows"] = result["rows"]
        layer["last_ingested_at"] = datetime.now(timezone.utc).isoformat()
        layer.pop("expected_physical_table", None)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_report(results: list[dict[str, Any]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Dynamic Traffic Layer Ingestion", "", f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`", ""]
    for result in results:
        lines.append(
            f"- `{result['layer_id']}`: rows={result['rows']}, months={', '.join(result['available_months'])}, levels={result['levels']}"
        )
    (REPORTS / "dynamic_traffic_ingestion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest AIS/V-PASS route-density grids into PostGIS.")
    parser.add_argument("--layers", nargs="*", default=list(SOURCES), choices=sorted(SOURCES))
    parser.add_argument("--levels", nargs="*", type=int, default=[1, 2], help="Grid levels to ingest. Use 1 2 3 4 5 for full detail.")
    parser.add_argument("--months", nargs="*", default=None, help="YYYYMM months to ingest. Defaults to all months in selected archives.")
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--update-registry", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    levels = set(args.levels)
    months = set(args.months) if args.months else None
    all_rows: list[dict[str, Any]] = []
    per_layer: dict[str, list[dict[str, Any]]] = {}
    for layer_id in args.layers:
        source = SOURCES[layer_id]
        rows = list(iter_rows(source, levels=levels, months=months, max_records=args.max_records))
        per_layer[layer_id] = rows
        all_rows.extend(rows)
    results = []
    with psycopg2.connect(db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            inserted = insert_rows(cur, all_rows, set(args.layers) if args.replace else set())
        conn.commit()
    for layer_id, rows in per_layer.items():
        results.append({
            "layer_id": layer_id,
            "rows": len(rows),
            "table": "serving.dynamic_traffic_layer",
            "levels": sorted({row["grid_level"] for row in rows}),
            "available_months": sorted({f"{row['observed_month']:%Y%m}" for row in rows}),
        })
    if args.update_registry:
        update_registry(results)
    write_report(results)
    print(json.dumps({"status": "OK", "inserted_rows": inserted, "results": results}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
