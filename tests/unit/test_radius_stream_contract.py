"""Exercise the public stream serializers without starting the graph or a database."""

import ast
from copy import deepcopy
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def serializers():
    path = Path(__file__).resolve().parents[2] / "services/orchestrator/router.py"
    names = {
        "_to_jsonable", "_compact_agent_result_for_stream", "_compact_final_result_for_stream",
        "_preserve_spatial_stream_payload", "_terminal_result_for_stream",
        "_is_radius_state", "_is_place_clarification_state", "_radius_restart_state",
    }
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    module = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
    namespace = {"os": os, "AgentStatus": SimpleNamespace(RECEIVED="RECEIVED")}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


def radius_result(returned=30):
    rows = [
        {
            "feature_instance_id": str(i), "dataset_id": "test-s101", "result_id": "result-1",
            "evidence_id": f"feature:{i}", "feature_name": "Wreck", "distance_m": i + 0.5,
        }
        for i in range(returned)
    ]
    geojson = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [129.075, 35.075]}, "properties": row} for row in rows],
    }
    return {
        "task_id": "task-1", "status": "COMPLETED", "summary": "119 matches, nearest 30 returned",
        "structured_result": {
            "analysis_type": "feature_search_by_radius", "count": 119, "total_count": 119,
            "returned_count": returned, "result_limit": returned, "truncated": True,
            "feature_ids": [row["feature_instance_id"] for row in rows], "features": rows,
            "geojson": geojson, "result_id": "result-1", "query_execution_id": "execution-1",
            "returned_counts_by_type": {"Wreck": returned}, "total_counts_by_type": {"Wreck": 119},
            "location_text": "Confirmed place", "distance_m": 3000, "original_query": "Wreck within 3km",
            "distance_policy": {"default_applied": True, "summary": "부근 기본 반경 3km를 적용했습니다."},
            "user_evidence_summary": {"distance_basis": "부근 기본 반경 3km를 적용했습니다.", "data_basis": "S-101 전자해도 공간 레이어를 조회했습니다."},
            "offset": 30, "target_features": ["Wreck"], "exclusions": ["Obstruction"], "crs": "EPSG:4326",
            "place_id": "dataset-a:place-1", "place_version": "version-1",
            "spatial_context": {"target_features": ["Wreck"], "exclusions": ["Obstruction"], "result_limit": returned},
            "location_resolution": {"place_id": "dataset-a:place-1", "place_version": "version-1", "source_records": [{"source_ref": "dataset-a", "record_id": "place-1"}]},
        },
        "map_layers": [{"role": "matched_features", "inline_geojson": geojson}],
        "evidence_bundle": {
            "spatial_feature_evidence": [{"evidence_id": row["evidence_id"], "evidence_type": "spatial_feature", "source_ref": "test.s101", "data": row} for row in rows],
        },
        "spatial_result_summary": {"result_id": "result-1", "query_execution_id": "execution-1", "total_count": 119, "returned_count": returned},
    }


@pytest.mark.parametrize("returned", [0, 30, 100])
@pytest.mark.parametrize("serializer", ["_compact_agent_result_for_stream", "_compact_final_result_for_stream"])
def test_stream_keeps_every_spatial_surface_and_identity(serializers, serializer, returned):
    result = radius_result(returned)
    original = deepcopy(result)

    compact = serializers[serializer](result)

    assert compact["structured_result"] == result["structured_result"] | {
        "retrieved_count": None, "documents": [], "citations": [], "requires_external_api": None,
        "api_params": None, "external_data_requirement": None, "status": None, "evidence_candidate_summary": None,
    }
    for field in ("map_layers", "evidence_bundle", "spatial_result_summary"):
        assert compact[field] == result[field]
    assert compact["structured_result"]["distance_policy"] == result["structured_result"]["distance_policy"]
    assert compact["structured_result"]["user_evidence_summary"] == result["structured_result"]["user_evidence_summary"]
    ids = compact["structured_result"]["feature_ids"]
    assert ids == [item["properties"]["feature_instance_id"] for item in compact["map_layers"][0]["inline_geojson"]["features"]]
    assert ids == [item["data"]["feature_instance_id"] for item in compact["evidence_bundle"]["spatial_feature_evidence"]]
    assert result == original


@pytest.mark.parametrize("status", ["NEEDS_CLARIFICATION", "BLOCKED", "FAILED", "COMPLETED"])
def test_terminal_events_preserve_radius_result_for_every_status(serializers, monkeypatch, status):
    monkeypatch.delenv("GEOLLM_STREAM_FULL_RESULT", raising=False)
    result = radius_result(0)
    result.update(status=status, clarification_questions=["Which entrance?"], clarification_options=[{"label": "Candidate", "value": "candidate-1"}])
    candidate = {
        "place_id": "candidate-1", "label": "Candidate", "base_location": "Port entrance",
        "geometry": "POINT(129.075 35.075)", "crs": "EPSG:4326", "status": "test",
        "source_ref": "fixture", "requires_confirmation": True,
        "place_version": "version-1", "source_records": [{"source_ref": "dataset-a", "record_id": "place-1", "source_revision": "2026-09"}],
    }
    result["structured_result"]["location_candidates"] = [candidate]

    payload = serializers["_terminal_result_for_stream"]({"status": status, "final_dict": result})

    assert payload["final_result"]["status"] == status
    assert payload["final_result"]["structured_result"]["location_candidates"] == [candidate]
    assert payload["final_result"]["structured_result"]["original_query"] == "Wreck within 3km"
    assert payload["clarification_questions"] == result["clarification_questions"]
    assert payload["clarification_options"] == result["clarification_options"]


def test_failed_stream_without_final_dict_retains_error(serializers):
    assert serializers["_terminal_result_for_stream"]({"status": "FAILED", "error_message": "Connection failed"}) == {"error_message": "Connection failed"}


def test_nonspatial_compaction_keeps_document_limit(serializers):
    result = {"structured_result": {"documents": [{"id": i} for i in range(8)]}}
    compact = serializers["_compact_final_result_for_stream"](result)
    assert len(compact["structured_result"]["documents"]) == 3
    assert "map_layers" not in compact


@pytest.mark.parametrize("analysis_type", ["place_lookup", "nearest_feature"])
@pytest.mark.parametrize("serializer", ["_compact_agent_result_for_stream", "_compact_final_result_for_stream"])
@pytest.mark.parametrize("analysis_source", ["structured", "route"])
def test_completed_place_or_nearest_stream_preserves_source_identity_without_candidates(serializers, analysis_type, serializer, analysis_source):
    result = radius_result(1 if analysis_type == "place_lookup" else 30)
    structured = result["structured_result"]
    structured["analysis_type"] = analysis_type
    structured["geometry"] = "POINT(129.075 35.075)"
    result["orchestrator_v2"] = {"route_plan": {"analysis_type": analysis_type}}
    if analysis_source == "route":
        structured.pop("analysis_type")
    assert "location_candidates" not in structured
    compact = serializers[serializer](result)
    for key in ("geometry", "place_id", "place_version", "location_resolution", "geojson", "features", "returned_count"):
        assert compact["structured_result"][key] == structured[key]
    assert compact["map_layers"] == result["map_layers"]
    assert compact["evidence_bundle"] == result["evidence_bundle"]
    assert compact["spatial_result_summary"] == result["spatial_result_summary"]


@pytest.mark.parametrize("structured", [None, [], "invalid"])
def test_nonspatial_compaction_tolerates_unstructured_payload(serializers, structured):
    result = {"structured_result": structured, "orchestrator_v2": {"route_plan": "unstructured"}}
    assert serializers["_compact_final_result_for_stream"](result)["structured_result"]["documents"] == []


def test_radius_confirmation_restarts_same_task_with_fresh_context(serializers):
    state = {
        "task_id": "same-task", "query": "Wreck within 3km", "status": "NEEDS_CLARIFICATION",
        "spatial_context": {"map_bounds": [129, 35, 130, 36]},
        "query_execution_context": {"revision": 3, "route_plan": {"analysis_type": "feature_search_by_radius"}},
        "final_dict": {"stale": True}, "agent_result": {"stale": True}, "task_plan": {"stale": True},
        "agent_request": {"stale": True}, "context_result": {"stale": True}, "extracted_slots": {"distance_m": 99},
    }
    original = deepcopy(state)
    request = SimpleNamespace(query="Wreck within 3km", spatial_context={"base_location": "Confirmed entrance", "geometry": "POINT(129.075 35.075)", "crs": "EPSG:4326", "buffer_distance": 3000})

    assert serializers["_is_radius_state"](state)
    restarted = serializers["_radius_restart_state"](state, request)

    assert restarted["task_id"] == "same-task"
    assert restarted["query"] == request.query
    assert restarted["execution_revision"] == 4
    assert restarted["spatial_context"]["geometry"] == request.spatial_context["geometry"]
    assert restarted["spatial_context"]["map_bounds"] == original["spatial_context"]["map_bounds"]
    for key in ("final_dict", "agent_result", "agent_request", "task_plan", "query_execution_context", "context_result", "extracted_slots"):
        assert restarted[key] is None
    assert state == original


def test_changed_place_without_geometry_does_not_reuse_previous_center(serializers):
    state = {"query": "Wreck within 3km", "execution_revision": 4, "spatial_context": {"base_location": "Old entrance", "geometry": "POINT(129 35)", "crs": "EPSG:4326"}}
    request = SimpleNamespace(query="New entrance", spatial_context={"base_location": "New entrance"})

    restarted = serializers["_radius_restart_state"](state, request)

    assert restarted["query"] == "Wreck within 3km New entrance"
    assert restarted["execution_revision"] == 5
    assert "geometry" not in restarted["spatial_context"]
    assert "crs" not in restarted["spatial_context"]


def test_nonradius_state_does_not_enter_radius_restart(serializers):
    assert not serializers["_is_radius_state"]({"task_plan": {"analysis_type": "document_search"}})


def test_radius_stream_preserves_approved_context_policy_and_snapshot(serializers):
    result = radius_result()
    qec = {
        "readiness": "EXECUTION_READY", "revision": 2, "plan_hash": "hash-2",
        "slots": {"context": "navigation_safety", "target_features": ["Wreck"]},
        "semantic_resolution": {"target_policy": "approved.radius.policy"},
        "snapshot_versions": {"data_snapshot": "snapshot-2"},
        "route_plan": {"execution_ready": True},
        "provenance": {"location_resolution": {"status": "user_confirmed"}},
    }
    result["orchestrator_v2"] = {"query_execution_context": qec}

    compact = serializers["_compact_final_result_for_stream"](result)

    actual = compact["orchestrator_v2"]["query_execution_context"]
    for key, value in qec.items():
        assert actual[key] == value


@pytest.mark.parametrize("selection", [
    {"place_id": "dataset-b:place-2", "place_version": "version-2"},
    {"place_id": "dataset-a:place-1", "place_version": "version-2"},
])
def test_changed_gazetteer_selection_clears_previous_geometry_and_provenance(serializers, selection):
    state = {
        "query": "Wreck within 3km", "spatial_context": {
            "base_location": "Same label", "geometry": "POINT(129 35)", "crs": "EPSG:4326",
            "place_id": "dataset-a:place-1", "place_version": "version-1",
            "location_resolution": {"source_records": [{"source_ref": "old-source"}]},
            "target_features": ["Wreck"], "exclusions": ["Obstruction"], "result_limit": 17,
        },
    }
    request = SimpleNamespace(query=state["query"], spatial_context={"base_location": "Same label", **selection})

    spatial = serializers["_radius_restart_state"](state, request)["spatial_context"]

    assert spatial["place_id"] == selection["place_id"]
    assert spatial["place_version"] == selection["place_version"]
    assert "geometry" not in spatial
    assert "crs" not in spatial
    assert "location_resolution" not in spatial
    assert spatial["target_features"] == ["Wreck"]
    assert spatial["exclusions"] == ["Obstruction"]
    assert spatial["result_limit"] == 17


def test_same_task_manual_point_clears_old_gazetteer_selection_after_merge(serializers):
    state = {"query": "Wreck within 3km", "spatial_context": {
        "place_id": "dataset-a:place-1", "place_version": "version-1", "geometry": "POINT(129 35)",
        "location_resolution": {"source_ref": "old-source"}, "target_features": ["Wreck"], "result_limit": 17,
    }}
    request = SimpleNamespace(query=state["query"], spatial_context={
        "geometry": "POINT(126 37)", "crs": "EPSG:4326", "location_resolution": {"source_ref": "unverified-input"},
    })

    spatial = serializers["_radius_restart_state"](state, request)["spatial_context"]

    assert spatial["geometry"] == "POINT(126 37)"
    assert spatial["crs"] == "EPSG:4326"
    assert all(key not in spatial for key in ("place_id", "place_version", "location_resolution"))
    assert spatial["target_features"] == ["Wreck"]
    assert spatial["result_limit"] == 17


@pytest.mark.parametrize("analysis_type", ["place_lookup", "nearest_feature"])
@pytest.mark.parametrize("status", ["NEEDS_CLARIFICATION", "BLOCKED"])
def test_generic_location_confirmation_restarts_same_task_with_fresh_gates(serializers, analysis_type, status):
    state = {
        "task_id": "generic-task", "query": "Nearest Wreck to Island A", "status": status,
        "execution_revision": 2,
        "final_dict": {"status": status, "structured_result": {"analysis_type": analysis_type}},
        "spatial_context": {"place_id": "island:1", "place_version": "v1", "target_features": ["Wreck"], "exclusions": ["Obstruction"], "k": 4, "result_limit": 17},
        "query_execution_context": {"readiness": "EXECUTION_READY", "stale": True},
        "task_plan": {"stale": True}, "agent_result": {"stale": True}, "context_result": {"stale": True},
    }
    original = deepcopy(state)
    request = SimpleNamespace(query=state["query"], spatial_context={"place_id": "island:1", "place_version": "v1", "geometry": "POINT(129 35)", "crs": "EPSG:4326"})
    assert serializers["_is_place_clarification_state"](state)
    restarted = serializers["_radius_restart_state"](state, request)
    assert restarted["task_id"] == "generic-task"
    assert restarted["query"] == request.query
    assert restarted["execution_revision"] == 3
    assert restarted["status"] == "RECEIVED"
    assert restarted["spatial_context"]["place_id"] == "island:1"
    assert restarted["spatial_context"]["place_version"] == "v1"
    assert restarted["spatial_context"]["k"] == 4
    assert restarted["spatial_context"]["target_features"] == ["Wreck"]
    assert restarted["spatial_context"]["exclusions"] == ["Obstruction"]
    assert "buffer_distance" not in restarted["spatial_context"]
    for key in ("final_dict", "query_execution_context", "task_plan", "context_result", "agent_result"):
        assert restarted[key] is None
    assert state == original


@pytest.mark.parametrize("analysis_type,status", [("place_lookup", "PROCESSING"), ("nearest_feature", "PROCESSING"), ("document_search", "NEEDS_CLARIFICATION"), ("document_search", "BLOCKED")])
def test_generic_restart_guard_does_not_expand_to_running_or_unrelated_tasks(serializers, analysis_type, status):
    state = {"final_dict": {"status": status, "structured_result": {"analysis_type": analysis_type}}}
    assert not serializers["_is_place_clarification_state"](state)


@pytest.mark.parametrize("supplied", [{}, {"buffer_distance": 1000}])
def test_new_generic_query_does_not_inherit_previous_radius(serializers, supplied):
    state = {
        "query": "Find hazards within 3km", "spatial_context": {"buffer_distance": 3000, "target_features": ["Wreck"], "k": 4},
        "final_dict": {"status": "NEEDS_CLARIFICATION", "structured_result": {"analysis_type": "nearest_feature"}},
    }
    request = SimpleNamespace(query="Nearest Wreck to Island B", spatial_context=supplied)
    restarted = serializers["_radius_restart_state"](state, request)
    assert restarted["query"] == request.query
    assert restarted["spatial_context"].get("buffer_distance") == supplied.get("buffer_distance")
    assert restarted["spatial_context"]["target_features"] == ["Wreck"]
    assert restarted["spatial_context"]["k"] == 4


@pytest.mark.parametrize("analysis_type", ["place_lookup", "nearest_feature"])
@pytest.mark.parametrize("selection", [
    {"place_id": "island:1", "place_version": "stale-version"},
    {"geometry": "POINT(126 37)", "crs": "EPSG:4326"},
])
def test_completed_place_request_rechecks_changed_selection_or_manual_point(serializers, analysis_type, selection):
    state = {
        "task_id": "completed-place-task", "query": "Nearest Wreck to Island A", "status": "COMPLETED", "execution_revision": 3,
        "final_dict": {"status": "COMPLETED", "structured_result": {"analysis_type": analysis_type, "place_id": "island:1", "place_version": "current-version"}},
        "spatial_context": {
            "place_id": "island:1", "place_version": "current-version", "geometry": "POINT(129 35)", "crs": "EPSG:4326",
            "location_resolution": {"status": "CONFIRMED_SELECTION", "source_ref": "old-source"},
            "target_features": ["Wreck"], "exclusions": ["Obstruction"], "k": 4,
        },
        "query_execution_context": {"readiness": "EXECUTION_READY", "provenance": {"location_resolution": {"status": "CONFIRMED_SELECTION"}}},
        "task_plan": {"execution_ready": True}, "agent_result": {"status": "COMPLETED"}, "context_result": {"geometry": "POINT(129 35)"},
    }
    original = deepcopy(state)
    assert serializers["_is_place_clarification_state"](state)
    request = SimpleNamespace(query=state["query"], spatial_context=selection)
    restarted = serializers["_radius_restart_state"](state, request)
    assert restarted["task_id"] == state["task_id"]
    assert restarted["execution_revision"] == 4
    assert restarted["status"] == "RECEIVED"
    assert restarted["query"] == request.query
    spatial = restarted["spatial_context"]
    assert spatial["target_features"] == ["Wreck"]
    assert spatial["exclusions"] == ["Obstruction"]
    assert spatial["k"] == 4
    assert "location_resolution" not in spatial
    if "place_id" in selection:
        assert spatial["place_id"] == "island:1"
        assert spatial["place_version"] == "stale-version"
        assert "geometry" not in spatial
        assert "crs" not in spatial
    else:
        assert spatial["geometry"] == "POINT(126 37)"
        assert spatial["crs"] == "EPSG:4326"
        assert "place_id" not in spatial
        assert "place_version" not in spatial
    for key in ("final_dict", "query_execution_context", "task_plan", "agent_result", "context_result"):
        assert restarted[key] is None
    assert state == original
