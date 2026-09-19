"""Profile a proposed raw AIS CSV before linking it to U-Port ETA labels.

This audit prints aggregates only. It never copies candidate records into the
training store, and it does not interpret timezone-free clocks as UTC or KST.
"""

import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

from scripts.collect_uport_eta_history import DEFAULT_DB

# These names cover the historical ministry AIS CSV schema and a conventional
# English export. An aggregate grid/statistics file lacks this full contract.
COLUMNS = {
    "mmsi": ("MMSI", "mmsi", "선박번호"),
    "observed": ("수신시간", "수신시각", "observed_at", "timestamp"),
    "longitude": ("경도", "longitude", "lon"),
    "latitude": ("위도", "latitude", "lat"),
}


def field_map(headers: list[str]) -> dict[str, str]:
    """Fail closed if any position field is absent from the source schema."""
    mapping = {}
    for field, aliases in COLUMNS.items():
        actual = next((name for name in aliases if name in headers), None)
        if actual is None:
            raise ValueError("missing_required_" + field)
        mapping[field] = actual
    return mapping


def parse_observed(raw: str) -> datetime | None:
    """Accept documented clock shapes while leaving the time zone unknown."""
    for pattern in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime((raw or "").strip(), pattern)
        except ValueError:
            continue
    return None


def arrival_inventory(db: sqlite3.Connection) -> tuple[set[str], set[int]]:
    """Read only vessel IDs and arrival years needed for coarse overlap.

    MMSI-to-voyage mapping comes from the existing position collector. This
    coarse comparison is not a voyage join or an ETA training label.
    """
    mmsi = {str(row[0]) for row in db.execute(
        "SELECT DISTINCT mmsi FROM positions WHERE mmsi IS NOT NULL")}
    years = set()
    for (raw,) in db.execute(
            "SELECT job_at_raw FROM events WHERE event_name = ?", ("\uc785\ud56d",)):
        if parsed := parse_observed(str(raw or "")):
            years.add(parsed.year)
    return mmsi, years


def audit(path: Path, db_path: Path | None = None, *, encoding: str = "utf-8-sig",
          max_rows: int = 1_000_000) -> dict:
    """Stream a bounded candidate CSV and report completeness and overlap."""
    if max_rows < 1:
        raise ValueError("max_rows_must_be_positive")
    known_mmsi: set[str] = set()
    arrival_years: set[int] = set()
    if db_path is not None:
        with sqlite3.connect(db_path) as db:
            known_mmsi, arrival_years = arrival_inventory(db)
    counts = Counter()
    observed_years = Counter()
    matching_mmsi: set[str] = set()
    with path.open("r", encoding=encoding, newline="") as source:
        reader = csv.DictReader(source)
        mapping = field_map(reader.fieldnames or [])
        for row in reader:
            counts["rows_scanned"] += 1
            if counts["rows_scanned"] > max_rows:
                raise ValueError("candidate_row_limit_exceeded")
            mmsi = (row.get(mapping["mmsi"]) or "").strip()
            if len(mmsi) != 9 or not mmsi.isdigit():
                counts["invalid_mmsi"] += 1
                continue
            observed = parse_observed(row.get(mapping["observed"]) or "")
            if observed is None:
                counts["invalid_observation_clock"] += 1
                continue
            try:
                longitude = float(row.get(mapping["longitude"]) or "")
                latitude = float(row.get(mapping["latitude"]) or "")
            except ValueError:
                counts["invalid_coordinates"] += 1
                continue
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                counts["invalid_coordinates"] += 1
                continue
            counts["valid_observations"] += 1
            observed_years[observed.year] += 1
            if mmsi in known_mmsi:
                matching_mmsi.add(mmsi)
                counts["rows_with_known_mmsi"] += 1
    overlapping_years = sorted(set(observed_years) & arrival_years)
    return {
        "rows_scanned": counts["rows_scanned"],
        "valid_observations": counts["valid_observations"],
        "invalid_mmsi": counts["invalid_mmsi"],
        "invalid_observation_clock": counts["invalid_observation_clock"],
        "invalid_coordinates": counts["invalid_coordinates"],
        "observation_year_counts": dict(sorted(observed_years.items())),
        "arrival_years": sorted(arrival_years),
        "overlapping_years": overlapping_years,
        "rows_with_known_mmsi": counts["rows_with_known_mmsi"],
        "distinct_matching_mmsi": len(matching_mmsi),
        "source_timezone_verified": False,
        "voyage_join_verified": False,
        "eta_training_ready": False,
    }


def main() -> None:
    """Expose a local read-only CLI with a strict row cap."""
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--arrival-db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--max-rows", type=int, default=1_000_000)
    args = parser.parse_args()
    print(json.dumps(audit(args.csv, args.arrival_db, encoding=args.encoding,
                           max_rows=args.max_rows), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
