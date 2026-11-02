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
        return []  # Runtime coordinates must come from the serving DB or explicit input.
    candidates = []
    for identifier, place in places.items():
        geometry = place.get("geometry_wkt") or place.get("geometry")
        crs = place.get("crs") or f"EPSG:{place.get('srid')}"
        label = place.get("canonical_name") or place.get("label") or identifier
        if not geometry:
            continue
        record = {"source_ref": "data/place_geometry_registry.yaml", "source_id": identifier, "provenance": place.get("provenance")}
        try:
            candidates.append(_candidate(identifier, label, place.get("aliases") or [], geometry, [record], place.get("status", "candidate"), crs))
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
        candidates, unavailable, invalid_names = [], [], []
        # Published public coordinates are separate from unreviewed seed registries.
        anchor_path = ROOT / 'data/public_place_anchors.json'
        if anchor_path.exists():
            for item in json.loads(anchor_path.read_text(encoding='utf-8'))['places']:
                record = {'source_ref': item['source_url'], 'source_id': item['place_id'],
                          'provenance': item}
                candidates.append(_candidate(item['place_id'], item['label'], item['aliases'],
                    f"POINT({item['longitude']} {item['latitude']})", [record]))
        sources = [
            ("S101_DB_URL", "serving.small_harbour_guide", "small_harbour", """
                SELECT source_id AS id, name, NULL::text AS name_en,
                       ST_AsText(geom) AS wkt, ST_SRID(geom) AS srid,
                       properties, provenance, provenance->>'source_sha256' AS revision
                FROM serving.small_harbour_guide ORDER BY source_id
            """),
            ("S101_DB_URL", "projection.s101_feature_valid", "harbour", """
                SELECT min(feature_instance_id)::text AS id, attributes->>'name' AS name,
                       NULL::text AS name_en,
                       ST_AsText(ST_PointOnSurface(ST_Collect(geometry))) AS wkt,
                       4326 AS srid, max(dataset_version_id)::text AS revision
                FROM projection.s101_feature_valid
                WHERE feature_type_name = 'HarbourAreaAdministrative'
                  AND product_specification = 'INT.IHO.S-101.2.0'
                  AND geometry IS NOT NULL
                  AND coalesce(attributes->>'name', '') <> ''
                GROUP BY attributes->>'name'
            """),
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
                    invalid_names.append(str(row.get('name') or ''))
                    if relation not in unavailable:
                        unavailable.append(relation)
                    continue
                record = {"source_ref": relation, "source_id": row["id"], **{key: row[key] for key in ("source_asset", "source_member", "provenance", "revision", "announcement") if row.get(key) is not None}}
                try:
                    identifier = row['id'] if namespace == 'small_harbour' else f"{namespace}:{row['id']}"
                    item = _candidate(identifier, row["name"], [row.get("name_en")], row["wkt"], [record], crs=f"EPSG:{row['srid']}")
                    kind = {'harbour': 'S-101 항만 행정구역 대표점', 'island': '도서지명 원천',
                            'khoa': '해양지명 원천', 'small_harbour': '소형선항만 안내 대표점'}[namespace]
                    item.update(candidate_kind=namespace, display_label=f"{row['name']} · {kind}",
                                geometry_role='representative_point')
                    if namespace == 'small_harbour':
                        props = row.get('properties') or {}
                        provenance = row.get('provenance') or {}
                        parent = re.fullmatch(r'(.+항)\s*\(([^()]+)\)', row['name'])
                        item.update(object_id=row['id'], parent_name=parent.group(1) if parent else None,
                                    geometry_role='harbour_reference_point_not_entrance',
                                    requires_confirmation=True, source_properties=props,
                                    source_provenance=provenance, coordinate_authority=False,
                                    photo_references=[{'field': key, 'filename': value,
                                                       'source_directory': props.get('PPATH'),
                                                       'asset_verified': False}
                                                      for key, value in props.items()
                                                      if re.fullmatch(r'PHOTO\d+_PAT', key) and value])
                        # Pin source metadata as well as the selected point.
                        item['source_records'][0]['properties_sha256'] = hashlib.sha256(
                            json.dumps(props, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
                        item['place_version'] = _version(item)
                    candidates.append(item)
                except PlaceResolutionProblem:
                    invalid_names.append(str(row.get('name') or ''))
                    if relation not in unavailable:
                        unavailable.append(relation)
                    continue
        result = {"candidates": _deduplicate(candidates), "unavailable_sources": unavailable, "invalid_names": invalid_names}
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


def _resolved(candidate, status):
    resolution = {key: candidate[key] for key in ("place_id", "place_version", "source_ref", "source_records")}
    resolution.update({key: candidate[key] for key in (
        'object_id', 'candidate_kind', 'display_label', 'geometry_role', 'parent_name',
        'source_properties', 'source_provenance', 'photo_references', 'coordinate_authority') if key in candidate})
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
    aliases = sorted({alias for candidate in candidates for alias in candidate["aliases"]}, key=len, reverse=True)
    modifier_re = r"입구|출구|앞바다|경계|해역|사이|\bentrance\b|\bexit\b|\boffshore\b|\bboundary\b|\bbetween\b"
    for text in (query or "", label or ""):
        for alias in aliases:
            pattern = r"(?<![A-Za-z0-9가-힣])" + r"\s*".join(re.escape(part) for part in alias.split())
            text = re.sub(pattern, " ", text, flags=re.I)
        if re.search(modifier_re, text, re.I):
            return True
    return False


def _family_matches(text, candidates, *, exact=False):
    """Expand only a source-declared parenthetical harbour family, not fuzzy neighbours."""
    direct = _matches(text, candidates, exact=exact)
    if any(item.get('parent_name') for item in direct):
        return direct  # An explicitly named child must not become all siblings.
    families = {}
    for item in candidates:
        if item.get('parent_name'):
            families.setdefault(item['parent_name'], []).append(item)
    expanded = []
    for parent, children in families.items():
        probe = {'place_id': parent, 'aliases': [parent]}
        if _matches(text, [probe], exact=exact):
            expanded.extend(children)
    return list({item['place_id']: item for item in [*expanded, *direct]}.values())


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
        # Selecting the parent harbour is not evidence for an entrance/exit.
        # A genuinely qualified source name binds its qualifier through aliases;
        # otherwise only a separately specified point can resolve that request.
        if _has_unbound_qualifier(query, label, [candidate]):
            parent = {**candidate, 'requires_confirmation': True,
                      'selection_scope': 'PARENT_PLACE_ONLY',
                      'qualifier_binding_verified': False}
            raise PlaceResolutionProblem(
                'NEEDS_USER_INPUT', 'LOCATION_UNCONFIRMED',
                f"선택한 '{candidate['label']}'은 요청한 입구·출구 등 세부 위치로 확인되지 않았습니다. 해당 세부 위치를 지도에서 직접 지정하거나 경도·위도를 입력해 주세요.",
                candidates=[parent])
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
        candidates = [{**item, 'selection_scope': 'PARENT_PLACE_ONLY', 'qualifier_binding_verified': False}
                      if _has_unbound_qualifier(query, label, [item]) else item for item in local]
        message = ("등록된 후보는 요청한 입구·출구 등 세부 위치로 확인되지 않았습니다. 세부 위치를 지도에서 직접 지정하거나 경도·위도를 입력해 주세요."
                   if all(item.get('selection_scope') == 'PARENT_PLACE_ONLY' for item in candidates)
                   else "등록된 기준점 후보를 확인하고 사용할 위치를 선택해 주세요.")
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "LOCATION_UNCONFIRMED", message, candidates=candidates)
    loaded = catalog if catalog is not None else load_catalog()
    available = loaded["candidates"]
    named = _family_matches(query or "", available)
    matches = _family_matches(label, available, exact=True) if label else named
    if label and named and matches and {item["place_id"] for item in named} != {item["place_id"] for item in matches}:
        candidates = list({item["place_id"]: {**item, "requires_confirmation": True} for item in [*named, *matches]}.values())
        raise PlaceResolutionProblem("NEEDS_USER_INPUT", "CONFLICTING_LOCATION", "질의와 지정된 기준 위치가 다릅니다. 사용할 위치를 선택해 주세요.", candidates=candidates)
    # Spatial qualifiers change the requested location; a parent place is a candidate only.
    modified = _has_unbound_qualifier(query, label, matches)
    if not matches and label and modified:
        parent = re.sub(_MODIFIERS, " ", label, flags=re.I).strip()
        matches = _matches(parent, available, exact=True)
        modified = _has_unbound_qualifier(query, label, matches)
    unavailable = loaded.get("unavailable_sources") or []
    invalid_match = any(_normalized(name) and _normalized(name) in _normalized(label or query or '') for name in loaded.get('invalid_names', []))
    healthy_matches = [item for item in matches if not any(record.get('source_ref') in unavailable for record in item.get('source_records', []))]
    if unavailable and (invalid_match or not healthy_matches):
        raise PlaceResolutionProblem("BLOCKED_DATA", "GAZETTEER_UNAVAILABLE", "지명 원본의 연결 또는 품질을 확인해야 합니다. 좌표를 직접 지정하거나 잠시 후 다시 조회해 주세요.", candidates=[{**item, "requires_confirmation": True} for item in matches])
    if unavailable:
        matches = healthy_matches
    if len(matches) == 1 and not modified and not matches[0].get('requires_confirmation'):
        geometry, resolved_label, crs, resolution = _resolved(matches[0], "RESOLVED_GAZETTEER")
        if unavailable:
            resolution.update(unavailable_sources=unavailable, coverage_complete=False,
                              warnings=['Resolved from a healthy source; other gazetteer sources are unavailable'])
        return geometry, resolved_label, crs, resolution
    message = "지명을 찾지 못했습니다. 정확한 지명이나 경도·위도를 알려 주세요."
    if matches:
        message = "여러 위치 또는 기준점 후보가 있습니다. 사용할 위치를 선택해 주세요."
        if any(item.get('parent_name') for item in matches):
            message = "같은 항만의 세부 항구와 다른 원천의 기준점이 있습니다. 지도에 후보를 함께 표시했습니다. 이동할 항구를 선택해 주세요. 안내도의 대표점은 입구 좌표가 아니며 최신 시설 현황을 보증하지 않습니다."
    candidates = [{**item, "requires_confirmation": True,
                   **({'selection_scope': 'PARENT_PLACE_ONLY', 'qualifier_binding_verified': False}
                      if _has_unbound_qualifier(query, label, [item]) else {})} for item in matches]
    if candidates and all(item.get('selection_scope') == 'PARENT_PLACE_ONLY' for item in candidates):
        message = "후보는 요청한 입구·출구 등 세부 위치로 확인되지 않았습니다. 세부 위치를 지도에서 직접 지정하거나 경도·위도를 입력해 주세요."
    raise PlaceResolutionProblem("NEEDS_USER_INPUT", "LOCATION_UNCONFIRMED", message, candidates=candidates)
