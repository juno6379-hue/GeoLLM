"""Read the public vessel-navigation API without exposing its service key.

The provider's base URL alone does not identify a callable operation. The
operator supplies the documented GET operation through an environment variable;
the API never accepts a caller-controlled URL or operation name.
"""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException, Query

BASE_URL = "https://apis.data.go.kr/B551938/VslNvgtInfoService"
CARGO_BASE_URL = "https://apis.data.go.kr/B551938/IntgCagInfoService"
MAX_RESPONSE_BYTES = 2_000_000
OPERATION_PATTERN = re.compile(r"^get[A-Za-z0-9]+$")
router = APIRouter(prefix="/uport/vessel-navigation", tags=["U-Port Vessel Navigation"])
cargo_router = APIRouter(prefix="/uport/cargo", tags=["U-Port Import Export Cargo"])


def _configured_operation(operation_variable: str) -> tuple[str, str]:
    """Require a documented operation and one shared, server-side service key."""
    key = (os.getenv("UPORT_PORT_DATA_SERVICE_KEY", "") or
           os.getenv("UPORT_VSL_NVGT_SERVICE_KEY", "")).strip()
    operation = os.getenv(operation_variable, "").strip()
    if not key or not OPERATION_PATTERN.fullmatch(operation):
        raise HTTPException(status_code=503, detail={
            "code": "VESSEL_NAVIGATION_NOT_CONFIGURED",
            "message": "Service key and documented GET operation must be configured",
        })
    return key, operation


def _parse_provider_response(payload: bytes, content_type: str) -> dict:
    """Normalize the provider's JSON/XML envelope within a fixed size bound."""
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("provider response exceeds size limit")
    text = payload.decode("utf-8-sig")
    if "json" in content_type.lower() or text.lstrip().startswith("{"):
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError("provider JSON response is not an object")
        return result
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("provider XML declarations are unsupported")
    root = ElementTree.fromstring(text)

    # Preserve repeated XML children as arrays instead of silently dropping
    # all but the last item. This supports both common public-data envelopes
    # and provider-specific nested response fields without guessing names.
    def convert(node: ElementTree.Element):
        children = list(node)
        if not children:
            return (node.text or "").strip()
        value: dict = {}
        for child in children:
            child_value = convert(child)
            if child.tag in value:
                if not isinstance(value[child.tag], list):
                    value[child.tag] = [value[child.tag]]
                value[child.tag].append(child_value)
            else:
                value[child.tag] = child_value
        return value

    return {root.tag: convert(root)}


def _provider_error(response: dict) -> str | None:
    """Identify provider-declared errors even when HTTP itself returns 200."""
    header = response.get("response", {}).get("header", {}) if isinstance(response.get("response"), dict) else {}
    if isinstance(header, dict) and str(header.get("resultCode", "00")) not in {"00", "0"}:
        return str(header.get("resultMsg") or "provider rejected the request")
    service = response.get("OpenAPI_ServiceResponse", {})
    if isinstance(service, dict) and "cmmMsgHeader" in service:
        return "provider rejected the request"
    return None


def _fetch_records(base_url: str, operation_variable: str, page_no: int,
                   num_of_rows: int, response_format: str) -> dict:
    """Fetch one page through a fixed provider host with a concealed key."""
    key, operation = _configured_operation(operation_variable)
    params = {"serviceKey": key, "pageNo": page_no,
              "numOfRows": num_of_rows, "_type": response_format}
    url = f"{base_url}/{operation}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json, application/xml"})
    try:
        # The public gateway can stall; a short timeout protects API workers.
        with urlopen(request, timeout=10) as upstream:
            content_type = upstream.headers.get("Content-Type", "")
            payload = upstream.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        # Exception text and URLs can contain serviceKey; expose no exception
        # content to the client or application logs.
        raise HTTPException(status_code=502, detail={
            "code": "VESSEL_NAVIGATION_UPSTREAM_ERROR",
            "message": "Vessel navigation provider is unavailable",
        }) from None
    try:
        result = _parse_provider_response(payload, content_type)
    except (UnicodeError, ValueError, json.JSONDecodeError, ElementTree.ParseError):
        raise HTTPException(status_code=502, detail={
            "code": "VESSEL_NAVIGATION_INVALID_RESPONSE",
            "message": "Vessel navigation provider returned an invalid response",
        }) from None
    if _provider_error(result):
        raise HTTPException(status_code=502, detail={
            "code": "VESSEL_NAVIGATION_PROVIDER_REJECTED",
            "message": "Vessel navigation provider rejected the request",
        })
    return {"source": base_url.removeprefix("https://apis.data.go.kr/"), "operation": operation,
            "page_no": page_no, "num_of_rows": num_of_rows,
            "response_format": response_format, "data": result}


@router.get("/records")
def get_vessel_navigation_records(
    page_no: int = Query(default=1, ge=1, le=10000),
    num_of_rows: int = Query(default=20, ge=1, le=100),
    response_format: str = Query(default="json", pattern="^(json|xml)$"),
) -> dict:
    """Expose vessel-navigation records using its configured operation."""
    return _fetch_records(BASE_URL, "UPORT_VSL_NVGT_OPERATION", page_no,
                          num_of_rows, response_format)


@cargo_router.get("/records")
def get_import_export_cargo_records(
    page_no: int = Query(default=1, ge=1, le=10000),
    num_of_rows: int = Query(default=20, ge=1, le=100),
    response_format: str = Query(default="json", pattern="^(json|xml)$"),
) -> dict:
    """Expose import/export cargo records using its configured operation."""
    return _fetch_records(CARGO_BASE_URL, "UPORT_INTG_CAG_OPERATION", page_no,
                          num_of_rows, response_format)
