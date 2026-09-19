"""Check that an AIS candidate needs vessel fixes in the arrival period."""

import csv

import pytest

from scripts import audit_uport_ais_candidate as candidate
from scripts import collect_uport_eta_history as collector


def test_aggregate_schema_is_rejected():
    """A regional vessel-count grid cannot stand in for an AIS track."""
    with pytest.raises(ValueError, match="missing_required_mmsi"):
        candidate.field_map(["grid_id", "vessel_count", "hour"])


def test_historical_tracks_do_not_match_current_arrival_year(tmp_path):
    """Matching MMSI alone cannot bridge a four-year temporal gap."""
    csv_path = tmp_path / "historical.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["MMSI", "수신시간", "경도", "위도"])
        writer.writeheader()
        writer.writerow({"MMSI": "123456789", "수신시간": "20220101120000",
                         "경도": "129.4", "위도": "35.5"})
        writer.writerow({"MMSI": "123456789", "수신시간": "20220101130000",
                         "경도": "999", "위도": "35.5"})
    db_path = tmp_path / "arrivals.sqlite3"
    with collector.connect(db_path) as db:
        db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,observed_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?)",
                   ("123456789", "A", "2026", "01", "20260919120000", "2026-09-19T00:00:00Z"))
        db.execute("INSERT INTO events (callsgn,arrival_year,voyage,event_name,job_at_raw,port_entry_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?,?)",
                   ("A", "2026", "01", "\uc785\ud56d", "20260919100000",
                    "20260919100000", "2026-09-19T00:00:00Z"))
        db.commit()
    result = candidate.audit(csv_path, db_path)
    assert result["valid_observations"] == 1
    assert result["invalid_coordinates"] == 1
    assert result["distinct_matching_mmsi"] == 1
    assert result["overlapping_years"] == []
    assert result["eta_training_ready"] is False
