"""Prevent runtime audit success on missing or contradictory evidence."""
from copy import deepcopy

from scripts.check_coverage_availability_20261102 import inspect_case


def blocked_row():
    return {'observation': 'COMPLETED_EVENT_RECEIVED', 'completion': {'final_result': {
        'status': 'BLOCKED', 'error_code': 'DATA_COVERAGE_UNVERIFIED',
        'structured_result': {'count': None},
        'orchestrator_v2': {'query_execution_context': {
            'readiness': 'BLOCKED_DATA', 'provenance': {
                'coverage_validation': {'status': 'UNKNOWN', 'required': True, 'absence_certified': False},
                'spatial_preflight': {'status': 'BLOCKED_BEFORE_DISPATCH',
                    'execution_attempted': False, 'execution_started': False,
                    'tool_called': False, 'sql_executed': False}}}}}}}


def test_blocked_requires_observed_false_not_missing():
    row = blocked_row()
    assert inspect_case(row, 'blocked')['passed']
    del row['completion']['final_result']['orchestrator_v2']['query_execution_context']['provenance']['spatial_preflight']['sql_executed']
    assert not inspect_case(row, 'blocked')['passed']


def test_blocked_zero_is_not_unknown_count():
    row = blocked_row()
    row['completion']['final_result']['structured_result']['count'] = 0
    assert not inspect_case(row, 'blocked')['passed']


def test_timeout_is_not_completed_block():
    row = blocked_row()
    row['observation'] = 'OBSERVATION_ERROR'
    assert not inspect_case(row, 'blocked')['passed']


def test_old_blocked_gazetteer_is_not_availability_success():
    assert not inspect_case(deepcopy(blocked_row()), 'corpus')['passed']
