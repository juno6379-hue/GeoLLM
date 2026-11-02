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


@pytest.mark.parametrize('operation', sorted(coverage.SPATIAL_OPERATIONS - {'source_attribute_search'}))
@pytest.mark.parametrize('client_required', [None, False, True])
def test_unknown_spatial_scope_blocks_independently_of_client_flag(operation, client_required):
    request=qec(operation)
    if client_required is not None:
        request.slots.filters['require_complete_coverage']=client_required
    request.provenance['coverage_validation']={'status':'ADEQUATE','required':False}
    result=validate_execution_context(request,binding_adapter=adapter(request))
    assert result.readiness.value=='BLOCKED_DATA'
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in result.blockers
    assert not is_execution_authorized(result)
    assert result.provenance['coverage_validation']['required'] is True


def test_missing_selected_geometry_still_requests_input():
    request=qec('feature_search_by_area'); request.slots.reference_geometry=None
    result=validate_execution_context(request,binding_adapter=adapter(request))
    assert result.readiness.value=='NEEDS_USER_INPUT'
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' not in result.blockers


def test_verified_scope_authorizes_and_receipt_tamper_revokes(tmp_path, monkeypatch):
    request=qec(); bound=adapter(request); bound.layer_registry=declaration(tmp_path)
    original=coverage.assess_coverage
    monkeypatch.setattr(coverage,'assess_coverage',lambda q,r:original(q,r,root=tmp_path))
    result=validate_execution_context(request,binding_adapter=bound)
    assert is_execution_authorized(result)
    result.provenance['coverage_validation']['required']=False
    assert not is_execution_authorized(result)


@pytest.mark.parametrize('operation',['document_search','place_lookup','selected_feature_lookup'])
def test_non_spatial_lookup_does_not_acquire_scope_requirement(operation):
    assert coverage.assess_coverage(qec(operation),{})['required'] is False


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


@pytest.mark.parametrize('area', [False, True])
def test_unknown_scope_denies_before_spatial_tool_dispatch(monkeypatch, area):
    from services.orchestrator import s101_radius_execution as radius
    request=qec('feature_search_by_area' if area else 'feature_search_by_radius')
    request.slots.reference_geometry='POINT(131.87 37.24)'
    bound=adapter(request)
    monkeypatch.setattr(radius,'SchemaBindingAdapter',lambda **kwargs:bound)
    monkeypatch.setattr(radius,'prepare_radius_request',lambda state:(request,{}, {}, {}))
    monkeypatch.setattr(radius,'prepare_bounds_request',lambda state:(request,{}, {}))
    fetch=Mock(side_effect=AssertionError('spatial tool must not be dispatched'))
    monkeypatch.setattr(radius,'_fetch_result',fetch)
    monkeypatch.setattr(radius,'_fetch_bounds_result',fetch)
    spatial={'map_bounds':[131,37,132,38]} if area else {}
    result=radius.execute_radius_request({'task_id':'scope-negative','query':'Find wrecks within 5km','spatial_context':spatial})
    fetch.assert_not_called()
    assert result['status']=='BLOCKED'
    assert result['error_code']=='DATA_COVERAGE_UNVERIFIED'
    assert result['structured_result']['count'] is None
    assert '실행하지 않았습니다' in result['answer_text']
    provenance=result['orchestrator_v2']['query_execution_context']['provenance']
    assert provenance['coverage_validation']['required'] is True
    assert provenance['spatial_preflight']=={
        'status':'BLOCKED_BEFORE_DISPATCH','scope':'target_spatial_query',
        'execution_attempted':False,'execution_started':False,'tool_called':False,'sql_executed':False}


def test_direct_radius_executor_denies_before_spatial_select(monkeypatch):
    from unittest.mock import MagicMock
    from services.orchestrator import s101_radius_execution as radius
    request=qec()
    connection=MagicMock(); connection.__enter__.return_value=connection
    monkeypatch.setenv('S101_DB_URL','fixture-only')
    monkeypatch.setattr(radius.psycopg2,'connect',lambda *args,**kwargs:connection)
    monkeypatch.setattr(radius,'SchemaBindingAdapter',lambda **kwargs:adapter(request))
    with pytest.raises(radius.RadiusProblem) as exc:
        radius._fetch_result(request,{}, {}, {})
    assert exc.value.code=='DATA_COVERAGE_UNVERIFIED'
    connection.cursor.assert_not_called()
    assert [stage['stage'] for stage in request.provenance['execution_stages']]==['execution_validation']


@pytest.mark.parametrize('crs',[None,'EPSG:3857'])
def test_unusable_coverage_crs_cannot_authorize(crs):
    request=qec();request.slots.crs=crs
    result=validate_execution_context(request,binding_adapter=adapter(request))
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in result.blockers


def test_out_of_range_geographic_coordinate_cannot_authorize():
    request=qec();request.slots.reference_geometry='POINT(999 999)'
    result=validate_execution_context(request,binding_adapter=adapter(request))
    assert not is_execution_authorized(result)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in result.blockers


@pytest.mark.parametrize('code',['DATA_COVERAGE_UNVERIFIED','DATA_OUT_OF_SCOPE'])
def test_generic_gate_explains_coverage_denial_without_zero_claim(code):
    from services.orchestrator.execution_validator import execution_gate_failure
    from shared.schemas.agent import PlanStatus
    request=qec('feature_dwithin')
    request.readiness=PlanStatus.BLOCKED_DATA
    request.blockers=['BLOCKED_DATA: '+code]
    final=execution_gate_failure({'task_id':'denied','query':'독도 주변 지명'},request)['final_dict']
    assert final['error_code']==code
    assert '공간 검색을 실행하지 않았습니다' in final['answer_text']
    assert '0건이라는 뜻은 아닙니다' in final['answer_text']
    assert final['structured_result']['search_execution']=={'status':'NOT_RUN','reason':code}
    assert final['structured_result']['count'] is None
    assert final['orchestrator_v2']['query_execution_context']['blockers']==request.blockers
