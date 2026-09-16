"""Ingest AIS/V-PASS major-route PNG tile inventories into PostGIS.

The major-route archives are nested ZIP -> monthly TAR -> Lzz/x/y.png tile
sets. This adapter records tile metadata and provenance without expanding the
large PNG payloads into the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tarfile
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
import yaml


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
DATA = ROOT / "data"
REPORTS = ROOT / "outputs" / "reports"


@dataclass(frozen=True)
class TileSource:
    layer_id: str
    layer_source: str
    source_asset: str
    tar_prefix: str


SOURCES = {
    "ais_major_route": TileSource("ais_major_route", "AIS", "AIS주요통항로분석.zip", "AIS"),
    "vpass_major_route": TileSource("vpass_major_route", "V-PASS", "V-PASS주요통항로분석.zip", "VPASS"),
}

TILE_RE = re.compile(r"^(?P<root>[^/]+)/L(?P<zoom>\d{2})/(?P<x>\d+)/(?P<y>\d+)\.png$", re.I)


def db_url() -> str:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL or POSTGIS_URL is required")
    return url


def db_connect():
    parsed = urlparse(db_url().replace("postgresql+psycopg2://", "postgresql://", 1))
    if parsed.scheme.startswith("postgresql") and parsed.hostname:
        return psycopg2.connect(
            dbname=(parsed.path or "").lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            connect_timeout=5,
        )
    return psycopg2.connect(db_url(), connect_timeout=5)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_tar_month(name: str, base_year: int) -> date | None:
    match = re.search(r"(?P<month>\d{2})M\.tar$", name, re.I)
    if not match:
        return None
    month = int(match.group("month"))
    if month < 1 or month > 12:
        return None
    return date(base_year, month, 1)


def tile_source_id(source: TileSource, tar_name: str, tile_path: str) -> str:
    raw = f"{source.layer_id}|{source.source_asset}|{tar_name}|{tile_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def iter_tile_rows(
    source: TileSource,
    *,
    base_year: int,
    months: set[str] | None,
    zooms: set[int] | None,
) -> Iterable[dict[str, Any]]:
    archive = DATASET / source.source_asset
    if not archive.exists():
        raise FileNotFoundError(f"source archive not found: {archive}")
    archive_hash = sha256_file(archive)
    with zipfile.ZipFile(archive) as zf:
        for tar_name in sorted(n for n in zf.namelist() if n.lower().endswith(".tar")):
            observed_month = parse_tar_month(tar_name, base_year)
            if not observed_month:
                continue
            month_key = f"{observed_month:%Y%m}"
            if months and month_key not in months:
                continue
            tar_bytes = zf.read(tar_name)
            with tarfile.open(fileobj=BytesIO(tar_bytes)) as tf:
                for member in tf:
                    if not member.isfile():
                        continue
                    normalized = member.name.replace("\\", "/")
                    match = TILE_RE.match(normalized)
                    if not match:
                        continue
                    zoom = int(match.group("zoom"))
                    if zooms and zoom not in zooms:
                        continue
                    tile_x = int(match.group("x"))
                    tile_y = int(match.group("y"))
                    provenance = {
                        "source_asset": f"Dataset/{source.source_asset}",
                        "source_member": tar_name,
                        "tile_path": normalized,
                        "source_sha256": archive_hash,
                        "ingestion_script": "scripts/ingest_dynamic_traffic_tiles.py",
                    }
                    yield {
                        "source_id": tile_source_id(source, tar_name, normalized),
                        "layer_id": source.layer_id,
                        "layer_source": source.layer_source,
                        "observed_month": observed_month,
                        "observed_at": datetime(observed_month.year, observed_month.month, 1, tzinfo=timezone.utc),
                        "zoom_level": zoom,
                        "tile_x": tile_x,
                        "tile_y": tile_y,
                        "tile_path": normalized,
                        "source_asset": f"Dataset/{source.source_asset}",
                        "source_member": tar_name,
                        "source_sha256": archive_hash,
                        "tile_size_bytes": int(member.size),
                        "properties": {"tile_matrix": f"L{zoom:02d}", "tile_x": tile_x, "tile_y": tile_y},
                        "provenance": provenance,
                    }


def ensure_tables(cur) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.dynamic_traffic_tile_archive (
            raw_id text PRIMARY KEY,
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            source_asset text NOT NULL,
            source_member text NOT NULL,
            source_sha256 text NOT NULL,
            tile_path text NOT NULL,
            tile_size_bytes integer NOT NULL,
            raw_properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS serving.dynamic_traffic_tile_layer (
            source_id text PRIMARY KEY,
            observed_at timestamptz NOT NULL,
            observed_month date NOT NULL,
            time_bucket text NOT NULL,
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            zoom_level integer NOT NULL,
            tile_x integer NOT NULL,
            tile_y integer NOT NULL,
            tile_path text NOT NULL,
            source_asset text NOT NULL,
            source_member text NOT NULL,
            source_sha256 text NOT NULL,
            tile_size_bytes integer NOT NULL,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_tile_archive_layer ON raw.dynamic_traffic_tile_archive (layer_id, layer_source)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_tile_layer_month ON serving.dynamic_traffic_tile_layer (observed_month, layer_source)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_tile_layer_zxy ON serving.dynamic_traffic_tile_layer (zoom_level, tile_x, tile_y)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dynamic_traffic_tile_layer_layer ON serving.dynamic_traffic_tile_layer (layer_id, layer_source)")


def insert_batch(cur, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    raw_values = [
        (
            r["source_id"],
            r["layer_id"],
            r["layer_source"],
            r["source_asset"],
            r["source_member"],
            r["source_sha256"],
            r["tile_path"],
            r["tile_size_bytes"],
            json.dumps(r["properties"], ensure_ascii=False, default=str),
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO raw.dynamic_traffic_tile_archive
          (raw_id, layer_id, layer_source, source_asset, source_member, source_sha256,
           tile_path, tile_size_bytes, raw_properties)
        VALUES %s
        ON CONFLICT (raw_id) DO UPDATE SET
          tile_size_bytes = EXCLUDED.tile_size_bytes,
          raw_properties = EXCLUDED.raw_properties,
          ingested_at = now()
        """,
        raw_values,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)",
    )
    serving_values = [
        (
            r["source_id"],
            r["observed_at"],
            r["observed_month"],
            "month",
            r["layer_id"],
            r["layer_source"],
            r["zoom_level"],
            r["tile_x"],
            r["tile_y"],
            r["tile_path"],
            r["source_asset"],
            r["source_member"],
            r["source_sha256"],
            r["tile_size_bytes"],
            json.dumps(r["properties"], ensure_ascii=False, default=str),
            json.dumps(r["provenance"], ensure_ascii=False, default=str),
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.dynamic_traffic_tile_layer
          (source_id, observed_at, observed_month, time_bucket, layer_id, layer_source,
           zoom_level, tile_x, tile_y, tile_path, source_asset, source_member,
           source_sha256, tile_size_bytes, properties, provenance)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          tile_size_bytes = EXCLUDED.tile_size_bytes,
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          ingested_at = now()
        """,
        serving_values,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)",
    )
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
        layer["layer_type"] = "dynamic_traffic_tile"
        layer["physical_table"] = "serving.dynamic_traffic_tile_layer"
        layer["raw_table"] = "raw.dynamic_traffic_tile_archive"
        layer["geometry_type"] = "raster_tile"
        layer["tile_path_column"] = "tile_path"
        layer["temporal_column"] = "observed_at"
        layer["time_bucket_column"] = "observed_month"
        layer["zoom_column"] = "zoom_level"
        layer["tile_x_column"] = "tile_x"
        layer["tile_y_column"] = "tile_y"
        layer["available_months"] = result["available_months"]
        layer["available_zooms"] = result["available_zooms"]
        layer["ingested_tiles"] = result["rows"]
        layer["last_ingested_at"] = datetime.now(timezone.utc).isoformat()
        layer.pop("expected_physical_table", None)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_report(results: list[dict[str, Any]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Dynamic Traffic Major Route Tile Ingestion", "", f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`", ""]
    for result in results:
        lines.append(
            f"- `{result['layer_id']}`: tiles={result['rows']}, months={', '.join(result['available_months'])}, zooms={result['available_zooms']}"
        )
    (REPORTS / "dynamic_traffic_tile_ingestion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ingest_source(cur, source: TileSource, *, base_year: int, months: set[str] | None, zooms: set[int] | None, replace: bool, batch_size: int) -> dict[str, Any]:
    if replace:
        cur.execute("DELETE FROM raw.dynamic_traffic_tile_archive WHERE layer_id = %s", (source.layer_id,))
        cur.execute("DELETE FROM serving.dynamic_traffic_tile_layer WHERE layer_id = %s", (source.layer_id,))
    count = 0
    seen_months: set[str] = set()
    seen_zooms: set[int] = set()
    batch: list[dict[str, Any]] = []
    for row in iter_tile_rows(source, base_year=base_year, months=months, zooms=zooms):
        batch.append(row)
        seen_months.add(f"{row['observed_month']:%Y%m}")
        seen_zooms.add(int(row["zoom_level"]))
        if len(batch) >= batch_size:
            count += insert_batch(cur, batch)
            batch.clear()
    count += insert_batch(cur, batch)
    return {
        "layer_id": source.layer_id,
        "rows": count,
        "table": "serving.dynamic_traffic_tile_layer",
        "available_months": sorted(seen_months),
        "available_zooms": sorted(seen_zooms),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest AIS/V-PASS major-route PNG tile inventories.")
    parser.add_argument("--layers", nargs="*", default=list(SOURCES), choices=sorted(SOURCES))
    parser.add_argument("--base-year", type=int, default=2023)
    parser.add_argument("--months", nargs="*", default=None, help="YYYYMM months to ingest")
    parser.add_argument("--zooms", nargs="*", type=int, default=None, help="Tile zoom levels, e.g. 7 8 9 10 11 12")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--update-registry", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    months = set(args.months) if args.months else None
    zooms = set(args.zooms) if args.zooms else None
    results = []
    with db_connect() as conn:
        with conn.cursor() as cur:
            ensure_tables(cur)
            for layer_id in args.layers:
                result = ingest_source(
                    cur,
                    SOURCES[layer_id],
                    base_year=args.base_year,
                    months=months,
                    zooms=zooms,
                    replace=args.replace,
                    batch_size=args.batch_size,
                )
                results.append(result)
            cur.execute("ANALYZE raw.dynamic_traffic_tile_archive")
            cur.execute("ANALYZE serving.dynamic_traffic_tile_layer")
        conn.commit()
    if args.update_registry:
        update_registry(results)
    write_report(results)
    print(json.dumps({"status": "OK", "results": results}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
