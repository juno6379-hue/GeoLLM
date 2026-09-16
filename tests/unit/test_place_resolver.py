"""Dataset resolution fixtures: no network, external geocoder, or database writes."""

import copy
from unittest.mock import Mock

import pytest

from services.spatial_analysis_agent import place_resolver as resolver
from services.orchestrator import s101_radius_execution as radius


def candidate(identifier="island:fixture1", label="테스트항", geometry="POINT(127 35)", aliases=None):
    return resolver._candidate(identifier, label, aliases or ["Fixture Port"], geometry, [{"source_ref": "fixture.gazetteer", "source_id": identifier, "revision": "v1"}])


@pytest.fixture
def catalog(monkeypatch):
    data = {"candidates": [candidate()], "unavailable_sources": []}
    monkeypatch.setattr(resolver, "load_catalog", lambda **kwargs: copy.deepcopy(data))
    return data


@pytest.mark.parametrize("query", ["테스트항 3km 이내 위험객체", "테스트항에서 3km 이내 위험객체", "Find hazards within 3km of Fixture Port", "Fixture Port 위치"])
def test_named_query_returns_source_identity(query, catalog):
    geometry, label, crs, resolution = resolver.resolve_location(query, places={})
    assert geometry == "POINT(127 35)"
    assert label == "테스트항" and crs == "EPSG:4326"
    assert resolution["status"] == "RESOLVED_GAZETTEER"
    assert resolution["place_id"] == "island:fixture1"
    assert len(resolution["place_version"]) == 64
    assert resolution["source_records"][0]["revision"] == "v1"


def test_duplicate_rows_share_a_candidate_but_keep_all_sources():
    items = [candidate(), candidate("khoa:fixture2", geometry="POINT(127.00000001 35)")]
    grouped = resolver._deduplicate(items)
    assert len(grouped) == 1
    assert len(grouped[0]["source_records"]) == 2
    assert grouped[0]["place_version"] != items[0]["place_version"]


def test_matching_does_not_compile_patterns_for_the_whole_catalog(monkeypatch):
    original = resolver.re.finditer
    matcher = Mock(wraps=original)
    monkeypatch.setattr(resolver.re, "finditer", matcher)
    unrelated = [{"place_id": str(i), "aliases": [f"UnrelatedPlace{i}"]} for i in range(2000)]
    assert resolver._matches("테스트항 3km", [*unrelated, candidate()])[0]["place_id"] == "island:fixture1"
    assert matcher.call_count == 1


def test_same_name_different_points_never_uses_first_row(catalog):
    catalog["candidates"].append(candidate("island:fixture2", geometry="POINT(128 35)"))
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location("테스트항", places={})
    assert len(exc.value.candidates) == 2
    assert all(item["requires_confirmation"] for item in exc.value.candidates)


def test_unknown_explicit_name_does_not_use_a_different_query_name(catalog):
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location("테스트항 3km", {"base_location": "Unknown Port"}, places={})
    assert exc.value.candidates == []


@pytest.mark.parametrize("query", ["다른항 3km", "테스트항과 다른항 주변 3km"])
def test_conflicting_or_multiple_dataset_names_are_not_reduced_to_one(catalog, query):
    catalog["candidates"].append(candidate("khoa:other", "다른항", "POINT(128 35)", ["Other Port"]))
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location(query, {"base_location": "테스트항"}, places={})
    assert exc.value.code == "CONFLICTING_LOCATION"
    assert len(exc.value.candidates) == 2


@pytest.mark.parametrize("changed", ["place_version", "place_id", "geometry"])
def test_stale_or_forged_selection_does_not_execute(catalog, changed):
    selected = dict(catalog["candidates"][0])
    selected[changed] = "POINT(128 35)" if changed == "geometry" else "stale"
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location("테스트항", selected, places={})
    assert exc.value.code in {"STALE_PLACE_SELECTION", "CONFLICTING_LOCATION"}


def test_selection_revalidates_fresh_sources_and_ignores_client_provenance(monkeypatch):
    item = candidate()
    load = Mock(return_value={"candidates": [item], "unavailable_sources": []})
    monkeypatch.setattr(resolver, "load_catalog", load)
    _, _, _, resolution = resolver.resolve_location("테스트항", {**item, "source_records": [{"source_ref": "forged"}], "location_resolution": {"status": "approved"}}, places={})
    load.assert_called_once_with(refresh=True)
    assert resolution["source_records"] == item["source_records"]
    assert resolution["status"] == "CONFIRMED_SELECTION"


@pytest.mark.parametrize("geometry", ["POINT EMPTY", "POINT(127 91)", "POINT Z(127 35 1)", "LINESTRING(127 35, 128 36)"])
def test_manual_point_validation_without_catalog_lookup(monkeypatch, geometry):
    load = Mock(side_effect=AssertionError("Invalid explicit reference must not query a source"))
    monkeypatch.setattr(resolver, "load_catalog", load)
    with pytest.raises(resolver.PlaceResolutionProblem):
        resolver.resolve_location("위험객체", {"geometry": geometry, "crs": "EPSG:4326"}, places={})
    load.assert_not_called()


def test_missing_source_is_not_an_empty_success(catalog):
    catalog["unavailable_sources"] = ["fixture.offline"]
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location("테스트항", places={})
    assert exc.value.code == "GAZETTEER_UNAVAILABLE"


def test_radius_contract_contains_dataset_reference_and_version(catalog):
    context, _, _, params = radius.prepare_radius_request({"task_id": "gazetteer-fixture", "query": "테스트항 3km 이내 위험객체"})
    assert context.provenance["location_resolution"]["place_id"] == "island:fixture1"
    assert params["base_wkt"] == "POINT (127 35)"
    assert params["distance_m"] == 3000


def test_geocoding_tool_uses_same_catalog_and_preserves_qualifier(catalog):
    from services.spatial_analysis_agent.geocoding_tool import get_maritime_coordinates

    assert get_maritime_coordinates.invoke("Fixture Port") == "POINT(127 35)"
    assert get_maritime_coordinates.invoke("테스트항 입구").startswith("ERROR: LOCATION_UNCONFIRMED")


def test_invalid_source_row_cannot_hide_ambiguity(monkeypatch):
    monkeypatch.setenv("S101_DB_URL", "fixture-no-connection")
    monkeypatch.setenv("POSTGIS_URL", "fixture-no-connection")
    monkeypatch.setattr(resolver, "_cache", None)
    rows = [{"id": "1", "name": "테스트항", "wkt": "POINT(127 35)", "srid": 4326}, {"id": "2", "name": "테스트항", "wkt": "POINT EMPTY", "srid": 4326}]
    monkeypatch.setattr(resolver, "_read_source", lambda *args: rows)
    loaded = resolver.load_catalog(refresh=True)
    assert loaded["unavailable_sources"]
    with pytest.raises(resolver.PlaceResolutionProblem) as exc:
        resolver.resolve_location("테스트항", places={}, catalog=loaded)
    assert exc.value.code == "GAZETTEER_UNAVAILABLE"
