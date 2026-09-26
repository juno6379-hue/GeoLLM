import pytest
from services.orchestrator import selected_feature_evidence as module


@pytest.fixture(autouse=True)
def source_schema(monkeypatch):
    from services.orchestrator.schema_binding_adapter import schema_binding_adapter
    monkeypatch.setattr(schema_binding_adapter, '_inspect_relation', lambda _: {
        'exists': True, 'has_select': True, 'columns': [{'name': name} for name in
        ('feature_instance_id', 'feature_type_name', 'attributes', 'geometry')]})


def state(query='지도에서 선택한 이 객체 정보를 설명해줘', **selection):
    return {'task_id': 'fixture', 'query': query, 'spatial_context': {'selected_feature': selection}}


@pytest.mark.parametrize('selection,code', [
    ({'id': 1}, 'SELECTED_FEATURE_SOURCE_REQUIRED'),
    ({'id': 1, 'source_ref': 'other.table'}, 'SELECTED_FEATURE_SOURCE_REQUIRED'),
    ({'id': True, 'source_ref': module.SOURCE}, 'INVALID_SELECTED_FEATURE_ID'),
    ({'id': '1 OR 1=1', 'source_ref': module.SOURCE}, 'INVALID_SELECTED_FEATURE_ID'),
])
def test_invalid_identity_never_queries_source(monkeypatch, selection, code):
    monkeypatch.setattr(module, 'fetch_feature', lambda _: pytest.fail('unexpected DB read'))
    result = module.execute(state(**selection))
    assert result['final_dict']['error_code'] == code
    assert result['query_execution_context']['execution_status'] == 'NOT_RUN'


@pytest.mark.parametrize('rows,code', [([], 'SELECTED_FEATURE_NOT_FOUND'), ([{}, {}], 'SELECTED_FEATURE_AMBIGUOUS')])
def test_missing_or_ambiguous_identity_is_not_completed(monkeypatch, rows, code):
    monkeypatch.setattr(module, 'fetch_feature', lambda _: rows)
    assert module.execute(state(id=1, source_ref=module.SOURCE))['final_dict']['error_code'] == code


@pytest.mark.parametrize('portrayal', [False, True])
def test_db_evidence_overrides_client_claims_and_portrayal_stays_partial(monkeypatch, portrayal):
    row = {'feature_instance_id': 1, 'feature_type_name': 'Wreck',
           'attributes': {'categoryOfWreck': 1, 'waterLevelEffect': 3},
           'geometry': {'type': 'Point', 'coordinates': [129, 35]}}
    monkeypatch.setattr(module, 'fetch_feature', lambda _: [row])
    query = '지도에서 선택한 이 객체 정보를 설명해줘' + (' 심볼 매칭도 설명해줘' if portrayal else '')
    final = module.execute(state(query, id=1, source_ref=module.SOURCE,
                                 properties={'feature_type_name': 'Invented'}))['final_dict']
    assert final['status'] == ('PARTIAL' if portrayal else 'COMPLETED')
    evidence = final['structured_result']['selected_feature_evidence']
    assert evidence['feature_type'] == 'Wreck'
    assert len(evidence['row_sha256']) == 64
    assert not final['structured_result']['portrayal_candidate']['official_rule_executed']
    assert 'portrayal_binding' not in final['structured_result']
    qec = final['orchestrator_v2']['query_execution_context']
    assert qec['readiness'] == 'EXECUTION_READY'
    assert qec['slots']['feature_instance_id'] == 1
    assert qec['data_bindings'][0]['relation'] == module.SOURCE
    assert evidence['query_execution_id'] == qec['provenance']['execution']['query_execution_id']
    assert final['evidence_bundle']['spatial_feature_evidence'][0]['data'] == evidence


def test_execution_validator_blocks_tool_when_schema_is_unavailable(monkeypatch):
    from services.orchestrator.schema_binding_adapter import schema_binding_adapter
    monkeypatch.setattr(schema_binding_adapter, '_inspect_relation', lambda _: {'exists': False})
    monkeypatch.setattr(module, 'fetch_feature', lambda _: pytest.fail('validator was bypassed'))
    result = module.execute(state(id=1, source_ref=module.SOURCE))
    assert result['final_dict']['error_code'] == 'SELECTED_FEATURE_EXECUTION_BLOCKED'
    assert result['query_execution_context']['execution_status'] == 'NOT_RUN'


def test_source_failure_has_no_fabricated_evidence(monkeypatch):
    def unavailable(_):
        raise module.psycopg2.OperationalError('fixture')
    monkeypatch.setattr(module, 'fetch_feature', unavailable)
    final = module.execute(state(id=1, source_ref=module.SOURCE))['final_dict']
    assert final['error_code'] == 'SELECTED_FEATURE_SOURCE_UNAVAILABLE'
    assert not final['structured_result']
