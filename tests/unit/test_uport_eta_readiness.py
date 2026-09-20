"""Protect the ETA readiness dashboard from raw vessel data disclosure."""

import json

import pytest

# The lightweight workstation Python used for collector tests omits the web
# stack. CI/backend images run these API assertions with FastAPI installed.
fastapi = pytest.importorskip("fastapi")
HTTPException = fastapi.HTTPException

from scripts.collect_uport_eta_history import connect, write_readiness
from services.uport.prediction.router import get_eta_readiness


def test_aggregate_report_excludes_identifiers_and_blocks_training(tmp_path, monkeypatch):
    """A collected fix becomes a count, never a public MMSI or fake model."""
    path = tmp_path / "history.sqlite3"
    with connect(path) as db:
        db.execute("INSERT INTO positions (mmsi,callsgn,arrival_year,voyage,source_updated_at_raw,collected_at_utc) VALUES (?,?,?,?,?,?)",
                   ("123456789", "TEST", "2026", "01", "20260919120000",
                    "2026-09-19T00:00:00Z"))
        db.commit()
        report_path = write_readiness(db, path, "2026-09-19T00:00:00Z")
    raw = report_path.read_text(encoding="utf-8")
    assert "123456789" not in raw
    assert "TEST" not in raw
    assert json.loads(raw)["quality"]["stored_positions"] == 1
    monkeypatch.setenv("UPORT_ETA_READINESS_PATH", str(report_path))
    public = get_eta_readiness()
    assert public["status"] == "blocked"
    assert public["quality"]["stored_positions"] == 1
    assert public["quality"]["position_clock_verified"] is False
    assert "mmsi" not in json.dumps(public).lower()


def test_missing_or_invalid_report_is_unavailable(tmp_path, monkeypatch):
    """Dashboard API must not silently convert a broken feed into zero ETA."""
    path = tmp_path / "eta_readiness.json"
    monkeypatch.setenv("UPORT_ETA_READINESS_PATH", str(path))
    with pytest.raises(HTTPException) as missing:
        get_eta_readiness()
    assert missing.value.status_code == 503
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(HTTPException) as malformed:
        get_eta_readiness()
    assert malformed.value.status_code == 503
