from research.marine_geollm_scie.baselines.self_reviewer import parse_review, review_prompt
from research.marine_geollm_scie.fault_injection.pilot import cases
from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
import pytest


@pytest.fixture(autouse=True)
def synthetic_coverage_for_legacy_gate_unit_tests(monkeypatch):
    # Only these no-network schema/receipt tests assume established coverage.
    # No research runner or operational registry obtains this synthetic grant.
    monkeypatch.setattr('services.orchestrator.spatial_coverage.assess_coverage',
        lambda *args, **kwargs: {'authority': 'UNIT_TEST_ONLY_SYNTHETIC_COVERAGE',
            'version': 'fixture', 'status': 'ADEQUATE', 'required': True,
            'absence_certified': False, 'sources': []})


def test_real_validator_diagnostic_controls():
    for name, code, expected, qec, adapter, env in cases():
        original = qec.model_dump()
        result = validate_execution_context(qec, binding_adapter=adapter)
        assert (not is_execution_authorized(result)) == expected, name
        assert original == qec.model_dump()


def test_reviewer_parse_abstains_without_boolean():
    assert parse_review('{"invalid":false}') is False
    assert parse_review('{"invalid":"false"}') is None
    assert parse_review('not json') is None


def test_review_input_no_authored_labels():
    name, code, expected, qec, adapter, env = next(cases())
    prompt = review_prompt(qec.model_dump(), env)
    assert "expected_invalid" not in prompt
    assert "failure_code" not in prompt


def test_post_approval_mutation_revokes_production_receipt():
    name, code, expected, qec, adapter, env = next(cases())
    checked = validate_execution_context(qec, binding_adapter=adapter)
    assert is_execution_authorized(checked)
    checked.slots.distance_m = 50001
    assert not is_execution_authorized(checked)
