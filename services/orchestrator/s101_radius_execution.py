"""Registry policy, confirmed locations, and one result set for radius searches."""

import hashlib
import json
import math
import os
import re
import time
from contextlib import contextmanager
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2 import sql
import yaml
from shapely import wkt
from shapely.geometry import shape, box
from shapely.errors import ShapelyError

from services.orchestrator.execution_validator import MAX_RADIUS_M, validate_execution_context, apply_execution_decision
from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
from services.orchestrator.s101_portrayal import resolve_s101_portrayal
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location
from shared.schemas.agent import DataBinding, EvidenceBundle, EvidenceItem, ExecutionSlots, PlanStatus, QueryExecutionContext, ToolBinding

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OPERATION = "feature_search_by_radius"
PROFILE = "s101_hazard_radius"
CONCEPT = "navigation_hazard_object"


class RadiusProblem(Exception):
    def __init__(self, status, code, message, *, candidates=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.candidates = candidates or []


@contextmanager
def _execution_stage(qec, stage):
    """Record statement phase without exposing SQL, DSN or database errors."""
    row = {'stage': stage, 'status': 'STARTED'}
    qec.provenance.setdefault('execution_stages', []).append(row)
    started = time.perf_counter()
    try:
        yield
        row['status'] = 'COMPLETED'
    except Exception as exc:
        row.update(status='FAILED', error_type=type(exc).__name__, sqlstate=getattr(exc, 'pgcode', None))
        raise
    finally:
        row['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 3)


def _execute_stage(cursor, qec, stage, statement, params=None):
    with _execution_stage(qec, stage):
        if params is None:
            cursor.execute(statement)
        else:
            cursor.execute(statement, params)


def _registry(filename):
    try:
        value = yaml.safe_load((DATA_DIR / filename).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("registry must be a mapping")
        return value
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise RadiusProblem("BLOCKED_CONFIG", "INVALID_REGISTRY", "실행 설정을 읽을 수 없습니다.") from exc


def _place_entries():
    return {}  # Resolve runtime places from authoritative serving data.


def _spatial(state):
    value = state.get("spatial_context") or {}
    return value.model_dump() if hasattr(value, "model_dump") else dict(value)


def _alias_present(text, alias):
    suffix = r"(?=$|[\s,.;?!]|s(?=$|[\s,.;?!])|에서|으로|을|를|의|은|는|만|이내|주변|근처|기준|반경)"
    return re.search(r"(?<![A-Za-z0-9가-힣])" + re.escape(alias) + suffix, text, re.I) is not None


def _place_candidates(text, places, *, exact=False):
    found = []
    for place_id, place in places.items():
        names = [place.get("canonical_name", ""), *(place.get("aliases") or [])]
        names = [name for name in names if name]
        matched = any(
            re.sub(r"\s+", "", text).casefold() == re.sub(r"\s+", "", name).casefold()
            if exact else _alias_present(text, name)
            for name in names
        )
        if matched and place.get("geometry_wkt"):
            found.append({
                "place_id": place_id, "label": place.get("canonical_name") or place_id,
                "base_location": place.get("canonical_name") or place_id,
                "geometry": place["geometry_wkt"], "crs": f"EPSG:{place.get('srid')}",
                "status": place.get("status", "candidate"),
                "source_ref": place.get("provenance"), "requires_confirmation": True,
            })
    return found


def resolve_reference(query, spatial, places):
    try:
        return resolve_location(query, spatial, places=places)
    except PlaceResolutionProblem as exc:
        raise RadiusProblem(exc.status, exc.code, str(exc), candidates=exc.candidates) from exc


def parse_distance(query, spatial):
    from services.orchestrator.slot_evidence import radius_quantities
    quantities = radius_quantities(query)
    if any(item['validation_status'] != 'GROUNDED' for item in quantities):
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_RADIUS", "반경은 유한한 양수여야 합니다.")
    distances = {item['normalized_value'] for item in quantities}
    supplied = spatial.get("buffer_distance")
    try:
        if supplied is not None:
            if isinstance(supplied, bool):
                raise ValueError("boolean radius")
            distances.add(float(supplied))
    except (TypeError, ValueError) as exc:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_RADIUS", "반경을 양의 거리로 지정해 주세요.") from exc
    if not distances:
        raise RadiusProblem("NEEDS_USER_INPUT", "DISTANCE_REQUIRED", "검색 반경 또는 지도 범위를 지정해 주세요.")
    if len(distances) > 1:
        raise RadiusProblem("NEEDS_USER_INPUT", "CONFLICTING_RADIUS", "서로 다른 반경이 지정되어 있습니다. 사용할 반경을 알려 주세요.")
    distance = distances.pop()
    if not math.isfinite(distance) or distance <= 0:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_RADIUS", "반경은 유한한 양수여야 합니다.")
    if distance > MAX_RADIUS_M:
        raise RadiusProblem("BLOCKED_POLICY", "RADIUS_LIMIT", f"검색 반경은 {MAX_RADIUS_M / 1000:g}km 이하여야 합니다.")
    return distance


def _distance_policy(query, spatial, distance):
    explicit = _extract_explicit_distance(query) or spatial.get("buffer_distance") is not None
    if explicit:
        return {
            "default_applied": False,
            "label": f"사용자가 지정한 반경 {distance:g}m",
            "summary": f"질의 또는 지도 컨텍스트에 지정된 반경 {distance:g}m를 적용했습니다.",
        }
    raise RadiusProblem("NEEDS_USER_INPUT", "DISTANCE_REQUIRED", "검색 반경 또는 지도 범위를 지정해 주세요.")


def _extract_explicit_distance(query):
    from services.orchestrator.slot_evidence import radius_quantities
    return bool(radius_quantities(query or ''))


def _alias_present(text, alias):
    suffix = r"(?=$|[\s,.;?!]|s(?=$|[\s,.;?!])|에서|으로|를|을|만|이내|주변|근처|기준|반경|까지)"
    flexible_alias = r"\s*".join(re.escape(part) for part in str(alias).split())
    return re.search(r"(?<![A-Za-z0-9가-힣])" + flexible_alias + suffix, text, re.I) is not None


def select_targets(query, spatial, profile):
    allowed = list(profile.get("target_features") or [])
    aliases = profile.get("feature_aliases") or {}
    mentions, exclusions = [], []
    for feature in allowed:
        for alias in [feature, *(aliases.get(feature) or [])]:
            if not _alias_present(query, alias):
                continue
            escaped = re.escape(alias)
            excluded = re.search(escaped + r"(?:를|을)?\s*(?:제외|빼고)", query, re.I) or re.search(
                r"(?:without|except|excluding|exclude)\s+(?:the\s+)?" + escaped,
                query,
                re.I,
            )
            (exclusions if excluded else mentions).append(feature)
    requested = spatial.get("target_features")
    explicit_exclusions = list(spatial.get("exclusions") or [])
    for item in explicit_exclusions:
        for feature in allowed:
            if str(item).casefold() in {str(alias).casefold() for alias in [feature, *(aliases.get(feature) or [])]}:
                exclusions.append(feature)
    if requested is not None:
        if not isinstance(requested, list) or not requested or any(item not in allowed for item in requested):
            raise RadiusProblem("NEEDS_USER_INPUT", "UNSUPPORTED_TARGET", "요청 대상을 승인된 위험객체 종류로 지정해 주세요.")
        targets = requested
    else:
        generic = any(term in query.casefold() for term in ["위험객체", "위험 객체", "항행위험", "hazard", CONCEPT])
        only = re.search(r"(?:wrecks?|obstructions?|underwaterawashrocks?|침선|난파선|장애물|간출암|수중암)\s*(?:만|only)", query, re.I)
        if not generic and not mentions and not exclusions:
            raise RadiusProblem("NEEDS_USER_INPUT", "UNSUPPORTED_TARGET", "검색할 위험객체 종류를 확인해 주세요.")
        targets = mentions if mentions and (not generic or only) else allowed
    targets = [feature for feature in dict.fromkeys(targets) if feature not in exclusions]
    if not targets:
        raise RadiusProblem("NEEDS_USER_INPUT", "EMPTY_TARGET_SET", "제외 조건을 적용하면 검색할 대상이 없습니다. 대상 종류를 지정해 주세요.")
    return targets, list(dict.fromkeys([*exclusions, *explicit_exclusions]))


def _codes_for_feature(feature_code_map, feature):
    raw = feature_code_map.get(feature)
    values = raw if isinstance(raw, list) else [raw]
    codes = []
    for value in values:
        try:
            codes.append(int(value))
        except (TypeError, ValueError):
            continue
    return codes


def _codes_for_targets(feature_code_map, targets):
    codes = []
    for feature in targets:
        codes.extend(_codes_for_feature(feature_code_map, feature))
    return list(dict.fromkeys(codes))


def conservative_envelope(point, distance):
    # This radius is below both WGS84 curvature radii. Its spherical cap contains
    # the ellipsoidal distance ball; ST_DWithin remains the exact final predicate.
    angle = distance / 6330000.0
    latitude = math.radians(point.y)
    delta_lat = math.degrees(angle)
    ymin, ymax = max(-90, point.y - delta_lat), min(90, point.y + delta_lat)
    if abs(latitude) + angle >= math.pi / 2:
        return (-180.0, ymin, 180.0, ymax)
    delta_lon = math.degrees(math.asin(min(1.0, math.sin(angle) / math.cos(latitude))))
    xmin, xmax = point.x - delta_lon, point.x + delta_lon
    if xmin < -180 or xmax > 180:
        xmin, xmax = -180.0, 180.0
    return xmin, ymin, xmax, ymax


def _integer_option(spatial, name, default, maximum):
    raw = spatial.get(name, default)
    try:
        value = int(raw)
        if isinstance(raw, bool) or (not isinstance(raw, str) and raw != value) or not 0 <= value <= maximum:
            raise ValueError(name)
        if name == "result_limit" and value == 0:
            raise ValueError(name)
        return value
    except (ValueError, TypeError, OverflowError) as exc:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_PAGE", "표시 건수와 페이지 범위를 확인해 주세요.") from exc


def _map_bounds_polygon(spatial):
    raw = spatial.get("map_bounds") or spatial.get("bbox") or spatial.get("bounds")
    if not raw:
        return None
    if isinstance(raw, dict):
        raw = [raw.get("west"), raw.get("south"), raw.get("east"), raw.get("north")]
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_MAP_BOUNDS", "현재 지도 범위는 [west, south, east, north] 형식이어야 합니다.")
    try:
        west, south, east, north = [float(value) for value in raw]
    except (TypeError, ValueError) as exc:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_MAP_BOUNDS", "현재 지도 범위 좌표를 숫자로 확인해 주세요.") from exc
    if not all(math.isfinite(value) for value in [west, south, east, north]):
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_MAP_BOUNDS", "현재 지도 범위 좌표가 유효하지 않습니다.")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_MAP_BOUNDS", "현재 지도 범위는 EPSG:4326 경도·위도 bbox여야 합니다.")
    return box(west, south, east, north)


def _has_reference_location(spatial):
    return bool(spatial.get("geometry") or spatial.get("base_location") or spatial.get("location_text") or spatial.get("place_id"))


def _looks_like_contextual_hazard_only(query):
    text = query or ""
    if not any(term in text for term in ["주변", "근처", "여기", "이 근처", "현 지도", "현재 지도", "현화면", "화면"]):
        return False
    residue = text
    for term in [
        "navigation_hazard_object", "위험객체", "위험 객체", "항행위험", "hazard",
        "주변", "근처", "여기", "이 근처", "현 지도", "현재 지도", "현화면", "화면",
        "찾아줘", "찾아", "검색", "조회", "보여줘", "표시", "지도", "내의", "안의",
        "를", "을", "은", "는", "이", "가", "의", "에서",
    ]:
        residue = residue.replace(term, " ")
    residue = re.sub(r"[\s,.;?!]+", "", residue)
    return not residue


def prepare_radius_request(state):
    query, spatial = state.get("query", ""), _spatial(state)
    if state.get("user_id") == "blocked_user":
        raise RadiusProblem("BLOCKED_POLICY", "ACCESS_DENIED", "이 요청에 대한 접근 권한이 없습니다.")
    profile = ((_registry("derived_concept_registry_v2.yaml").get("derived_concepts") or {}).get(CONCEPT, {}).get("execution_profiles") or {}).get(PROFILE) or {}
    if not profile.get("target_features") or profile.get("context") != "navigation_safety":
        raise RadiusProblem("BLOCKED_CONFIG", "MISSING_TARGET_POLICY", "위험객체 실행 정책이 준비되지 않았습니다.")
    requested_context = spatial.get("context")
    if requested_context not in (None, profile["context"]) or (
        requested_context is None and any(term in query for term in ["해상풍력", "입지 평가", "양식장 적지"])
    ):
        raise RadiusProblem("NEEDS_USER_INPUT", "CONTEXT_CONFIRMATION", "항행안전 기준의 객체 조회인지, 다른 업무 목적의 분석인지 확인해 주세요.")
    distance = parse_distance(query, spatial)
    distance_policy = _distance_policy(query, spatial, distance)
    geometry, label, crs, resolution = resolve_reference(query, spatial, _place_entries())
    if crs != "EPSG:4326":
        raise RadiusProblem("NEEDS_USER_INPUT", "CRS_REQUIRED", "기준점의 좌표계를 확인해 주세요. EPSG:4326 경도·위도 좌표가 필요합니다.")
    try:
        point = wkt.loads(geometry)
        if point.geom_type != "Point" or point.is_empty or not point.is_valid or not all(math.isfinite(v) for v in point.bounds) or not -180 <= point.x <= 180 or not -90 <= point.y <= 90:
            raise ValueError("invalid point")
    except (ShapelyError, ValueError, TypeError) as exc:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_GEOMETRY", "유효한 경도·위도 기준점을 지정해 주세요.") from exc
    targets, exclusions = select_targets(query, spatial, profile)
    layer_id, template_id = profile.get("layer"), profile.get("query_template")
    layer = (_registry("spatial_layer_registry.yaml").get("layers") or {}).get(layer_id) or {}
    template = (_registry("query_template_registry.yaml").get("templates") or {}).get(template_id) or {}
    if layer.get("execution_status") != "executable":
        raise RadiusProblem("BLOCKED_DATA", "LAYER_NOT_EXECUTABLE", "공간 데이터가 실행 가능한 상태가 아닙니다.")
    if layer.get("srid") != 4326 or "dwithin" not in (layer.get("supported_operations") or []):
        raise RadiusProblem("BLOCKED_CONFIG", "LAYER_CRS_OPERATION", "공간 레이어의 좌표계 또는 거리검색 설정을 확인해야 합니다.")
    if layer_id not in (template.get("allowed_layers") or []) or template.get("executor") != "postgis.dwithin" or not (template.get("sql") or {}).get("execute"):
        raise RadiusProblem("BLOCKED_CONFIG", "TEMPLATE_MISMATCH", "승인된 거리검색 템플릿이 레이어와 연결되지 않았습니다.")
    codes = profile.get("feature_code_map") or {}
    if any(not _codes_for_feature(codes, feature) for feature in targets):
        raise RadiusProblem("BLOCKED_CONFIG", "FEATURE_CODE_MISSING", "대상 객체의 데이터셋 코드 연결이 없습니다.")
    target_codes = _codes_for_targets(codes, targets)
    request_id = str(state["task_id"])
    slots = ExecutionSlots(
        location_text=label, reference_geometry=point.wkt, crs=crs,
        resolution_status=resolution["status"], distance_m=distance,
        target_term=CONCEPT, concept_id=CONCEPT, context=profile["context"],
        target_features=targets, resolved_target_set=targets, exclusions=exclusions,
        nftc_codes=target_codes, analysis_type=OPERATION,
    )
    limit = _integer_option(spatial, "result_limit", profile.get("result_limit", 500), 1000)
    offset = _integer_option(spatial, "offset", 0, 100000)
    route = {
        "task_id": request_id, "intent": "marine_hazard_feature_search", "context": profile["context"],
        "analysis_type": OPERATION, "derived_concept": CONCEPT, "primary_agent": "Spatial Analysis Agent",
        "slots": slots.model_dump(), "tools": ["postgis.dwithin"], "data": [layer_id],
        "radius_layer_id": layer_id, "radius_template_id": template_id,
        "execution_ready": False, "status": "DRAFT", "route_plan_status": "DRAFT",
    }
    qec = QueryExecutionContext(
        request_id=request_id, task_id=request_id, revision=state.get("execution_revision") or 1, original_query=query, normalized_query=state.get("normalized_query") or query,
        slots=slots, route_plan=route, spatial={"spatial_context": {"geometry": point.wkt, "crs": crs}},
        semantic_resolution={"context": profile["context"], "target_policy": f"{CONCEPT}.{PROFILE}", "source_ref": "data/derived_concept_registry_v2.yaml", "policy_version": profile.get("policy_version")},
        provenance={"location_resolution": resolution, "distance_policy": distance_policy},
    )
    qec.plan_hash = hashlib.sha256(json.dumps({"slots": slots.model_dump(), "location_resolution": resolution, "layer": layer, "template": template, "limit": limit, "offset": offset}, sort_keys=True).encode()).hexdigest()
    xmin, ymin, xmax, ymax = conservative_envelope(point, distance)
    params = {"base_wkt": point.wkt, "srid": 4326, "distance_m": distance, "feature_codes": slots.nftc_codes,
              "feature_code_map": {feature: _codes_for_feature(codes, feature) for feature in targets},
              "target_features": targets, "result_limit": limit, "offset": offset,
              "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}
    return qec, layer, template, params


def prepare_bounds_request(state):
    query, spatial = state.get("query", ""), _spatial(state)
    if state.get("user_id") == "blocked_user":
        raise RadiusProblem("BLOCKED_POLICY", "ACCESS_DENIED", "이 요청에 대한 접근 권한이 없습니다.")
    bounds = _map_bounds_polygon(spatial)
    if bounds is None:
        raise RadiusProblem("NEEDS_USER_INPUT", "LOCATION_REQUIRED", "현재 지도 범위 또는 기준 지점을 확인해 주세요.")
    profile = ((_registry("derived_concept_registry_v2.yaml").get("derived_concepts") or {}).get(CONCEPT, {}).get("execution_profiles") or {}).get(PROFILE) or {}
    if not profile.get("target_features") or profile.get("context") != "navigation_safety":
        raise RadiusProblem("BLOCKED_CONFIG", "MISSING_TARGET_POLICY", "위험객체 실행 정책이 준비되지 않았습니다.")
    targets, exclusions = select_targets(query, spatial, profile)
    layer_id, template_id = profile.get("layer"), profile.get("query_template")
    layer = (_registry("spatial_layer_registry.yaml").get("layers") or {}).get(layer_id) or {}
    if layer.get("execution_status") != "executable" or "intersects" not in (layer.get("supported_operations") or []):
        raise RadiusProblem("BLOCKED_DATA", "LAYER_NOT_EXECUTABLE", "공간 데이터가 실행 가능한 상태가 아닙니다.")
    codes = profile.get("feature_code_map") or {}
    if any(not _codes_for_feature(codes, feature) for feature in targets):
        raise RadiusProblem("BLOCKED_CONFIG", "FEATURE_CODE_MISSING", "대상 객체의 데이터셋 코드 연결이 없습니다.")
    target_codes = _codes_for_targets(codes, targets)
    request_id = str(state["task_id"])
    slots = ExecutionSlots(
        location_text="현재 지도 범위",
        reference_geometry=bounds.centroid.wkt,
        crs="EPSG:4326",
        resolution_status="MAP_BOUNDS",
        distance_m=None,
        target_term=CONCEPT,
        concept_id=CONCEPT,
        context=profile["context"],
        target_features=targets,
        resolved_target_set=targets,
        exclusions=exclusions,
        nftc_codes=target_codes,
        analysis_type="feature_search_by_area",
    )
    limit = _integer_option(spatial, "result_limit", profile.get("result_limit", 500), 1000)
    offset = _integer_option(spatial, "offset", 0, 100000)
    route = {
        "task_id": request_id,
        "intent": "marine_hazard_feature_search",
        "context": profile["context"],
        "analysis_type": "feature_search_by_area",
        "derived_concept": CONCEPT,
        "primary_agent": "Spatial Analysis Agent",
        "slots": slots.model_dump(),
        "tools": ["postgis.intersects"],
        "data": [layer_id],
        "radius_layer_id": layer_id,
        "radius_template_id": template_id,
        "execution_ready": False,
        "status": "PLAN_READY",
        "route_plan_status": "PLAN_READY",
    }
    qec = QueryExecutionContext(
        request_id=request_id,
        task_id=request_id,
        revision=state.get("execution_revision") or 1,
        original_query=query,
        normalized_query=state.get("normalized_query") or query,
        slots=slots,
        route_plan=route,
        spatial={"spatial_context": {"map_bounds": list(bounds.bounds), "crs": "EPSG:4326"}},
        semantic_resolution={"context": profile["context"], "target_policy": f"{CONCEPT}.{PROFILE}", "source_ref": "data/derived_concept_registry_v2.yaml", "policy_version": profile.get("policy_version")},
        provenance={
            "location_resolution": {"status": "MAP_BOUNDS", "method": "request.spatial_context.map_bounds", "source_ref": "current_map_viewport"},
            "area_policy": {"summary": "기준 지점이 없어 현재 지도 bbox 안의 위험객체를 먼저 조회했습니다."},
        },
    )
    qec.plan_hash = hashlib.sha256(json.dumps({"slots": slots.model_dump(), "bounds": bounds.bounds, "layer": layer, "limit": limit, "offset": offset}, sort_keys=True).encode()).hexdigest()
    params = {
        "bounds_wkt": bounds.wkt,
        "srid": 4326,
        "feature_codes": slots.nftc_codes,
        "feature_code_map": {feature: _codes_for_feature(codes, feature) for feature in targets},
        "target_features": targets,
        "result_limit": limit,
        "offset": offset,
    }
    return qec, layer, params


def _statement(layer, template):
    relation = str(layer.get("physical_table") or "").split(".")
    if len(relation) != 2 or not all(relation):
        raise RadiusProblem("BLOCKED_CONFIG", "INVALID_RELATION", "공간 데이터 연결 설정이 올바르지 않습니다.")
    names = {name: sql.Identifier(layer[name]) for name in ("id_column", "code_column", "name_column", "geometry_column", "attributes_column")}
    names["relation"] = sql.Identifier(*relation)
    return sql.SQL(template["sql"]["execute"]).format(**names)


def _fetch_result(qec, layer, template, params):
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RadiusProblem("BLOCKED_CONFIG", "DB_NOT_CONFIGURED", "공간 데이터베이스 연결이 설정되지 않았습니다.")
    with psycopg2.connect(url, connect_timeout=3) as connection:
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        adapter = SchemaBindingAdapter(connection=connection)
        with _execution_stage(qec, "execution_validation"):
            validated = validate_execution_context(qec, binding_adapter=adapter)
        validated.provenance["execution_stages"] = qec.provenance["execution_stages"]
        if validated.readiness != PlanStatus.EXECUTION_READY:
            apply_execution_decision(qec, validated)
            coverage = validated.provenance.get('coverage_validation') or {}
            if coverage.get('status') in {'OUT_OF_COVERAGE', 'PARTIAL'}:
                raise RadiusProblem('BLOCKED_DATA', 'DATA_OUT_OF_SCOPE', '현재 연결된 데이터 범위로는 요청 영역의 결과를 확정할 수 없습니다.')
            if coverage.get('required') and coverage.get('status') == 'UNKNOWN':
                raise RadiusProblem('BLOCKED_DATA', 'DATA_COVERAGE_UNVERIFIED', '완전한 결과에 필요한 데이터 범위가 검증되지 않았습니다.')
            raise RadiusProblem(validated.readiness.value, "EXECUTION_GATE", "실행 검증을 통과하지 못했습니다. 데이터 연결과 입력 조건을 확인해 주세요.")
        qec.data_bindings, qec.tool_bindings = validated.data_bindings, validated.tool_bindings
        qec.provenance.update(validated.provenance)
        if not any(binding.relation == layer["physical_table"] and binding.geometry_column == layer["geometry_column"] and binding.srid == 4326 for binding in validated.data_bindings):
            raise RadiusProblem("BLOCKED_CONFIG", "REGISTRY_CHANGED", "데이터 연결 설정이 변경되었습니다. 다시 조회해 주세요.")
        if adapter.template_registry.get("templates", {}).get(qec.route_plan["radius_template_id"]) != template:
            raise RadiusProblem("BLOCKED_CONFIG", "REGISTRY_CHANGED", "검색 템플릿이 변경되었습니다. 다시 조회해 주세요.")
        apply_execution_decision(qec, validated)
        info = validated.provenance["schema_binding"]["inspected_relations"].get(layer["physical_table"], {})
        columns = {column["name"] for column in info.get("columns", [])}
        required = {layer["id_column"], layer["code_column"], layer["name_column"], layer["geometry_column"], layer["attributes_column"], "dataset_id", "dataset_version_id"}
        if not required.issubset(columns):
            raise RadiusProblem("BLOCKED_CONFIG", "SCHEMA_MISMATCH", "객체 식별자 또는 데이터 버전 컬럼이 없습니다.")
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', '30000', true)")
            cursor.execute("SELECT set_config('lock_timeout', '1000', true)")
            code_query = sql.SQL("SELECT DISTINCT {name}, {code} FROM {relation} WHERE {name} = ANY(%s) AND {code} = ANY(%s)").format(
                name=sql.Identifier(layer["name_column"]), code=sql.Identifier(layer["code_column"]),
                relation=sql.Identifier(*layer["physical_table"].split(".")),
            )
            _execute_stage(cursor, qec, "feature_code_verification", code_query, (params["target_features"], params["feature_codes"]))
            expected = {
                (feature, int(code))
                for feature, codes in params.get("feature_code_map", {}).items()
                for code in codes
            }
            observed = {(str(name), int(code)) for name, code in cursor.fetchall()}
            if observed - expected:
                raise RadiusProblem("BLOCKED_CONFIG", "FEATURE_CODE_CONFLICT", "데이터셋의 객체 코드가 실행 정책과 일치하지 않습니다.")
            _execute_stage(cursor, qec, "spatial_select", _statement(layer, template), params)
            total, counts, rows, search_geometry = cursor.fetchone()
            _execute_stage(cursor, qec, "snapshot_receipt", "SELECT txid_current_snapshot()::text, transaction_timestamp()::text")
            snapshot, captured_at = cursor.fetchone()
    qec.snapshot_versions.update(data_snapshot=snapshot, captured_at=captured_at)
    return int(total), counts, rows, search_geometry


def _validate_bounds_columns(connection, layer):
    adapter = SchemaBindingAdapter(connection=connection)
    info = adapter._inspect_relation(layer["physical_table"])
    columns = {column["name"] for column in info.get("columns", [])}
    required = {
        layer["id_column"],
        layer["code_column"],
        layer["name_column"],
        layer["geometry_column"],
        layer["attributes_column"],
        "dataset_id",
        "dataset_version_id",
    }
    if not required.issubset(columns):
        raise RadiusProblem("BLOCKED_CONFIG", "SCHEMA_MISMATCH", "객체 식별자 또는 데이터 버전 컬럼이 없습니다.")
    return adapter


def _fetch_bounds_result(qec, layer, params):
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RadiusProblem("BLOCKED_CONFIG", "DB_NOT_CONFIGURED", "공간 데이터베이스 연결이 설정되지 않았습니다.")
    relation = str(layer.get("physical_table") or "").split(".")
    if len(relation) != 2 or not all(relation):
        raise RadiusProblem("BLOCKED_CONFIG", "INVALID_RELATION", "공간 데이터 연결 설정이 올바르지 않습니다.")
    with psycopg2.connect(url, connect_timeout=3) as connection:
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        adapter = _validate_bounds_columns(connection, layer)
        qec.data_bindings = [DataBinding(
            dataset_id=(qec.route_plan.get("data") or ["GBENC_S101_feature"])[0],
            relation=layer["physical_table"],
            geometry_column=layer["geometry_column"],
            srid=4326,
            layer_type=layer.get("layer_type"),
            source_asset=layer.get("source_asset"),
            execution_status=layer.get("execution_status"),
            read_only=True,
        )]
        qec.tool_bindings = [ToolBinding(
            tool_id="postgis.intersects",
            operation="ST_Intersects",
            query_template_id="feature_search_by_area",
        )]
        inspected = adapter._inspect_relation(layer["physical_table"])
        qec.provenance.update({"schema_binding": {"inspected_relations": {layer["physical_table"]: inspected}}})
        with _execution_stage(qec, "execution_validation"):
            validated = validate_execution_context(qec, binding_adapter=adapter)
        validated.provenance["execution_stages"] = qec.provenance["execution_stages"]
        if validated.readiness != PlanStatus.EXECUTION_READY:
            apply_execution_decision(qec, validated)
            coverage = validated.provenance.get('coverage_validation') or {}
            if coverage.get('status') in {'OUT_OF_COVERAGE', 'PARTIAL'}:
                raise RadiusProblem('BLOCKED_DATA', 'DATA_OUT_OF_SCOPE', '현재 연결된 데이터 범위로는 요청 영역의 결과를 확정할 수 없습니다.')
            if coverage.get('required') and coverage.get('status') == 'UNKNOWN':
                raise RadiusProblem('BLOCKED_DATA', 'DATA_COVERAGE_UNVERIFIED', '완전한 결과에 필요한 데이터 범위가 검증되지 않았습니다.')
            raise RadiusProblem(validated.readiness.value, "EXECUTION_GATE", "지도 범위 실행 검증을 통과하지 못했습니다.")
        apply_execution_decision(qec, validated)
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', '30000', true)")
            cursor.execute("SELECT set_config('lock_timeout', '1000', true)")
            code_query = sql.SQL("SELECT DISTINCT {name}, {code} FROM {relation} WHERE {name} = ANY(%s) AND {code} = ANY(%s)").format(
                name=sql.Identifier(layer["name_column"]),
                code=sql.Identifier(layer["code_column"]),
                relation=sql.Identifier(*relation),
            )
            _execute_stage(cursor, qec, "feature_code_verification", code_query, (params["target_features"], params["feature_codes"]))
            expected = {
                (feature, int(code))
                for feature, codes in params.get("feature_code_map", {}).items()
                for code in codes
            }
            observed = {(str(name), int(code)) for name, code in cursor.fetchall()}
            if observed - expected:
                raise RadiusProblem("BLOCKED_CONFIG", "FEATURE_CODE_CONFLICT", "데이터셋의 객체 코드가 실행 정책과 일치하지 않습니다.")
            statement = sql.SQL(
                """
                WITH bounds AS (
                    SELECT ST_SetSRID(ST_GeomFromText(%(bounds_wkt)s), %(srid)s) AS geom
                ),
                matches AS MATERIALIZED (
                    SELECT
                        f.{id_column} AS id,
                        f.dataset_id AS source_dataset_id,
                        f.dataset_version_id AS dataset_version_id,
                        f.{code_column} AS feature_type_code,
                        f.{name_column} AS feature_type_name,
                        ST_AsGeoJSON(f.{geometry_column})::json AS geometry,
                        GeometryType(f.{geometry_column}) AS geometry_type,
                        f.{attributes_column} AS attributes,
                        ST_Distance(f.{geometry_column}::geography, ST_Centroid(b.geom)::geography) AS distance_m
                    FROM {relation} AS f
                    CROSS JOIN bounds AS b
                    WHERE f.{code_column} = ANY(%(feature_codes)s)
                      AND f.{name_column} = ANY(%(target_features)s)
                      AND f.{geometry_column} IS NOT NULL
                      AND f.{geometry_column} && b.geom
                      AND ST_Intersects(f.{geometry_column}, b.geom)
                ),
                totals AS (
                    SELECT COUNT(*)::int AS total FROM matches
                ),
                counts AS (
                    SELECT COALESCE(jsonb_object_agg(feature_type_name, cnt), '{{}}'::jsonb) AS by_type
                    FROM (
                        SELECT feature_type_name, COUNT(*)::int AS cnt
                        FROM matches
                        GROUP BY feature_type_name
                    ) grouped
                ),
                page AS (
                    SELECT *
                    FROM matches
                    ORDER BY distance_m ASC NULLS LAST, feature_type_name ASC, id ASC
                    LIMIT %(result_limit)s OFFSET %(offset)s
                )
                SELECT
                    totals.total,
                    counts.by_type,
                    COALESCE(jsonb_agg(to_jsonb(page.*)) FILTER (WHERE page.id IS NOT NULL), '[]'::jsonb) AS rows,
                    ST_AsGeoJSON((SELECT geom FROM bounds))::json AS search_geometry
                FROM totals, counts
                LEFT JOIN page ON true
                GROUP BY totals.total, counts.by_type
                """
            ).format(
                relation=sql.Identifier(*relation),
                id_column=sql.Identifier(layer["id_column"]),
                code_column=sql.Identifier(layer["code_column"]),
                name_column=sql.Identifier(layer["name_column"]),
                geometry_column=sql.Identifier(layer["geometry_column"]),
                attributes_column=sql.Identifier(layer["attributes_column"]),
            )
            _execute_stage(cursor, qec, "spatial_select", statement, params)
            total, counts, rows, search_geometry = cursor.fetchone()
            _execute_stage(cursor, qec, "snapshot_receipt", "SELECT txid_current_snapshot()::text, transaction_timestamp()::text")
            snapshot, captured_at = cursor.fetchone()
    qec.snapshot_versions.update(data_snapshot=snapshot, captured_at=captured_at)
    return int(total), dict(counts or {}), list(rows or []), search_geometry


def _source_layer(layer):
    return {
        "layer_id": "GBENC_S101_feature",
        "physical_table": layer.get("physical_table"),
        "geometry_column": layer.get("geometry_column"),
        "id_column": layer.get("id_column"),
        "code_column": layer.get("code_column"),
        "name_column": layer.get("name_column"),
        "srid": layer.get("srid"),
    }


def _quality_metrics(method, *, fast_path, exact=True):
    from services.orchestrator.quality import unmeasured_quality
    return {**unmeasured_quality(method=method, exact_registry_match=exact), "fast_path": fast_path}


def _feature_rows_to_geojson(qec, layer, rows, result_id, execution_id):
    properties, features, evidence = [], [], []
    for row in rows:
        try:
            geometry = shape(row["geometry"])
            if geometry.is_empty or not geometry.is_valid:
                raise ValueError("invalid result geometry")
        except (ShapelyError, AttributeError, KeyError, TypeError, ValueError) as exc:
            raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "지도에 표시할 객체 도형을 검증하지 못했습니다.") from exc
        identifier = str(row["id"])
        evidence_id = f"spatial:{execution_id}:{identifier}"
        geometry_type = row["geometry"].get("type") if isinstance(row.get("geometry"), dict) else geometry.geom_type
        portrayal = resolve_s101_portrayal(row["feature_type_name"], geometry_type, row.get("attributes"))
        item = {
            "feature_instance_id": identifier,
            "feature_name": row["feature_type_name"],
            "feature_type_code": row["feature_type_code"],
            "source_dataset_id": row["source_dataset_id"],
            "dataset_version_id": row["dataset_version_id"],
            "dataset_id": layer.get("dataset_id") or row["source_dataset_id"],
            "geometry_type": row.get("geometry_type") or geometry_type,
            "attributes": row.get("attributes") or {},
            "distance_m": float(row["distance_m"]) if row.get("distance_m") is not None else None,
            "source": layer["physical_table"],
            "result_id": result_id,
            "query_execution_id": execution_id,
            "evidence_id": evidence_id,
            "portrayal": portrayal,
            "portrayal_symbol": portrayal.get("symbol"),
            "portrayal_symbol_asset": portrayal.get("asset"),
            "s101_symbol": portrayal.get("symbol"),
            "s101_symbol_asset": portrayal.get("asset"),
            "s101_symbol_format": "svg",
        }
        properties.append(item)
        features.append({"type": "Feature", "id": identifier, "geometry": row["geometry"], "properties": item})
        evidence.append(EvidenceItem(evidence_id=evidence_id, evidence_type="spatial_feature", source_ref=layer["physical_table"], data=item))
    return properties, {"type": "FeatureCollection", "features": features}, evidence


def _qualify_unverified_empty(result, observed_total):
    """A successful SELECT proves snapshot rows, not geographic coverage.

    These executors currently have no authoritative coverage verifier. Do not
    trust caller-provided coverage flags or fabricate a verified-empty branch.
    Keep execution evidence while withholding an absence/completeness claim.
    """
    if observed_total != 0:
        return result
    text = ("연결된 공간 데이터에서 조건에 맞는 행은 조회되지 않았습니다. "
            "해당 자료가 요청 영역과 대상 유형을 충분히 포함하는지 검증되지 않아 "
            "실제 객체가 0개라고 확정할 수 없습니다.")
    result.update(status="PARTIAL", summary=text, answer_text=text,
                  error_code="DATA_COVERAGE_UNVERIFIED")
    structured = result["structured_result"]
    structured.update(status="NO_EVIDENCE", coverage_status="UNKNOWN",
                      absence_confirmed=False, query_execution_succeeded=True)
    # Apply the same interpretation to summary, map metadata and evidence.
    seen = set()
    def qualify(value):
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                return
            seen.add(id(value))
        if isinstance(value, dict):
            if "total_count" in value or "total_hazard_count" in value:
                for key in ("count", "total_count", "total_hazard_count",
                            "total_counts_by_type", "feature_type_breakdown"):
                    if key in value:
                        value["observed_" + key] = value[key]
                        value[key] = None
                value.update(coverage_status="UNKNOWN", absence_confirmed=False)
            for child in list(value.values()):
                qualify(child)
        elif isinstance(value, list):
            for child in value:
                qualify(child)
    for key in ("structured_result", "spatial_result_summary", "map_layers", "evidence_bundle"):
        qualify(result.get(key))
    for evidence in result.get("evidence_bundle", {}).get("spatial_layer_evidence", []):
        evidence["summary"] = text
    for surface in (structured, structured.get("result_surface", {})):
        surface.setdefault("user_evidence_summary", {})["coverage_basis"] = text
    for claim in result.get("claims", []):
        claim["text"] = text
    for task in result.get("task_results", []):
        task.update(status="NO_EVIDENCE", coverage_status="UNKNOWN")
    return result


def build_bounds_result(qec, layer, params, total, counts, rows, search_geometry):
    request_id = qec.request_id
    snapshot_hash = hashlib.sha256(json.dumps(qec.snapshot_versions, sort_keys=True).encode()).hexdigest()[:12]
    execution_id = f"{request_id}:r{qec.revision}:{qec.plan_hash[:16]}:{snapshot_hash}"
    result_id = f"result:{execution_id}"
    properties, collection, evidence = _feature_rows_to_geojson(qec, layer, rows, result_id, execution_id)
    ids = [row["feature_instance_id"] for row in properties]
    expected_returned = min(params["result_limit"], max(0, total - params["offset"]))
    if len(ids) != len(set(ids)) or len(rows) != expected_returned or sum(counts.values()) != total:
        raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "검색 결과의 식별자와 건수를 검증하지 못했습니다.")
    if any(row["feature_name"] not in qec.slots.target_features for row in properties):
        raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "검색 결과가 요청한 대상 조건과 일치하지 않습니다.")
    summary_values = {
        "result_id": result_id,
        "query_execution_id": execution_id,
        "count": total,
        "total_count": total,
        "returned_count": len(rows),
        "nearest_returned_count": len(rows),
        "feature_ids": ids,
        "result_limit": params["result_limit"],
        "offset": params["offset"],
        "truncated": total > len(rows),
        "returned_counts_by_type": dict(Counter(row["feature_name"] for row in properties)),
        "total_counts_by_type": counts,
        "feature_type_breakdown": counts,
    }
    user_evidence_summary = {
        "query_interpretation": f"'{qec.original_query}' 질의를 항행안전 위험객체 조회로 해석했습니다.",
        "location_basis": "기준 지점이 명시되지 않아 사용자가 보고 있는 현재 지도 범위(bbox)를 검색 범위로 사용했습니다.",
        "data_basis": f"S-101 전자해도 공간 레이어({layer['physical_table']})에서 Registry가 승인한 위험객체 유형만 조회했습니다.",
        "result_basis": "PostGIS 공간 교차검색(ST_Intersects)으로 현재 지도 bbox 안에 걸치는 객체를 선별했습니다.",
    }
    summary_id = f"spatial-summary:{execution_id}"
    bundle = EvidenceBundle(
        spatial_feature_evidence=evidence,
        spatial_layer_evidence=[EvidenceItem(
            evidence_id=summary_id,
            evidence_type="spatial_query_summary",
            source_ref=layer["physical_table"],
            summary="; ".join(user_evidence_summary.values()),
            data={**summary_values, "snapshot": qec.snapshot_versions, "user_evidence_summary": user_evidence_summary},
        )],
        kg_provenance=[EvidenceItem(
            evidence_id=f"kg:{execution_id}:hazard-policy",
            evidence_type="registry_policy",
            source_ref="data/derived_concept_registry_v2.yaml#navigation_hazard_object.s101_hazard_radius",
            summary="위험객체 대상은 Registry/KG의 navigation_hazard_object 실행 정책에서 승인된 S-101 feature class로 제한했습니다.",
            data={"target_features": qec.slots.target_features, "feature_codes": params["feature_codes"]},
        )],
    )
    evidence_counts = {
        "spatial_feature_evidence": len(evidence),
        "spatial_layer_evidence": 1,
        "rag_evidence": 0,
        "kg_provenance": 1,
        "regulatory_evidence": 0,
    }
    quality_metrics = _quality_metrics("s101_hazard_bbox_quality_v1", fast_path="validated_s101_hazard_bbox")
    source_layer = _source_layer(layer)
    usage = {"web_used": False, "rag_used": False, "llm_used": False, "execution_path": "postgis.intersects", "embedding_independent": True}
    text = f"현재 지도 범위 안에서 위험객체 {total}건을 찾았습니다. 지도·표·근거는 같은 객체 목록 {len(rows)}건을 기준으로 표시합니다."
    map_layers = [{
        "layer_id": result_id,
        "title": "현재 지도 범위 위험객체",
        "role": "matched_features",
        "source_type": "geojson",
        "geometry_type": "GEOMETRY",
        "inline_geojson": collection,
        "feature_count": len(rows),
        "metadata": {**summary_values, "role": "matched_features"},
    }]
    if search_geometry:
        map_layers.append({
            "layer_id": f"{result_id}:bbox",
            "title": "현재 지도 범위",
            "role": "search_area",
            "source_type": "geojson",
            "geometry_type": "POLYGON",
            "inline_geojson": {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": search_geometry, "properties": {"role": "search_area", "basis": "current_map_bbox"}}]},
            "feature_count": 1,
            "metadata": {"role": "search_area", "result_id": result_id, "opacity": 0.12, "clickable": False},
        })
    result_surface = {
        "total_hazard_count": total,
        "nearest_returned_count": len(rows),
        "feature_type_breakdown": counts,
        "returned_feature_type_breakdown": summary_values["returned_counts_by_type"],
        "source_layer": source_layer,
        "reference_geometry": qec.slots.reference_geometry,
        "reference_crs": qec.slots.crs,
        "geojson": {"feature_count": len(collection["features"]), "available": True},
        "map_layers": {"count": len(map_layers), "feature_layer_id": result_id, "search_area_layer_id": f"{result_id}:bbox" if search_geometry else None},
        "evidence_bundle": evidence_counts,
        "web_rag_usage": usage,
        "user_evidence_summary": user_evidence_summary,
    }
    result = {
        "task_id": request_id,
        "request_id": request_id,
        "contract_version": qec.contract_version,
        "agent_name": "Spatial Analysis Agent",
        "status": "COMPLETED",
        "summary": text,
        "answer_text": text,
        "quality_metrics": quality_metrics,
        "structured_result": {
            **summary_values,
            "status": "SUCCESS" if total else "SUCCESS_EMPTY",
            "analysis_type": "feature_search_by_area",
            "location_text": qec.slots.location_text,
            "reference_geometry": qec.slots.reference_geometry,
            "reference_crs": qec.slots.crs,
            "source_layer": source_layer,
            "distance_m": None,
            "original_query": qec.original_query,
            "target_features": qec.slots.target_features,
            "exclusions": qec.slots.exclusions,
            "location_resolution": qec.provenance["location_resolution"],
            "features": properties,
            "geojson": collection,
            "geojson_feature_count": len(collection["features"]),
            "map_layer_count": len(map_layers),
            "evidence_bundle_counts": evidence_counts,
            "web_rag_usage": usage,
            "user_evidence_summary": user_evidence_summary,
            "quality_metrics": quality_metrics,
            "result_surface": result_surface,
        },
        "spatial_result_summary": summary_values,
        "features": collection,
        "map_layers": map_layers,
        "evidence_bundle": bundle.model_dump(mode="json"),
        "claims": [{"claim_id": f"claim:{execution_id}", "text": text, "evidence_ids": [summary_id, *[item.evidence_id for item in evidence]]}],
        "task_results": [{"task_id": request_id, "result_id": result_id, "status": "SUCCESS" if total else "SUCCESS_EMPTY"}],
        "orchestrator_v2": {
            "route_plan": qec.route_plan,
            "query_execution_context": qec.model_dump(mode="json"),
            "embedding_independent": True,
            "fast_path": "validated_s101_hazard_bbox",
            "quality_metrics": quality_metrics,
        },
    }
    return _qualify_unverified_empty(result, total)


def build_hazard_definition_result(state):
    query, spatial = state.get("query", ""), _spatial(state)
    request_id = str(state["task_id"])
    profile = ((_registry("derived_concept_registry_v2.yaml").get("derived_concepts") or {}).get(CONCEPT, {}).get("execution_profiles") or {}).get(PROFILE) or {}
    targets = list(profile.get("target_features") or [])
    aliases = profile.get("feature_aliases") or {}
    text = (
        "위험객체는 항행안전 관점에서 선박 운항에 주의가 필요한 전자해도 객체 후보입니다. "
        "이 시스템에서는 Registry/KG 정책에 따라 S-101의 Wreck(침선), Obstruction(장애물), UnderwaterAwashRock(수중·간출암), "
        "고립위험 표지와 관련 부표·표지류를 위험객체 대상에 포함합니다. 현재 지도 범위가 전달되면 그 bbox 안에서 바로 찾고, "
        "기준 지명이 있으면 기본 부근 3km 이내부터 조회합니다."
    )
    quality_metrics = _quality_metrics("s101_hazard_definition_quality_v1", fast_path="hazard_definition_fallback", exact=False)
    evidence_id = f"kg:{request_id}:hazard-definition"
    bundle = EvidenceBundle(kg_provenance=[EvidenceItem(
        evidence_id=evidence_id,
        evidence_type="registry_policy",
        source_ref="data/derived_concept_registry_v2.yaml#navigation_hazard_object.s101_hazard_radius",
        summary="navigation_hazard_object 실행 정책의 target_features와 feature_aliases를 근거로 위험객체 범위를 설명했습니다.",
        data={"target_features": targets, "feature_aliases": aliases},
    )])
    qec = QueryExecutionContext(
        request_id=request_id,
        task_id=request_id,
        revision=state.get("execution_revision") or 1,
        original_query=query,
        normalized_query=state.get("normalized_query") or query,
        slots=ExecutionSlots(
            location_text=spatial.get("base_location") or spatial.get("location_text"),
            target_term=CONCEPT,
            concept_id=CONCEPT,
            context=profile.get("context") or "navigation_safety",
            target_features=targets,
            resolved_target_set=targets,
            analysis_type="hazard_definition",
        ),
        route_plan={
            "task_id": request_id,
            "intent": "marine_hazard_definition_or_map_context_request",
            "analysis_type": "hazard_definition",
            "primary_agent": "Spatial Analysis Agent",
            "execution_ready": False,
            "status": "NEEDS_SPATIAL_CONTEXT",
            "route_plan_status": "NEEDS_SPATIAL_CONTEXT",
            "tools": [],
            "data": ["data/derived_concept_registry_v2.yaml"],
        },
        semantic_resolution={"context": profile.get("context") or "navigation_safety", "target_policy": f"{CONCEPT}.{PROFILE}", "source_ref": "data/derived_concept_registry_v2.yaml"},
        provenance={"hazard_definition": {"source_ref": "data/derived_concept_registry_v2.yaml", "target_features": targets}},
    )
    return {
        "task_id": request_id,
        "request_id": request_id,
        "contract_version": qec.contract_version,
        "agent_name": "Spatial Analysis Agent",
        "status": "COMPLETED",
        "summary": text,
        "answer_text": text,
        "quality_metrics": quality_metrics,
        "structured_result": {
            "status": "SUCCESS",
            "analysis_type": "hazard_definition",
            "count": None,
            "returned_count": 0,
            "original_query": query,
            "location_text": spatial.get("base_location") or spatial.get("location_text"),
            "target_term": CONCEPT,
            "target_features": targets,
            "feature_aliases": aliases,
            "requires_map_context_for_search": True,
            "suggested_search_inputs": {
                "current_map_bbox": "지도 화면 범위를 전달하면 현 bbox 안의 위험객체를 조회합니다.",
                "reference_location": "예: 부산항 입구 위험객체, 독도 주변 위험객체",
                "default_nearby_radius_m": None,
            },
            "evidence_bundle_counts": {"spatial_feature_evidence": 0, "spatial_layer_evidence": 0, "rag_evidence": 0, "kg_provenance": 1, "regulatory_evidence": 0},
            "quality_metrics": quality_metrics,
            "user_evidence_summary": {
                "query_interpretation": f"'{query}'를 위험객체 개념 설명 및 지도 검색 준비 질의로 해석했습니다.",
                "definition_basis": "위험객체 범위는 derived_concept_registry_v2.yaml의 navigation_hazard_object 실행 정책에서 가져왔습니다.",
                "execution_basis": "현재 지도 bbox 또는 기준 지점이 확정되면 공간검색을 실행합니다.",
            },
        },
        "map_layers": [],
        "evidence_bundle": bundle.model_dump(mode="json"),
        "claims": [{"claim_id": f"claim:{request_id}:hazard-definition", "text": text, "evidence_ids": [evidence_id]}],
        "task_results": [{"task_id": request_id, "result_id": f"result:{request_id}:hazard-definition", "status": "SUCCESS"}],
        "orchestrator_v2": {
            "route_plan": qec.route_plan,
            "query_execution_context": qec.model_dump(mode="json"),
            "embedding_independent": True,
            "fast_path": "hazard_definition_fallback",
            "quality_metrics": quality_metrics,
        },
    }


def build_result(qec, layer, params, total, counts, rows, search_geometry):
    request_id = qec.request_id
    snapshot_hash = hashlib.sha256(json.dumps(qec.snapshot_versions, sort_keys=True).encode()).hexdigest()[:12]
    execution_id = f"{request_id}:r{qec.revision}:{qec.plan_hash[:16]}:{snapshot_hash}"
    result_id = f"result:{execution_id}"
    properties, features, evidence = [], [], []
    for row in rows:
        try:
            geometry = shape(row["geometry"])
            if geometry.is_empty or not geometry.is_valid:
                raise ValueError("invalid result geometry")
        except (ShapelyError, AttributeError, KeyError, TypeError, ValueError) as exc:
            raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "지도에 표시할 객체 도형을 검증하지 못했습니다.") from exc
        identifier = str(row["id"])
        evidence_id = f"spatial:{execution_id}:{identifier}"
        geometry_type = row["geometry"].get("type") if isinstance(row.get("geometry"), dict) else geometry.geom_type
        portrayal = resolve_s101_portrayal(row["feature_type_name"], geometry_type, row.get("attributes"))
        item = {
            "feature_instance_id": identifier, "feature_name": row["feature_type_name"],
            "feature_type_code": row["feature_type_code"], "source_dataset_id": row["source_dataset_id"],
            "dataset_version_id": row["dataset_version_id"], "dataset_id": qec.data_bindings[0].dataset_id,
            "geometry_type": row.get("geometry_type") or geometry_type,
            "attributes": row.get("attributes") or {},
            "distance_m": float(row["distance_m"]), "source": layer["physical_table"],
            "result_id": result_id, "query_execution_id": execution_id, "evidence_id": evidence_id,
            "portrayal": portrayal, "portrayal_symbol": portrayal.get("symbol"),
            "portrayal_symbol_asset": portrayal.get("asset"), "s101_symbol": portrayal.get("symbol"),
            "s101_symbol_asset": portrayal.get("asset"), "s101_symbol_format": "svg",
        }
        properties.append(item)
        features.append({"type": "Feature", "id": identifier, "geometry": row["geometry"], "properties": item})
        evidence.append(EvidenceItem(evidence_id=evidence_id, evidence_type="spatial_feature", source_ref=layer["physical_table"], data=item))
    ids = [row["feature_instance_id"] for row in properties]
    expected_returned = min(params["result_limit"], max(0, total - params["offset"]))
    if len(ids) != len(set(ids)) or len(rows) != expected_returned or sum(counts.values()) != total:
        raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "검색 결과의 식별자와 건수를 검증하지 못했습니다.")
    if any(row["feature_name"] not in qec.slots.target_features or not math.isfinite(row["distance_m"]) or not 0 <= row["distance_m"] <= qec.slots.distance_m for row in properties):
        raise RadiusProblem("FAILED", "RESULT_CONTRACT_MISMATCH", "검색 결과가 요청한 대상 또는 거리 조건과 일치하지 않습니다.")
    collection = {"type": "FeatureCollection", "features": features}
    summary_values = {
        "result_id": result_id, "query_execution_id": execution_id, "count": total, "total_count": total,
        "returned_count": len(rows), "nearest_returned_count": len(rows), "feature_ids": ids, "result_limit": params["result_limit"],
        "offset": params["offset"], "truncated": total > len(rows),
        "returned_counts_by_type": dict(Counter(row["feature_name"] for row in properties)),
        "total_counts_by_type": counts, "feature_type_breakdown": counts,
    }
    summary_id = f"spatial-summary:{execution_id}"
    bundle = EvidenceBundle(
        spatial_feature_evidence=evidence,
    )
    distance_policy = qec.provenance.get("distance_policy") or {}
    user_evidence_summary = {
        "query_interpretation": f"'{qec.original_query}' 질의를 항행안전 위험객체 조회로 해석했습니다.",
        "location_basis": f"기준점은 '{qec.slots.location_text}'이며 좌표는 {qec.slots.reference_geometry} ({qec.slots.crs})입니다.",
        "distance_basis": distance_policy.get("summary") or f"검색 반경 {qec.slots.distance_m:g}m를 적용했습니다.",
        "data_basis": f"S-101 전자해도 공간 레이어({layer['physical_table']})에서 승인된 위험객체 유형만 조회했습니다.",
        "result_basis": f"PostGIS 거리검색(ST_DWithin)으로 기준점에서 {qec.slots.distance_m:g}m 이내인 객체를 선별했습니다.",
    }
    bundle.spatial_layer_evidence = [EvidenceItem(
        evidence_id=summary_id,
        evidence_type="spatial_query_summary",
        source_ref=layer["physical_table"],
        summary="; ".join(user_evidence_summary.values()),
        data={
            **summary_values,
            "query_template_id": qec.route_plan["radius_template_id"],
            "snapshot": qec.snapshot_versions,
            "distance_policy": distance_policy,
            "user_evidence_summary": user_evidence_summary,
        },
    )]
    default_note = " 부근 기본 반경 3km를 먼저 적용했습니다." if distance_policy.get("default_applied") else ""
    text = f"{qec.slots.location_text} 기준 {qec.slots.distance_m:g}m 이내 위험객체 {total}건을 찾았습니다.{default_note} 지도·표·객체 근거에 동일한 {len(rows)}건을 표시합니다."
    source_layer = {
        "layer_id": qec.route_plan.get("radius_layer_id"),
        "physical_table": layer.get("physical_table"),
        "geometry_column": layer.get("geometry_column"),
        "id_column": layer.get("id_column"),
        "code_column": layer.get("code_column"),
        "name_column": layer.get("name_column"),
        "srid": layer.get("srid"),
    }
    evidence_counts = {
        "spatial_feature_evidence": len(evidence),
        "spatial_layer_evidence": 1,
        "rag_evidence": 0,
        "kg_provenance": 0,
        "regulatory_evidence": 0,
    }
    usage = {
        "web_used": False,
        "rag_used": False,
        "llm_used": False,
        "execution_path": "postgis.dwithin",
        "embedding_independent": True,
    }
    result_surface = {
        "total_hazard_count": total,
        "nearest_returned_count": len(rows),
        "feature_type_breakdown": counts,
        "returned_feature_type_breakdown": summary_values["returned_counts_by_type"],
        "source_layer": source_layer,
        "reference_geometry": qec.slots.reference_geometry,
        "reference_crs": qec.slots.crs,
        "geojson": {"feature_count": len(features), "available": True},
        "map_layers": {"count": 2 if search_geometry else 1, "feature_layer_id": result_id, "search_area_layer_id": f"{result_id}:range" if search_geometry else None},
        "evidence_bundle": evidence_counts,
        "web_rag_usage": usage,
        "user_evidence_summary": user_evidence_summary,
        "distance_policy": distance_policy,
    }
    map_layers = [{"layer_id": result_id, "title": "검색된 객체", "role": "matched_features", "source_type": "geojson", "geometry_type": "GEOMETRY", "inline_geojson": collection, "feature_count": len(rows), "metadata": {**summary_values, "role": "matched_features"}}]
    if search_geometry:
        map_layers.append({"layer_id": f"{result_id}:range", "title": "검색 범위", "role": "search_area", "source_type": "geojson", "geometry_type": "POLYGON", "inline_geojson": {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": search_geometry, "properties": {"role": "search_area", "distance_m": qec.slots.distance_m}}]}, "feature_count": 1, "metadata": {"role": "search_area", "result_id": result_id}})
    result = {
        "task_id": request_id, "request_id": request_id, "contract_version": qec.contract_version,
        "agent_name": "Spatial Analysis Agent", "status": "COMPLETED", "summary": text, "answer_text": text,
        "structured_result": {**summary_values, "status": "SUCCESS" if total else "SUCCESS_EMPTY", "analysis_type": OPERATION,
                              "location_text": qec.slots.location_text, "reference_geometry": qec.slots.reference_geometry,
                              "reference_crs": qec.slots.crs, "source_layer": source_layer,
                              "distance_m": qec.slots.distance_m, "original_query": qec.original_query,
                              "target_features": qec.slots.target_features, "exclusions": qec.slots.exclusions,
                              "distance_policy": distance_policy, "user_evidence_summary": user_evidence_summary,
                              "place_id": qec.provenance["location_resolution"].get("place_id"),
                              "place_version": qec.provenance["location_resolution"].get("place_version"),
                              "location_resolution": qec.provenance["location_resolution"], "features": properties, "geojson": collection,
                              "geojson_feature_count": len(features), "map_layer_count": len(map_layers),
                              "evidence_bundle_counts": evidence_counts, "web_rag_usage": usage, "result_surface": result_surface},
        "spatial_result_summary": summary_values, "features": collection, "map_layers": map_layers,
        "evidence_bundle": bundle.model_dump(mode="json"),
        "claims": [{"claim_id": f"claim:{execution_id}", "text": text, "evidence_ids": [summary_id, *[item.evidence_id for item in evidence]]}],
        "task_results": [{"task_id": request_id, "result_id": result_id, "status": "SUCCESS" if total else "SUCCESS_EMPTY"}],
        "orchestrator_v2": {"route_plan": qec.route_plan, "query_execution_context": qec.model_dump(mode="json"), "embedding_independent": True, "fast_path": "validated_s101_hazard_radius"},
    }
    return _qualify_unverified_empty(result, total)


def execute_radius_request(state):
    qec = None
    try:
        spatial = _spatial(state)
        if _map_bounds_polygon(spatial) is not None and not _has_reference_location(spatial):
            qec, layer, params = prepare_bounds_request(state)
            return build_bounds_result(qec, layer, params, *_fetch_bounds_result(qec, layer, params))
        qec, layer, template, params = prepare_radius_request(state)
        result = build_result(qec, layer, params, *_fetch_result(qec, layer, template, params))
        if result.get("status") != "COMPLETED":
            return result
        distance_policy = qec.provenance.get("distance_policy") or {}
        default_note = " 부근 기본 반경 3km를 먼저 적용했습니다." if distance_policy.get("default_applied") else ""
        text = (
            f"{qec.slots.location_text} 기준 {qec.slots.distance_m:g}m 이내 "
            f"위험객체 {result['structured_result']['total_count']}건을 찾았습니다.{default_note} "
            f"지도에는 객체 {result['structured_result']['returned_count']}건과 검색 범위를 표시합니다."
        )
        result["summary"] = text
        result["answer_text"] = text
        if result.get("claims"):
            result["claims"][0]["text"] = text
        return result
    except RadiusProblem as exc:
        problem = exc
    except psycopg2.Error as exc:
        code = "DB_TIMEOUT" if exc.pgcode == "57014" else "DB_EXECUTION_FAILED"
        problem = RadiusProblem("FAILED", code, "공간 데이터 조회에 실패했습니다. 결과를 생성하지 않았습니다.")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        problem = RadiusProblem("BLOCKED_CONFIG", "INVALID_EXECUTION_CONFIG", "실행 설정 또는 응답 형식을 확인해야 합니다.")
    if problem.code in {"LOCATION_REQUIRED", "PLACE_NOT_FOUND", "LOCATION_UNCONFIRMED"} and _looks_like_contextual_hazard_only(state.get("query", "")):
        return build_hazard_definition_result(state)
    status = "NEEDS_CLARIFICATION" if problem.status == "NEEDS_USER_INPUT" else "FAILED" if problem.status == "FAILED" else "BLOCKED"
    spatial = _spatial(state)
    if qec is None:
        qec = QueryExecutionContext(request_id=str(state["task_id"]), revision=state.get("execution_revision") or 1, original_query=state.get("query"), route_plan={"analysis_type": OPERATION, "primary_agent": "Spatial Analysis Agent"})
    if problem.status != "FAILED":
        qec.readiness = PlanStatus(problem.status)
    qec.blockers = [f"{problem.status}: {problem.code}"]
    if problem.status != "FAILED":
        qec.route_plan.update(status=qec.readiness.value, route_plan_status=qec.readiness.value, execution_ready=False)
    try:
        distance_hint = parse_distance(state.get("query", ""), spatial)
    except RadiusProblem:
        distance_hint = None
    surface = {
        "total_hazard_count": None,
        "nearest_returned_count": 0,
        "feature_type_breakdown": {},
        "returned_feature_type_breakdown": {},
        "source_layer": None,
        "reference_geometry": spatial.get("geometry"),
        "reference_crs": spatial.get("crs"),
        "geojson": {"feature_count": 0, "available": False},
        "map_layers": {"count": 0, "feature_layer_id": None, "search_area_layer_id": None},
        "evidence_bundle": {"spatial_feature_evidence": 0, "spatial_layer_evidence": 0, "rag_evidence": 0, "kg_provenance": 0, "regulatory_evidence": 0},
        "web_rag_usage": {"web_used": False, "rag_used": False, "llm_used": False, "execution_path": "postgis.dwithin", "embedding_independent": True},
    }
    return {
        "task_id": state["task_id"], "request_id": state["task_id"], "status": status,
        "agent_name": "Spatial Analysis Agent", "contract_version": qec.contract_version,
        "error_code": problem.code, "summary": str(problem), "answer_text": str(problem),
        "clarification_questions": [str(problem)] if status == "NEEDS_CLARIFICATION" else [],
        "clarification_options": problem.candidates,
        "structured_result": {"analysis_type": OPERATION, "status": status, "count": None, "returned_count": 0,
                              "nearest_returned_count": 0, "feature_type_breakdown": {},
                              "total_counts_by_type": {}, "returned_counts_by_type": {},
                              "original_query": state.get("query"), "location_text": spatial.get("base_location"),
                              "spatial_context": {key: value for key, value in spatial.items() if key in {
                                  "base_location", "location_text", "geometry", "crs", "buffer_distance",
                                  "target_features", "exclusions", "context", "result_limit", "offset",
                                  "place_id", "place_version",
                              }},
                              "distance_m": distance_hint, "location_candidates": problem.candidates,
                              "source_layer": None, "reference_geometry": spatial.get("geometry"),
                              "reference_crs": spatial.get("crs"), "geojson_feature_count": 0,
                              "map_layer_count": 0, "evidence_bundle_counts": surface["evidence_bundle"],
                              "web_rag_usage": surface["web_rag_usage"], "result_surface": surface},
        "map_layers": [], "evidence_bundle": EvidenceBundle().model_dump(mode="json"),
        "orchestrator_v2": {"route_plan": qec.route_plan, "query_execution_context": qec.model_dump(mode="json")},
    }
