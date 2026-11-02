"""Source inventory execution is distinct from complete geographic coverage."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from services.orchestrator.spatial_coverage import assess_source_corpus
from shared.schemas.agent import QueryExecutionContext, ExecutionSlots, DataBinding, ToolBinding


def request(query='등록된 해양지명 자료에서 독도 반경 5km 지명을 찾아줘'):
    return QueryExecutionContext(request_id='source-corpus-test', original_query=query,
        route_plan={'analysis_type': 'feature_dwithin'},
        slots=ExecutionSlots(crs='EPSG:4326', reference_geometry='POINT(131.87 37.24)',
            distance_m=5000, target_layers=['marine_gazetteer']),
        data_bindings=[DataBinding(dataset_id='marine_gazetteer',
            relation='serving.marine_gazetteer_current', geometry_column='geometry', srid=4326)])


def setup():
    contract = {'kind': 'csv_exact_inventory_v1', 'source_asset': 'fixture.csv',
                'source_sha256': 'a'*64, 'allowed_operations': ['feature_dwithin']}
    registry = {'layers': {'marine_gazetteer': {
        'physical_table': 'serving.marine_gazetteer_current', 'geometry_column': 'geometry',
        'corpus_contract': contract}}}
    observed = {'status': 'VERIFIED', 'dataset_id': 'marine_gazetteer',
                'relation': 'serving.marine_gazetteer_current', 'source_asset': 'fixture.csv',
                'source_sha256': 'a'*64, 'snapshot_version': 'sha256:'+'b'*64, 'row_count': 3}
    return registry, observed


def adapter(qec, registry, observed):
    return SimpleNamespace(layer_registry=registry,
        verify_corpus_identity=Mock(return_value=observed),
        build_bindings=lambda *args: SimpleNamespace(data_bindings=qec.data_bindings,
            tool_bindings=[ToolBinding(tool_id='postgis.dwithin', operation='spatial')],
            blockers=[], warnings=[], inspected_relations={}))


@pytest.mark.parametrize('query', ['등록된 해양지명 자료에서 독도 반경 5km 지명을 찾아줘',
    '독도 부근 5km 이내 해양지명을 알려줘', 'Find marine names within 5km of Dokdo'])
def test_source_inventory_has_separate_scope_and_signed_decision(query):
    qec = request(query); registry, observed = setup(); bound = adapter(qec, registry, observed)
    result = validate_execution_context(qec, binding_adapter=bound)
    assert is_execution_authorized(result)
    receipt = result.provenance['coverage_validation']
    assert receipt['status'] == 'CORPUS_VERIFIED'
    assert receipt['geographic_coverage'] == 'UNKNOWN'
    assert receipt['query_scope'] == 'SOURCE_CORPUS'
    assert receipt['absence_certified'] is False
    bound.verify_corpus_identity.assert_called_once()
    receipt['absence_certified'] = True
    assert not is_execution_authorized(result)


@pytest.mark.parametrize('query', [
    '독도 반경 5km 전체 지명을 찾아줘',
    '자료에서 독도 반경 5km 실제 존재하는 지명을 찾아줘',
    '자료에서 독도 반경 5km 지명을 누락 없이 찾아줘',
    '독도에서 가장 가까운 지명을 찾아줘',
    'Explain the CSV then find all real-world names within 5km',
])
def test_unrestricted_or_complete_query_cannot_be_silently_narrowed(query):
    qec = request(query); registry, observed = setup(); bound = adapter(qec, registry, observed)
    qec.slots.filters['query_scope'] = 'SOURCE_CORPUS'
    qec.provenance['coverage_validation'] = {'status': 'CORPUS_VERIFIED'}
    result = validate_execution_context(qec, binding_adapter=bound)
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in result.blockers
    bound.verify_corpus_identity.assert_not_called()


@pytest.mark.parametrize('change', [
    {'status': 'UNVERIFIED'}, {'source_sha256': 'c'*64}, {'source_asset': 'other.csv'},
    {'snapshot_version': None}, {'row_count': 0}, {'relation': 'other.table'},
    {'dataset_id': 'other'}, {'snapshot_version': '2.0'}, {'row_count': True},
])
def test_source_mismatch_and_missing_identity_fail_closed(change):
    qec = request(); registry, observed = setup(); observed.update(change)
    result = validate_execution_context(qec, binding_adapter=adapter(qec, registry, observed))
    assert not is_execution_authorized(result)
    assert result.provenance['coverage_validation']['status'] == 'UNKNOWN'


@pytest.mark.parametrize('mutation', ['complete', 'nearest', 'invalid_crs', 'missing_geometry',
                                     'other_layer', 'feature_target', 'unregistered_contract'])
def test_source_scope_does_not_bypass_other_contracts(mutation):
    qec = request(); registry, observed = setup()
    if mutation == 'complete': qec.slots.filters['require_complete_coverage'] = True
    elif mutation == 'nearest': qec.route_plan['analysis_type'] = 'nearest_feature'
    elif mutation == 'invalid_crs': qec.slots.crs = 'EPSG:3857'
    elif mutation == 'missing_geometry': qec.slots.reference_geometry = None
    elif mutation == 'other_layer': qec.slots.target_layers.append('unregistered')
    elif mutation == 'feature_target': qec.slots.target_features = ['Wreck']
    else: registry['layers']['marine_gazetteer']['corpus_contract'] = {}
    verifier = Mock(return_value=observed)
    assert assess_source_corpus(qec, registry, verifier) is None
    verifier.assert_not_called()


def test_known_geographic_outside_is_not_overridden(monkeypatch):
    from services.orchestrator import spatial_coverage
    qec = request(); registry, observed = setup(); bound = adapter(qec, registry, observed)
    monkeypatch.setattr(spatial_coverage, 'assess_coverage', lambda *args: {
        'status': 'OUT_OF_COVERAGE', 'required': True, 'absence_certified': False})
    result = validate_execution_context(qec, binding_adapter=bound)
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_OUT_OF_SCOPE' in result.blockers
    bound.verify_corpus_identity.assert_not_called()


def test_all_bound_sources_must_be_verified():
    qec = request(); registry, observed = setup()
    qec.data_bindings.append(DataBinding(dataset_id='unknown', relation='unknown.source'))
    assert assess_source_corpus(qec, registry, Mock(return_value=observed)) is None


def test_verifier_exception_blocks_without_leaking_details():
    qec = request(); registry, observed = setup(); bound = adapter(qec, registry, observed)
    bound.verify_corpus_identity.side_effect = RuntimeError('SECRET source connection')
    result = validate_execution_context(qec, binding_adapter=bound)
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in result.blockers
    assert 'SECRET' not in str(result.model_dump())


def test_adapter_source_failure_hides_connection_details(monkeypatch):
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
    # Import supplied by the source-verifier module, not a QEC receipt.
    import sys
    verifier = Mock(side_effect=RuntimeError('SECRET connection credentials'))
    monkeypatch.setitem(sys.modules, 'services.orchestrator.gazetteer_corpus',
                        SimpleNamespace(verify_gazetteer_corpus=verifier))
    qec = request(); registry, _ = setup()
    from unittest.mock import MagicMock
    connection = MagicMock()
    result = SchemaBindingAdapter(connection=connection).verify_corpus_identity(qec.data_bindings[0],
        registry['layers']['marine_gazetteer']['corpus_contract'])
    assert result == {'status': 'UNVERIFIED', 'reason': 'RuntimeError'}


def test_adapter_preflight_uses_own_readonly_transaction(monkeypatch):
    import sys
    import psycopg2
    from unittest.mock import MagicMock
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
    qec = request(); registry, observed = setup()
    verifier = Mock(return_value=observed)
    monkeypatch.setitem(sys.modules, 'services.orchestrator.gazetteer_corpus',
                        SimpleNamespace(verify_gazetteer_corpus=verifier))
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = connection.cursor.return_value.__enter__.return_value
    connect = Mock(return_value=connection)
    monkeypatch.setattr(psycopg2, 'connect', connect)
    monkeypatch.setenv('S101_DB_URL', 'fixture-only')
    monkeypatch.setenv('POSTGIS_URL', 'gazetteer-fixture')
    result = SchemaBindingAdapter().verify_corpus_identity(qec.data_bindings[0],
        registry['layers']['marine_gazetteer']['corpus_contract'])
    assert result == observed
    connect.assert_called_once_with('fixture-only', connect_timeout=3)
    connection.set_session.assert_called_once_with(readonly=True, isolation_level='REPEATABLE READ')
    verifier.assert_called_once_with(cursor=cursor)


def test_unregistered_source_does_not_invoke_database_verifier(monkeypatch):
    import psycopg2
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
    connect = Mock(side_effect=AssertionError('unregistered corpus must not connect'))
    monkeypatch.setattr(psycopg2, 'connect', connect)
    binding = DataBinding(dataset_id='GBENC_S101_feature', relation='projection.s101_feature_current')
    result = SchemaBindingAdapter().verify_corpus_identity(binding, {'kind': 'csv_exact_inventory_v1'})
    assert result['status'] == 'UNVERIFIED'
    connect.assert_not_called()
