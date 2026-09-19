"""Contract checks for the credential-safe vessel-navigation API proxy."""

import io
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.uport.prediction import vessel_navigation


def _client() -> TestClient:
    """Mount only the new router to keep provider tests independent."""
    app = FastAPI()
    app.include_router(vessel_navigation.router, prefix="/api/v1")
    app.include_router(vessel_navigation.cargo_router, prefix="/api/v1")
    return TestClient(app)


class _Reply:
    """Small context manager matching urllib's response contract."""
    def __init__(self, body: bytes, content_type: str):
        self.stream = io.BytesIO(body)
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.stream.close()

    def read(self, size: int) -> bytes:
        return self.stream.read(size)


def test_missing_operation_or_key_blocks_provider_call(monkeypatch):
    """A base URL is insufficient and must never trigger path guessing."""
    monkeypatch.delenv("UPORT_VSL_NVGT_SERVICE_KEY", raising=False)
    monkeypatch.delenv("UPORT_VSL_NVGT_OPERATION", raising=False)
    monkeypatch.setattr(vessel_navigation, "urlopen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("called")))
    response = _client().get("/api/v1/uport/vessel-navigation/records")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "VESSEL_NAVIGATION_NOT_CONFIGURED"


def test_json_request_limits_and_never_returns_service_key(monkeypatch):
    """Send only bounded page parameters and retain credentials server-side."""
    monkeypatch.setenv("UPORT_VSL_NVGT_SERVICE_KEY", "private-test-key")
    monkeypatch.setenv("UPORT_VSL_NVGT_OPERATION", "getVslNvgtInfo")
    requests = []

    def fake_open(request, timeout):
        requests.append((request.full_url, timeout))
        return _Reply(b'{"response":{"header":{"resultCode":"00"},"body":{"items":[]}}}', "application/json")

    monkeypatch.setattr(vessel_navigation, "urlopen", fake_open)
    response = _client().get("/api/v1/uport/vessel-navigation/records?page_no=2&num_of_rows=5")
    assert response.status_code == 200
    assert response.json()["data"]["response"]["body"]["items"] == []
    assert "private-test-key" not in response.text
    parsed = urlparse(requests[0][0])
    assert parsed.path.endswith("/getVslNvgtInfo")
    assert parse_qs(parsed.query)["serviceKey"] == ["private-test-key"]
    assert requests[0][1] == 10
    assert _client().get("/api/v1/uport/vessel-navigation/records?num_of_rows=101").status_code == 422


def test_xml_items_and_provider_rejection(monkeypatch):
    """Repeated XML items survive parsing while provider errors fail closed."""
    monkeypatch.setenv("UPORT_VSL_NVGT_SERVICE_KEY", "private-test-key")
    monkeypatch.setenv("UPORT_VSL_NVGT_OPERATION", "getVslNvgtInfo")
    xml = b"<response><header><resultCode>00</resultCode></header><body><items><item><name>A</name></item><item><name>B</name></item></items></body></response>"
    monkeypatch.setattr(vessel_navigation, "urlopen", lambda *_a, **_k: _Reply(xml, "application/xml"))
    result = _client().get("/api/v1/uport/vessel-navigation/records?response_format=xml")
    assert result.status_code == 200
    assert len(result.json()["data"]["response"]["body"]["items"]["item"]) == 2
    monkeypatch.setattr(vessel_navigation, "urlopen", lambda *_a, **_k: _Reply(b'<response><header><resultCode>03</resultCode></header></response>', "application/xml"))
    assert _client().get("/api/v1/uport/vessel-navigation/records").status_code == 502


def test_upstream_exception_does_not_leak_key(monkeypatch):
    """urllib exceptions often contain the full URL, including serviceKey."""
    monkeypatch.setenv("UPORT_VSL_NVGT_SERVICE_KEY", "private-test-key")
    monkeypatch.setenv("UPORT_VSL_NVGT_OPERATION", "getVslNvgtInfo")
    monkeypatch.setattr(vessel_navigation, "urlopen", lambda *_a, **_k: (_ for _ in ()).throw(URLError("private-test-key")))
    result = _client().get("/api/v1/uport/vessel-navigation/records")
    assert result.status_code == 502
    assert "private-test-key" not in result.text


def test_cargo_uses_its_own_operation_with_the_shared_key(monkeypatch):
    """A cargo request cannot reuse the vessel operation or reveal the key."""
    monkeypatch.setenv("UPORT_PORT_DATA_SERVICE_KEY", "shared-private-key")
    monkeypatch.setenv("UPORT_INTG_CAG_OPERATION", "getIntgCagInfo")
    monkeypatch.delenv("UPORT_VSL_NVGT_OPERATION", raising=False)
    urls = []

    def fake_open(request, timeout):
        urls.append(request.full_url)
        return _Reply(b'{"response":{"header":{"resultCode":"00"}}}', "application/json")

    monkeypatch.setattr(vessel_navigation, "urlopen", fake_open)
    result = _client().get("/api/v1/uport/cargo/records")
    assert result.status_code == 200
    assert result.json()["source"] == "B551938/IntgCagInfoService"
    assert urlparse(urls[0]).path.endswith("/IntgCagInfoService/getIntgCagInfo")
    assert parse_qs(urlparse(urls[0]).query)["serviceKey"] == ["shared-private-key"]
    assert "shared-private-key" not in result.text
