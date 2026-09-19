"""Multi-intent planning and validation contract for the U-Port domain."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.uport.planning import UportPlanRequest, _ordered_steps, plan_query
from services.uport.planning_router import router
from shared.schemas.agent import PlanStatus


def test_compound_query_expands_registry_dependencies_before_visualization():
    # ETA and berth optimization must consume AIS/berth inputs before a map
    # highlight is planned; unavailable live datasets block execution.
    qec = plan_query(UportPlanRequest(
        query="입항 선박 ETA 지연을 보고 선석 재배정안을 지도에 보여줘",
        port_id="ulsan",
    ))
    ids = [step["capability_id"] for step in qec.route_plan["steps"]]
    assert ids.index("uport.ais.search") < ids.index("uport.eta.predict")
    assert ids.index("uport.eta.predict") < ids.index("uport.berth.optimize")
    assert ids.index("uport.s101.berth.search") < ids.index("uport.berth.optimize")
    assert ids[-1] == "uport.map.visualize"
    assert qec.readiness == PlanStatus.BLOCKED_DATA
    assert qec.route_plan["execution_mode"] == "plan_only"


def test_map_selection_enters_existing_qec_with_candidate_ontology_binding():
    qec = plan_query(UportPlanRequest(
        query="이 선석을 지도에 보여줘",
        map_selection={
            "entity_type": "s101_berth", "feature_id": "feature-123",
            "dataset_id": "dataset-1", "dataset_version_id": "version-2",
        },
    ))
    assert qec.slots.feature_instance_ref["feature_instance_id"] == "feature-123"
    assert qec.context["resolved_entity"]["ontology_class"] == "S101.Berth"
    assert qec.context["resolved_entity"]["verification_status"] == "CANDIDATE"
    assert qec.readiness == PlanStatus.PLAN_READY


def test_unknown_query_requests_clarification_instead_of_execution():
    qec = plan_query(UportPlanRequest(query="무슨 뜻인가요"))
    assert qec.readiness == PlanStatus.NEEDS_USER_INPUT
    assert qec.route_plan["steps"] == []


def test_registry_dependency_cycle_is_rejected():
    with pytest.raises(ValueError, match="cyclic"):
        _ordered_steps(["a"], {"a": {"depends_on": ["b"]}, "b": {"depends_on": ["a"]}})


def test_planning_endpoint_rejects_unknown_map_entity_type():
    # The API must reject an unregistered ontology class before a QEC is made.
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post("/api/v1/uport/query/plan", json={
        "query": "이 선석", "map_selection": {
            "entity_type": "vessel", "feature_id": "1",
            "dataset_id": "d", "dataset_version_id": "v",
        },
    })
    assert response.status_code == 422


def test_planning_endpoint_returns_shared_qec_without_tool_execution():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post("/api/v1/uport/query/plan", json={
        "query": "선석을 지도에 보여줘",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "geollm.execution.v1"
    assert body["readiness"] == "PLAN_READY"
    assert body["route_plan"]["execution_mode"] == "plan_only"
    assert body["tool_bindings"] == []
