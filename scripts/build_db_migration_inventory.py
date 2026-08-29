"""Inventory and compare the S-101 v1 and v2 PostgreSQL databases."""

from __future__ import annotations

import csv
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DBS = {
    "v1": {"host": os.getenv("V1_DB_HOST", "127.0.0.1"), "port": 55433, "dbname": "gbhd_ref", "user": "gbhd_ref_admin", "password": "CHANGE_ME_LOCAL_ONLY"},
    "v2": {"host": os.getenv("V2_DB_HOST", "127.0.0.1"), "port": 55432, "dbname": "s100_dev", "user": "s100_dev", "password": "CHANGE_ME_LOCAL_ONLY"},
}


def connect(config):
    return psycopg2.connect(connect_timeout=10, **config)


def tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_type IN ('BASE TABLE', 'VIEW')
            ORDER BY table_schema, table_name
        """)
        return cur.fetchall()


def columns(conn, schema, table):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema=%s AND table_name=%s
            ORDER BY ordinal_position
        """, (schema, table))
        return cur.fetchall()


def safe_count(conn, schema, table):
    try:
        with conn.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
            return cur.fetchone()[0]
    except Exception:
        conn.rollback()
        return None


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    connections = {}
    errors = {}
    for version, config in DBS.items():
        try:
            connections[version] = connect(config)
        except Exception as exc:
            errors[version] = str(exc)

    rows = []
    table_sets = {}
    for version, conn in connections.items():
        table_sets[version] = {(schema, table) for schema, table in tables(conn)}
        for schema, table in sorted(table_sets[version]):
            cols = columns(conn, schema, table)
            rows.append({
                "database_version": version,
                "database": DBS[version]["dbname"],
                "schema_name": schema,
                "table_name": table,
                "object_type": "table_or_view",
                "columns": ";".join(f"{name}:{dtype}" for name, dtype in cols),
                "column_count": len(cols),
                "row_count": safe_count(conn, schema, table),
                "has_geometry": any(dtype == "USER-DEFINED" and name in {"geom", "geometry"} for name, dtype in cols),
            })

    write_csv(OUT / "inventories" / "v2_table_inventory.csv", [r for r in rows if r["database_version"] == "v2"], list(rows[0]) if rows else ["database_version"])
    schema_rows = []
    for row in rows:
        schema_rows.append({"database_version": row["database_version"], "schema_name": row["schema_name"], "table_name": row["table_name"], "column_count": row["column_count"], "row_count": row["row_count"], "has_geometry": row["has_geometry"]})
    write_csv(OUT / "inventories" / "v2_schema_inventory.csv", [r for r in schema_rows if r["database_version"] == "v2"], list(schema_rows[0]) if schema_rows else ["database_version"])

    v1_names = {table for _, table in table_sets.get("v1", set())}
    v2_names = {table for _, table in table_sets.get("v2", set())}
    mapping = []
    for v1 in sorted(v1_names):
        exact = v1 if v1 in v2_names else ""
        candidates = [v2 for v2 in sorted(v2_names) if v1.lower() in v2.lower() or v2.lower() in v1.lower()]
        mapping.append({"v1_schema": next((s for s, t in table_sets["v1"] if t == v1), ""), "v1_table": v1, "v2_schema": next((s for s, t in table_sets["v2"] if t == exact), "") if exact else "", "v2_table": exact or (candidates[0] if candidates else ""), "mapping_status": "exact" if exact else ("candidate" if candidates else "unmapped")})
    for v2 in sorted(v2_names - v1_names):
        mapping.append({"v1_schema": "", "v1_table": "", "v2_schema": next(s for s, t in table_sets["v2"] if t == v2), "v2_table": v2, "mapping_status": "v2_only"})
    write_csv(OUT / "mappings" / "v1_v2_table_mapping.csv", mapping, ["v1_schema", "v1_table", "v2_schema", "v2_table", "mapping_status"])

    feature_rows = []
    for version, conn in connections.items():
        for schema, table in sorted(table_sets[version]):
            col_names = {name for name, _ in columns(conn, schema, table)}
            if not {"nftc", "geom"}.issubset(col_names):
                continue
            try:
                with conn.cursor() as cur:
                    cur.execute(f'SELECT nftc, COUNT(*), COUNT(geom) FROM "{schema}"."{table}" GROUP BY nftc ORDER BY nftc')
                    for nftc, count, geometry_count in cur.fetchall():
                        feature_rows.append({"database_version": version, "schema_name": schema, "table_name": table, "nftc_code": nftc, "feature_count": count, "geometry_count": geometry_count})
            except Exception as exc:
                conn.rollback()
                errors[f"{version}.{schema}.{table}"] = str(exc)
    write_csv(OUT / "mappings" / "v1_v2_feature_mapping.csv", feature_rows, ["database_version", "schema_name", "table_name", "nftc_code", "feature_count", "geometry_count"])

    for conn in connections.values():
        conn.close()

    generated = datetime.now(timezone.utc).isoformat()
    v2_count = sum(1 for r in rows if r["database_version"] == "v2")
    report = [
        "# 02 DB Restore v2.0",
        "",
        f"- 생성 시각(UTC): `{generated}`",
        "- 복원 대상: `s100_dev_postgis` / `s100_dev`",
        "- v1.0 기준: `gbhd_ref_postgis` / `gbhd_ref`",
        "- 원본: `Dataset/_s100_dev_20260827.dump`",
        "",
        "## 수행 결과",
        "",
        "- 컨테이너 및 DB 접속정보 확인: 완료",
        "- v1.0 백업: 완료 (`outputs/backups/gbhd_ref_v1_20260827.dump`)",
        "- 기존 v2.0 백업: 완료 (`outputs/backups/s100_dev_pre_restore_20260827.dump`)",
        "- 원본 dump 형식: UTF-16LE로 감싸진 Custom Dump 형태",
        "- 정규화 파일: `outputs/staging/_s100_dev_20260827.normalized.dump`",
        "- `pg_restore -l` 검증: 실패 (`end of file`)",
        "- v2.0 덮어쓰기 복원: **중단**",
        "",
        "## 중단 사유",
        "",
        "원본 파일은 `FF FE 50 00 47 00 44 00 4D 00 50 00`로 시작합니다. 이는 정상 바이너리 Custom Dump의 `PGDMP`가 UTF-16LE 코드 유닛으로 변환된 형태입니다. BOM과 코드 유닛을 제거한 정규화 파일도 PostgreSQL `pg_restore`에서 EOF가 발생하므로, 원본 바이너리 dump가 인코딩 변환 과정에서 손상된 것으로 판단됩니다.",
        "",
        "복원되지 않은 상태에서 `s100_dev`를 덮어쓰지 않았습니다. v1.0 및 기존 v2.0 백업은 보존되어 있습니다.",
        "",
        "## 다음 조치",
        "",
        "- 원본 생성 시스템에서 PostgreSQL Custom Format으로 다시 export한 바이너리 dump를 확보한다.",
        "- 재전달 dump의 첫 5바이트가 `50 47 44 4D 50`인지 확인한다.",
        "- 유효 dump 확보 후 `pg_restore --clean --if-exists`를 `s100_dev`에 수행한다.",
    ]
    (OUT / "reports" / "02_db_restore_v2.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    migration = [
        "# 03 v1.0 to v2.0 Migration Report",
        "",
        f"- 생성 시각(UTC): `{generated}`",
        "- v1.0: `gbhd_ref_postgis.gbhd_ref`",
        "- v2.0: `s100_dev_postgis.s100_dev`",
        "",
        "## 비교 상태",
        "",
        f"- v1.0 접속: `{('성공' if 'v1' in connections else '실패')}`",
        f"- v2.0 접속: `{('성공' if 'v2' in connections else '실패')}`",
        f"- v2.0 현재 테이블/뷰 수: `{v2_count}`",
        "- v2.0 dump restore: `BLOCKED`",
        "",
        "## 해석",
        "",
        "현재 생성된 v2 Inventory는 dump 복원 전 `s100_dev` 상태를 나타냅니다. 따라서 이 결과를 v2.0 최종 스키마로 간주하지 않습니다.",
        "",
        "복원 실패 원인은 DB 권한이나 PostGIS 확장이 아니라 dump 파일 자체의 바이너리 인코딩/손상 문제입니다.",
        "",
        "## 생성 산출물",
        "",
        "- `outputs/inventories/v2_schema_inventory.csv`",
        "- `outputs/inventories/v2_table_inventory.csv`",
        "- `outputs/mappings/v1_v2_table_mapping.csv`",
        "- `outputs/mappings/v1_v2_feature_mapping.csv`",
    ]
    (OUT / "reports" / "03_v1_to_v2_migration_report.md").write_text("\n".join(migration) + "\n", encoding="utf-8")
    print(f"v1_tables={len(table_sets.get('v1', set()))} v2_tables={v2_count} errors={len(errors)}")
    if errors:
        for key, value in errors.items():
            print(f"ERROR {key}: {value}")


if __name__ == "__main__":
    main()
