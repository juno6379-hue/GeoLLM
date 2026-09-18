"""Dataset zip 공간자료를 PostGIS serving table로 적재한다.

기본 대상은 shapefile 기반의 비교적 작은 정적 공간 레이어다.
AIS/V-PASS처럼 대용량 동적 교통 레이어는 명시 옵션을 준 경우에만 처리한다.
"""
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
from datetime import datetime, timezone
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
REVIEW = ROOT / "outputs" / "review"


@dataclass(frozen=True)
class ShapefileLayerSpec:
    layer_id: str
    table: str
    source_assets: tuple[str, ...]
    name_fields: tuple[str, ...] = ()
    layer_source: str | None = None
    dynamic: bool = False


def _hazard_spec(layer_id: str, source_asset: str, *name_fields: str) -> ShapefileLayerSpec:
    return ShapefileLayerSpec(
        layer_id=layer_id,
        table="serving.hazard_area_current",
        source_assets=(source_asset,),
        name_fields=name_fields or ("NOBJNM", "OBJNAM", "NAME", "OBJ_SN", "OBJNUM"),
    )


STATIC_SPECS = {
    "island_gazetteer": ShapefileLayerSpec(
        layer_id="island_gazetteer",
        table="serving.island_gazetteer_current",
        source_assets=("Dataset/도서지명.zip",),
        name_fields=("NP_HNM", "NP_ENM"),
    ),
    "planned_port_area": ShapefileLayerSpec(
        layer_id="planned_port_area",
        table="serving.planned_port_area_current",
        source_assets=("Dataset/신항만예정지역.zip",),
        name_fields=("OBJ_SN",),
    ),
    "eddy_hazard_area": ShapefileLayerSpec(
        layer_id="eddy_hazard_area",
        table="serving.eddy_hazard_area_current",
        source_assets=("Dataset/와류.zip",),
        name_fields=("NOBJNM", "OBJNAM", "OBJNUM"),
    ),
    "vessel_traffic_control_area": ShapefileLayerSpec(
        layer_id="vessel_traffic_control_area",
        table="serving.vessel_traffic_control_area_current",
        source_assets=("Dataset/선박안전교통관제구역.zip",),
        name_fields=("OBJ_SN",),
    ),
    "caution_warning_area": _hazard_spec("caution_warning_area", "Dataset/주의경계해역.zip", "OBJ_SN"),
    "speed_restriction_area": _hazard_spec("speed_restriction_area", "Dataset/속도제한구역.zip", "NAME", "NOBJNM", "OBJNAM"),
    "entry_restricted_area": _hazard_spec("entry_restricted_area", "Dataset/진입제한.zip", "NOBJNM", "OBJNAM", "OBJ_SN"),
    "anchoring_prohibited_area": _hazard_spec("anchoring_prohibited_area", "Dataset/정박금지(투묘금지).zip", "NOBJNM", "OBJNAM", "OBJ_SN"),
    "fishing_prohibited_area": _hazard_spec("fishing_prohibited_area", "Dataset/낚시금지구역.zip", "NOBJNM", "OBJNAM", "OBJ_SN"),
    "fishing_restricted_area": _hazard_spec("fishing_restricted_area", "Dataset/낚시제한구역.zip", "NOBJNM", "OBJNAM", "OBJ_SN"),
    "dumping_ground_area": _hazard_spec("dumping_ground_area", "Dataset/투기장.zip", "NOBJNM", "OBJNAM", "OBJNUM"),
    "protected_sea_area": ShapefileLayerSpec(
        layer_id="protected_sea_area",
        table="serving.protected_area_current",
        source_assets=("Dataset/보호수역.zip",),
        name_fields=("NOBJNM", "OBJNAM", "OBJ_SN"),
    ),
}


DYNAMIC_SPECS = {
    "ais_route_analysis": ShapefileLayerSpec(
        layer_id="ais_route_analysis",
        table="serving.dynamic_traffic_layer",
        source_assets=("Dataset/AIS항로분석.zip",),
        name_fields=("OG_ID",),
        layer_source="AIS",
        dynamic=True,
    ),
    "vpass_route_analysis": ShapefileLayerSpec(
        layer_id="vpass_route_analysis",
        table="serving.dynamic_traffic_layer",
        source_assets=("Dataset/V-PASS항로분석.zip",),
        name_fields=("OG_ID",),
        layer_source="V-PASS",
        dynamic=True,
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def db_url() -> str:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL 또는 POSTGIS_URL 환경변수가 필요합니다.")
    return url


def split_relation(relation: str) -> tuple[str, str]:
    schema, table = relation.split(".", 1)
    return schema, table


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


def record_name(properties: dict[str, Any], fields: Iterable[str]) -> str | None:
    for field in fields:
        value = properties.get(field)
        if value not in (None, ""):
            return str(value)
    return None


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
    encodings = [read_cpg(path.with_suffix(".cpg")), "cp949", "euc-kr", "utf-8"]
    last_error: Exception | None = None
    attempts = [(encoding, "replace") for encoding in [item for item in dict.fromkeys(encodings) if item]]
    for encoding, errors in attempts:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                reader = shapefile.Reader(str(path), encoding=encoding, encodingErrors=errors)
            # 필드명과 첫 레코드를 실제로 읽어 인코딩 문제를 조기에 잡는다.
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
    raise RuntimeError(f"shapefile 인코딩 판독 실패: {path.name}: {last_error}")


def source_id(layer_id: str, source_asset: str, member: str, index: int, properties: dict[str, Any]) -> str:
    natural = properties.get("OBJECTID") or properties.get("OBJ_SN") or properties.get("OBJNUM") or properties.get("OG_ID") or index
    raw = f"{layer_id}|{source_asset}|{member}|{natural}|{index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def iter_shapefile_rows(spec: ShapefileLayerSpec, max_records: int | None = None) -> Iterable[dict[str, Any]]:
    yielded = 0
    for source_asset in spec.source_assets:
        archive = ROOT / source_asset
        if not archive.exists():
            raise FileNotFoundError(f"원천 archive를 찾을 수 없습니다: {source_asset}")
        archive_hash = sha256_file(archive)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with zipfile.ZipFile(archive) as z:
                z.extractall(tmpdir)
            for shp_path in sorted(Path(tmpdir).rglob("*.shp")):
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
                        yield {
                            "source_id": source_id(spec.layer_id, source_asset, shp_path.name, idx, props),
                            "layer_id": spec.layer_id,
                            "layer_source": spec.layer_source,
                            "source_asset": source_asset,
                            "source_member": str(shp_path.relative_to(tmpdir)).replace("\\", "/"),
                            "name": record_name(props, spec.name_fields),
                            "native_srid": native_srid,
                            "properties": props,
                            "provenance": {
                                "source_asset": source_asset,
                                "source_sha256": archive_hash,
                                "source_member": str(shp_path.relative_to(tmpdir)).replace("\\", "/"),
                                "ingestion_script": "scripts/ingest_spatial_layer_archives.py",
                            },
                            "wkt": geom.wkt,
                        }
                        yielded += 1
                        if max_records and yielded >= max_records:
                            return
                finally:
                    reader.close()


def ensure_static_table(cur, relation: str) -> None:
    schema, table = split_relation(relation)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(
        f"""
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
        """
    )
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_geometry ON {schema}.{table} USING gist (geometry)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_layer_id ON {schema}.{table} (layer_id)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_properties ON {schema}.{table} USING gin (properties)")


def ensure_dynamic_table(cur, relation: str) -> None:
    schema, table = split_relation(relation)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table} (
            source_id text PRIMARY KEY,
            observed_at timestamptz,
            ingested_at timestamptz NOT NULL DEFAULT now(),
            layer_id text NOT NULL,
            layer_source text NOT NULL,
            source_asset text NOT NULL,
            source_member text,
            native_srid integer NOT NULL,
            properties jsonb NOT NULL DEFAULT '{{}}'::jsonb,
            provenance jsonb NOT NULL DEFAULT '{{}}'::jsonb,
            geom geometry(Geometry,4326) NOT NULL
        )
        """
    )
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_geom ON {schema}.{table} USING gist (geom)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_source_time ON {schema}.{table} (layer_source, observed_at)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_layer_id ON {schema}.{table} (layer_id)")


def insert_static_rows(cur, spec: ShapefileLayerSpec, rows: list[dict[str, Any]], replace: bool) -> int:
    schema, table = split_relation(spec.table)
    ensure_static_table(cur, spec.table)
    if replace:
        cur.execute(f"DELETE FROM {schema}.{table} WHERE layer_id = %s", (spec.layer_id,))
    values = [
        (
            row["source_id"],
            row["layer_id"],
            row["source_asset"],
            row["source_member"],
            row["name"],
            row["native_srid"],
            json.dumps(row["properties"], ensure_ascii=False, default=str),
            json.dumps(row["provenance"], ensure_ascii=False, default=str),
            row["wkt"],
            row["native_srid"],
        )
        for row in rows
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
          name = EXCLUDED.name,
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          geometry = EXCLUDED.geometry,
          ingested_at = now()
        """,
        values,
        template="""(
            %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
            ST_Force2D(ST_MakeValid(ST_Transform(ST_SetSRID(ST_GeomFromText(%s), %s), 4326)))
        )""",
    )
    cur.execute(f"ANALYZE {schema}.{table}")
    return len(values)


def insert_dynamic_rows(cur, spec: ShapefileLayerSpec, rows: list[dict[str, Any]], replace: bool) -> int:
    schema, table = split_relation(spec.table)
    ensure_dynamic_table(cur, spec.table)
    if replace:
        cur.execute(f"DELETE FROM {schema}.{table} WHERE layer_id = %s", (spec.layer_id,))
    values = [
        (
            row["source_id"],
            row["layer_id"],
            row["layer_source"] or spec.layer_source or "UNKNOWN",
            row["source_asset"],
            row["source_member"],
            row["native_srid"],
            json.dumps(row["properties"], ensure_ascii=False, default=str),
            json.dumps(row["provenance"], ensure_ascii=False, default=str),
            row["wkt"],
            row["native_srid"],
        )
        for row in rows
    ]
    if not values:
        return 0
    psycopg2.extras.execute_values(
        cur,
        f"""
        INSERT INTO {schema}.{table}
          (source_id, layer_id, layer_source, source_asset, source_member, native_srid, properties, provenance, geom)
        VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
          properties = EXCLUDED.properties,
          provenance = EXCLUDED.provenance,
          geom = EXCLUDED.geom,
          ingested_at = now()
        """,
        values,
        template="""(
            %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
            ST_Force2D(ST_MakeValid(ST_Transform(ST_SetSRID(ST_GeomFromText(%s), %s), 4326)))
        )""",
    )
    cur.execute(f"ANALYZE {schema}.{table}")
    return len(values)


def update_yaml_registry(path: Path, layer_id: str, table: str, geometry_column: str) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    layer = data.setdefault("layers", {}).setdefault(layer_id, {})
    layer["execution_status"] = "executable"
    layer["physical_table"] = table
    layer.pop("expected_physical_table", None)
    layer["geometry_column"] = geometry_column
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_review_report(results: list[dict[str, Any]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = ["# Phase 7.2 공간 Dataset Adapter / Ingestion 결과", "", f"- 생성시각: `{generated_at}`", ""]
    for result in results:
        lines.append(f"- `{result['layer_id']}`: {result['status']}, rows={result.get('rows', 0)}, table={result.get('table')}")
    (REPORTS / "072_spatial_layer_ingestion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    review_items = [
        {
            "review_id": "spatial_ingestion_review:sea_parting_prediction",
            "layer_id": "sea_parting_prediction",
            "reason": "CSV/XML/JSON 예측자료에 위치 geometry가 포함되지 않아 도서지명 또는 별도 지점 기준 좌표와 연결해야 한다.",
            "source_assets": "Dataset/바다갈라짐예측정보_*.ZIP",
            "status": "NEEDS_SCHEMA_REVIEW",
        },
        {
            "review_id": "spatial_ingestion_review:tidal_current_surface",
            "layer_id": "tidal_current_surface",
            "reason": "대용량 .data 포맷의 header/grid 구조를 해석한 뒤 별도 raster/vector adapter가 필요하다.",
            "source_assets": "Dataset/수치조류도_국내연안2025.zip",
            "status": "NEEDS_SCHEMA_REVIEW",
        },
    ]
    (REVIEW / "spatial_ingestion_needs_review.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in review_items),
        encoding="utf-8",
    )


def ingest_specs(specs: list[ShapefileLayerSpec], replace: bool, update_registry: bool, max_records: int | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with psycopg2.connect(db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            for spec in specs:
                rows = list(iter_shapefile_rows(spec, max_records=max_records))
                inserted = insert_dynamic_rows(cur, spec, rows, replace) if spec.dynamic else insert_static_rows(cur, spec, rows, replace)
                geometry_column = "geom" if spec.dynamic else "geometry"
                results.append({"layer_id": spec.layer_id, "status": "INGESTED", "rows": inserted, "table": spec.table})
                if update_registry:
                    registry_path = DATA / ("traffic_layer_registry.yaml" if spec.dynamic else "spatial_layer_registry.yaml")
                    update_yaml_registry(registry_path, spec.layer_id, spec.table, geometry_column)
        conn.commit()
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dataset zip 공간자료를 PostGIS serving table로 적재합니다.")
    parser.add_argument("--layers", nargs="*", default=list(STATIC_SPECS), help="적재할 layer_id 목록")
    parser.add_argument("--include-dynamic-traffic", action="store_true", help="AIS/V-PASS 대용량 동적 교통 레이어도 포함")
    parser.add_argument("--replace", action="store_true", help="같은 layer_id 기존 row 삭제 후 재적재")
    parser.add_argument("--update-registry", action="store_true", help="적재 성공 시 registry를 executable/physical_table로 갱신")
    parser.add_argument("--max-records", type=int, default=None, help="레이어별 최대 적재 row 수. 대용량 시험용")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    available = dict(STATIC_SPECS)
    if args.include_dynamic_traffic:
        available.update(DYNAMIC_SPECS)
    missing = [layer for layer in args.layers if layer not in available]
    if missing:
        raise SystemExit(f"알 수 없는 layer_id: {', '.join(missing)}")
    specs = [available[layer] for layer in args.layers]
    results = ingest_specs(specs, replace=args.replace, update_registry=args.update_registry, max_records=args.max_records)
    write_review_report(results)
    print(json.dumps({"status": "OK", "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
