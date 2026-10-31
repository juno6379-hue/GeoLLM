import pytest
from research.marine_geollm_scie.runners.spatial_execution_observer import SpatialExecutionObserver, classify_sql


@pytest.mark.parametrize('query',[
    'SELECT 1', 'SELECT column_name FROM information_schema.columns',
    "SELECT content FROM chunks WHERE text ILIKE 'ST_DWithin(foo)'",
    'SELECT 1 -- ST_Intersects(foo)',
])
def test_documents_metadata_are_not_gis(query):
    assert classify_sql(query)[0]=='NON_SPATIAL_SQL'


@pytest.mark.parametrize('query',[
    'SELECT ST_DWithin(a::geography,b::geography,1000)',
    'SELECT * FROM f WHERE geom && ST_MakeEnvelope(1,2,3,4,4326)',
    'SELECT ST_Covers(a,b)',
])
def test_spatial_predicates_are_classified(query):
    assert classify_sql(query)[0]=='SPATIAL_SQL'


def test_direct_dbapi_error_records_attempt_and_failed_submission():
    class Cursor:
        def execute(self,*args):raise ValueError('intentional explicit fixture failure')
    observer=SpatialExecutionObserver('fixture')
    cursor=observer.cursor_type(Cursor)()
    with pytest.raises(ValueError):cursor.execute('SELECT ST_Intersects(a,b)')
    observer.complete=True
    result=observer.result()
    assert result['execution_attempted'] is True
    assert result['execution_started'] is True
    assert result['sql_executed'] is True
    assert result['execution_succeeded'] is False
    assert 'SELECT' not in str(result['events'])


def test_complete_document_only_window_proves_no_instrumented_gis():
    observer=SpatialExecutionObserver('fixture')
    kind,digest=observer.submission('SELECT content FROM chunks',None,'fixture')
    observer.finished(kind,digest,'fixture',True)
    observer.complete=True
    result=observer.result()
    assert result['execution_attempted'] is False
    assert result['sql_executed'] is False
    assert result['non_spatial_sql_submissions']==1


def test_interrupted_or_opaque_window_is_not_false_nonexecution():
    observer=SpatialExecutionObserver('fixture')
    assert observer.result()['execution_attempted'] is None
    observer.complete=True
    observer.instrumentation_issues.append('SUBPROCESS_OUTSIDE_OBSERVATION')
    assert observer.result()['observation_complete'] is False
    assert observer.result()['execution_attempted'] is None
