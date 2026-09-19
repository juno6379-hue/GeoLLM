"""Audit whether public U-Port position and arrival records can train ETA.

This is a read-only, bounded audit against the locally deployed U-Port proxy.
It intentionally emits aggregate quality counts only: vessel identifiers and
the public-data credential never enter the report or terminal output.
"""

import json
import math
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "http://localhost:8000/api/v1/uport"
PAGE_SIZE = 100
MAX_POSITION_PAGES = 10
MAX_VOYAGES = 100


def _rows(response: dict) -> list[dict]:
    """Normalize the provider's zero, one, or many item envelope shapes."""
    payload = response["data"]
    data = payload.get("response", payload)
    # The provider sometimes puts no-data resultCode directly at the root
    # rather than inside response.header; read either documented variant.
    code = str(data.get("header", {}).get("resultCode", data.get("resultCode")))
    body = data.get("body") or {}
    # Some successful zero-row responses omit a header altogether. Accept
    # that shape only when the body explicitly reports zero total rows.
    if code == "None" and isinstance(body, dict) and str(body.get("totalCount")) == "0":
        return []
    # The official Swagger describes 030 as a successful lookup with no
    # matching rows. It may omit the usual response wrapper in that case.
    if code in {"030", "03"}:
        return []
    if code != "00":
        if code == "None":
            # Schema names alone help diagnose the provider's empty/error
            # envelope without exposing a queried vessel or request URL.
            shape = "_".join(sorted(str(name) for name in data.keys()))[:60]
            raise ValueError(f"provider_result_None_shape_{shape}")
        raise ValueError(f"provider_result_{code[:12]}")
    items = data.get("body", {}).get("items") or {}
    value = items.get("item") if isinstance(items, dict) else None
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _request(path: str, **params: object) -> dict:
    """Read only the local proxy and cap each response and network wait."""
    url = f"{BASE_URL}/{path}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("proxy response exceeds audit size limit")
    return json.loads(payload)


def _present(value: object) -> bool:
    """Treat XML/JSON placeholders as missing source values."""
    return str(value or "").strip().lower() not in {"", "none", "null", "nan"}


def _time(value: object) -> datetime | None:
    """Parse provider-local timestamps without inventing a time zone."""
    if not _present(value):
        return None
    try:
        return datetime.strptime(str(value), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _key(row: dict) -> tuple[str, str, str] | None:
    """Require all three source keys before attempting an exact voyage join."""
    values = (row.get("callsgn"), row.get("ptentYr"), row.get("vyg"))
    return tuple(str(value).strip() for value in values) if all(_present(value) for value in values) else None


def _navigation_for(key: tuple[str, str, str]) -> tuple[tuple[str, str, str], list[dict]]:
    """Fetch one documented vessel/year/voyage filter and verify it locally."""
    callsgn, year, voyage = key
    response = _request("vessel-navigation/records", callsgn=callsgn,
                        ptent_vts_yr=year, vyg=voyage, num_of_rows=PAGE_SIZE)
    # The navigation provider calls its year field ptentVtsYr. Never trust
    # upstream filters alone when generating model labels.
    matching = [row for row in _rows(response)
                if str(row.get("callsgn", "")) == callsgn
                and str(row.get("ptentVtsYr", "")) == year
                and str(row.get("vyg", "")) == voyage]
    return key, matching


def audit() -> dict:
    """Join eligible snapshots to arrival events and report leakage risks."""
    first = _request("vessel-position/records", page_no=1, num_of_rows=PAGE_SIZE)
    total = int(first["data"]["response"]["body"].get("totalCount", 0))
    pages = min(MAX_POSITION_PAGES, math.ceil(total / PAGE_SIZE))
    truncated = total > MAX_POSITION_PAGES * PAGE_SIZE
    positions = _rows(first)
    for page in range(2, pages + 1):
        positions.extend(_rows(_request("vessel-position/records", page_no=page,
                                       num_of_rows=PAGE_SIZE)))

    # A snapshot service often contains only one observation per vessel. Check
    # that explicitly before treating it as a sequence-model training source.
    mmsi_counts = Counter(str(row.get("mmsiNo", "")) for row in positions if _present(row.get("mmsiNo")))
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in positions:
        key = _key(row)
        if key is not None:
            grouped[key].append(row)
    if len(grouped) > MAX_VOYAGES:
        raise ValueError("audit voyage limit exceeded; increase the explicit cap after review")

    metrics = Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_navigation_for, key) for key in grouped]
        for future in as_completed(futures):
            try:
                key, events = future.result()
            except ValueError as exc:
                # A provider rejection is not equivalent to a confirmed
                # missing voyage. Keep it in a separate quality count.
                metrics[str(exc)] += 1
                continue
            except Exception:
                # Network and proxy failures must remain visible as failed
                # checks, without writing sensitive request URLs to output.
                metrics["provider_transport_failure"] += 1
                continue
            if events:
                metrics["voyages_with_exact_event_match"] += 1
            # The provider's event label, rather than a guessed numeric code,
            # identifies the actual arrival. Multiple arrivals for one voyage
            # are ambiguous and cannot yield a trustworthy single target.
            arrivals = [row for row in events if row.get("ioprtVtsNm") == "입항"]
            if len(arrivals) != 1:
                metrics["voyages_without_unique_arrival"] += 1
                continue
            arrival_at = _time(arrivals[0].get("jobDt"))
            if arrival_at is None:
                metrics["voyages_with_invalid_arrival_time"] += 1
                continue
            metrics["voyages_with_valid_arrival"] += 1
            prearrival_times: set[datetime] = set()
            for position in grouped[key]:
                observed_at = _time(position.get("updtTm"))
                if observed_at is None:
                    metrics["positions_with_invalid_observation_time"] += 1
                elif observed_at < arrival_at:
                    metrics["prearrival_pairs"] += 1
                    prearrival_times.add(observed_at)
                else:
                    metrics["at_or_after_arrival_pairs"] += 1
            if len(prearrival_times) >= 2:
                metrics["voyages_with_prearrival_sequence"] += 1

    # No raw rows or identifiers are persisted; the returned object is safe
    # for a checked-in readiness report and a CI quality gate.
    return {
        "provider_total_at_first_page": total,
        "position_rows_fetched": len(positions),
        "position_pages_fetched": pages,
        "position_audit_truncated": truncated,
        "missing_callsign": sum(not _present(row.get("callsgn")) for row in positions),
        "missing_arrival_year": sum(not _present(row.get("ptentYr")) for row in positions),
        "missing_voyage": sum(not _present(row.get("vyg")) for row in positions),
        "missing_mmsi": sum(not _present(row.get("mmsiNo")) for row in positions),
        "unique_mmsi": len(mmsi_counts),
        "vessels_with_two_or_more_positions": sum(count >= 2 for count in mmsi_counts.values()),
        "voyages_with_complete_join_key": len(grouped),
        **{name: metrics[name] for name in (
            "voyages_with_exact_event_match", "voyages_without_unique_arrival",
            "voyages_with_invalid_arrival_time", "voyages_with_valid_arrival",
            "positions_with_invalid_observation_time", "prearrival_pairs",
            "at_or_after_arrival_pairs", "voyages_with_prearrival_sequence")},
        "provider_failures": {name: count for name, count in metrics.items()
                              if name.startswith("provider_result_") or name == "provider_transport_failure"},
        # Thirty labeled sequences are only a minimum screening gate. Passing
        # it would still require train/holdout separation and license review.
        "sequence_data_gate_passed": metrics["voyages_with_prearrival_sequence"] >= 30
                                     and not truncated
                                     and not any(name.startswith("provider_result_") or name == "provider_transport_failure"
                                                 for name in metrics),
        "readiness_reason": "Need at least 30 distinct voyages with repeated pre-arrival observations and verified arrival events",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
