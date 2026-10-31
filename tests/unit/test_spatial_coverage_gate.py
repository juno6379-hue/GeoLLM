"""Coverage declaration fixtures are not approved geographic source metadata."""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from shared.schemas.agent import QueryExecutionContext, ExecutionSlots, DataBinding, ToolBinding
from services.orchestrator import spatial_coverage as coverage
from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from services.orchestrator.s101_radius_execution import _execute_stage


def qec(operation='feature_search_by_radius'):
    return QueryExecutionContext(request_id='coverage-fixture', original_query='Find wrecks',
        route_plan={'analysis_type':operation},
        slots=ExecutionSlots(crs='EPSG:4326',reference_geometry='POINT(129 35)',distance_m=1000,target_features=['Wreck']),
        data_bindings=[DataBinding(dataset_id='fixture',relation='fixture.features',snapshot_version='v1')])


def declaration(tmp_path, **changes):
    contract={'approval_status':'APPROVED','source_locator':'fixture-only', 'dataset_id':'fixture',
              'relation':'fixture.features','snapshot_version':'v1','target_features':['Wreck'],'crs':'EPSG:4326',
              'geometry_wkt':'POLYGON((128 34,130 34,130 36,128 36,128 34))'}
    contract.update(changes)
    path=tmp_path/'coverage.json'; path.write_text(json.dumps(contract),encoding='utf-8')
    return {'layers':{'fixture':{'physical_table':'fixture.features','coverage_contract':{
        'path':'coverage.json','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}}


@pytest.mark.parametrize('geometry,expected',[
    ('POINT(129 35)','ADEQUATE'),('POINT(150 0)','OUT_OF_COVERAGE'),('POINT(128 35)','PARTIAL')])
def test_verified_source_scope(tmp_path, geometry, expected):
    request=qec(); request.slots.reference_geometry=geometry
    assert coverage.assess_coverage(request,declaration(tmp_path),root=tmp_path)['status']==expected


@pytest.mark.parametrize('change',[{'snapshot_version':'v2'},{'approval_status':'DRAFT'},
    {'target_features':['Rock']},{'crs':'EPSG:3857'},{'geometry_wkt':'broken'},{'source_locator':None}])
def test_unverified_contract_is_unknown(tmp_path,change):
    assert coverage.assess_coverage(qec(),declaration(tmp_path,**change),root=tmp_path)['status']=='UNKNOWN'


def test_hash_tamper_and_client_flag_are_not_trusted(tmp_path):
    registry=declaration(tmp_path)
    (tmp_path/'coverage.json').write_text('{}')
    request=qec(); request.provenance['coverage_validation']={'status':'ADEQUATE'}
    assert coverage.assess_coverage(request,registry,root=tmp_path)['status']=='UNKNOWN'


def test_nearest_point_coverage_is_insufficient(tmp_path):
    request=qec('nearest_feature');request.slots.distance_m=None
    receipt=coverage.assess_coverage(request,declaration(tmp_path),root=tmp_path)
    assert receipt['status']=='UNKNOWN' and receipt['required'] is True


def adapter(request):
    return SimpleNamespace(layer_registry={},build_bindings=lambda *args:SimpleNamespace(
        data_bindings=request.data_bindings,tool_bindings=[ToolBinding(tool_id='fixture',operation='spatial')],
        blockers=[],warnings=[],inspected_relations={}))


def test_unknown_radius_observation_warns_but_complete_or_nearest_blocks():
    request=qec()
    result=validate_execution_context(request,binding_adapter=adapter(request))
    assert is_execution_authorized(result)
    assert result.provenance['coverage_validation']['status']=='UNKNOWN'
    result.provenance['coverage_validation']['status']='ADEQUATE'
    assert not is_execution_authorized(result)
    request.slots.filters['require_complete_coverage']=True
    assert validate_execution_context(request,binding_adapter=adapter(request)).readiness.value=='BLOCKED_DATA'
    request=qec('nearest_feature');request.slots.distance_m=None
    assert validate_execution_context(request,binding_adapter=adapter(request)).readiness.value=='BLOCKED_DATA'


def test_known_outside_gate_blocks_before_executor(tmp_path, monkeypatch):
    request=qec();request.slots.reference_geometry='POINT(150 0)'
    bound=adapter(request);bound.layer_registry=declaration(tmp_path)
    original=coverage.assess_coverage
    monkeypatch.setattr(coverage,'assess_coverage',lambda q,r:original(q,r,root=tmp_path))
    result=validate_execution_context(request,binding_adapter=bound)
    assert result.readiness.value=='BLOCKED_DATA'
    assert 'BLOCKED_DATA: DATA_OUT_OF_SCOPE' in result.blockers
    assert not is_execution_authorized(result)
    assert result.provenance['coverage_validation']['status']=='OUT_OF_COVERAGE'


def test_statement_failure_has_stage_not_sql_or_secret():
    request=qec(); cursor=Mock(); cursor.execute.side_effect=RuntimeError('SECRET database message')
    with pytest.raises(RuntimeError):
        _execute_stage(cursor,request,'spatial_select','SECRET SQL',{'private':'value'})
    trace=request.provenance['execution_stages'][0]
    assert trace['status']=='FAILED' and trace['stage']=='spatial_select'
    assert trace['elapsed_ms']>=0
    assert 'SECRET' not in json.dumps(trace) and 'private' not in json.dumps(trace)


def test_statement_success_has_completed_receipt():
    request=qec(); cursor=Mock()
    _execute_stage(cursor,request,'feature_code_verification','fixture SQL',(1,))
    cursor.execute.assert_called_once_with('fixture SQL',(1,))
    assert request.provenance['execution_stages'][0]['status']=='COMPLETED'
