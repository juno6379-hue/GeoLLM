"""Persist UPA position snapshots and matching arrival evidence for ETA research.

The provider exposes current positions, so repeated executions are necessary to
obtain a real history. Source clock values remain raw until their zone is proven.
"""

import argparse
import json
import math
import os
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from scripts import audit_uport_eta_pairs as source

# Compose sets this path to a Docker-managed volume. A local direct run keeps
# its ignored repository path, which is useful for inspection and tests.
DEFAULT_DB = Path(os.getenv("UPORT_ETA_DB_PATH", "geollm_results/uport_eta_history.sqlite3"))


def connect(path: Path) -> sqlite3.Connection:
    """Create an ignored, local database with idempotent observation keys."""
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS collection_runs (
            id INTEGER PRIMARY KEY, collected_at_utc TEXT NOT NULL,
            provider_total INTEGER NOT NULL, pages INTEGER NOT NULL,
            positions_seen INTEGER NOT NULL, positions_inserted INTEGER NOT NULL,
            event_lookups_failed INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY, mmsi TEXT, callsgn TEXT, arrival_year TEXT,
            voyage TEXT, source_updated_at_raw TEXT, latitude TEXT, longitude TEXT,
            sog TEXT, collected_at_utc TEXT NOT NULL,
            UNIQUE(mmsi, callsgn, arrival_year, voyage, source_updated_at_raw)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, callsgn TEXT NOT NULL, arrival_year TEXT NOT NULL,
            voyage TEXT NOT NULL, event_name TEXT NOT NULL,
            job_at_raw TEXT, port_entry_at_raw TEXT, collected_at_utc TEXT NOT NULL,
            UNIQUE(callsgn, arrival_year, voyage, event_name, job_at_raw, port_entry_at_raw)
        );
    """)
    # Phase 18 stored updtTm under an observation-like column name. Swagger
    # defines it as an update clock. Rename in place so prior rows and unique
    # constraints survive without recopying or reinterpreting timestamps.
    columns = {row[1] for row in db.execute("PRAGMA table_info(positions)")}
    if "observed_at_raw" in columns and "source_updated_at_raw" not in columns:
        db.execute("ALTER TABLE positions RENAME COLUMN observed_at_raw TO source_updated_at_raw")
    # SQLite treats NULLs as distinct in a UNIQUE constraint. This expression
    # index also deduplicates incomplete provider records after migration.
    db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS positions_source_key ON positions
        (COALESCE(mmsi,''), COALESCE(callsgn,''), COALESCE(arrival_year,''),
         COALESCE(voyage,''), COALESCE(source_updated_at_raw,''))""")
    db.commit()
    return db


def collect(db: sqlite3.Connection) -> dict:
    """Fetch every bounded snapshot page and exact voyage events once per run.

    A failed page aborts the whole transaction. Event lookup failures remain
    counted separately, so a partial event refresh cannot look like no data.
    """
    source.BASE_URL = os.getenv("UPORT_PROXY_URL", source.BASE_URL).rstrip("/")
    first = source._request("vessel-position/records", page_no=1, num_of_rows=source.PAGE_SIZE)
    total = int(first["data"]["response"]["body"].get("totalCount", 0))
    pages = math.ceil(total / source.PAGE_SIZE)
    if pages > source.MAX_POSITION_PAGES:
        raise ValueError("position pagination exceeds reviewed collection cap")
    rows = source._rows(first)
    for page in range(2, pages + 1):
        rows.extend(source._rows(source._request("vessel-position/records", page_no=page,
                                                num_of_rows=source.PAGE_SIZE)))
    now = datetime.now(timezone.utc).isoformat()
    before = db.total_changes
    keys = set()
    for row in rows:
        key = source._key(row)
        if key:
            keys.add(key)
        # Preserve the original update clock as text. The provider does not
        # define updtTm as an AIS observation timestamp, and collection time
        # is a separate UTC fact that cannot replace either source field.
        db.execute("""INSERT OR IGNORE INTO positions
            (mmsi, callsgn, arrival_year, voyage, source_updated_at_raw,
             latitude, longitude, sog, collected_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (row.get("mmsiNo"), row.get("callsgn"), row.get("ptentYr"),
             row.get("vyg"), row.get("updtTm"), row.get("lat"),
             row.get("lot"), row.get("sog"), now))
    inserted = db.total_changes - before
    # The previous one-off audit capped navigation lookups at 100. A durable
    # collector must tolerate future growth up to its position-page cap.
    if len(keys) > source.MAX_POSITION_PAGES * source.PAGE_SIZE:
        db.rollback()
        raise ValueError("voyage lookup exceeds reviewed collection cap")
    failures = 0
    for key in sorted(keys):
        try:
            _, events = source._navigation_for(key)
        except Exception:
            # A provider/network failure must not be mistaken for an absent
            # arrival. Later collection cycles can retry the same voyage.
            failures += 1
            continue
        for event in events:
            db.execute("""INSERT OR IGNORE INTO events
                (callsgn, arrival_year, voyage, event_name, job_at_raw,
                 port_entry_at_raw, collected_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (*key, event.get("ioprtVtsNm"), event.get("jobDt"),
                 event.get("ptentDt"), now))
    db.execute("""INSERT INTO collection_runs
        (collected_at_utc, provider_total, pages, positions_seen,
         positions_inserted, event_lookups_failed) VALUES (?, ?, ?, ?, ?, ?)""",
        (now, total, pages, len(rows), inserted, failures))
    db.commit()
    # Reports contain aggregate counts only; no vessel IDs or credentials.
    return {"collected_at_utc": now, "provider_total": total,
            "pages": pages, "positions_seen": len(rows),
            "positions_inserted": inserted, "event_lookups_failed": failures}


def write_readiness(db: sqlite3.Connection, database_path: Path,
                    collected_at_utc: str) -> Path:
    """Publish only aggregate ETA quality facts for the dashboard.

    The public report lives in a separate Docker volume from raw SQLite
    history. An atomic rename prevents readers from seeing partial JSON.
    """
    from scripts.build_uport_eta_dataset import build

    report, _, _ = build(db)
    payload = {"status": "ready" if report["export_ready"] else "blocked",
               "last_collection_utc": collected_at_utc, "quality": report}
    # Local runs keep the report beside their test database. Compose points
    # this variable to a dedicated volume that contains no vessel records.
    target = Path(os.getenv("UPORT_ETA_READINESS_PATH",
                             str(database_path.with_name("eta_readiness.json"))))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    os.replace(temporary, target)
    return target


def main() -> None:
    """Run once for verification or at a fixed interval in Compose."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-hours", type=float, default=6)
    args = parser.parse_args()
    if args.interval_hours < 1:
        parser.error("interval-hours must be at least one")
    while True:
        try:
            # sqlite3's context manager controls transactions but does not
            # close the handle. Close every cycle in this long-lived service.
            with closing(connect(args.db)) as db:
                result = collect(db)
                write_readiness(db, args.db, result["collected_at_utc"])
                print(json.dumps(result), flush=True)
        except Exception as exc:
            # URL-bearing transport exceptions can include query secrets.
            # Print only the exception class and retry on the next cycle.
            print(json.dumps({"collection_error_type": type(exc).__name__}), flush=True)
            if not args.loop:
                raise SystemExit(1) from None
            # Compose starts the collector after the backend container starts,
            # which can precede API readiness. Retry failures within five
            # minutes instead of waiting a full six-hour collection interval.
            time.sleep(min(args.interval_hours * 3600, 300))
            continue
        if not args.loop:
            break
        time.sleep(args.interval_hours * 3600)


if __name__ == "__main__":
    main()
