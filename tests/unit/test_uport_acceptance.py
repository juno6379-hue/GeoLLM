"""Phase 10 acceptance gates for the six requested natural-language scenarios."""

import pytest

from services.uport.execution import execute_query
from services.uport.planning import UportPlanRequest, plan_query
from shared.schemas.agent import PlanStatus


class _ForbiddenDatabase:
    """Any access would mean an unavailable capability crossed the validator."""

    def execute(self, *_args, **_kwargs):
        raise AssertionError("blocked scenario must not query the database")


@pytest.mark.parametrize("scenario,query,required_capabilities", [
    ("A", "현재 입항 예정 선박을 보여줘", {"uport.ais.search", "uport.map.visualize"}),
    ("B", "ETA가 30분 이상 지연된 선박을 지도에 표시해줘",
     {"uport.ais.search", "uport.eta.predict", "uport.map.visualize"}),
    ("C", "3번 선석 주변 선박을 보여줘",
     {"uport.s101.berth.search", "uport.ais.search", "uport.map.visualize"}),
    ("D", "현재 배정안보다 대기시간을 줄이는 선석 계획을 만들어줘",
     {"uport.berth.optimize", "uport.eta.predict", "uport.s101.berth.search"}),
    ("E", "추천된 선석이 적합한 이유를 설명해줘",
     {"uport.berth.explain", "uport.berth.optimize"}),
    ("F", "이 선박 주변의 S-101 항행 위험 객체를 찾아줘",
     {"uport.s101.hazard.search", "uport.ais.search"}),
])
def test_scenario_routes_and_blocks_without_authoritative_data(scenario, query, required_capabilities):
    """Assert intent/dependency coverage and zero fabricated execution facts."""

    request = UportPlanRequest(query=query, port_id="ulsan")
    plan = plan_query(request)
    steps = [row["capability_id"] for row in plan.route_plan["steps"]]
    assert required_capabilities <= set(steps), scenario
    assert plan.readiness == PlanStatus.BLOCKED_DATA, scenario
    assert plan.route_plan["execution_mode"] == "plan_only", scenario
    for step in plan.route_plan["steps"]:
        assert set(step["depends_on"]) <= set(steps[:steps.index(step["capability_id"])]), scenario

    result = execute_query(request, _ForbiddenDatabase())
    assert result.status == "blocked", scenario
    assert result.error_code == "DATASET_NOT_AVAILABLE", scenario
    assert result.features == [] and result.map_layers == [] and result.evidence == [], scenario
    assert result.narrative is None, scenario


def test_hazard_and_recommendation_explanation_are_explicitly_unavailable():
    """An S-101 berth lookup must not impersonate hazard or optimizer evidence."""

    for query, capability in [
        ("이 선박 주변의 S-101 항행 위험 객체를 찾아줘", "uport.s101.hazard.search"),
        ("추천된 선석이 적합한 이유를 설명해줘", "uport.berth.explain"),
    ]:
        plan = plan_query(UportPlanRequest(query=query, port_id="ulsan"))
        assert capability in [row["capability_id"] for row in plan.route_plan["steps"]]
        assert any(capability in blocker for blocker in plan.blockers)
