"""Validate collected ETA sequences and split distinct voyages by arrival time."""

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.collect_uport_eta_history import DEFAULT_DB

ARRIVAL = "\uc785\ud56d"


def parse_clock(raw: str | None) -> datetime | None:
    """Reject malformed provider clocks instead of silently repairing them."""
    try:
        return datetime.strptime(raw or "", "%Y%m%d%H%M%S")
    except ValueError:
        return None


def build(db: sqlite3.Connection, provider_timezone: str | None = None,
          minimum_voyages: int = 30,
          arrival_definition_verified: bool = False,
          position_clock_verified: bool = False) -> tuple[dict, list[dict], list[dict]]:
    """Require exact identity, unique arrival evidence and two earlier fixes.

    The split is chronological by arrival and groups every observation for a
    voyage in one partition. Model features use only positions preceding the
    target, preventing a known arrival or later fix from leaking into input.
    """
    reasons = defaultdict(int)
    arrivals = defaultdict(list)
    arrival_event_rows = 0
    agreeing_arrival_clocks = 0
    for callsgn, year, voyage, name, job, entry in db.execute(
            "SELECT callsgn, arrival_year, voyage, event_name, job_at_raw, port_entry_at_raw FROM events"):
        if name == ARRIVAL:
            arrival_event_rows += 1
            if parse_clock(job) is not None and parse_clock(job) == parse_clock(entry):
                agreeing_arrival_clocks += 1
            arrivals[(callsgn, year, voyage)].append((job, entry))
    positions = defaultdict(list)
    stored_positions = 0
    for row in db.execute("""SELECT mmsi, callsgn, arrival_year, voyage,
        source_updated_at_raw, latitude, longitude, sog FROM positions"""):
        stored_positions += 1
        mmsi, callsgn, year, voyage, observed, lat, lon, sog = row
        if not all((mmsi, callsgn, year, voyage)):
            reasons["incomplete_identity"] += 1
            continue
        positions[(callsgn, year, voyage)].append((mmsi, observed, lat, lon, sog))
    sequences = []
    repeated_voyages = 0
    voyages_with_prearrival_update = 0
    for key, fixes in positions.items():
        # Diagnose whether repeated provider updates are accumulating even
        # before an unambiguous arrival event is available for the voyage.
        if len({parse_clock(fix[1]) for fix in fixes if parse_clock(fix[1])}) >= 2:
            repeated_voyages += 1
        evidence = arrivals.get(key, [])
        if len(evidence) != 1:
            reasons["missing_or_ambiguous_arrival"] += 1
            continue
        job, entry = evidence[0]
        # The provider's Swagger names ptentDt "arrival date/time" and
        # jobDt "work date/time". Use ptentDt as the candidate arrival clock;
        # require agreement because their operational meanings still differ.
        arrival = parse_clock(entry)
        if arrival is None or arrival != parse_clock(job):
            reasons["arrival_time_disagreement"] += 1
            continue
        earlier = []
        for mmsi, observed, lat, lon, sog in fixes:
            timestamp = parse_clock(observed)
            if timestamp is None or timestamp >= arrival:
                reasons["invalid_or_late_fix"] += 1
                continue
            try:
                latitude, longitude = float(lat), float(lon)
            except (TypeError, ValueError):
                reasons["invalid_coordinate"] += 1
                continue
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                reasons["invalid_coordinate"] += 1
                continue
            earlier.append((timestamp, mmsi, latitude, longitude, sog))
        if earlier:
            voyages_with_prearrival_update += 1
        # Check the vessel identity before collapsing duplicate timestamps;
        # otherwise a same-time fix from a different MMSI could disappear.
        mixed_vessel = len({fix[1] for fix in earlier}) != 1
        earlier = sorted({fix[0]: fix for fix in earlier}.values())
        if len(earlier) < 2 or mixed_vessel:
            reasons["insufficient_or_mixed_vessel_history"] += 1
            continue
        sequences.append((arrival, key, earlier))
    sequences.sort(key=lambda item: (item[0], item[1]))
    # The public provider does not state a time zone in the inspected field
    # definitions. A caller must supply a verified IANA zone explicitly.
    timezone_verified = provider_timezone is not None
    # Windows Python often lacks the optional IANA tzdata package. KST has a
    # fixed UTC+09:00 offset for the contemporary observations in this feed.
    # Other IANA zones still use ZoneInfo so historical transitions apply.
    zone = (timezone(timedelta(hours=9)) if provider_timezone == "Asia/Seoul"
            else timezone.utc if provider_timezone == "UTC"
            else ZoneInfo(provider_timezone) if timezone_verified else None)
    # updtTm means provider update time, not confirmed AIS observation time.
    # A separate evidence gate is required even when chronology looks valid.
    ready = (timezone_verified and arrival_definition_verified
             and position_clock_verified
             and len(sequences) >= minimum_voyages)
    report = {"stored_positions": stored_positions, "stored_voyages": len(positions),
              "voyages_with_repeated_update_times": repeated_voyages,
              "arrival_event_rows": arrival_event_rows,
              "arrival_rows_with_equal_valid_clocks": agreeing_arrival_clocks,
              "voyages_with_prearrival_update": voyages_with_prearrival_update,
              "structural_prearrival_update_sequences": len(sequences),
              "minimum_voyages": minimum_voyages, "timezone_verified": timezone_verified,
              "provider_timezone": provider_timezone,
              "arrival_definition_verified": arrival_definition_verified,
              "position_clock_verified": position_clock_verified,
              "position_clock_source_field": "updtTm (provider update time)",
              "train_voyages": 0,
              "holdout_voyages": 0, "export_ready": ready,
              "excluded": dict(sorted(reasons.items()))}
    if not ready:
        return report, [], []
    # Newest voyages form a held-out future period. At least one voyage goes
    # into holdout and all fixes of a voyage remain in its own partition.
    cut = len(sequences) - max(1, (len(sequences) + 4) // 5)
    def encode(item: tuple) -> dict:
        arrival, key, fixes = item
        return {"voyage": {"callsgn": key[0], "arrival_year": key[1], "vyg": key[2]},
                "arrival_utc": arrival.replace(tzinfo=zone).astimezone(
                    timezone.utc).isoformat(),
                "positions": [{"observed_utc": stamp.replace(tzinfo=zone).astimezone(
                    timezone.utc).isoformat(), "mmsi": mmsi,
                    "latitude": lat, "longitude": lon, "sog": sog}
                    for stamp, mmsi, lat, lon, sog in fixes]}
    train = [encode(item) for item in sequences[:cut]]
    holdout = [encode(item) for item in sequences[cut:]]
    report["train_voyages"] = len(train)
    report["holdout_voyages"] = len(holdout)
    return report, train, holdout


def main() -> None:
    """Write ignored JSONL artifacts only after all readiness gates pass."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--provider-timezone")
    parser.add_argument("--arrival-definition-verified", action="store_true")
    parser.add_argument("--position-clock-verified", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("geollm_results/uport_eta_dataset"))
    args = parser.parse_args()
    with sqlite3.connect(args.db) as db:
        report, train, holdout = build(db, args.provider_timezone,
                                     arrival_definition_verified=args.arrival_definition_verified,
                                     position_clock_verified=args.position_clock_verified)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["export_ready"]:
        return
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("holdout", holdout)):
        (args.output / f"{name}.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
