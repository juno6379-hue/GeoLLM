"""Check collection deduplication and ETA split safety on synthetic voyages."""

import sqlite3

from scripts import build_uport_eta_dataset as dataset
from scripts import collect_uport_eta_history as collector


def test_legacy_update_clock_column_is_renamed_without_losing_rows(tmp_path):
    """Existing operational history survives the semantic column migration."""
    path = tmp_path / "history.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE positions (
            id INTEGER PRIMARY KEY, mmsi TEXT, callsgn TEXT, arrival_year TEXT,
            voyage TEXT, observed_at_raw TEXT, latitude TEXT, longitude TEXT,
            sog TEXT, collected_at_utc TEXT NOT NULL)""")
        db.execute("INSERT INTO positions (mmsi,observed_at_raw,collected_at_utc) VALUES (?,?,?)",
                   ("123456789", "20260919120000", "2026-09-19T00:00:00Z"))
    with collector.connect(path) as db:
        names = {column[1] for column in db.execute("PRAGMA table_info(positions)")}
        assert "source_updated_at_raw" in names
        assert "observed_at_raw" not in names
        assert db.execute("SELECT source_updated_at_raw FROM positions").fetchone()[0] == "20260919120000"


def test_repeated_collection_does_not_duplicate_observations(tmp_path, monkeypatch):
    """The same provider update seen twice is one historical fix."""
    row = {"mmsiNo": "111", "callsgn": "A", "ptentYr": "2026", "vyg": "01",
           "updtTm": "20260918010000", "lat": "35", "lot": "129", "sog": "4"}
    monkeypatch.setattr(collector.source, "_request", lambda *a, **k: {
        "data": {"response": {"header": {"resultCode": "00"},
                              "body": {"totalCount": 1, "items": {"item": [row]}}}}})
    monkeypatch.setattr(collector.source, "_navigation_for", lambda key: (key, []))
    with collector.connect(tmp_path / "history.sqlite3") as db:
        assert collector.collect(db)["positions_inserted"] == 1
        assert collector.collect(db)["positions_inserted"] == 0
        assert db.execute("SELECT count(*) FROM positions").fetchone()[0] == 1


def test_arrival_agreement_and_chronological_voyage_split(tmp_path):
    """Later positions are removed and whole voyages stay in one partition."""
    with collector.connect(tmp_path / "history.sqlite3") as db:
        for voyage in range(5):
            key = ("A", "2026", f"{voyage:02d}")
            arrival = f"202609{voyage + 10:02d}120000"
            db.execute("INSERT INTO events (callsgn,arrival_year,voyage,event_name,job_at_raw,port_entry_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?,?)",
                       (*key, dataset.ARRIVAL, arrival, arrival, "2026-09-19T00:00:00Z"))
            for hour in (9, 10, 13):
                observed = f"202609{voyage + 10:02d}{hour:02d}0000"
                db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,source_updated_at_raw,latitude,longitude,sog,collected_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                           ("111", *key, observed, "35", "129", "4", "2026-09-19T00:00:00Z"))
        db.commit()
        blocked, _, _ = dataset.build(db, minimum_voyages=5)
        assert blocked["structural_prearrival_update_sequences"] == 5
        assert blocked["voyages_with_repeated_update_times"] == 5
        assert blocked["voyages_with_prearrival_update"] == 5
        assert blocked["arrival_rows_with_equal_valid_clocks"] == 5
        assert blocked["export_ready"] is False
        still_blocked, _, _ = dataset.build(db, "Asia/Seoul", minimum_voyages=5)
        assert still_blocked["export_ready"] is False
        still_blocked_clock, _, _ = dataset.build(db, "Asia/Seoul", minimum_voyages=5,
                                                  arrival_definition_verified=True)
        assert still_blocked_clock["export_ready"] is False
        report, train, holdout = dataset.build(db, "Asia/Seoul", minimum_voyages=5,
                                               arrival_definition_verified=True,
                                               position_clock_verified=True)
        assert report["export_ready"] is True
        assert (len(train), len(holdout)) == (4, 1)
        assert all(len(item["positions"]) == 2 for item in train + holdout)
        assert {x["voyage"]["vyg"] for x in train}.isdisjoint(
            {x["voyage"]["vyg"] for x in holdout})
        assert max(x["arrival_utc"] for x in train) < min(x["arrival_utc"] for x in holdout)


def test_disagreeing_arrival_clocks_cannot_label_a_sequence(tmp_path):
    """A matching event name alone does not prove the actual arrival instant."""
    with collector.connect(tmp_path / "history.sqlite3") as db:
        db.execute("INSERT INTO events (callsgn,arrival_year,voyage,event_name,job_at_raw,port_entry_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?,?)",
                   ("A", "2026", "01", dataset.ARRIVAL, "20260918120000",
                    "20260918130000", "2026-09-19T00:00:00Z"))
        for hour in (9, 10):
            db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,source_updated_at_raw,latitude,longitude,sog,collected_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                       ("111", "A", "2026", "01", f"20260918{hour:02d}0000",
                        "35", "129", "4", "2026-09-19T00:00:00Z"))
        db.commit()
        report, train, holdout = dataset.build(
            db, "Asia/Seoul", minimum_voyages=1, arrival_definition_verified=True)
        assert report["structural_prearrival_update_sequences"] == 0
        assert report["arrival_rows_with_equal_valid_clocks"] == 0
        assert report["excluded"]["arrival_time_disagreement"] == 1
        assert (train, holdout) == ([], [])


def test_same_timestamp_from_two_vessels_is_rejected(tmp_path):
    """Timestamp deduplication must not hide a conflicting MMSI."""
    with collector.connect(tmp_path / "history.sqlite3") as db:
        db.execute("INSERT INTO events (callsgn,arrival_year,voyage,event_name,job_at_raw,port_entry_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?,?)",
                   ("A", "2026", "01", dataset.ARRIVAL, "20260918120000",
                    "20260918120000", "2026-09-19T00:00:00Z"))
        for mmsi, hour in (("111", 9), ("222", 9), ("111", 10)):
            db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,source_updated_at_raw,latitude,longitude,sog,collected_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                       (mmsi, "A", "2026", "01", f"20260918{hour:02d}0000",
                        "35", "129", "4", "2026-09-19T00:00:00Z"))
        db.commit()
        report, _, _ = dataset.build(
            db, "Asia/Seoul", minimum_voyages=1, arrival_definition_verified=True)
        assert report["structural_prearrival_update_sequences"] == 0
        assert report["excluded"]["insufficient_or_mixed_vessel_history"] == 1
