import asyncio

import pytest

from services.orchestrator import graph, place_router


def arrange(monkeypatch, *, reject_second=False, sql_error=False, row_count=0):
    import psycopg2
    calls = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, sql, params=None):
            if 'ST_DWithin' in sql:
                calls.append('search')
                if sql_error:
                    raise RuntimeError('fixture database failure')

        def fetchall(self):
            return [dict(source_id=str(i), name='fixture', properties={}, provenance={},
                         geojson={'type': 'Point', 'coordinates': [131.87, 37.24]}, distance_m=i)
                    for i in range(row_count)]

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_session(self, **kwargs):
            assert kwargs == {'readonly': True, 'isolation_level': 'REPEATABLE READ'}

        def cursor(self, **kwargs):
            return Cursor()

    connection = Connection()
    monkeypatch.setattr(psycopg2, 'connect', lambda *args, **kwargs: connection)
    monkeypatch.setenv('S101_DB_URL', 'fixture-only')
    monkeypatch.setattr(place_router, 'resolve_payload', lambda *args: {
        'status': 'RESOLVED', 'geometry': 'POINT(131.87 37.24)', 'location_text': 'fixture',
        'crs': 'EPSG:4326', 'location_resolution': {}})
    monkeypatch.setattr(graph, '_record_query_quality_issues', lambda *args: None)
    monkeypatch.setattr(graph, 'project_execution_decision', lambda *args: None)

    def validate(qec, **kwargs):
        calls.append('validate')
        if kwargs:
            assert kwargs['binding_adapter'].connection is connection
        qec.provenance['coverage_validation'] = {'status': 'CORPUS_VERIFIED', 'absence_certified': False}
        return qec

    monkeypatch.setattr(graph, 'validate_execution_context', validate)
    actual_authorized = graph.is_execution_authorized
    monkeypatch.setattr(graph, 'is_execution_authorized',
                        lambda qec: actual_authorized(qec) if qec.route_plan.get('analysis_type') == 'place_lookup'
                        else not (reject_second and calls.count('validate') == 2))
    monkeypatch.setattr(graph, 'execution_gate_failure', lambda *args: {'final_dict': {'status': 'BLOCKED'}})
    return calls


def run():
    return asyncio.run(graph.fast_requested_spatial_layer_execute_node({
        'query': '독도 반경 5km 해양지명을 찾아줘', 'task_id': 'transaction-fixture'}))['final_dict']


def test_second_identity_rejection_never_dispatches_search(monkeypatch):
    calls = arrange(monkeypatch, reject_second=True)
    assert run()['status'] == 'BLOCKED'
    assert calls == ['validate', 'validate']


def test_database_failure_preserves_attempt_and_no_zero_count(monkeypatch):
    calls = arrange(monkeypatch, sql_error=True)
    result = run()
    assert calls == ['validate', 'validate', 'search']
    structured = result['structured_result']
    assert result['status'] == 'BLOCKED'
    assert structured.get('count') is None
    assert structured['search_execution']['execution_attempted'] is True
    assert structured['search_execution']['sql_executed'] is None


@pytest.mark.parametrize('row_count', [0, 100])
def test_source_result_count_does_not_claim_exhaustive_world_count(monkeypatch, row_count):
    calls = arrange(monkeypatch, row_count=row_count)
    result = run()
    assert calls == ['validate', 'validate', 'search']
    structured = result['structured_result']
    assert structured['count'] == row_count
    assert structured['total_count'] is None
    assert structured['absence_certified'] is False
    assert structured['possibly_truncated'] is (row_count == 100)
    assert structured['count_scope'] == 'SOURCE_CORPUS_RETURNED_ROWS'
    assert '2022-12-31' in result['answer_text']
    assert '보증하지 않습니다' in result['answer_text']
