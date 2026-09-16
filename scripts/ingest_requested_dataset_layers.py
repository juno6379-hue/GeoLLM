"""Ingest requested Dataset layers into PostGIS serving/knowledge tables."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import psycopg2
import psycopg2.extras
import shapefile
from shapely.geometry import shape as geojson_to_shape


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
REPORTS = ROOT / "outputs" / "reports"


@dataclass(frozen=True)
class LayerSpec:
    layer_id: str
    source_asset: str
    table: str
    name_fields: tuple[str, ...]
    kind: str


REQUESTED_SHAPE_LAYERS = [
    LayerSpec("anchorage_area", "정박지(면).zip", "serving.anchorage_area_current", ("NOBJNM", "OBJNAM", "OBJ_SN", "NAME"), "anchorage"),
    LayerSpec("anchorage_point", "정박지(점).zip", "serving.anchorage_point_current", ("NOBJNM", "OBJNAM", "OBJ_SN", "NAME"), "anchorage"),
    LayerSpec("fairway_area", "일반항로.zip", "serving.fairway_area_current", ("NOBJNM", "OBJNAM", "OBJ_SN", "NAME"), "fairway"),
    LayerSpec("traffic_separation_boundary", "통항분리경계선.zip", "serving.traffic_separation_boundary_current", ("NOBJNM", "OBJNAM", "OBJ_SN", "NAME"), "traffic_separation"),
    LayerSpec("entry_restricted_area", "진입제한.zip", "serving.hazard_area_current", ("NOBJNM", "OBJNAM", "OBJ_SN", "NAME"), "hazard"),
    LayerSpec("speed_restriction_area", "속도제한구역.zip", "serving.hazard_area_current", ("NAME", "NOBJNM", "OBJNAM", "OBJ_SN"), "hazard"),
    LayerSpec("island_gazetteer", "도서지명.zip", "serving.island_gazetteer_current", ("NP_HNM", "NP_ENM", "NAME"), "gazetteer"),
]


def db_url() -> str:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def split_relation(relation: str) -> tuple[str, str]:
    schema, table = relation.split(".", 1)
    return schema, table


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def read_cpg(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="ascii", errors="ignore").strip().lower()
    if raw in {"949", "cp949"}:
        return "cp949"
    if raw in {"utf_8", "utf-8"}:
        return "utf-8"
    return raw or None


def open_shapefile(path: Path) -> shapefile.Reader:
    encodings = [read_cpg(path.with_suffix(".cpg")), "utf-8", "cp949", "euc-kr"]
    last_error: Exception | None = None
    for encoding in [item for item in dict.fromkeys(encodings) if item]:
        try:
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
    raise RuntimeError(f"Cannot decode shapefile {path}: {last_error}")


def first_value(properties: dict[str, Any], names: Iterable[str]) -> str | None:
    for name in names:
        value = properties.get(name)
        if value not in (None, ""):
            return str(value)
    return None


def source_id(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def iter_shapefile_rows(spec: LayerSpec, max_records: int | None = None) -> Iterable[dict[str, Any]]:
    archive = DATASET / spec.source_asset
    archive_hash = sha256_file(archive)
    yielded = 0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmpdir)
        for shp_path in sorted(Path(tmpdir).rglob("*.shp")):
            prj_path = shp_path.with_suffix(".prj")
            native_srid = srid_from_prj(prj_path.read_text(encoding="utf-8", errors="ignore") if prj_path.exists() else None)
            reader = open_shapefile(shp_path)
            fields = [field[0] for field in reader.fields[1:]]
            try:
                for idx, shape_record in enumerate(reader.iterShapeRecords(), start=1):
                    props = dict(zip(fields, shape_record.record))
                    geom = geojson_to_shape(shape_record.shape.__geo_interface__)
                    if geom.is_empty:
                        continue
                    member = str(shp_path.relative_to(tmpdir)).replace("\\", "/")
                    yield {
                        "source_id": source_id(spec.layer_id, spec.source_asset, member, props.get("OBJECTID") or props.get("OBJ_SN") or idx),
                        "layer_id": spec.layer_id,
                        "source_asset": f"Dataset/{spec.source_asset}",
                        "source_member": member,
                        "name": first_value(props, spec.name_fields),
                        "native_srid": native_srid,
                        "properties": props,
                        "provenance": {
                            "source_asset": f"Dataset/{spec.source_asset}",
                            "source_sha256": archive_hash,
                            "source_member": member,
                            "ingestion_script": "scripts/ingest_requested_dataset_layers.py",
                        },
                        "wkt": geom.wkt,
                    }
                    yielded += 1
                    if max_records and yielded >= max_records:
                        return
            finally:
                reader.close()


def ensure_spatial_table(cur, relation: str) -> None:
    schema, table = split_relation(relation)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table} (
            source_id text PRIMARY KEY,
            layer_id text NOT NULL,
            source_asset text NOT NULL,
            source_member text,
            name text,
            native_srid integer NOT NULL,
            properties jsonb NOT NULL DEFAULT '{{}}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{{}}'::jsonb,
            geometry geometry(Geometry,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_geometry ON {schema}.{table} USING gist (geometry)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_layer_id ON {schema}.{table} (layer_id)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_properties ON {schema}.{table} USING gin (properties)")


def insert_spatial_rows(cur, spec: LayerSpec, rows: list[dict[str, Any]], replace: bool) -> int:
    ensure_spatial_table(cur, spec.table)
    schema, table = split_relation(spec.table)
    if replace:
        cur.execute(f"DELETE FROM {schema}.{table} WHERE layer_id = %s", (spec.layer_id,))
    deduped = {row["source_id"]: row for row in rows}
    values = [
        (
            row["source_id"], row["layer_id"], row["source_asset"], row["source_member"], row["name"], row["native_srid"],
            json.dumps(row["properties"], ensure_ascii=False, default=str),
            json.dumps(row["provenance"], ensure_ascii=False, default=str),
            row["wkt"], row["native_srid"],
        )
        for row in deduped.values()
    ]
    if not values:
        return 0
    psycopg2.extras.execute_values(
        cur,
        f"""
        INSERT INTO {schema}.{table}
          (source_id, layer_id, source_asset, source_member, name, native_srid, properties, provenance, geometry)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          name=EXCLUDED.name,
          properties=EXCLUDED.properties,
          provenance=EXCLUDED.provenance,
          geometry=EXCLUDED.geometry,
          ingested_at=now()
        """,
        values,
        template="""(
            %s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,
            ST_Force2D(ST_MakeValid(ST_Transform(ST_SetSRID(ST_GeomFromText(%s), %s), 4326)))
        )""",
        page_size=500,
    )
    cur.execute(f"ANALYZE {schema}.{table}")
    return len(values)


DMS_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*([NSEW])\s*$", re.I)


def dms_to_decimal(value: str) -> float:
    match = DMS_RE.match(value)
    if not match:
        raise ValueError(f"Unsupported DMS value: {value}")
    deg, minutes, seconds, hemi = match.groups()
    decimal = float(deg) + float(minutes) / 60 + float(seconds) / 3600
    if hemi.upper() in {"S", "W"}:
        decimal *= -1
    return decimal


def parse_navigation_aid_location(value: str) -> tuple[float, float]:
    lat_text, lon_text = [part.strip() for part in value.split(",", 1)]
    return dms_to_decimal(lon_text), dms_to_decimal(lat_text)


def ensure_navigation_aid_table(cur) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS serving.navigation_aid_current (
            source_id text PRIMARY KEY,
            layer_id text NOT NULL,
            aid_no text,
            name text,
            active boolean,
            address text,
            location_text text,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            geometry geometry(Point,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_navigation_aid_current_geometry ON serving.navigation_aid_current USING gist (geometry)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_navigation_aid_current_name ON serving.navigation_aid_current (name)")


def ingest_navigation_aids(cur, replace: bool) -> int:
    path = DATASET / "해양수산부 부산지방해양수산청_항로표지정보_20250623.csv"
    file_hash = sha256_file(path)
    ensure_navigation_aid_table(cur)
    if replace:
        cur.execute("DELETE FROM serving.navigation_aid_current WHERE layer_id = %s", ("navigation_aid_busan",))
    rows = []
    with path.open("r", encoding="cp949", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lon, lat = parse_navigation_aid_location(row["위치"])
            except Exception:
                continue
            rows.append((
                source_id("navigation_aid_busan", row.get("순번"), row.get("이름"), row.get("위치")),
                "navigation_aid_busan",
                row.get("순번"),
                row.get("이름"),
                row.get("사용 유무") == "Y",
                row.get("주소"),
                row.get("위치"),
                json.dumps(row, ensure_ascii=False),
                json.dumps({
                    "source_asset": "Dataset/해양수산부 부산지방해양수산청_항로표지정보_20250623.csv",
                    "source_sha256": file_hash,
                    "encoding": "cp949",
                    "ingestion_script": "scripts/ingest_requested_dataset_layers.py",
                }, ensure_ascii=False),
                lon,
                lat,
            ))
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.navigation_aid_current
          (source_id, layer_id, aid_no, name, active, address, location_text, properties, provenance, geometry)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          name=EXCLUDED.name,
          active=EXCLUDED.active,
          address=EXCLUDED.address,
          location_text=EXCLUDED.location_text,
          properties=EXCLUDED.properties,
          provenance=EXCLUDED.provenance,
          geometry=EXCLUDED.geometry,
          ingested_at=now()
        """,
        rows,
        template="(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,ST_SetSRID(ST_MakePoint(%s,%s),4326))",
        page_size=500,
    )
    cur.execute("ANALYZE serving.navigation_aid_current")
    return len(rows)


def ensure_marine_gazetteer_table(cur) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS serving.marine_gazetteer_current (
            source_id text PRIMARY KEY,
            layer_id text NOT NULL,
            name text NOT NULL,
            name_en text,
            place_type text,
            location_text text,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            geometry geometry(Geometry,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_marine_gazetteer_current_geometry ON serving.marine_gazetteer_current USING gist (geometry)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_marine_gazetteer_current_name ON serving.marine_gazetteer_current (name)")


def ingest_marine_gazetteer_csv(cur, replace: bool) -> int:
    path = DATASET / "해양수산부_공동활용체계_해양지명_20221231.csv"
    file_hash = sha256_file(path)
    ensure_marine_gazetteer_table(cur)
    if replace:
        cur.execute("DELETE FROM serving.marine_gazetteer_current WHERE layer_id = %s", ("marine_gazetteer_mof",))
    rows = []
    with path.open("r", encoding="cp949", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wkt = row.get("공간정보")
            name = row.get("지명명")
            if not wkt or not name:
                continue
            rows.append((
                source_id("marine_gazetteer_mof", row.get("공간정보일련번호"), name),
                "marine_gazetteer_mof",
                name,
                row.get("지명영문명"),
                row.get("토지유형"),
                row.get("해양지위치정보"),
                json.dumps(row, ensure_ascii=False),
                json.dumps({
                    "source_asset": "Dataset/해양수산부_공동활용체계_해양지명_20221231.csv",
                    "source_sha256": file_hash,
                    "encoding": "cp949",
                    "native_srid": 5179,
                    "ingestion_script": "scripts/ingest_requested_dataset_layers.py",
                }, ensure_ascii=False),
                wkt,
            ))
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.marine_gazetteer_current
          (source_id, layer_id, name, name_en, place_type, location_text, properties, provenance, geometry)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          name=EXCLUDED.name,
          name_en=EXCLUDED.name_en,
          place_type=EXCLUDED.place_type,
          location_text=EXCLUDED.location_text,
          properties=EXCLUDED.properties,
          provenance=EXCLUDED.provenance,
          geometry=EXCLUDED.geometry,
          ingested_at=now()
        """,
        rows,
        template="(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,ST_Transform(ST_SetSRID(ST_GeomFromText(%s),5179),4326))",
        page_size=500,
    )
    cur.execute("ANALYZE serving.marine_gazetteer_current")
    return len(rows)


def write_report(results: list[dict[str, Any]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Requested Dataset Layer Ingestion", "", f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`", ""]
    for item in results:
        lines.append(f"- `{item['layer_id']}` -> `{item['table']}`: `{item['rows']}` rows")
    (REPORTS / "requested_dataset_layer_ingestion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ingest(args: argparse.Namespace) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with psycopg2.connect(args.database_url or db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            if args.navigation_aids:
                rows = ingest_navigation_aids(cur, args.replace)
                results.append({"layer_id": "navigation_aid_busan", "table": "serving.navigation_aid_current", "rows": rows})
            if args.shape_layers:
                specs = REQUESTED_SHAPE_LAYERS if args.shape_layers == ["all"] else [s for s in REQUESTED_SHAPE_LAYERS if s.layer_id in set(args.shape_layers)]
                for spec in specs:
                    rows = list(iter_shapefile_rows(spec, max_records=args.max_records))
                    count = insert_spatial_rows(cur, spec, rows, args.replace)
                    results.append({"layer_id": spec.layer_id, "table": spec.table, "rows": count})
            if args.marine_gazetteer:
                rows = ingest_marine_gazetteer_csv(cur, args.replace)
                results.append({"layer_id": "marine_gazetteer_mof", "table": "serving.marine_gazetteer_current", "rows": rows})
        conn.commit()
    write_report(results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--navigation-aids", action="store_true")
    parser.add_argument("--marine-gazetteer", action="store_true")
    parser.add_argument("--shape-layers", nargs="*", default=[])
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all:
        args.navigation_aids = True
        args.marine_gazetteer = True
        args.shape_layers = ["all"]
    results = ingest(args)
    print(json.dumps({"status": "OK", "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
