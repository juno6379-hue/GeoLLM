from services.orchestrator.graph import _sanitize_graph_context_for_execution
from services.orchestrator.query_candidate_broker import execution_contract_ready, query_candidate_broker
from services.orchestrator.route_planner import RoutePlanner


def test_graph_rag_recall_candidates_do_not_become_resolved_slots():
    raw_context = {
        "target_features": ["Obstruction", "SideThruster"],
        "target_layers": ["GBENC_S101_feature"],
        "target_dynamic_layers": ["ais_monthly_grid"],
        "derived_concepts": ["temporary storage", "accident_event"],
        "candidate_tools": ["gbenc.s101_feature_search_by_radius"],
        "execution_hints": {"requires_spatial_analysis": True},
    }

    context = _sanitize_graph_context_for_execution(
        raw_context,
        "독도 부근 사고 이력",
        {"target_features": ["사고"], "derived_concepts": ["accident_event"]},
    )

    assert context["target_features"] == []
    assert context["target_layers"] == []
    assert context["target_dynamic_layers"] == []
    assert context["derived_concepts"] == ["accident_event"]
    assert context["candidate_target_features"] == ["Obstruction", "SideThruster"]
    assert context["candidate_derived_concepts"] == ["temporary storage", "accident_event"]
    assert context["execution_hints"]["requires_spatial_analysis"] is False


def test_route_planner_does_not_merge_unverified_graph_candidates():
    planner = RoutePlanner()

    plan = planner.generate_plan(
        normalized_query="독도 부근 사고 이력",
        slots={"location_text": "독도", "target_term": "사고", "distance_m": 10000},
        derived_concept="accident_event",
        context="incident_response",
        analysis_type="accident_spatial_history_lookup",
        intent="ACCIDENT_ANALYSIS",
        graph_context={
            "target_features": ["Obstruction"],
            "candidate_tools": ["gbenc.s101_feature_search_by_radius"],
            "candidate_query_templates": ["feature_search_by_radius"],
        },
        data_discovery_result={},
    )

    assert "gbenc.s101_feature_search_by_radius" not in plan["required_tools"]
    assert plan["candidate_query_templates"] == ["feature_search_by_radius"]


def test_broker_readiness_is_limited_to_selected_execution_route(monkeypatch):
    monkeypatch.setenv("GEOLLM_CAPABILITY_PGVECTOR", "false")

    trace = query_candidate_broker.build_trace("독도 부근 사고 이력")

    assert trace["execution_contract"]["execution_route"] == "ACCIDENT_ANALYSIS"
    assert execution_contract_ready(
        trace,
        route="ACCIDENT_ANALYSIS",
        capability_id="tool.accident_spatial_history_lookup",
    )
    assert not execution_contract_ready(
        trace,
        route="SPATIAL_ANALYSIS",
        capability_id="tool.spatial_radius_search",
    )
