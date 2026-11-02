"""Final UI projection cannot grant authority from a candidate plan."""
from copy import deepcopy
from unittest.mock import Mock

import pytest


@pytest.fixture
def graph(monkeypatch):
    monkeypatch.setenv('DISABLE_LLM_API', 'true')
    monkeypatch.setenv('GEOLLM_CAPABILITY_PGVECTOR', 'false')
    monkeypatch.setenv('GEOLLM_SEMANTIC_PRIOR_OLLAMA', 'false')
    import requests
    import psycopg2
    monkeypatch.setattr(requests.sessions.Session, 'request', Mock(side_effect=AssertionError('No HTTP')))
    monkeypatch.setattr(psycopg2, 'connect', Mock(side_effect=AssertionError('No DB')))
    from services.orchestrator import graph
    return graph


@pytest.mark.parametrize('status', ['BLOCKED', 'NEEDS_CLARIFICATION', 'COMPLETED'])
def test_candidate_ready_without_qec_is_never_execution_authority(graph, status):
    trace = {'execution_contract': {'status': 'ready', 'tools': ['spatial']}}
    before = deepcopy(trace)
    result = graph._attach_candidate_trace({'candidate_trace': trace}, {'status': status})
    contract = result['structured_result']['execution_contract']
    assert contract['planning_status'] == 'ready'
    assert contract['status'] == status
    assert contract['status_scope'] == 'FINAL_RESULT'
    assert contract['execution_authorized'] is False
    assert contract['execution_readiness'] == 'NOT_VALIDATED'
    assert trace == before


def test_missing_area_records_spatial_nonexecution_and_unknown_count():
    from services.orchestrator.korean_query_analysis import guard_result
    result = guard_result({'task_id': 'missing-area', 'query': 'Find wrecks in selected area'},
                          {'slots': [], 'constraints': []},
                          {'status': 'NEEDS_CLARIFICATION', 'code': 'AOI_REQUIRED',
                           'missing_slots': ['selected_area_geometry'], 'message': 'Select area'})
    final = result['final_dict']
    structured = final['structured_result']
    for key in ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed'):
        assert structured[key] is False
        assert result['query_execution_context']['provenance']['spatial_preflight'][key] is False
    assert all(structured[key] is None for key in ('count', 'total_count', 'returned_count'))
    assert structured['count_scope'] == 'NOT_EXECUTED'
    assert final['status'] == 'NEEDS_CLARIFICATION'
