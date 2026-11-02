from unittest.mock import Mock

import pytest

from services.orchestrator.s101_radius_execution import _execute_stage
from shared.schemas.agent import QueryExecutionContext


def test_metadata_sql_is_not_spatial_execution():
    qec = QueryExecutionContext()
    _execute_stage(Mock(), qec, 'feature_code_verification', 'metadata')
    assert 'spatial_execution' not in qec.provenance


def test_successful_spatial_select_records_server_acknowledgement():
    qec = QueryExecutionContext()
    cursor = Mock()
    _execute_stage(cursor, qec, 'spatial_select', 'spatial', {'radius': 1000})
    trace = qec.provenance['spatial_execution']
    assert all(trace[k] is True for k in ('execution_attempted', 'tool_called', 'execution_started', 'sql_executed', 'execution_succeeded', 'observation_complete'))
    cursor.execute.assert_called_once_with('spatial', {'radius': 1000})


def test_transport_failure_keeps_server_execution_unknown():
    qec = QueryExecutionContext()
    cursor = Mock(); cursor.execute.side_effect = ConnectionError('synthetic')
    with pytest.raises(ConnectionError):
        _execute_stage(cursor, qec, 'spatial_select', 'spatial')
    trace = qec.provenance['spatial_execution']
    assert trace['execution_attempted'] is True
    assert trace['sql_executed'] is None
    assert trace['execution_started'] is None
    assert trace['observation_complete'] is False
