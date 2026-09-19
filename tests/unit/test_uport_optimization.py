"""Physical feasibility, reproducible search and honest solver boundaries."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.uport.optimization.algorithms import FCFSOptimizer, NSGAIIOptimizer
from services.uport.optimization.contracts import OptimizationInfeasible, OptimizationRequest
from services.uport.optimization.router import router

NOW = datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc)


def request_data():
    """Two equally sized berths reveal conflicts and waiting time."""

    return {
        "port_id": "ulsan", "source_dataset_id": "fixture:berth-v1",
        "berths": [
            {"berth_id": "B1", "length_m": 200, "water_depth_m": 12,
             "max_beam_m": 30, "cargo_types": ["general"],
             "available_from": NOW.isoformat(),
             "available_until": (NOW + timedelta(hours=8)).isoformat()},
            {"berth_id": "B2", "length_m": 200, "water_depth_m": 12,
             "max_beam_m": 30, "cargo_types": ["general"],
             "available_from": NOW.isoformat(),
             "available_until": (NOW + timedelta(hours=8)).isoformat()},
        ],
        "jobs": [
            {"job_id": "J1", "loa_m": 150, "beam_m": 20, "draft_m": 8,
             "cargo_type": "general", "arrival_at": NOW.isoformat(), "service_minutes": 120},
            {"job_id": "J2", "loa_m": 150, "beam_m": 20, "draft_m": 8,
             "cargo_type": "general", "arrival_at": NOW.isoformat(), "service_minutes": 120},
        ],
    }


def test_fcfs_assignments_do_not_overlap_and_keep_source():
    request = OptimizationRequest.model_validate(request_data())
    result = FCFSOptimizer().optimize(request)
    assert result.total_waiting_minutes == 0
    assert {assignment.berth_id for assignment in result.assignments} == {"B1", "B2"}
    assert result.source_dataset_id == "fixture:berth-v1"


def test_single_berth_serializes_jobs_and_counts_wait():
    payload = request_data()
    payload["berths"] = payload["berths"][:1]
    result = FCFSOptimizer().optimize(OptimizationRequest.model_validate(payload))
    assert result.assignments[0].end_at == result.assignments[1].start_at
    assert result.total_waiting_minutes == 120


def test_physical_limits_and_availability_make_request_infeasible():
    payload = request_data()
    payload["jobs"][0]["draft_m"] = 13
    with pytest.raises(OptimizationInfeasible, match="J1"):
        FCFSOptimizer().optimize(OptimizationRequest.model_validate(payload))
    payload = request_data()
    payload["berths"][0]["available_until"] = (NOW + timedelta(minutes=30)).isoformat()
    payload["berths"][1]["available_until"] = (NOW + timedelta(minutes=30)).isoformat()
    with pytest.raises(OptimizationInfeasible):
        FCFSOptimizer().optimize(OptimizationRequest.model_validate(payload))


def test_nsga_is_reproducible_and_no_worse_than_baseline_on_simple_case():
    request = OptimizationRequest.model_validate(request_data())
    first = NSGAIIOptimizer(population_size=8, generations=3, seed=4).optimize(request)
    second = NSGAIIOptimizer(population_size=8, generations=3, seed=4).optimize(request)
    assert first == second
    assert first.total_waiting_minutes <= FCFSOptimizer().optimize(request).total_waiting_minutes


def test_input_requires_unique_ids_and_timezone():
    payload = request_data()
    payload["jobs"][1]["job_id"] = "J1"
    with pytest.raises(ValidationError, match="duplicate job_id"):
        OptimizationRequest.model_validate(payload)
    payload = request_data()
    payload["jobs"][0]["arrival_at"] = "2026-09-19T00:00:00"
    with pytest.raises(ValidationError, match="timezone"):
        OptimizationRequest.model_validate(payload)


def test_compare_api_reports_optional_solvers_without_fabricated_results():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post("/api/v1/uport/optimization/compare", json=request_data())
    assert response.status_code == 200
    outcomes = {item["algorithm"]: item for item in response.json()["outcomes"]}
    assert outcomes["FCFS"]["result"]["total_waiting_minutes"] == 0
    assert outcomes["NSGA-II"]["result"] is not None
    assert outcomes["MIP/CBC"]["error_code"] == "SOLVER_NOT_AVAILABLE"
    assert outcomes["MIP/HiGHS"]["result"] is None
