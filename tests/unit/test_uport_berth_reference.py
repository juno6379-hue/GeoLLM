"""Decode a source CSV and preserve quality findings without inventing status."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from services.uport.operations.berth_reference import BerthReferenceError, load_berth_reference
from services.uport.operations.router import router

HEADER = "항구코드,부두코드,선석시설코드,항구명,부두명,선석명,시작접안가능톤수,종료접안가능톤수,접안가능척수\n"


def _client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_cp949_source_preserves_reference_values_and_flags(tmp_path):
    path = tmp_path / "berths.csv"
    content = HEADER + (
        "820,MB6,1,울산본항,6부두,1선석,1000,2000,2\n"
        "820,MB6,2,울산본항,6부두,2선석,3000,2000,0\n"
        "820,MB6,2,울산본항,6부두,2선석,0,0,0\n"
        "820,MB6,3,울산본항,6부두,3선석,invalid,2000,1\n"
    )
    path.write_bytes(content.encode("cp949"))
    result = load_berth_reference(path)
    assert result.encoding == "cp949"
    assert result.row_count == 3 and result.rejected_rows == 1
    assert result.warning_counts == {
        "TONNAGE_RANGE_REVERSED": 1, "CAPACITY_ZERO": 2,
        "DUPLICATE_FACILITY_KEY": 1, "UPPER_TONNAGE_ZERO": 1,
    }
    assert result.berths[0].berth_name == "1선석"
    assert result.operational_status_available is False
    assert result.optimizer_constraints_available is False
    assert len(result.content_sha256) == 64


def test_wrong_schema_is_rejected_even_when_utf8_decodes(tmp_path):
    path = tmp_path / "wrong.csv"
    path.write_text("port,quay,facility,other,other,other,1,2,3\n", encoding="utf-8")
    with pytest.raises(BerthReferenceError, match="key columns"):
        load_berth_reference(path)


def test_api_requires_configuration_and_reports_reference_only(tmp_path, monkeypatch):
    client = _client()
    monkeypatch.delenv("UPORT_BERTH_SPEC_CSV", raising=False)
    missing = client.get("/api/v1/uport/operations/berth-reference")
    assert missing.status_code == 503
    assert missing.json()["detail"]["code"] == "DATASET_NOT_AVAILABLE"
    path = tmp_path / "berths.csv"
    path.write_text(HEADER + "820,MB6,1,울산본항,6부두,1선석,1000,2000,2\n", encoding="utf-8-sig")
    monkeypatch.setenv("UPORT_BERTH_SPEC_CSV", str(path))
    ready = client.get("/api/v1/uport/operations/berth-reference")
    assert ready.status_code == 200
    assert ready.json()["berths"][0]["port_code"] == "820"
    assert ready.json()["operational_status_available"] is False
