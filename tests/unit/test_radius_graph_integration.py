"""Exercise the compiled graph with explicit fixtures and no database or LLM calls."""

import asyncio
from unittest.mock import Mock
from uuid import uuid4

import pytest
import requests

from services.orchestrator import s101_radius_execution as radius
from shared.schemas.agent import AgentStatus, DataBinding, EvidenceBundle, PlanStatus, QueryExecutionContext


BASE_QUERY = "\ubd80\uc0b0\ud56d \uc785\uad6c 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4\ub97c \ucc3e\uc544\uc918"
CONFIRMED_LOCATION = {
    "base_location": "\ubd80\uc0b0\ud56d \uc785\uad6c", "geometry": "POINT(129.075 35.075)",
    "crs": "EPSG:4326", "buffer_distance": 3000,
}


@pytest.fixture
def graph_module(monkeypatch):
    monkeypatch.setenv("DISABLE_LLM_API", "true")
    connect = Mock(side_effect=AssertionError("Graph integration fixtures must not open a database"))
    http_request = Mock(side_effect=AssertionError("Graph integration fixtures must not make HTTP requests"))
    monkeypatch.setattr(radius.psycopg2, "connect", connect)
    monkeypatch.setattr(requests.sessions.Session, "request", http_request)
    from services.orchestrator import graph

    http_request.reset_mock()
    monkeypatch.setattr(graph.cache, "check_cache", Mock(side_effect=AssertionError("Deterministic radius route must not call semantic cache")))
    monkeypatch.setattr(graph.router, "route_query", Mock(side_effect=AssertionError("Deterministic radius route must not call embeddings")))
    monkeypatch.setattr(graph, "ChatOpenAI", Mock(side_effect=AssertionError("Graph integration fixtures must not invoke an LLM")))
    yield graph
    connect.assert_not_called()
    http_request.assert_not_called()


def invoke_graph(graph, **overrides):
    task_id = "radius-graph-fixture-" + str(uuid4())
    state = {
        "task_id": task_id, "query": BASE_QUERY, "user_id": "fixture-user",
        "organization_id": "fixture-org", "status": AgentStatus.RECEIVED,
        "state_history": [], **overrides,
    }
    return asyncio.run(graph.build_orchestrator_graph().ainvoke(
        state, config={"configurable": {"thread_id": task_id}},
    ))


@pytest.mark.parametrize("revision_patch", [{}, {"execution_revision": None}])
def test_compiled_graph_returns_typed_location_clarification(graph_module, revision_patch):
    result = invoke_graph(graph_module, **revision_patch)

    assert result["status"] == AgentStatus.NEEDS_CLARIFICATION
    assert isinstance(result["status"], AgentStatus)
    final = result["final_dict"]
    assert final["status"] == "NEEDS_CLARIFICATION"
    assert final["error_code"] == "LOCATION_UNCONFIRMED"
    assert final["structured_result"]["count"] is None
    assert final["structured_result"]["distance_m"] == 3000
    assert final["clarification_questions"]
    assert final["clarification_options"][0]["requires_confirmation"] is True
    context = QueryExecutionContext.model_validate(result["query_execution_context"])
    assert context.revision == 1
    assert context.readiness == PlanStatus.NEEDS_USER_INPUT
    assert context.route_plan["execution_ready"] is False
    assert result["state_history"][-1]["actor"] == "ValidatedS101HazardRadius"


def test_compiled_graph_preserves_confirmed_fixture_across_result_surfaces(graph_module, monkeypatch):
    def fetch_fixture(context, layer, template, params):
        assert params["distance_m"] == 3000
        assert params["base_wkt"] == "POINT (129.075 35.075)"
        context.readiness = PlanStatus.EXECUTION_READY
        context.route_plan.update(execution_ready=True, status="EXECUTION_READY", route_plan_status="EXECUTION_READY")
        context.data_bindings = [DataBinding(
            dataset_id="GBENC_S101_feature", relation=layer["physical_table"],
            geometry_column=layer["geometry_column"], srid=4326,
        )]
        context.snapshot_versions = {"data_snapshot": "explicit-fixture-snapshot"}
        return 2, {"Wreck": 2}, [
            {"id": number, "source_dataset_id": "fixture-dataset", "dataset_version_id": "fixture-version",
             "feature_type_code": 101, "feature_type_name": "Wreck", "distance_m": float(number),
             "geometry": {"type": "Point", "coordinates": [129.075, 35.075]}}
            for number in (1, 2)
        ], None

    fetch = Mock(side_effect=fetch_fixture)
    monkeypatch.setattr(radius, "_fetch_result", fetch)

    result = invoke_graph(graph_module, spatial_context=CONFIRMED_LOCATION, execution_revision=None)

    fetch.assert_called_once()
    assert result["status"] == AgentStatus.COMPLETED
    final = result["final_dict"]
    structured = final["structured_result"]
    assert structured["status"] == "SUCCESS"
    assert structured["total_count"] == structured["returned_count"] == 2
    assert structured["feature_ids"] == ["1", "2"]
    assert final["spatial_result_summary"]["feature_ids"] == ["1", "2"]
    assert [feature["id"] for feature in final["map_layers"][0]["inline_geojson"]["features"]] == ["1", "2"]
    bundle = EvidenceBundle.model_validate(final["evidence_bundle"])
    assert [item.data["feature_instance_id"] for item in bundle.spatial_feature_evidence] == ["1", "2"]
    context = QueryExecutionContext.model_validate(result["query_execution_context"])
    assert context.readiness == PlanStatus.EXECUTION_READY
    assert context.revision == 1
    assert context.provenance["location_resolution"]["status"] == "CONFIRMED_INPUT"
    assert result["state_history"][-1]["actor"] == "ValidatedS101HazardRadius"


@pytest.mark.parametrize("query", [
    "Find the nearest Wreck to Busan Port Entrance",
    "\ubd80\uc0b0\ud56d \uc785\uad6c\uc5d0\uc11c \uac00\uc7a5 \uac00\uae4c\uc6b4 \uce68\uc120\uc744 \ucc3e\uc544\uc918",
])
def test_nearest_wreck_without_radius_does_not_enter_radius_route(graph_module, monkeypatch, query):
    state = {
        "query": query, "status": AgentStatus.INTENT_PARSED,
        "spatial_context": {key: value for key, value in CONFIRMED_LOCATION.items() if key != "buffer_distance"},
    }
    monkeypatch.setattr(graph_module, "_s101_nearest_feature_config", lambda targets: {"feature_codes": [101]})

    assert graph_module._should_fast_execute_s101_hazard_radius(state) is False
    assert graph_module.check_intent_parsed(state) != "fast_s101_hazard_radius_execute"


def test_hazard_definition_question_does_not_enter_spatial_or_place_route(graph_module):
    state = {
        "query": "위험객체란",
        "status": AgentStatus.INTENT_PARSED,
        "spatial_context": {},
    }

    assert graph_module._looks_like_standard_rag_query("위험객체란")
    assert graph_module._looks_like_definition_question("위험객체란")
    assert graph_module._should_fast_execute_s101_hazard_radius(state) is False
    assert graph_module.check_intent_parsed(state) == "create_plan"
