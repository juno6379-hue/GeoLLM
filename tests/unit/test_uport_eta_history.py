"""Check collection deduplication and ETA split safety on synthetic voyages."""

import sqlite3

from scripts import build_uport_eta_dataset as dataset
from scripts import collect_uport_eta_history as collector


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
                db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,observed_at_raw,latitude,longitude,sog,collected_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                           ("111", *key, observed, "35", "129", "4", "2026-09-19T00:00:00Z"))
        db.commit()
        blocked, _, _ = dataset.build(db, minimum_voyages=5)
        assert blocked["eligible_sequences"] == 5
        assert blocked["export_ready"] is False
        still_blocked, _, _ = dataset.build(db, "Asia/Seoul", minimum_voyages=5)
        assert still_blocked["export_ready"] is False
        report, train, holdout = dataset.build(db, "Asia/Seoul", minimum_voyages=5,
                                               arrival_definition_verified=True)
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
            db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,observed_at_raw,latitude,longitude,sog,collected_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                       ("111", "A", "2026", "01", f"20260918{hour:02d}0000",
                        "35", "129", "4", "2026-09-19T00:00:00Z"))
        db.commit()
        report, train, holdout = dataset.build(
            db, "Asia/Seoul", minimum_voyages=1, arrival_definition_verified=True)
        assert report["eligible_sequences"] == 0
        assert report["excluded"]["arrival_time_disagreement"] == 1
        assert (train, holdout) == ([], [])
