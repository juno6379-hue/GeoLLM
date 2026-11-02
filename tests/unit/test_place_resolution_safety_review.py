"""Location semantics regressions using only synthetic, in-memory sources."""

import pytest

from services.spatial_analysis_agent.place_resolver import (
    PlaceResolutionProblem,
    _candidate,
    resolve_location,
)


def candidate(identifier, label, geometry="POINT(129 35)"):
    return _candidate(identifier, label, [], geometry, [{"source_ref": "fixture", "source_id": identifier}])


def catalog(*candidates, unavailable=()):
    return {"candidates": list(candidates), "unavailable_sources": list(unavailable)}


@pytest.mark.parametrize("spatial", [{}, {"base_location": "Port Alpha"}])
def test_parent_dataset_name_does_not_resolve_entrance(spatial):
    point = candidate("island:1", "Port Alpha")
    with pytest.raises(PlaceResolutionProblem) as error:
        resolve_location("Port Alpha entrance within 3km", spatial, places={}, catalog=catalog(point))
    assert error.value.code == "LOCATION_UNCONFIRMED"
    assert [item["place_id"] for item in error.value.candidates] == [point["place_id"]]


@pytest.mark.parametrize("spatial", [{}, {"base_location": "Port Alpha"}])
def test_approved_registry_parent_does_not_resolve_entrance(spatial):
    places = {"port-alpha": {"canonical_name": "Port Alpha", "geometry_wkt": "POINT(129 35)", "srid": 4326, "status": "approved"}}
    with pytest.raises(PlaceResolutionProblem) as error:
        resolve_location("Port Alpha entrance within 3km", spatial, places=places, catalog=catalog())
    assert error.value.code == "LOCATION_UNCONFIRMED"


def test_approved_registry_explicit_entrance_name_remains_resolvable():
    places = {"port-alpha": {"canonical_name": "Port Alpha entrance", "geometry_wkt": "POINT(129 35)", "srid": 4326, "status": "approved"}}
    geometry, _, _, resolution = resolve_location("Port Alpha entrance within 3km", places=places, catalog=catalog())
    assert geometry == "POINT(129 35)"
    assert resolution["status"] == "APPROVED_REGISTRY"


@pytest.mark.parametrize("conjunction", ["\uacfc", "\uc640", "\ub791", "\ud558\uace0"])
def test_compound_place_names_remain_ambiguous(conjunction):
    first = candidate("island:1", "\uac00\ud56d")
    second = candidate("khoa:2", "\ub098\ud56d", "POINT(128 35)")
    with pytest.raises(PlaceResolutionProblem) as error:
        resolve_location(f"{first['label']}{conjunction} {second['label']} \uc0ac\uc774 3km", places={}, catalog=catalog(first, second))
    assert error.value.code == "LOCATION_UNCONFIRMED"
    assert {item["place_id"] for item in error.value.candidates} == {first["place_id"], second["place_id"]}


def test_partial_catalog_preserves_healthy_source_and_discloses_incomplete_coverage():
    point = candidate("island:1", "Port Alpha")
    geometry, _, _, resolution = resolve_location("Port Alpha within 3km", places={}, catalog=catalog(point, unavailable=["public.maritime_gazetteer_khoa"]))
    assert geometry == point['geometry']
    assert resolution['coverage_complete'] is False
    assert resolution['unavailable_sources'] == ['public.maritime_gazetteer_khoa']


def test_fresh_verified_selection_does_not_need_unrelated_source():
    point = candidate("island:1", "Port Alpha entrance")
    geometry, _, _, resolution = resolve_location(
        "Port Alpha entrance within 3km",
        {"place_id": point["place_id"], "place_version": point["place_version"], "geometry": point["geometry"], "crs": point["crs"]},
        places={}, catalog=catalog(point, unavailable=["public.maritime_gazetteer_khoa"]),
    )
    assert geometry == point["geometry"]
    assert resolution["status"] == "CONFIRMED_SELECTION"
