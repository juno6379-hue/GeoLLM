from copy import deepcopy
from pathlib import Path

import pytest

from research.marine_geollm_scie.reliability.registry import load, validate


def test_full_taxonomy_and_30_unexecuted_specs():
    c, p = load()
    result = validate(c, p)
    assert result['case_count'] == 40
    assert result['representative_spec_count'] == 30
    assert {r['category'] for r in c['cases']} == set('ABCDEFGHIJKLM')
    assert all(t['execution_status'] == 'NOT_EXECUTED' for t in c['representative_test_specs'])


@pytest.mark.parametrize('mutation', ['duplicate', 'broken_policy', 'activate', 'adopt_default',
                                   'superiority', 'claim', 'bad_rq', 'missing_test', 'repair'])
def test_reject_invalid_or_overclaiming_registry(mutation):
    c, p = deepcopy(load())
    if mutation == 'duplicate': c['cases'].append(c['cases'][0])
    if mutation == 'broken_policy': c['cases'][0]['policy_id'] = 'missing'
    if mutation == 'activate': p['production_enabled'] = True
    if mutation == 'adopt_default': p['default_distance_m'] = 1000
    if mutation == 'superiority': c['cases'][0]['detector_superiority_measured'] = True
    if mutation == 'claim': c['cases'][0]['production_status'] = 'IMPLEMENTED'
    if mutation == 'bad_rq': c['cases'][0]['rq'] = ['RQ6']
    if mutation == 'missing_test': c['representative_test_specs'].pop()
    if mutation == 'repair': p['matched_plan']['p0_compilation'] = 'REASONING_REPAIR'
    with pytest.raises(ValueError): validate(c, p)


def test_missing_area_and_outside_coverage_never_become_empty_success():
    c, p = load()
    by = {r['case_id']: r for r in c['cases']}
    missing = by['R-B3']['expected_decision']
    assert missing['readiness'] == 'NEEDS_USER_INPUT'
    assert all(missing[k] is False for k in ['execution_attempted','execution_started','tool_called','sql_executed'])
    assert missing['observation_scope'] == 'SPATIAL_EXECUTION_ONLY'
    outside = by['R-C1']['expected_decision']
    assert outside['readiness'] == 'BLOCKED_DATA'
    assert outside['result_count'] is None and outside['spatial_gold'] is None
    assert by['R-M1']['expected_decision']['preconditions'] == ['coverage_adequate','execution_succeeded','actual_result_count_is_zero']
    assert p['missing_observation'] is None


def test_related_paths_exist_but_are_only_audit_targets():
    c, _ = load()
    root = Path(__file__).resolve().parents[3]
    for row in c['cases']:
        assert row['related_code_role'] == 'AUDIT_TARGET_NOT_IMPLEMENTATION_PROOF'
        assert row['production_status'] is None
        assert row['verification_status'] == 'NOT_AUDITED'
        for path in row['related_code']:
            assert (root / path).is_file(), path
