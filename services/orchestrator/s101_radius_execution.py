"""Registry policy, confirmed locations, and one result set for radius searches."""

import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2 import sql
import yaml
from shapely import wkt
from shapely.geometry import shape
from shapely.errors import ShapelyError

from services.orchestrator.execution_validator import MAX_RADIUS_M, validate_execution_context
from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
from services.orchestrator.s101_portrayal import resolve_s101_portrayal
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location
from shared.schemas.agent import EvidenceBundle, EvidenceItem, ExecutionSlots, PlanStatus, QueryExecutionContext

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


def _registry(filename):
    try:
        value = yaml.safe_load((DATA_DIR / filename).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("registry must be a mapping")
        return value
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise RadiusProblem("BLOCKED_CONFIG", "INVALID_REGISTRY", "실행 설정을 읽을 수 없습니다.") from exc


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
    pattern = r"(?<![\d.])([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|[+-]?\.\d+)\s*(킬로미터|킬로|km|㎞|해리|nm|미터|m)(?![A-Za-z])"
    factors = {"킬로미터": 1000, "킬로": 1000, "km": 1000, "㎞": 1000, "해리": 1852, "nm": 1852}
    distances = {float(number.replace(",", "")) * factors.get(unit.lower(), 1) for number, unit in re.findall(pattern, query, re.I)}
    supplied = spatial.get("buffer_distance")
    try:
        if supplied is not None:
            if isinstance(supplied, bool):
                raise ValueError("boolean radius")
            distances.add(float(supplied))
    except (TypeError, ValueError) as exc:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_RADIUS", "반경을 양의 거리로 지정해 주세요.") from exc
    if not distances:
        raise RadiusProblem("NEEDS_USER_INPUT", "RADIUS_REQUIRED", "검색 반경을 지정해 주세요. 예: 3km.")
    if len(distances) > 1:
        raise RadiusProblem("NEEDS_USER_INPUT", "CONFLICTING_RADIUS", "서로 다른 반경이 지정되어 있습니다. 사용할 반경을 알려 주세요.")
    distance = distances.pop()
    if not math.isfinite(distance) or distance <= 0:
        raise RadiusProblem("NEEDS_USER_INPUT", "INVALID_RADIUS", "반경은 유한한 양수여야 합니다.")
    if distance > MAX_RADIUS_M:
        raise RadiusProblem("BLOCKED_POLICY", "RADIUS_LIMIT", f"검색 반경은 {MAX_RADIUS_M / 1000:g}km 이하여야 합니다.")
    return distance


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
            excluded = re.search(escaped + r"(?:을|를|은|는)?\s*(?:제외|빼고|빼줘)", query, re.I) or re.search(r"(?:without|except|excluding|exclude)\s+(?:the\s+)?" + escaped, query, re.I)
            (exclusions if excluded else mentions).append(feature)
    requested = spatial.get("target_features")
    explicit_exclusions = list(spatial.get("exclusions") or [])
    for item in explicit_exclusions:
        for feature in allowed:
            if str(item).casefold() in {str(alias).casefold() for alias in [feature, *(aliases.get(feature) or [])]}:
                exclusions.append(feature)
    if requested is not None:
        if not isinstance(requested, list) or not requested or any(item not in allowed for item in requested):
            raise RadiusProblem("NEEDS_USER_INPUT", "UNSUPPORTED_TARGET", "요청한 대상을 승인된 위험객체 종류로 지정해 주세요.")
        targets = requested
    else:
        generic = any(term in query.casefold() for term in ["위험객체", "위험 객체", "hazard", CONCEPT])
        only = re.search(r"(?:wrecks?|obstructions?|underwaterawashrocks?|침선|난파선|장애물|간출암|수중암)\s*(?:만|only)", query, re.I)
        if not generic and not mentions and not exclusions:
            raise RadiusProblem("NEEDS_USER_INPUT", "UNSUPPORTED_TARGET", "검색할 위험객체 종류를 확인해 주세요.")
        targets = mentions if mentions and (not generic or only) else allowed
    targets = [feature for feature in dict.fromkeys(targets) if feature not in exclusions]
    if not targets:
        raise RadiusProblem("NEEDS_USER_INPUT", "EMPTY_TARGET_SET", "제외 조건을 적용하면 검색할 대상이 없습니다. 대상 종류를 지정해 주세요.")
    return targets, list(dict.fromkeys([*exclusions, *explicit_exclusions]))


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
    geometry, label, crs, resolution = resolve_reference(query, spatial, _registry("place_geometry_registry.yaml").get("places") or {})
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
        provenance={"location_resolution": resolution},
    )
    qec.plan_hash = hashlib.sha256(json.dumps({"slots": slots.model_dump(), "location_resolution": resolution, "layer": layer, "template": template, "limit": limit, "offset": offset}, sort_keys=True).encode()).hexdigest()
    xmin, ymin, xmax, ymax = conservative_envelope(point, distance)
    params = {"base_wkt": point.wkt, "srid": 4326, "distance_m": distance, "feature_codes": slots.nftc_codes,
              "feature_code_map": {feature: _codes_for_feature(codes, feature) for feature in targets},
              "target_features": targets, "result_limit": limit, "offset": offset,
              "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}
    return qec, layer, template, params


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
        validated = validate_execution_context(qec, binding_adapter=adapter)
        if validated.readiness != PlanStatus.EXECUTION_READY:
            raise RadiusProblem(validated.readiness.value, "EXECUTION_GATE", "실행 검증을 통과하지 못했습니다. 데이터 연결과 입력 조건을 확인해 주세요.")
        qec.data_bindings, qec.tool_bindings = validated.data_bindings, validated.tool_bindings
        qec.provenance.update(validated.provenance)
        if not any(binding.relation == layer["physical_table"] and binding.geometry_column == layer["geometry_column"] and binding.srid == 4326 for binding in validated.data_bindings):
            raise RadiusProblem("BLOCKED_CONFIG", "REGISTRY_CHANGED", "데이터 연결 설정이 변경되었습니다. 다시 조회해 주세요.")
        if adapter.template_registry.get("templates", {}).get(qec.route_plan["radius_template_id"]) != template:
            raise RadiusProblem("BLOCKED_CONFIG", "REGISTRY_CHANGED", "검색 템플릿이 변경되었습니다. 다시 조회해 주세요.")
        qec.readiness = PlanStatus.EXECUTION_READY
        qec.route_plan.update(execution_ready=True, status="EXECUTION_READY", route_plan_status="EXECUTION_READY")
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
            cursor.execute(code_query, (params["target_features"], params["feature_codes"]))
            expected = {
                (feature, int(code))
                for feature, codes in params.get("feature_code_map", {}).items()
                for code in codes
            }
            observed = {(str(name), int(code)) for name, code in cursor.fetchall()}
            if observed - expected:
                raise RadiusProblem("BLOCKED_CONFIG", "FEATURE_CODE_CONFLICT", "데이터셋의 객체 코드가 실행 정책과 일치하지 않습니다.")
            cursor.execute(_statement(layer, template), params)
            total, counts, rows, search_geometry = cursor.fetchone()
            cursor.execute("SELECT txid_current_snapshot()::text, transaction_timestamp()::text")
            snapshot, captured_at = cursor.fetchone()
    qec.readiness = PlanStatus.EXECUTION_READY
    qec.route_plan.update(execution_ready=True, status="EXECUTION_READY", route_plan_status="EXECUTION_READY")
    qec.snapshot_versions.update(data_snapshot=snapshot, captured_at=captured_at)
    return int(total), counts, rows, search_geometry


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
        spatial_layer_evidence=[EvidenceItem(evidence_id=summary_id, evidence_type="spatial_query_summary", source_ref=layer["physical_table"], data={**summary_values, "query_template_id": qec.route_plan["radius_template_id"], "snapshot": qec.snapshot_versions})],
    )
    text = f"{qec.slots.location_text} 기준 {qec.slots.distance_m:g}m 이내 주의 후보 객체 {total}건을 찾았습니다. 지도·표·객체 근거에 동일한 {len(rows)}건을 표시합니다."
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
    }
    map_layers = [{"layer_id": result_id, "title": "검색된 객체", "role": "matched_features", "source_type": "geojson", "geometry_type": "GEOMETRY", "inline_geojson": collection, "feature_count": len(rows), "metadata": {**summary_values, "role": "matched_features"}}]
    if search_geometry:
        map_layers.append({"layer_id": f"{result_id}:range", "title": "검색 범위", "role": "search_area", "source_type": "geojson", "geometry_type": "POLYGON", "inline_geojson": {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": search_geometry, "properties": {"role": "search_area", "distance_m": qec.slots.distance_m}}]}, "feature_count": 1, "metadata": {"role": "search_area", "result_id": result_id}})
    return {
        "task_id": request_id, "request_id": request_id, "contract_version": qec.contract_version,
        "agent_name": "Spatial Analysis Agent", "status": "COMPLETED", "summary": text, "answer_text": text,
        "structured_result": {**summary_values, "status": "SUCCESS" if total else "SUCCESS_EMPTY", "analysis_type": OPERATION,
                              "location_text": qec.slots.location_text, "reference_geometry": qec.slots.reference_geometry,
                              "reference_crs": qec.slots.crs, "source_layer": source_layer,
                              "distance_m": qec.slots.distance_m, "original_query": qec.original_query,
                              "target_features": qec.slots.target_features, "exclusions": qec.slots.exclusions,
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


def execute_radius_request(state):
    qec = None
    try:
        qec, layer, template, params = prepare_radius_request(state)
        result = build_result(qec, layer, params, *_fetch_result(qec, layer, template, params))
        text = (
            f"{qec.slots.location_text} 기준 {qec.slots.distance_m:g}m 이내 "
            f"위험객체 {result['structured_result']['total_count']}건을 찾았습니다. "
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
