"""Read public berth specification CSV as attributed reference metadata.

The source has tonnage and simultaneous-vessel fields, but lacks authoritative
berth length, water depth and occupancy windows. This adapter intentionally
does not convert it into an OptimizationRequest or live berth status.
"""

import csv
import hashlib
import io
from pathlib import Path

from pydantic import BaseModel, Field

MAX_SOURCE_BYTES = 2_000_000
EXPECTED_COLUMNS = 9
EXPECTED_KEYS = ("항구코드", "부두코드", "선석시설코드")


class BerthReferenceError(Exception):
    """A configured file cannot be safely interpreted as berth reference data."""


class BerthReference(BaseModel):
    """One source row, preserving official identifiers and quality flags."""

    port_code: str
    quay_code: str
    facility_code: str
    port_name: str
    quay_name: str
    berth_name: str
    minimum_tonnage: int = Field(ge=0)
    maximum_tonnage: int = Field(ge=0)
    simultaneous_vessel_count: int = Field(ge=0)
    quality_flags: list[str] = Field(default_factory=list)


class BerthReferenceCollection(BaseModel):
    """Provenance and parser quality for the complete configured file."""

    source: str
    content_sha256: str
    encoding: str
    row_count: int
    rejected_rows: int
    warning_counts: dict[str, int]
    operational_status_available: bool = False
    optimizer_constraints_available: bool = False
    berths: list[BerthReference]


def load_berth_reference(path: Path) -> BerthReferenceCollection:
    """Decode CP949/UTF-8, validate the schema and label suspect source rows.

    The source path is configured by the server operator, never supplied by
    an API caller. Reading all bytes once allows an immutable content hash to
    accompany every response and avoids mixed snapshots during parsing.
    """

    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise BerthReferenceError("berth source exceeds the size limit")
        raw = path.read_bytes()
    except OSError as exc:
        raise BerthReferenceError("configured berth source cannot be read") from exc
    if not raw:
        raise BerthReferenceError("configured berth source is empty")
    text = None
    encoding = ""
    for candidate in ("utf-8-sig", "cp949"):
        try:
            decoded = raw.decode(candidate)
        except UnicodeDecodeError:
            continue
        # A successful byte decode alone is insufficient: accept only the
        # official key columns, so an unrelated or mojibake CSV is rejected.
        header = next(csv.reader(io.StringIO(decoded)), [])
        normalized = tuple(value.replace(" ", "").lstrip("\ufeff") for value in header[:3])
        if len(header) == EXPECTED_COLUMNS and normalized == EXPECTED_KEYS:
            text, encoding = decoded, candidate
            break
    if text is None:
        raise BerthReferenceError("berth source encoding or key columns are unsupported")

    rows = csv.reader(io.StringIO(text))
    next(rows)
    berths = []
    rejected = 0
    counts: dict[str, int] = {}
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if len(row) != EXPECTED_COLUMNS or not all(row[index].strip() for index in range(3)):
            rejected += 1
            continue
        try:
            low, high, capacity = (int(row[index].strip()) for index in (6, 7, 8))
            if min(low, high, capacity) < 0:
                raise ValueError("negative capacity")
        except ValueError:
            rejected += 1
            continue
        key = tuple(value.strip() for value in row[:3])
        flags = []
        if key in seen:
            flags.append("DUPLICATE_FACILITY_KEY")
        seen.add(key)
        if low > high:
            flags.append("TONNAGE_RANGE_REVERSED")
        if high == 0:
            flags.append("UPPER_TONNAGE_ZERO")
        if capacity == 0:
            flags.append("CAPACITY_ZERO")
        for flag in flags:
            counts[flag] = counts.get(flag, 0) + 1
        berths.append(BerthReference(
            port_code=key[0], quay_code=key[1], facility_code=key[2],
            port_name=row[3].strip(), quay_name=row[4].strip(), berth_name=row[5].strip(),
            minimum_tonnage=low, maximum_tonnage=high,
            simultaneous_vessel_count=capacity, quality_flags=flags,
        ))
    return BerthReferenceCollection(
        source=path.name, content_sha256=hashlib.sha256(raw).hexdigest(),
        encoding=encoding, row_count=len(berths), rejected_rows=rejected,
        warning_counts=counts, berths=berths,
    )
