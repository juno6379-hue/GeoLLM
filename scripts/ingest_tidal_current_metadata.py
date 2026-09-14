"""수치조류도 archive의 바이너리 구조 메타데이터를 PostGIS에 등록한다.

이 스크립트는 조류 속도/방향 grid 값을 해석하지 않는다. `header.data`,
`dataset.data`, `2025_tide.data`의 크기, 해시, 헤더 코드/offset 후보만 보존해
실행계약이 "metadata_only" 상태를 명확히 판단하도록 만든다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "outputs" / "reports"
REVIEW = ROOT / "outputs" / "review"
SOURCE_ASSET = "Dataset/수치조류도_국내연안2025.zip"
TABLE = "serving.tidal_current_surface_metadata"


def db_url() -> str:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL 또는 POSTGIS_URL 환경변수가 필요합니다.")
    return url


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_header(data: bytes, *, limit: int = 40) -> list[dict[str, Any]]:
    """헤더의 `KR...` 코드와 4-byte little-endian offset 후보를 추출한다."""
    rows: list[dict[str, Any]] = []
    pattern = re.compile(rb"KR[0-9A-Z]{6,12}")
    for match in pattern.finditer(data):
        offset_pos = match.end()
        value = None
        if offset_pos + 4 <= len(data):
            value = struct.unpack("<I", data[offset_pos : offset_pos + 4])[0]
        rows.append(
            {
                "code": match.group(0).decode("ascii", errors="ignore"),
                "byte_position": match.start(),
                "offset_candidate": value,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def inspect_archive() -> dict[str, Any]:
    archive = ROOT / SOURCE_ASSET
    if not archive.exists():
        raise FileNotFoundError(f"원천 archive를 찾을 수 없습니다: {SOURCE_ASSET}")
    members: dict[str, Any] = {}
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            item = {
                "filename": info.filename,
                "size": info.file_size,
                "compress_size": info.compress_size,
            }
            if info.filename in {"header.data", "dataset.data", "2025_tide.data"}:
                payload = z.read(info.filename)
                item["sha256"] = sha256_bytes(payload)
                item["head_hex"] = payload[:64].hex()
                if info.filename == "header.data":
                    item["header_records"] = parse_header(payload)
            members[info.filename] = item
    return {
        "layer_id": "tidal_current_surface",
        "source_asset": SOURCE_ASSET,
        "source_sha256": sha256_file(archive),
        "members": members,
        "interpretation_status": "METADATA_ONLY",
        "parser_status": "NEEDS_BINARY_GRID_SPEC",
        "notes": [
            "2025_tide.data는 header.data와 dataset.data가 결합된 바이너리로 보인다.",
            "dataset.data의 수치 encoding, 격자 원점, 해상도, 시간축은 테이블 정의서/제품 사양 기반 추가 해석이 필요하다.",
        ],
    }


def ensure_table(cur) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS serving")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS serving.tidal_current_surface_metadata (
            layer_id text PRIMARY KEY,
            source_asset text NOT NULL,
            source_sha256 text NOT NULL,
            metadata jsonb NOT NULL,
            parser_status text NOT NULL,
            coverage_geometry geometry(Polygon,4326),
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_tidal_current_surface_metadata_coverage "
        "ON serving.tidal_current_surface_metadata USING gist (coverage_geometry)"
    )


def upsert_metadata(metadata: dict[str, Any]) -> None:
    # 수치조류도 국내연안 archive의 실제 coverage는 바이너리 parser 확정 전까지
    # 값 조회에 쓰지 않는다. metadata 검색용으로만 넓은 국내연안 envelope를 둔다.
    coverage_wkt = "POLYGON((124 32,132 32,132 39,124 39,124 32))"
    with psycopg2.connect(db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            ensure_table(cur)
            cur.execute(
                """
                INSERT INTO serving.tidal_current_surface_metadata
                  (layer_id, source_asset, source_sha256, metadata, parser_status, coverage_geometry)
                VALUES (%s, %s, %s, %s::jsonb, %s, ST_GeomFromText(%s, 4326))
                ON CONFLICT (layer_id) DO UPDATE SET
                  source_sha256 = EXCLUDED.source_sha256,
                  metadata = EXCLUDED.metadata,
                  parser_status = EXCLUDED.parser_status,
                  coverage_geometry = EXCLUDED.coverage_geometry,
                  ingested_at = now()
                """,
                (
                    metadata["layer_id"],
                    metadata["source_asset"],
                    metadata["source_sha256"],
                    json.dumps(metadata, ensure_ascii=False),
                    metadata["parser_status"],
                    coverage_wkt,
                ),
            )
        conn.commit()


def update_registry(update: bool) -> None:
    if not update:
        return
    path = DATA / "spatial_layer_registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    layer = data.setdefault("layers", {}).setdefault("tidal_current_surface", {})
    layer["execution_status"] = "metadata_only"
    layer["metadata_table"] = TABLE
    layer["metadata_geometry_column"] = "coverage_geometry"
    layer["parser_status"] = "NEEDS_BINARY_GRID_SPEC"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_reports(metadata: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    members = metadata["members"]
    lines = [
        "# Phase 7.4 수치조류도 Metadata Adapter 결과",
        "",
        f"- 생성시각: `{datetime.now(timezone.utc).isoformat()}`",
        f"- 원천: `{SOURCE_ASSET}`",
        f"- metadata table: `{TABLE}`",
        f"- 상태: `{metadata['parser_status']}`",
        "",
        "## 주요 member",
    ]
    for key in ("header.data", "dataset.data", "2025_tide.data"):
        item = members.get(key, {})
        lines.append(f"- `{key}`: {item.get('size', 0)} bytes")
    header_records = members.get("header.data", {}).get("header_records", [])
    if header_records:
        lines.extend(["", "## header.data 코드 후보"])
        for row in header_records[:12]:
            lines.append(f"- `{row['code']}`: byte={row['byte_position']}, offset_candidate={row['offset_candidate']}")
    (REPORTS / "074_tidal_current_metadata_adapter.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    review_item = {
        "review_id": "spatial_ingestion_review:tidal_current_surface_binary_grid",
        "layer_id": "tidal_current_surface",
        "reason": "metadata table은 생성했지만 조류 속도/방향 grid 값 해석을 위해 바이너리 격자 사양 확정이 필요하다.",
        "source_assets": SOURCE_ASSET,
        "metadata_table": TABLE,
        "status": "NEEDS_BINARY_GRID_SPEC",
    }
    (REVIEW / "tidal_current_needs_review.jsonl").write_text(
        json.dumps(review_item, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="수치조류도 바이너리 archive metadata를 적재합니다.")
    parser.add_argument("--update-registry", action="store_true", help="registry를 metadata_only 상태로 갱신")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = inspect_archive()
    upsert_metadata(metadata)
    update_registry(args.update_registry)
    write_reports(metadata)
    print(json.dumps({"status": "OK", "table": TABLE, "parser_status": metadata["parser_status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
