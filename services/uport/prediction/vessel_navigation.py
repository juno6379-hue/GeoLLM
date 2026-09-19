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
POSITION_BASE_URL = "https://apis.data.go.kr/B551938/VslPstnInfoService"
MAX_RESPONSE_BYTES = 2_000_000
OPERATION_PATTERN = re.compile(r"^get[A-Za-z0-9]+$")
router = APIRouter(prefix="/uport/vessel-navigation", tags=["U-Port Vessel Navigation"])
cargo_router = APIRouter(prefix="/uport/cargo", tags=["U-Port Import Export Cargo"])
position_router = APIRouter(prefix="/uport/vessel-position", tags=["U-Port Vessel Position"])


def _configured_operation(operation_variable: str, verified_default: str | None = None) -> tuple[str, str]:
    """Require a documented operation and one shared, server-side service key."""
    key = (os.getenv("UPORT_PORT_DATA_SERVICE_KEY", "") or
           os.getenv("UPORT_VSL_NVGT_SERVICE_KEY", "")).strip()
    operation = os.getenv(operation_variable, verified_default or "").strip()
    if not key or not OPERATION_PATTERN.fullmatch(operation):
        raise HTTPException(status_code=503, detail={
            "code": "VESSEL_NAVIGATION_NOT_CONFIGURED",
            "message": "Service key and documented GET operation must be configured",
        })
    return key, operation


def _parse_provider_response(payload: bytes, content_type: str) -> tuple[dict, str]:
    """Normalize JSON/XML and report the actual wire format, not the request."""
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("provider response exceeds size limit")
    text = payload.decode("utf-8-sig")
    # This provider returned XML to a JSON request in the live verification.
    # Detect the payload itself so a misleading Content-Type cannot break it.
    if text.lstrip().startswith("{"):
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError("provider JSON response is not an object")
        return result, "json"
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

    return {root.tag: convert(root)}, "xml"


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
                   num_of_rows: int, response_format: str,
                   verified_default: str | None = None,
                   filters: dict[str, str] | None = None) -> dict:
    """Fetch one page through a fixed provider host with a concealed key."""
    key, operation = _configured_operation(operation_variable, verified_default)
    # The provider's official Swagger uses resultType, while the earlier
    # generic _type parameter was ignored and returned XML for JSON requests.
    params = {"serviceKey": key, "pageNo": page_no,
              "numOfRows": num_of_rows, "resultType": response_format}
    params.update(filters or {})
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
        result, received_format = _parse_provider_response(payload, content_type)
    except (UnicodeError, ValueError, json.JSONDecodeError, ElementTree.ParseError):
        raise HTTPException(status_code=502, detail={
            "code": "PORT_DATA_INVALID_RESPONSE",
            "message": "Port data provider returned an invalid response",
        }) from None
    if _provider_error(result):
        raise HTTPException(status_code=502, detail={
            "code": "PORT_DATA_PROVIDER_REJECTED",
            "message": "Port data provider rejected the request",
        })
    return {"source": base_url.removeprefix("https://apis.data.go.kr/"), "operation": operation,
            "page_no": page_no, "num_of_rows": num_of_rows,
            "response_format": response_format, "received_format": received_format,
            "data": result}


@router.get("/records")
def get_vessel_navigation_records(
    callsgn: str = Query(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$"),
    ptent_vts_yr: str = Query(min_length=4, max_length=4, pattern=r"^[0-9]{4}$"),
    vyg: str | None = Query(default=None, max_length=20, pattern=r"^[A-Za-z0-9]+$"),
    page_no: int = Query(default=1, ge=1, le=10000),
    num_of_rows: int = Query(default=20, ge=1, le=100),
    response_format: str = Query(default="json", pattern="^(json|xml)$"),
) -> dict:
    """Expose vessel-navigation records using its configured operation."""
    filters = {"callsgn": callsgn, "ptentVtsYr": ptent_vts_yr}
    if vyg:
        filters["vyg"] = vyg
    return _fetch_records(BASE_URL, "UPORT_VSL_NVGT_OPERATION", page_no,
                          num_of_rows, response_format,
                          "getVtsBaseVslNvgtInfo", filters)


@cargo_router.get("/records")
def get_import_export_cargo_records(
    prt_cd: str = Query(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9]+$"),
    ptent_yr: str = Query(min_length=4, max_length=4, pattern=r"^[0-9]{4}$"),
    vyg: str = Query(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$"),
    callsgn: str = Query(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$"),
    bzenty_cd: str = Query(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$"),
    page_no: int = Query(default=1, ge=1, le=10000),
    num_of_rows: int = Query(default=20, ge=1, le=100),
    response_format: str = Query(default="json", pattern="^(json|xml)$"),
) -> dict:
    """Expose import/export cargo records using its configured operation."""
    # The gateway returned SERVICE_KEY_IS_NULL for this path, proving that the
    # operation exists before credentials were configured.
    filters = {"prtCd": prt_cd, "ptentYr": ptent_yr, "vyg": vyg,
               "callsgn": callsgn, "bzentyCd": bzenty_cd}
    return _fetch_records(CARGO_BASE_URL, "UPORT_INTG_CAG_OPERATION", page_no,
                          num_of_rows, response_format, "getIntgCagInfo", filters)


@position_router.get("/records")
def get_vessel_position_records(
    page_no: int = Query(default=1, ge=1, le=10000),
    num_of_rows: int = Query(default=20, ge=1, le=100),
    response_format: str = Query(default="json", pattern="^(json|xml)$"),
) -> dict:
    """Expose observed positions without interpreting them as ETA labels."""
    # The same gateway check confirmed this position operation independently.
    return _fetch_records(POSITION_BASE_URL, "UPORT_VSL_PSTN_OPERATION", page_no,
                          num_of_rows, response_format, "getVslPstnInfo")
