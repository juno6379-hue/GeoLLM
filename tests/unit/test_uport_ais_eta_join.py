"""Verify AIS-to-arrival windows reject leakage and overlapping voyages."""

from scripts import audit_uport_ais_eta_join as join
from scripts import collect_uport_eta_history as collector

MAPPING = {"mmsi": "MMSI", "observed": "observed_at",
           "longitude": "longitude", "latitude": "latitude"}


def add_voyage(db, voyage: str, arrival: str) -> None:
    """Create one exact U-Port identity and one agreed arrival event."""
    db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,source_updated_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?)",
               ("123456789", "A", "2026", voyage, arrival, "2026-09-20T00:00:00Z"))
    db.execute("INSERT INTO events (callsgn,arrival_year,voyage,event_name,job_at_raw,port_entry_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?,?)",
               ("A", "2026", voyage, "\uc785\ud56d", arrival, arrival,
                "2026-09-20T00:00:00Z"))


def fix(clock: str, longitude: str = "129.4") -> dict:
    """Build one synthetic AIS observation without using live identifiers."""
    return {"MMSI": "123456789", "observed_at": clock,
            "longitude": longitude, "latitude": "35.5"}


def test_unique_prearrival_windows_and_required_evidence(tmp_path):
    """Each fix joins one voyage; later fixes and unchecked clocks stay out."""
    with collector.connect(tmp_path / "history.sqlite3") as db:
        add_voyage(db, "01", "20260919120000")
        add_voyage(db, "02", "20260922120000")
        db.commit()
        rows = [fix("2026-09-19 00:00:00"), fix("2026-09-19 01:00:00"),
                fix("2026-09-19 04:00:00"),  # After first arrival.
                fix("2026-09-22 00:00:00"), fix("2026-09-22 01:00:00"),
                fix("2026-09-22 00:30:00", "140.0")]
        missing_clock = join.audit_rows(rows, MAPPING, db, ais_timezone=None,
                                        arrival_timezone=None,
                                        bbox=(128, 34, 131, 37), minimum_voyages=2)
        assert missing_clock["clocks_comparable"] is False
        assert missing_clock["voyages_with_prearrival_sequence"] == 0
        report = join.audit_rows(rows, MAPPING, db, ais_timezone="UTC",
                                 arrival_timezone="Asia/Seoul",
                                 bbox=(128, 34, 131, 37), lookback_hours=12,
                                 minimum_voyages=2)
        assert report["voyages_with_prearrival_sequence"] == 2
        assert report["uniquely_windowed_fixes"] == 4
        assert report["outside_scope"] == 1
        assert report["eta_training_ready"] is False
        verified = join.audit_rows(rows, MAPPING, db, ais_timezone="UTC",
                                   arrival_timezone="Asia/Seoul",
                                   bbox=(128, 34, 131, 37), lookback_hours=12,
                                   minimum_voyages=2,
                                   arrival_definition_verified=True,
                                   source_usage_verified=True)
        assert verified["eta_training_ready"] is True


def test_overlapping_voyage_windows_are_ambiguous(tmp_path):
    """One MMSI fix cannot be reused as input for two nearby arrivals."""
    with collector.connect(tmp_path / "history.sqlite3") as db:
        add_voyage(db, "01", "20260919120000")
        add_voyage(db, "02", "20260920120000")
        db.commit()
        report = join.audit_rows([fix("2026-09-19 00:00:00")], MAPPING, db,
                                 ais_timezone="UTC", arrival_timezone="Asia/Seoul",
                                 bbox=(128, 34, 131, 37), lookback_hours=72)
        assert report["ambiguous_voyage_fixes"] == 1
        assert report["uniquely_windowed_fixes"] == 0
