"""Check whether a raw AIS candidate can form leakage-free U-Port ETA voyages.

This is a read-only structural audit. It emits only counts and never creates
training rows. Explicit clock zones and a spatial scope are required to compare
observations; the provider's arrival definition remains a separate gate.
"""

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.audit_uport_ais_candidate import field_map, parse_observed
from scripts.build_uport_eta_dataset import ARRIVAL, parse_clock
from scripts.collect_uport_eta_history import DEFAULT_DB


def resolve_zone(name: str):
    """Use the IANA database, with a Windows-safe KST offset for recent data."""
    if name == "Asia/Seoul":
        return timezone(timedelta(hours=9))
    if name == "UTC":
        return timezone.utc
    return ZoneInfo(name)


def arrival_windows(db: sqlite3.Connection, zone_name: str) -> dict[str, list[tuple]]:
    """Index unique arrival events by the single MMSI observed for each voyage."""
    zone = resolve_zone(zone_name)
    vessels = defaultdict(set)
    for mmsi, callsgn, year, voyage in db.execute(
            "SELECT mmsi, callsgn, arrival_year, voyage FROM positions"):
        if all((mmsi, callsgn, year, voyage)):
            vessels[(callsgn, year, voyage)].add(str(mmsi))
    events = defaultdict(list)
    for callsgn, year, voyage, job, entry in db.execute(
            """SELECT callsgn, arrival_year, voyage, job_at_raw,
            port_entry_at_raw FROM events WHERE event_name = ?""", (ARRIVAL,)):
        events[(callsgn, year, voyage)].append((job, entry))
    windows = defaultdict(list)
    for key, evidence in events.items():
        # Multiple arrival rows or multiple MMSIs make this voyage ambiguous.
        # Even matching source clock values cannot resolve that ambiguity.
        if len(evidence) != 1 or len(vessels[key]) != 1:
            continue
        job, entry = evidence[0]
        clock = parse_clock(job)
        if clock is None or clock != parse_clock(entry):
            continue
        arrival_utc = clock.replace(tzinfo=zone).astimezone(timezone.utc)
        mmsi = next(iter(vessels[key]))
        windows[mmsi].append((key, arrival_utc))
    return windows


def audit_rows(rows, mapping: dict[str, str], db: sqlite3.Connection, *,
               ais_timezone: str | None, arrival_timezone: str | None,
               bbox: tuple[float, float, float, float] | None,
               arrival_definition_verified: bool = False,
               source_usage_verified: bool = False,
               lookback_hours: int = 72, max_rows: int = 1_000_000,
               minimum_voyages: int = 30) -> dict:
    """Assign each pre-arrival fix only when exactly one voyage window fits.

    A row never enters two voyages. Two distinct observation instants are
    required per voyage, and no observed instant may equal or follow arrival.
    The function does not output identifiers or raw coordinates.
    """
    if lookback_hours < 1 or max_rows < 1:
        raise ValueError("lookback_and_row_limit_must_be_positive")
    if bbox is not None:
        west, south, east, north = bbox
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("invalid_bbox")
    clocks_comparable = bool(ais_timezone and arrival_timezone)
    windows = arrival_windows(db, arrival_timezone) if clocks_comparable else {}
    ais_zone = resolve_zone(ais_timezone) if ais_timezone else None
    counts = Counter()
    grouped = defaultdict(set)
    for row in rows:
        counts["rows_scanned"] += 1
        if counts["rows_scanned"] > max_rows:
            raise ValueError("candidate_row_limit_exceeded")
        mmsi = (row.get(mapping["mmsi"]) or "").strip()
        clock = parse_observed(row.get(mapping["observed"]) or "")
        try:
            lon = float(row.get(mapping["longitude"]) or "")
            lat = float(row.get(mapping["latitude"]) or "")
        except ValueError:
            counts["invalid_fix"] += 1
            continue
        if (len(mmsi) != 9 or not mmsi.isdigit() or clock is None
                or not (-180 <= lon <= 180 and -90 <= lat <= 90)):
            counts["invalid_fix"] += 1
            continue
        if bbox is not None and not (west <= lon <= east and south <= lat <= north):
            counts["outside_scope"] += 1
            continue
        counts["valid_in_scope"] += 1
        if not clocks_comparable:
            continue
        observed_utc = clock.replace(tzinfo=ais_zone).astimezone(timezone.utc)
        matches = [(key, arrival) for key, arrival in windows.get(mmsi, [])
                   if timedelta(0) < arrival - observed_utc <= timedelta(hours=lookback_hours)]
        if len(matches) == 1:
            grouped[matches[0][0]].add(observed_utc)
            counts["uniquely_windowed_fixes"] += 1
        elif len(matches) > 1:
            counts["ambiguous_voyage_fixes"] += 1
    repeat_voyages = sum(len(times) >= 2 for times in grouped.values())
    ready = bool(clocks_comparable and bbox is not None
                 and arrival_definition_verified and source_usage_verified
                 and repeat_voyages >= minimum_voyages)
    return {"rows_scanned": counts["rows_scanned"],
            "invalid_fix": counts["invalid_fix"],
            "outside_scope": counts["outside_scope"],
            "valid_in_scope": counts["valid_in_scope"],
            "uniquely_windowed_fixes": counts["uniquely_windowed_fixes"],
            "ambiguous_voyage_fixes": counts["ambiguous_voyage_fixes"],
            "voyages_with_prearrival_sequence": repeat_voyages,
            "minimum_voyages": minimum_voyages,
            "clocks_comparable": clocks_comparable,
            "spatial_scope_verified": bbox is not None,
            "arrival_definition_verified": arrival_definition_verified,
            "source_usage_verified": source_usage_verified,
            "eta_training_ready": ready}


def main() -> None:
    """Run a bounded CSV audit without persisting vessel observations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--arrival-db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--ais-timezone")
    parser.add_argument("--arrival-timezone")
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--arrival-definition-verified", action="store_true")
    parser.add_argument("--source-usage-verified", action="store_true")
    parser.add_argument("--lookback-hours", type=int, default=72)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--max-rows", type=int, default=1_000_000)
    args = parser.parse_args()
    with sqlite3.connect(args.arrival_db) as db, args.csv.open(
            "r", encoding=args.encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        mapping = field_map(reader.fieldnames or [])
        report = audit_rows(reader, mapping, db,
                            ais_timezone=args.ais_timezone,
                            arrival_timezone=args.arrival_timezone,
                            bbox=tuple(args.bbox) if args.bbox else None,
                            arrival_definition_verified=args.arrival_definition_verified,
                            source_usage_verified=args.source_usage_verified,
                            lookback_hours=args.lookback_hours,
                            max_rows=args.max_rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
