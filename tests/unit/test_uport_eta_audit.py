"""Protect the ETA readiness audit from temporal leakage and false joins."""

import pytest

from scripts import audit_uport_eta_pairs as audit


def test_join_requires_source_voyage_identity():
    """A callsign and observation year cannot replace the arrival-year key."""
    assert audit._key({"callsgn": "ABC", "ptentYr": None, "vyg": "003"}) is None
    assert audit._key({"callsgn": "ABC", "ptentYr": "2026", "vyg": "003"}) == ("ABC", "2026", "003")
    assert audit._time("None") is None


def test_no_data_is_distinct_from_provider_error():
    """A documented empty result is safe; an unknown error cannot be joined."""
    assert audit._rows({"data": {"header": {"resultCode": "030"}}}) == []
    assert audit._rows({"data": {"resultCode": "030", "resultMsg": "no data"}}) == []
    with pytest.raises(ValueError, match="provider_result_99"):
        audit._rows({"data": {"header": {"resultCode": "99"}}})


def test_audit_excludes_position_after_arrival(monkeypatch):
    """One snapshot after arrival must never become an ETA training pair."""
    positions = [
        {"callsgn": "ABC", "ptentYr": "2026", "vyg": "003",
         "mmsiNo": "111111111", "updtTm": "20260918070000"},
        {"callsgn": "ABC", "ptentYr": "2026", "vyg": "003",
         "mmsiNo": "111111111", "updtTm": "20260920070000"},
    ]
    monkeypatch.setattr(audit, "_request", lambda *_a, **_k: {
        "data": {"response": {"header": {"resultCode": "00"},
                              "body": {"totalCount": "2", "items": {"item": positions}}}}})
    monkeypatch.setattr(audit, "_navigation_for", lambda key: (key, [
        {"ioprtVtsNm": "입항", "jobDt": "20260919070000"}]))
    result = audit.audit()
    assert result["prearrival_pairs"] == 1
    assert result["at_or_after_arrival_pairs"] == 1
    assert result["voyages_with_prearrival_sequence"] == 0
    assert result["sequence_data_gate_passed"] is False
