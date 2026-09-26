from unittest.mock import MagicMock
import pytest
from services.orchestrator import marine_mapping_execution as module
from services.orchestrator.schema_binding_adapter import schema_binding_adapter
from services.orchestrator.marine_s101_mapping import resolve_mappings
from shared.schemas.agent import ExecutionSlots, QueryExecutionContext, EvidenceBundle, PlanStatus


@pytest.fixture
def grounded(monkeypatch):
    monkeypatch.setattr(schema_binding_adapter, '_inspect_relation', lambda _: {
        'exists': True, 'has_select': True, 'columns': [{'name': name} for name in
        ('feature_instance_id','feature_type_name','attributes','geometry')]})
    monkeypatch.setattr(module, 'resolve_reference', lambda *args: (
        'POINT(129 35)', 'fixture point', 'EPSG:4326', {'source_ref':'fixture'}))
    monkeypatch.setenv('S101_DB_URL','fixture-only')
    return {'task_id':'fixture','query':'반경 1km 이내 잠제를 찾아줘'}


def mock_database(monkeypatch, rows):
    connection=MagicMock()
    cursor=connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value={'total_count':len(rows),'rows':rows}
    connect=MagicMock(return_value=connection)
    monkeypatch.setattr(module.psycopg2,'connect',connect)
    return connect,cursor


@pytest.mark.parametrize('empty',[False,True])
def test_plan_validation_execution_and_evidence_share_identity(monkeypatch,grounded,empty):
    rows=[] if empty else [{'feature_instance_id':42,'feature_type_name':'ShorelineConstruction',
        'attributes':{'categoryOfShorelineConstruction':'1','waterLevelEffect':'3'},
        'distance_m':10,'geometry':{'type':'Point','coordinates':[129,35]}}]
    connect,cursor=mock_database(monkeypatch,rows)
    outcome=module.execute(grounded)
    final=outcome['final_dict']; qec=outcome['query_execution_context']
    typed=QueryExecutionContext.model_validate(qec)
    assert final['status']=='COMPLETED'
    assert typed.readiness==PlanStatus.EXECUTION_READY
    assert qec['execution_status']=='EXECUTED'
    assert typed.data_bindings[0].relation=='projection.s101_feature_valid'
    assert typed.tool_bindings[0].operation=='source_attribute_search'
    assert len(typed.plan_hash)==64
    execution=typed.provenance['execution']
    assert execution['query_execution_id']==final['structured_result']['query_execution_id']
    assert execution['parameters']['filters']==typed.slots.filters
    bundle=EvidenceBundle.model_validate(final['evidence_bundle'])
    assert len(bundle.spatial_feature_evidence)==len(rows)
    assert bundle.kg_provenance[0].data['registry_sha256']==typed.snapshot_versions['mapping_registry_sha256']
    if rows:
        assert bundle.spatial_feature_evidence[0].data['query_execution_id']==execution['query_execution_id']
    assert cursor.execute.call_args.args[1][-1]==['3']


def test_schema_failure_stops_feature_query(monkeypatch,grounded):
    monkeypatch.setattr(schema_binding_adapter,'_inspect_relation',lambda _: {'exists':False})
    connect=MagicMock(side_effect=AssertionError('feature SQL must not execute'))
    monkeypatch.setattr(module.psycopg2,'connect',connect)
    outcome=module.execute(grounded)
    assert outcome['final_dict']['error_code']=='SOURCE_ATTRIBUTE_EXECUTION_BLOCKED'
    assert outcome['query_execution_context']['execution_status']=='NOT_RUN'
    assert outcome['query_execution_context']['readiness']=='BLOCKED_DATA'
    connect.assert_not_called()


def test_database_failure_is_failed_execution_not_zero_results(monkeypatch,grounded):
    monkeypatch.setattr(module.psycopg2,'connect',MagicMock(side_effect=module.psycopg2.OperationalError('fixture')))
    outcome=module.execute(grounded)
    assert outcome['query_execution_context']['execution_status']=='FAILED'
    assert outcome['final_dict']['error_code']=='DB_EXECUTION_FAILED'
    assert 'total_count' not in outcome['final_dict']['structured_result']


@pytest.mark.parametrize('change',['predicate','snapshot','target','geometry','radius'])
def test_validator_rechecks_mapping_and_spatial_slots(grounded,change):
    mapping,=resolve_mappings(grounded['query'])
    slots=ExecutionSlots(reference_geometry='POINT(129 35)',crs='EPSG:4326',distance_m=1000,
        target_features=[mapping['feature']],filters={'attribute_filters':mapping['filters'],
        'mapping_registry_sha256':mapping['registry_sha256'],'fc_sha256':mapping['fc_sha256']})
    if change=='predicate': slots.filters['attribute_filters']={}
    elif change=='snapshot': slots.filters['mapping_registry_sha256']='stale'
    elif change=='target': slots.target_features=['Wreck']
    elif change=='geometry': slots.reference_geometry='POINT(999 35)'
    else: slots.distance_m=-1
    qec=QueryExecutionContext(original_query=grounded['query'],slots=slots,
                              route_plan={'analysis_type':'source_attribute_search'})
    assert module.validate_execution_context(qec).readiness!=PlanStatus.EXECUTION_READY
