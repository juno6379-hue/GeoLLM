"""Read-only, source-backed place resolution shared by tools and query execution."""

import hashlib
import json
import math
import os
import re
import threading
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from shapely import wkt
from shapely.errors import ShapelyError
import yaml

ROOT = Path(__file__).resolve().parents[2]
_cache = None
_cache_lock = threading.Lock()
_CACHE_SECONDS = 30
_MODIFIERS = r"입구|출구|앞바다|경계|해역|사이|\bentrance\b|\bexit\b|\boffshore\b|\bboundary\b|\bbetween\b"


class PlaceResolutionProblem(Exception):
    def __init__(self, status, code, message, *, candidates=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.candidates = candidates or []


def _normalized(value):
    return re.sub(r"\s+", "", str(value or "")).casefold()


def _usable_name(value):
    value = str(value or "").strip()
    return bool(value) and not any(ord(c) < 32 or c == "\ufffd" for c in value)


def _point(value, crs):
    if crs != "EPSG:4326":
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "CRS_REQUIRED", "기준점의 좌표계를 확인해 주세요. EPSG:4326 경도·위도 좌표가 필요합니다.")
    try:
        point = wkt.loads(value)
        if point.geom_type != "Point" or point.has_z or point.is_empty or not point.is_valid or not all(math.isfinite(v) for v in point.bounds) or not -180 <= point.x <= 180 or not -90 <= point.y <= 90:
            raise ValueError("Invalid point")
        return point
    except (ShapelyError, ValueError, TypeError) as exc:
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "INVALID_GEOMETRY", "유효한 경도·위도 기준점을 지정해 주세요.") from exc


def _version(candidate):
    payload = {key: candidate.get(key) for key in ("place_id", "label", "aliases", "geometry", "crs", "status", "source_records")}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode()).hexdigest()


def _candidate(place_id, label, aliases, geometry, records, status="source_backed", crs="EPSG:4326"):
    point = _point(geometry, crs)
    result = {
        "place_id": str(place_id), "label": label, "base_location": label,
        "aliases": sorted({str(name).strip() for name in [label, *aliases] if _usable_name(name)}),
        "geometry": geometry, "crs": crs, "status": status,
        "source_ref": records[0]["source_ref"], "source_records": records,
        "requires_confirmation": status not in {"approved", "verified", "source_backed"},
        "longitude": point.x, "latitude": point.y,
    }
    result["place_version"] = _version(result)
    return result


def _registry_candidates(places):
    if places is None:
        try:
            places = (yaml.safe_load((ROOT / "data/place_geometry_registry.yaml").read_text(encoding="utf-8")) or {}).get("places", {})
        except (OSError, ValueError, yaml.YAMLError) as exc:
            raise PlaceResolutionProblem("BLOCKED_CONFIG", "INVALID_REGISTRY", "기준 위치 설정을 읽을 수 없습니다.") from exc
    candidates = []
    for identifier, place in places.items():
        if not place.get("geometry_wkt"):
            continue
        record = {"source_ref": "data/place_geometry_registry.yaml", "source_id": identifier, "provenance": place.get("provenance")}
        try:
            candidates.append(_candidate(identifier, place.get("canonical_name") or identifier, place.get("aliases") or [], place["geometry_wkt"], [record], place.get("status", "candidate"), f"EPSG:{place.get('srid')}"))
        except PlaceResolutionProblem as exc:
            raise PlaceResolutionProblem("BLOCKED_CONFIG", "INVALID_REGISTRY", "등록된 기준 위치의 좌표 설정이 올바르지 않습니다.") from exc
    return candidates


def _read_source(env_name, statement):
    connection = psycopg2.connect(os.environ[env_name], connect_timeout=3)
    try:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5000ms'")
            cursor.execute(statement)
            return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def load_catalog(*, refresh=False):
    """Load clean source tables, never the legacy mojibake/merged dictionary."""
    global _cache
    key = tuple(os.getenv(name) for name in ("S101_DB_URL", "POSTGIS_URL"))
    with _cache_lock:
        if not refresh and _cache and _cache[0] == key and time.monotonic() - _cache[1] < _CACHE_SECONDS:
            return _cache[2]
        candidates, unavailable = [], []
        sources = [
            ("S101_DB_URL", "serving.island_gazetteer_current", "island", """
                SELECT source_id::text AS id, name, properties->>'NP_ENM' AS name_en,
                       ST_AsText(geometry) AS wkt, ST_SRID(geometry) AS srid,
                       source_asset, source_member, provenance, ingested_at::text AS revision
                FROM serving.island_gazetteer_current ORDER BY source_id
            """),
            ("POSTGIS_URL", "public.maritime_gazetteer_khoa", "khoa", """
                SELECT gid::text AS id, korn_nm AS name, eng_nm AS name_en,
                       ST_AsText(geometry) AS wkt, ST_SRID(geometry) AS srid,
                       ancmnt_yr AS revision, ancmnt_inf AS announcement
                FROM public.maritime_gazetteer_khoa ORDER BY gid
            """),
        ]
        for env_name, relation, namespace, statement in sources:
            if not os.getenv(env_name):
                unavailable.append(relation)
                continue
            try:
                rows = _read_source(env_name, statement)
            except psycopg2.Error:
                unavailable.append(relation)
                continue
            for row in rows:
                if not _usable_name(row.get("name")):
                    if relation not in unavailable:
                        unavailable.append(relation)
                    continue
                record = {"source_ref": relation, "source_id": row["id"], **{key: row[key] for key in ("source_asset", "source_member", "provenance", "revision", "announcement") if row.get(key) is not None}}
                try:
                    candidates.append(_candidate(f"{namespace}:{row['id']}", row["name"], [row.get("name_en")], row["wkt"], [record], crs=f"EPSG:{row['srid']}"))
                except PlaceResolutionProblem:
                    if relation not in unavailable:
                        unavailable.append(relation)
                    continue
        result = {"candidates": _deduplicate(candidates), "unavailable_sources": unavailable}
        _cache = (key, time.monotonic(), result)
        return result


def _deduplicate(candidates):
    groups = {}
    for candidate in candidates:
        key = (_normalized(candidate["label"]), round(candidate["longitude"], 6), round(candidate["latitude"], 6))
        if key not in groups:
            groups[key] = {**candidate, "aliases": list(candidate["aliases"]), "source_records": list(candidate["source_records"])}
            continue
        group = groups[key]
        group["aliases"] = sorted(set(group["aliases"] + candidate["aliases"]))
        group["source_records"].extend(candidate["source_records"])
        group["place_version"] = _version(group)
    return list(groups.values())


def _matches(text, candidates, *, exact=False):
    normalized_text = _normalized(text)
    if exact:
        return [candidate for candidate in candidates if any(normalized_text == _normalized(alias) for alias in candidate["aliases"])]
    hits = []
    suffix = rf"(?=$|[\s,.;?!]|에서|으로|을|를|의|은|는|이내|주변|근처|기준|반경|에|로|과|와|랑|하고|부터|까지|{_MODIFIERS})"
    for candidate in candidates:
        for alias in candidate["aliases"]:
            # Only compile boundary patterns for names present in this query.
            if _normalized(alias) not in normalized_text:
                continue
            pattern = r"(?<![A-Za-z0-9가-힣])" + r"\s*".join(re.escape(part) for part in alias.split()) + suffix
            match_count = 0
            for match in re.finditer(pattern, text, re.I):
                hits.append((match.start(), match.end(), candidate))
                match_count += 1
            if match_count == 0:
                start = normalized_text.find(_normalized(alias))
                if start >= 0:
                    hits.append((start, start + len(_normalized(alias)), candidate))
    result = {}
    for start, end, candidate in hits:
        if not any(other_start <= start and end <= other_end and (start, end) != (other_start, other_end) for other_start, other_end, _ in hits):
            result[candidate["place_id"]] = candidate
    return list(result.values())


def _has_unbound_qualifier(query, label, candidates):
    # A qualified registered name is valid, but a qualifier outside it is not a point.
    aliases = sorted({alias for candidate in candidates for alias in candidate["aliases"]}, key=len, reverse=True)
    for text in (query or "", label or ""):
        for alias in aliases:
            pattern = r"(?<![A-Za-z0-9가-힣])" + r"\s*".join(re.escape(part) for part in alias.split())
            text = re.sub(pattern, " ", text, flags=re.I)
        if re.search(_MODIFIERS, text, re.I):
            return True
    return False


def _resolved(candidate, status):
    resolution = {key: candidate[key] for key in ("place_id", "place_version", "source_ref", "source_records")}
    return candidate["geometry"], candidate["base_location"], candidate["crs"], {"status": status, **resolution}


def _matches(text, candidates, *, exact=False):
    normalized_text = _normalized(text)
    if exact:
        return [candidate for candidate in candidates if any(normalized_text == _normalized(alias) for alias in candidate["aliases"])]
    hits = []
    suffix = r"(?=$|[\s,.;?!]|에서|으로|를|을|이내|주변|근처|기준|반경|까지|입구|출구|앞바다|해역|\bentrance\b|\bexit\b|\boffshore\b)"
    for candidate in candidates:
        for alias in candidate["aliases"]:
            if _normalized(alias) not in normalized_text:
                continue
            pattern = r"(?<![A-Za-z0-9가-힣])" + r"\s*".join(re.escape(part) for part in alias.split()) + suffix
            for match in re.finditer(pattern, text, re.I):
                hits.append((match.start(), match.end(), candidate))
    result = {}
    for start, end, candidate in hits:
        if not any(other_start <= start and end <= other_end and (start, end) != (other_start, other_end) for other_start, other_end, _ in hits):
            result[candidate["place_id"]] = candidate
    return list(result.values())


def _has_unbound_qualifier(query, label, candidates):
    aliases = sorted({alias for candidate in candidates for alias in candidate["aliases"]}, key=len, reverse=True)
    modifier_re = r"입구|출구|앞바다|경계|해역|사이|\bentrance\b|\bexit\b|\boffshore\b|\bboundary\b|\bbetween\b"
    for text in (query or "", label or ""):
        for alias in aliases:
            pattern = r"(?<![A-Za-z0-9가-힣])" + r"\s*".join(re.escape(part) for part in alias.split())
            text = re.sub(pattern, " ", text, flags=re.I)
        if re.search(modifier_re, text, re.I):
            return True
    return False


def resolve_location(query, spatial=None, *, places=None, catalog=None):
    spatial = spatial or {}
    label = str(spatial.get("base_location") or spatial.get("location_text") or "").strip()
    registered = _registry_candidates(places)
    named = _matches(query or "", registered)
    local = _matches(label, registered, exact=True) if label else named
    selected_id = spatial.get("place_id")
    if selected_id:
        available = registered
        unavailable = []
        if not any(item["place_id"] == selected_id for item in registered):
            loaded = catalog if catalog is not None else load_catalog(refresh=True)
            unavailable = loaded.get("unavailable_sources")
            available = available + loaded["candidates"]
        candidate = next((item for item in available if item["place_id"] == selected_id), None)
        if candidate is None and unavailable:
            raise PlaceResolutionProblem("BLOCKED_DATA", "GAZETTEER_UNAVAILABLE", "선택한 지명의 원본을 확인할 수 없습니다. 잠시 후 다시 조회해 주세요.")
        if candidate is None or candidate["place_version"] != spatial.get("place_version"):
            raise PlaceResolutionProblem("NEEDS_USER_INPUT", "STALE_PLACE_SELECTION", "지명 후보가 변경되었습니다. 최신 후보를 다시 선택해 주세요.", candidates=[candidate] if candidate else [])
        if spatial.get("geometry") is not None:
            supplied = _point(spatial["geometry"], spatial.get("crs"))
            expected = _point(candidate["geometry"], candidate["crs"])
            if not supplied.equals_exact(expected, 1e-9):
                raise PlaceResolutionProblem("NEEDS_USER_INPUT", "CONFLICTING_LOCATION", "선택한 지명과 전달된 좌표가 다릅니다. 위치를 다시 선택해 주세요.", candidates=[candidate])
        return _resolved(candidate, "CONFIRMED_SELECTION")
    if spatial.get("place_version"):
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "STALE_PLACE_SELECTION", "지명 식별자가 없어 선택을 확인할 수 없습니다. 위치를 다시 선택해 주세요.")
    if label and len(named) == len(local) == 1 and named[0]["place_id"] != local[0]["place_id"]:
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "CONFLICTING_LOCATION", "질의와 지정된 기준 위치가 다릅니다. 사용할 위치를 선택해 주세요.", candidates=named + local)
    if spatial.get("geometry") is not None:
        _point(spatial["geometry"], spatial.get("crs"))
        return spatial["geometry"], label or "지정 위치", spatial.get("crs"), {"status": "CONFIRMED_INPUT", "source_ref": "request.spatial_context.geometry"}
    # Approved bindings take precedence; curated/test references require a choice.
    if local:
        if len(local) == 1 and local[0]["status"] in {"approved", "verified"} and not _has_unbound_qualifier(query, label, local):
            return _resolved(local[0], "APPROVED_REGISTRY")
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "LOCATION_UNCONFIRMED", "등록된 기준점 후보를 확인하고 사용할 위치를 선택해 주세요.", candidates=local)
    loaded = catalog if catalog is not None else load_catalog()
    available = loaded["candidates"]
    named = _matches(query or "", available)
    matches = _matches(label, available, exact=True) if label else named
    if label and named and matches and {item["place_id"] for item in named} != {item["place_id"] for item in matches}:
        candidates = list({item["place_id"]: {**item, "requires_confirmation": True} for item in [*named, *matches]}.values())
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "CONFLICTING_LOCATION", "질의와 지정된 기준 위치가 다릅니다. 사용할 위치를 선택해 주세요.", candidates=candidates)
    # Spatial qualifiers change the requested location; a parent place is a candidate only.
    modified = _has_unbound_qualifier(query, label, matches)
    if not matches and label and modified:
        parent = re.sub(_MODIFIERS, " ", label, flags=re.I).strip()
        matches = _matches(parent, available, exact=True)
        modified = _has_unbound_qualifier(query, label, matches)
    if loaded.get("unavailable_sources") and not matches:
        raise PlaceResolutionProblem("BLOCKED_DATA", "GAZETTEER_UNAVAILABLE", "지명 원본의 연결 또는 품질을 확인해야 합니다. 좌표를 직접 지정하거나 잠시 후 다시 조회해 주세요.", candidates=[{**item, "requires_confirmation": True} for item in matches])
    if len(matches) == 1 and not modified:
        return _resolved(matches[0], "RESOLVED_GAZETTEER")
    message = "지명을 찾지 못했습니다. 정확한 지명이나 경도·위도를 알려 주세요."
    if matches:
        message = "여러 위치 또는 기준점 후보가 있습니다. 사용할 위치를 선택해 주세요."
    raise PlaceResolutionProblem("NEEDS_USER_INPUT", "LOCATION_UNCONFIRMED", message, candidates=[{**item, "requires_confirmation": True} for item in matches])
