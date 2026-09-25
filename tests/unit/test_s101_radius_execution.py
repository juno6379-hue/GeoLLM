"""Policy/input and result identity tests; DB rows here are explicit fixtures."""

import copy
from unittest.mock import Mock

import pytest

from services.orchestrator import s101_radius_execution as radius
from shared.schemas.agent import DataBinding, EvidenceBundle, PlanStatus, QueryExecutionContext



@pytest.fixture(autouse=True)
def isolated_location_sources(monkeypatch):
    from services.spatial_analysis_agent import place_resolver
    places = {
        "busan_port_entrance": {"canonical_name": "부산항 입구", "aliases": ["Busan Port Entrance"], "geometry_wkt": "POINT(129.075 35.075)", "srid": 4326, "status": "curated"},
        "incheon_port": {"canonical_name": "인천항", "aliases": ["Incheon Port"], "geometry_wkt": "POINT(126.6 37.45)", "srid": 4326, "status": "curated"},
    }
    monkeypatch.setattr(radius, "_place_entries", lambda: places)
    monkeypatch.setattr(place_resolver, "load_catalog", lambda **kwargs: {"candidates": [], "unavailable_sources": []})
    return places

@pytest.fixture
def state():
    return {
        "task_id": "fixture-radius", "user_id": "fixture-user",
        "query": "부산항 입구 3km 이내 위험객체를 찾아줘",
        "spatial_context": {"base_location": "부산항 입구", "geometry": "POINT(129.075 35.075)", "crs": "EPSG:4326", "buffer_distance": 3000, "result_limit": 30},
    }


@pytest.fixture
def registries(monkeypatch, isolated_location_sources):
    original = radius._registry
    data = {name: original(name) for name in [
        "derived_concept_registry_v2.yaml", "place_geometry_registry.yaml",
        "spatial_layer_registry.yaml", "query_template_registry.yaml",
    ]}
    data["place_geometry_registry.yaml"] = {"places": isolated_location_sources}
    monkeypatch.setattr(radius, "_place_entries", lambda: data["place_geometry_registry.yaml"]["places"])
    monkeypatch.setattr(radius, "_registry", lambda name: copy.deepcopy(data[name]))
    return data


def test_curated_location_requires_confirmation_without_opening_db(state, registries, monkeypatch):
    registries["place_geometry_registry.yaml"]["places"]["busan_port_entrance"]["status"] = "curated"
    state["spatial_context"].pop("geometry")
    connect = Mock(side_effect=AssertionError("Unconfirmed location must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)

    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["error_code"] == "LOCATION_UNCONFIRMED"
    assert result["structured_result"]["count"] is None
    assert result["structured_result"]["location_candidates"][0]["geometry"] == "POINT(129.075 35.075)"
    assert not result["evidence_bundle"]["spatial_feature_evidence"]


def test_approved_registry_location_can_execute(state, registries):
    registries["place_geometry_registry.yaml"]["places"]["busan_port_entrance"]["status"] = "approved"
    state["spatial_context"].pop("geometry")
    context, *_ = radius.prepare_radius_request(state)

    assert context.provenance["location_resolution"]["status"] == "APPROVED_REGISTRY"
    assert context.slots.reference_geometry == "POINT (129.075 35.075)"


def test_unknown_explicit_place_does_not_fall_back_to_busan(state, monkeypatch):
    from services.spatial_analysis_agent import place_resolver
    monkeypatch.setattr(place_resolver, "load_catalog", lambda **kwargs: {"candidates": [], "unavailable_sources": []})
    state["spatial_context"] = {"base_location": "Unknown Port", "buffer_distance": 3000, "result_limit": 30}
    result = radius.execute_radius_request(state)

    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["structured_result"]["location_candidates"] == []


def test_conflicting_known_place_names_need_confirmation(state):
    state["spatial_context"]["base_location"] = "인천항"
    result = radius.execute_radius_request(state)

    assert result["error_code"] == "CONFLICTING_LOCATION"
    assert len(result["structured_result"]["location_candidates"]) == 2


@pytest.mark.parametrize("geometry", ["POINT EMPTY", "bad WKT", "POINT(35 200)", "POINT(NaN 35)", "LINESTRING(129 35,130 35)"])
def test_unusable_reference_never_queries_db(state, monkeypatch, geometry):
    state["spatial_context"]["geometry"] = geometry
    connect = Mock(side_effect=AssertionError("Invalid location must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)
    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["error_code"] == "INVALID_GEOMETRY"


@pytest.mark.parametrize("crs", [None, "EPSG:3857", "EPSG:0"])
def test_reference_crs_is_explicit(state, crs):
    state["spatial_context"]["crs"] = crs
    assert radius.execute_radius_request(state)["error_code"] == "CRS_REQUIRED"


@pytest.mark.parametrize(("expression", "expected"), [("3km", 3000), ("3000m", 3000), ("3,000미터", 3000), ("3킬로미터", 3000), ("0.5 km", 500), ("1해리", 1852)])
def test_distance_wording_is_normalized(expression, expected):
    assert radius.parse_distance(f"부산항 입구 {expression} 이내 위험객체", {}) == expected


def test_missing_radius_defaults_to_nearby_three_km_for_hazard_search(state):
    state["query"] = "부산항입구위험객체"
    state["spatial_context"].pop("buffer_distance")

    context, _, _, params = radius.prepare_radius_request(state)

    assert context.slots.distance_m == 3000
    assert params["distance_m"] == 3000
    assert context.provenance["distance_policy"]["default_applied"] is True
    assert "기본 부근 범위" in context.provenance["distance_policy"]["summary"]


def test_current_map_bounds_prepare_area_search_without_place_resolution(state):
    state["query"] = "주변 위험객체를 찾아줘"
    state["spatial_context"] = {"map_bounds": [129.0, 35.0, 129.2, 35.2], "crs": "EPSG:4326"}

    context, layer, params = radius.prepare_bounds_request(state)

    assert context.slots.analysis_type == "feature_search_by_area"
    assert context.slots.location_text == "현재 지도 범위"
    assert context.route_plan["tools"] == ["postgis.intersects"]
    assert params["bounds_wkt"].startswith("POLYGON")
    assert layer["physical_table"]


def test_contextual_hazard_without_map_bounds_returns_definition_not_place_error(state, monkeypatch):
    state["query"] = "주변 위험객체를 찾아줘"
    state["spatial_context"] = {}
    connect = Mock(side_effect=AssertionError("Definition fallback must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)

    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["status"] == "COMPLETED"
    assert result["structured_result"]["analysis_type"] == "hazard_definition"
    assert result["structured_result"]["requires_map_context_for_search"] is True
    assert "지명을 찾지 못했습니다" not in result["summary"]
    assert "위험객체" in result["summary"]


@pytest.mark.parametrize("value", [0, -1, True, float("nan"), float("inf"), "invalid"])
def test_invalid_explicit_radius_is_not_defaulted(value):
    with pytest.raises(radius.RadiusProblem):
        radius.parse_distance("위험객체", {"buffer_distance": value})


def test_conflicting_radius_is_not_silently_overwritten():
    with pytest.raises(radius.RadiusProblem, match="서로 다른 반경"):
        radius.parse_distance("반경 5km 위험객체", {"buffer_distance": 3000, "result_limit": 30})


def test_wreck_only_is_not_broadened_to_all_hazards(state):
    state["query"] = "부산항 입구 3km 이내 침선만 찾아줘"
    context, _, _, params = radius.prepare_radius_request(state)
    assert context.slots.target_features == ["Wreck"]
    assert params["feature_codes"] == [101]


@pytest.mark.parametrize(("query", "expected"), [
    ("Find wrecks within 3km of Busan Port Entrance", {"Wreck"}),
    ("Find obstructions within 3km of Busan Port Entrance", {"Obstruction"}),
    ("Find UnderwaterAwashRocks within 3km of Busan Port Entrance", {"UnderwaterAwashRock"}),
    ("Find hazards, wrecks only, within 3km of Busan Port Entrance", {"Wreck"}),
    ("Find hazards except wrecks within 3km of Busan Port Entrance", {"UnderwaterAwashRock", "Obstruction"}),
])
def test_plural_targets_preserve_requested_scope(state, query, expected):
    state["query"] = query
    context, _, _, params = radius.prepare_radius_request(state)

    expected = policy_targets() - {"Wreck"} if "except wrecks" in query.lower() else expected
    assert set(context.slots.target_features) == expected
    assert set(params["target_features"]) == expected
    assert set(params["target_features"]) == set(context.slots.target_features)
    assert all(isinstance(code, int) for code in params["feature_codes"])


@pytest.mark.parametrize("context", ["environmental_assessment", "grounding_risk", "", ["navigation_safety"]])
def test_unapproved_context_requests_confirmation_without_db(state, monkeypatch, context):
    state["spatial_context"]["context"] = context
    connect = Mock(side_effect=AssertionError("Unapproved context must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)

    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["error_code"] == "CONTEXT_CONFIRMATION"
    assert result["structured_result"]["count"] is None
    assert result["clarification_questions"]


@pytest.mark.parametrize("purpose", ["해상풍력", "입지 평가", "양식장 적지"])
def test_other_business_purpose_requires_explicit_context(state, purpose):
    state["query"] += " " + purpose

    assert radius.execute_radius_request(state)["error_code"] == "CONTEXT_CONFIRMATION"

    state["spatial_context"]["context"] = "navigation_safety"
    context, *_ = radius.prepare_radius_request(state)
    assert context.slots.context == "navigation_safety"


@pytest.mark.parametrize("targets", [[], "Wreck", ["BuoyIsolatedDanger"], ["Wreck", "UnapprovedFeature"]])
def test_unapproved_targets_never_fall_back_to_default_hazards(state, monkeypatch, targets):
    state["spatial_context"]["target_features"] = targets
    connect = Mock(side_effect=AssertionError("Unapproved target must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)

    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["error_code"] == "UNSUPPORTED_TARGET"
    assert result["structured_result"]["returned_count"] == 0
    assert not result["map_layers"]


@pytest.mark.parametrize("target", ["lighthouses", "shipwreckage", "등대"])
def test_unrecognized_target_words_are_not_defaulted(state, target):
    state["query"] = f"Find {target} within 3km of Busan Port Entrance"

    result = radius.execute_radius_request(state)

    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["error_code"] == "UNSUPPORTED_TARGET"


def test_exclusions_survive_default_hazard_expansion(state):
    state["query"] = "부산항 입구 3km 이내 침선을 제외하고 위험객체를 찾아줘"
    context, _, _, params = radius.prepare_radius_request(state)
    assert set(context.slots.target_features) == policy_targets() - {"Wreck"}
    assert "Wreck" in context.slots.exclusions
    assert 101 not in params["feature_codes"]


def test_candidate_ontology_features_are_not_execution_targets(state, registries):
    concept = registries["derived_concept_registry_v2.yaml"]["derived_concepts"][radius.CONCEPT]
    concept["target_features"].append("UnapprovedFeature")
    context, *_ = radius.prepare_radius_request(state)
    assert set(context.slots.target_features) == policy_targets()


@pytest.mark.parametrize(("registry", "field", "value", "code"), [
    ("spatial_layer_registry.yaml", "execution_status", "metadata_only", "LAYER_NOT_EXECUTABLE"),
    ("query_template_registry.yaml", "allowed_layers", [], "TEMPLATE_MISMATCH"),
    ("query_template_registry.yaml", "executor", "unknown.tool", "TEMPLATE_MISMATCH"),
])
def test_unready_registry_is_blocked_without_data_query(state, registries, monkeypatch, registry, field, value, code):
    if registry.startswith("spatial"):
        registries[registry]["layers"]["GBENC_S101_feature"][field] = value
    else:
        registries[registry]["templates"]["feature_search_by_radius"][field] = value
    connect = Mock(side_effect=AssertionError("Registry is not executable"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)
    result = radius.execute_radius_request(state)
    connect.assert_not_called()
    assert result["error_code"] == code


def test_denied_user_never_queries_db(state, monkeypatch):
    state["user_id"] = "blocked_user"
    connect = Mock(side_effect=AssertionError("User is denied"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)
    assert radius.execute_radius_request(state)["status"] == "BLOCKED"
    connect.assert_not_called()


def _fixture_result(state, total=119):
    context, layer, _, params = radius.prepare_radius_request(state)
    context.readiness = PlanStatus.EXECUTION_READY
    context.data_bindings = [DataBinding(dataset_id="GBENC_S101_feature", relation=layer["physical_table"], srid=4326)]
    rows = [{"id": number, "source_dataset_id": 1, "dataset_version_id": 2, "feature_type_code": 101,
             "feature_type_name": "Wreck", "geometry": {"type": "Point", "coordinates": [129.075, 35.075]}, "distance_m": float(number)}
            for number in range(params["offset"] + 1, min(total, params["offset"] + params["result_limit"]) + 1)]
    return context, layer, params, total, {"Wreck": total} if total else {}, rows, None


@pytest.mark.parametrize("total", [0, 1, 30, 119])
def test_one_result_drives_every_surface_and_distinguishes_total(state, total):
    fixture = _fixture_result(state, total)
    context, layer = fixture[0], fixture[1]
    result = radius.build_result(*fixture)
    structured = result["structured_result"]
    bundle = EvidenceBundle.model_validate(result["evidence_bundle"])
    context = QueryExecutionContext.model_validate(result["orchestrator_v2"]["query_execution_context"])
    ids = structured["feature_ids"]

    assert structured["total_count"] == total
    assert structured["returned_count"] == min(total, 30)
    assert structured["nearest_returned_count"] == structured["returned_count"]
    assert structured["result_surface"]["total_hazard_count"] == total
    assert structured["result_surface"]["nearest_returned_count"] == structured["returned_count"]
    assert structured["result_surface"]["source_layer"]["physical_table"] == layer["physical_table"]
    assert structured["result_surface"]["reference_geometry"] == context.slots.reference_geometry
    assert structured["result_surface"]["geojson"]["feature_count"] == len(ids)
    assert structured["result_surface"]["evidence_bundle"]["spatial_feature_evidence"] == len(ids)
    assert structured["result_surface"]["web_rag_usage"]["web_used"] is False
    assert structured["result_surface"]["web_rag_usage"]["rag_used"] is False
    assert structured["status"] == ("SUCCESS" if total else "SUCCESS_EMPTY")
    assert ids == result["spatial_result_summary"]["feature_ids"]
    assert ids == [row["feature_instance_id"] for row in structured["features"]]
    assert ids == [feature["id"] for feature in result["map_layers"][0]["inline_geojson"]["features"]]
    assert ids == [item.data["feature_instance_id"] for item in bundle.spatial_feature_evidence]
    assert sum(structured["returned_counts_by_type"].values()) == len(ids)
    assert sum(structured["total_counts_by_type"].values()) == total
    assert context.slots.distance_m == 3000
    evidence_ids = {item.evidence_id for item in [*bundle.spatial_feature_evidence, *bundle.spatial_layer_evidence]}
    assert set(result["claims"][0]["evidence_ids"]) == evidence_ids


def test_out_of_range_result_is_rejected(state):
    values = list(_fixture_result(state, 1))
    values[5][0]["distance_m"] = 3001
    with pytest.raises(radius.RadiusProblem, match="거리 조건"):
        radius.build_result(*values)


def test_duplicate_feature_id_is_rejected(state):
    values = list(_fixture_result(state, 2))
    values[5][1]["id"] = values[5][0]["id"]
    with pytest.raises(radius.RadiusProblem, match="식별자"):
        radius.build_result(*values)


@pytest.mark.parametrize("geometry", [
    None,
    {},
    {"type": "Point", "coordinates": []},
    {"type": "Point", "coordinates": [129.075]},
    {"type": "Point", "coordinates": [float("nan"), 35.075]},
    {"type": "Polygon", "coordinates": [[[129, 35], [130, 36], [130, 35], [129, 36], [129, 35]]]},
    {"type": "UnknownGeometry", "coordinates": [129.075, 35.075]},
])
def test_malformed_result_geometry_cannot_enter_any_surface(state, geometry):
    values = list(_fixture_result(state, 1))
    values[5][0]["geometry"] = geometry

    with pytest.raises(radius.RadiusProblem) as problem:
        radius.build_result(*values)

    assert problem.value.status == "FAILED"
    assert problem.value.code == "RESULT_CONTRACT_MISMATCH"


@pytest.mark.parametrize(("total", "offset", "limit", "returned"), [
    (119, 90, 30, 29), (119, 119, 30, 0), (119, 150, 30, 0),
    (119, 5, 5, 5), (3, 2, 30, 1), (0, 0, 30, 0),
])
def test_last_and_empty_pages_have_exact_lengths(state, total, offset, limit, returned):
    state["spatial_context"].update(offset=offset, result_limit=limit)

    result = radius.build_result(*_fixture_result(state, total))

    assert result["structured_result"]["total_count"] == total
    assert result["structured_result"]["returned_count"] == returned
    assert result["structured_result"]["offset"] == offset
    assert len(result["structured_result"]["features"]) == returned
    assert len(result["evidence_bundle"]["spatial_feature_evidence"]) == returned
    assert result["map_layers"][0]["feature_count"] == returned


@pytest.mark.parametrize("truncate", [True, False])
def test_incomplete_or_overfilled_page_is_rejected(state, truncate):
    state["spatial_context"].update(offset=90, result_limit=30)
    values = list(_fixture_result(state, 119))
    if truncate:
        values[5].pop()
    else:
        extra = copy.deepcopy(values[5][-1])
        extra["id"] = 120
        values[5].append(extra)

    with pytest.raises(radius.RadiusProblem) as problem:
        radius.build_result(*values)

    assert problem.value.code == "RESULT_CONTRACT_MISMATCH"


@pytest.mark.parametrize("changed_identity", ["revision", "snapshot"])
def test_reexecution_does_not_reuse_result_or_evidence_identity(state, changed_identity):
    first_values = list(_fixture_result(state, 1))
    first_values[0].snapshot_versions = {"data_snapshot": "fixture-snapshot-1"}
    second_values = copy.deepcopy(first_values)
    if changed_identity == "revision":
        second_values[0].revision += 1
    else:
        second_values[0].snapshot_versions["data_snapshot"] = "fixture-snapshot-2"

    first = radius.build_result(*first_values)
    second = radius.build_result(*second_values)

    assert first["task_id"] == second["task_id"]
    assert first["structured_result"]["feature_ids"] == second["structured_result"]["feature_ids"]
    assert first["spatial_result_summary"]["result_id"] != second["spatial_result_summary"]["result_id"]
    assert first["spatial_result_summary"]["query_execution_id"] != second["spatial_result_summary"]["query_execution_id"]
    assert set(first["claims"][0]["evidence_ids"]).isdisjoint(second["claims"][0]["evidence_ids"])
    assert first["map_layers"][0]["layer_id"] != second["map_layers"][0]["layer_id"]


def test_requested_revision_survives_preparation_and_clarification(state, registries):
    registries["place_geometry_registry.yaml"]["places"]["busan_port_entrance"]["status"] = "curated"
    state["execution_revision"] = 7
    context, *_ = radius.prepare_radius_request(state)
    assert context.revision == 7

    state["spatial_context"].pop("geometry")
    result = radius.execute_radius_request(state)
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["orchestrator_v2"]["query_execution_context"]["revision"] == 7


def test_none_revision_from_graph_defaults_to_first_execution(state, registries):
    registries["place_geometry_registry.yaml"]["places"]["busan_port_entrance"]["status"] = "curated"
    state["execution_revision"] = None

    context, *_ = radius.prepare_radius_request(state)

    assert context.revision == 1

    state["spatial_context"].pop("geometry")
    result = radius.execute_radius_request(state)

    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["orchestrator_v2"]["query_execution_context"]["revision"] == 1


def test_location_clarification_preserves_only_safe_resubmission_context(state, registries, monkeypatch):
    registries["place_geometry_registry.yaml"]["places"]["busan_port_entrance"]["status"] = "curated"
    state["spatial_context"].pop("geometry")
    state["spatial_context"].update(
        target_features=["Wreck"], exclusions=["Obstruction"], result_limit=7, offset=14,
        context="navigation_safety", private_api_token="fixture-private-context-token",
        arbitrary_context={"internal_value": "fixture-private-metadata"},
    )
    connect = Mock(side_effect=AssertionError("Location clarification must not query DB"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)

    result = radius.execute_radius_request(state)

    connect.assert_not_called()
    assert result["status"] == "NEEDS_CLARIFICATION"
    assert result["error_code"] == "LOCATION_UNCONFIRMED"
    assert result["structured_result"]["spatial_context"] == {
        "base_location": "부산항 입구", "crs": "EPSG:4326", "buffer_distance": 3000,
        "target_features": ["Wreck"], "exclusions": ["Obstruction"], "result_limit": 7,
        "offset": 14, "context": "navigation_safety",
    }
    assert "fixture-private-context-token" not in str(result)
    assert "fixture-private-metadata" not in str(result)


def test_database_failure_is_not_reported_as_empty_success(state, monkeypatch):
    monkeypatch.setattr(radius, "_fetch_result", Mock(side_effect=radius.psycopg2.OperationalError("fixture outage")))
    result = radius.execute_radius_request(state)
    assert result["status"] == "FAILED"
    assert result["structured_result"]["count"] is None
    assert not result["map_layers"]


def test_incheon_boundary_point_is_in_conservative_envelope():
    xmin, ymin, xmax, ymax = radius.conservative_envelope(radius.wkt.loads("POINT(126.592 37.456)"), 3000)
    assert xmin <= 126.6257 <= xmax
    assert ymin <= 37.456 <= ymax


@pytest.mark.parametrize("point", ["POINT(179.999 0)", "POINT(-179.999 0)", "POINT(0 89.99)"])
def test_envelope_is_conservative_at_wrap_and_poles(point):
    xmin, ymin, xmax, ymax = radius.conservative_envelope(radius.wkt.loads(point), 50000)
    assert xmin == -180 and xmax == 180
    assert -90 <= ymin <= ymax <= 90


def policy_targets():
    return set(radius._registry("derived_concept_registry_v2.yaml")["derived_concepts"][radius.CONCEPT]["execution_profiles"][radius.PROFILE]["target_features"])
