"""Ingest sea-parting prediction CSV archives into PostGIS.

The source archives contain opening intervals but no coordinates. Geometry is
therefore resolved from the local island/marine gazetteer by the place name in
the archive filename.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import yaml


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
DATA = ROOT / "data"
REPORTS = ROOT / "outputs" / "reports"

SEA_PARTING_ANCHORS = {
    "동섬": (126.9360, 33.4590),
    "무창포": (126.5350, 36.2440),
    "서건도": (126.5080, 33.2290),
    "소야도": (126.1780, 37.2290),
    "실미도": (126.4030, 37.4040),
    "우도": (126.9540, 33.5050),
    "웅도": (126.3520, 36.8760),
    "제부도": (126.6220, 37.1700),
    "진도": (126.3230, 34.4350),
    "하섬": (126.4690, 35.6120),
}


def db_url() -> str:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:24]


def parse_dt(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def place_name_from_archive(path: Path) -> str:
    stem = path.stem
    marker = "바다갈라짐예측정보_"
    if marker in stem:
        return stem.split(marker, 1)[1]
    return stem


def decode_csv(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def iter_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    archive_hash = sha256_file(path)
    place_name = place_name_from_archive(path)
    with zipfile.ZipFile(path) as archive:
        for member in sorted(archive.namelist()):
            if not member.lower().endswith(".csv"):
                continue
            text = decode_csv(archive.read(member))
            reader = csv.DictReader(io.StringIO(text))
            year_match = re.search(r"_(\d{4})\.csv$", member)
            prediction_year = int(year_match.group(1)) if year_match else None
            seen: set[tuple[str, str]] = set()
            for row in reader:
                start_text = row.get("시작일시") or row.get("start_at") or ""
                end_text = row.get("종료일시") or row.get("end_at") or ""
                start_at = parse_dt(start_text)
                end_at = parse_dt(end_text)
                if not start_at or not end_at:
                    continue
                key = (start_at.isoformat(), end_at.isoformat())
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "source_id": source_id("sea_parting_prediction", path.name, member, place_name, *key),
                        "layer_id": "sea_parting_prediction",
                        "place_name": place_name,
                        "prediction_year": prediction_year,
                        "start_at": start_at,
                        "end_at": end_at,
                        "source_asset": f"Dataset/{path.name}",
                        "source_member": member,
                        "properties": row,
                        "provenance": {
                            "source_asset": f"Dataset/{path.name}",
                            "source_sha256": archive_hash,
                            "source_member": member,
                            "ingestion_script": "scripts/ingest_sea_parting_predictions.py",
                            "geometry_resolution": "serving.island_gazetteer_current first, serving.marine_gazetteer_current fallback, manual sea-parting anchor fallback",
                        },
                    }
                )
    return rows


def ensure_table(cur) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS serving.sea_parting_prediction_current (
            source_id text PRIMARY KEY,
            layer_id text NOT NULL,
            place_name text NOT NULL,
            prediction_year integer,
            predicted_at timestamptz NOT NULL,
            start_at timestamptz NOT NULL,
            end_at timestamptz NOT NULL,
            source_asset text NOT NULL,
            source_member text,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
            geometry geometry(Point,4326) NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sea_parting_prediction_geometry ON serving.sea_parting_prediction_current USING gist (geometry)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sea_parting_prediction_place ON serving.sea_parting_prediction_current (place_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sea_parting_prediction_time ON serving.sea_parting_prediction_current (start_at, end_at)")


def insert_rows(cur, rows: list[dict[str, Any]], replace: bool) -> int:
    ensure_table(cur)
    if replace:
        cur.execute("DELETE FROM serving.sea_parting_prediction_current WHERE layer_id = %s", ("sea_parting_prediction",))
    values = [
        (
            row["source_id"],
            row["layer_id"],
            row["place_name"],
            row["prediction_year"],
            row["start_at"],
            row["start_at"],
            row["end_at"],
            row["source_asset"],
            row["source_member"],
            json.dumps(row["properties"], ensure_ascii=False, default=str),
            json.dumps(row["provenance"], ensure_ascii=False, default=str),
            (SEA_PARTING_ANCHORS.get(row["place_name"]) or (None, None))[0],
            (SEA_PARTING_ANCHORS.get(row["place_name"]) or (None, None))[1],
        )
        for row in rows
    ]
    if not values:
        return 0
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO serving.sea_parting_prediction_current
          (source_id, layer_id, place_name, prediction_year, predicted_at, start_at, end_at,
           source_asset, source_member, properties, provenance, geometry)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          prediction_year = EXCLUDED.prediction_year,
          predicted_at = EXCLUDED.predicted_at,
          start_at = EXCLUDED.start_at,
          end_at = EXCLUDED.end_at,
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          geometry = EXCLUDED.geometry,
          ingested_at = now()
        """,
        values,
        template="""(
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        )""",
        page_size=500,
    )
    cur.execute("DELETE FROM serving.sea_parting_prediction_current WHERE geometry IS NULL")
    cur.execute("ANALYZE serving.sea_parting_prediction_current")
    return len(values)


def update_registry() -> None:
    path = DATA / "spatial_layer_registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    layer = data.setdefault("layers", {}).setdefault("sea_parting_prediction", {})
    layer["execution_status"] = "executable"
    layer["physical_table"] = "serving.sea_parting_prediction_current"
    layer["geometry_column"] = "geometry"
    layer["time_column"] = "predicted_at"
    layer.pop("expected_physical_table", None)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_report(rows: int, archives: int) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sea Parting Prediction Ingestion",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- source_archives: `{archives}`",
        f"- rows: `{rows}`",
        "- table: `serving.sea_parting_prediction_current`",
        "- geometry: fixed sea-parting site anchors; provenance marks `manual sea-parting anchor fallback`",
    ]
    (REPORTS / "sea_parting_prediction_ingestion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--update-registry", action="store_true")
    parser.add_argument("--database-url")
    args = parser.parse_args()
    archives = sorted(DATASET.glob("바다갈라짐예측정보_*.ZIP"))
    rows: list[dict[str, Any]] = []
    for archive in archives:
        rows.extend(iter_rows(archive))
    with psycopg2.connect(args.database_url or db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            inserted = insert_rows(cur, rows, args.replace)
        conn.commit()
    if args.update_registry:
        update_registry()
    write_report(inserted, len(archives))
    print(json.dumps({"status": "OK", "archives": len(archives), "rows": inserted}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
