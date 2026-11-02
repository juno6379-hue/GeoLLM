"""Execution gate regressions with isolated schema bindings, without live DB access."""

import hashlib
import json
import pytest

from services.orchestrator import execution_validator
from services.orchestrator.schema_binding_adapter import BindingResult
from shared.schemas.agent import (
    DataBinding,
    ExecutionSlots,
    PlanStatus,
    QueryExecutionContext,
    ToolBinding,
)


@pytest.fixture
def bound_gate(monkeypatch, tmp_path):
    result = BindingResult(
        data_bindings=[
            DataBinding(
                dataset_id="fixture_dataset",
                snapshot_version="fixture-v1",
                relation="fixture.observations",
                srid=4326,
                execution_status="executable",
            )
        ],
        tool_bindings=[ToolBinding(tool_id="fixture.tool", operation="fixture_operation")],
    )
    monkeypatch.setattr(
        execution_validator.schema_binding_adapter,
        "build_bindings",
        lambda *_: result,
    )
    # Explicit local fixture scope, not a claim about operational source coverage.
    from services.orchestrator import spatial_coverage
    contract = {
        'approval_status':'APPROVED','source_locator':'fixture-only',
        'dataset_id':'fixture_dataset','relation':'fixture.observations',
        'snapshot_version':'fixture-v1','target_features':['Wreck'],'crs':'EPSG:4326',
        'geometry_wkt':'POLYGON((120 30,140 30,140 45,120 45,120 30))',
        'nearest_domain_complete':True,
    }
    path=tmp_path/'coverage.json'
    path.write_text(json.dumps(contract),encoding='utf-8')
    registry={'layers':{'fixture_dataset':{'physical_table':'fixture.observations',
        'coverage_contract':{'path':'coverage.json','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}}
    monkeypatch.setattr(execution_validator.schema_binding_adapter,'layer_registry',registry)
    assess=spatial_coverage.assess_coverage
    monkeypatch.setattr(spatial_coverage,'assess_coverage',lambda q,r:assess(q,r,root=tmp_path))
    return execution_validator.validate_execution_context


def _context(operation="feature_search_by_radius", **slots):
    values = {
        "reference_geometry": "POINT(129.075 35.075)",
        "crs": "EPSG:4326",
        "distance_m": 3000,
        "target_features": ["Wreck"],
    }
    values.update(slots)
    return QueryExecutionContext(
        route_plan={"analysis_type": operation},
        slots=ExecutionSlots(**values),
    )


@pytest.mark.parametrize("distance", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_radius_never_becomes_executable(bound_gate, distance):
    result = bound_gate(_context(distance_m=distance))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT
    assert any("finite" in blocker for blocker in result.blockers)


@pytest.mark.parametrize("distance", [None, 0, -1])
def test_missing_or_nonpositive_radius_requires_input(bound_gate, distance):
    assert bound_gate(_context(distance_m=distance)).readiness == PlanStatus.NEEDS_USER_INPUT


@pytest.mark.parametrize("distance", [0.1, 3000, 50000])
def test_valid_radius_remains_executable_without_mutating_input(bound_gate, distance):
    context = _context(distance_m=distance)
    original = context.model_dump()

    result = bound_gate(context)

    assert result.readiness == PlanStatus.EXECUTION_READY
    assert not result.blockers
    assert context.model_dump() == original


def test_oversized_radius_is_a_policy_block(bound_gate):
    assert bound_gate(_context(distance_m=50001)).readiness == PlanStatus.BLOCKED_POLICY


@pytest.mark.parametrize(
    "geometry",
    [
        "not a geometry",
        "POINT EMPTY",
        "GEOMETRYCOLLECTION EMPTY",
        "POINT(NaN 35)",
        "POLYGON((0 0,1 1,0 1,1 0,0 0))",
    ],
)
def test_invalid_or_empty_geometry_cannot_pass_on_truthiness(bound_gate, geometry):
    result = bound_gate(_context(reference_geometry=geometry))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT
    assert any("geometry" in blocker for blocker in result.blockers)


def test_geometry_reference_needs_resolution_before_execution(bound_gate):
    result = bound_gate(_context(reference_geometry=None, geometry_ref="missing:geometry:42"))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT


def test_resolved_geometry_reference_can_use_materialized_spatial_geometry(bound_gate):
    context = _context(reference_geometry=None, geometry_ref="geometry:42")
    context.spatial = {"spatial_context": {"geometry": "POINT(129.075 35.075)"}}

    assert bound_gate(context).readiness == PlanStatus.EXECUTION_READY


def test_area_search_still_does_not_require_radius(bound_gate):
    result = bound_gate(
        _context(
            "feature_within_area",
            reference_geometry="POLYGON((129 35,130 35,130 36,129 36,129 35))",
            distance_m=None,
        )
    )

    assert result.readiness == PlanStatus.EXECUTION_READY


@pytest.mark.parametrize("operation", [None, "", "unregistered_operation"])
def test_unknown_operation_is_not_ready_even_with_bindings(bound_gate, operation):
    result = bound_gate(_context(operation))

    assert result.readiness == PlanStatus.BLOCKED_CONFIG
    assert any("operation" in blocker for blocker in result.blockers)


@pytest.mark.parametrize("key", ["k", "limit"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, float("nan"), float("inf"), "invalid"])
def test_nearest_count_must_be_a_positive_integer(bound_gate, key, value):
    result = bound_gate(_context("nearest_feature", filters={key: value}))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT


def test_explicit_zero_k_is_not_replaced_by_limit(bound_gate):
    result = bound_gate(_context("nearest_feature", filters={"k": 0, "limit": 5}))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT


@pytest.mark.parametrize("value", [1, 100, "2"])
def test_valid_nearest_count_remains_executable(bound_gate, value):
    assert bound_gate(_context("nearest_feature", filters={"k": value})).readiness == PlanStatus.EXECUTION_READY


@pytest.mark.parametrize("key", ["horizon_steps", "horizon"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, float("nan"), float("inf"), "invalid"])
def test_forecast_horizon_must_be_a_positive_integer(bound_gate, key, value):
    result = bound_gate(_context("observed_time_series_forecast", filters={key: value}))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT


@pytest.mark.parametrize("value", [1, 168, "3"])
def test_valid_forecast_horizon_remains_executable(bound_gate, value):
    assert bound_gate(_context("observed_time_series_forecast", filters={"horizon_steps": value})).readiness == PlanStatus.EXECUTION_READY


def test_explicit_zero_horizon_is_not_replaced_by_alias(bound_gate):
    result = bound_gate(_context("observed_time_series_forecast", filters={"horizon_steps": 0, "horizon": 3}))

    assert result.readiness == PlanStatus.NEEDS_USER_INPUT


def test_forecast_horizon_limit_is_a_policy_block(bound_gate):
    assert bound_gate(_context("observed_time_series_forecast", filters={"horizon_steps": 169})).readiness == PlanStatus.BLOCKED_POLICY


@pytest.mark.parametrize(
    ("blocker", "expected"),
    [
        ("BLOCKED_POLICY: access denied", PlanStatus.BLOCKED_POLICY),
        ("BLOCKED_CONFIG: missing tool", PlanStatus.BLOCKED_CONFIG),
        ("BLOCKED_DATA: missing dataset", PlanStatus.BLOCKED_DATA),
    ],
)
def test_environment_or_policy_block_is_not_mislabeled_as_user_ambiguity(bound_gate, blocker, expected):
    context = _context(reference_geometry=None)
    context.blockers = [blocker]

    result = bound_gate(context)

    assert result.readiness == expected
    assert blocker in result.blockers
    assert any(item.startswith("NEEDS_USER_INPUT") for item in result.blockers)
