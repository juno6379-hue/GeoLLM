"""Explicit fixture rows, not geographic GOLD or live database coverage."""
import copy
import pytest
from services.orchestrator import s101_radius_execution as radius
from shared.schemas.agent import QueryExecutionContext, ExecutionSlots, DataBinding


def fixture(total=0):
    qec = QueryExecutionContext(request_id='empty-audit', plan_hash='a'*64,
        original_query='Find wrecks within 1000 m',
        slots=ExecutionSlots(location_text='explicit point', reference_geometry='POINT(129 35)', crs='EPSG:4326', distance_m=1000, target_features=['Wreck']),
        route_plan={'radius_template_id':'feature_search_by_radius'},
        data_bindings=[DataBinding(dataset_id='fixture', relation='fixture.features')],
        provenance={'location_resolution':{}})
    layer={'physical_table':'fixture.features'}
    params={'offset':0,'result_limit':30,'feature_codes':[101]}
    rows=[] if not total else [{'id':1,'geometry':{'type':'Point','coordinates':[129,35]},'feature_type_name':'Wreck','feature_type_code':101,'source_dataset_id':1,'dataset_version_id':1,'distance_m':0}]
    return qec,layer,params,total,{'Wreck':total} if total else {},rows,None


@pytest.mark.parametrize('builder',[radius.build_result,radius.build_bounds_result])
def test_empty_snapshot_does_not_prove_real_world_absence(builder):
    result=builder(*fixture())
    payload=result['structured_result']
    assert result['status']=='PARTIAL'
    assert payload['status']=='NO_EVIDENCE'
    assert payload['count'] is None and payload['total_count'] is None
    assert payload['observed_count']==payload['observed_total_count']==0
    assert payload['returned_count']==0
    assert payload['coverage_status']=='UNKNOWN'
    assert payload['query_execution_succeeded'] is True
    assert result['task_results'][0]['status']=='NO_EVIDENCE'
    assert result['claims'][0]['text']==result['answer_text']
    assert result['spatial_result_summary']['observed_total_count']==0
    assert result['map_layers'][0]['metadata']['observed_total_count']==0


@pytest.mark.parametrize('flag',['VERIFIED','ADEQUATE','OUT_OF_COVERAGE'])
def test_caller_or_stale_coverage_flag_is_not_authoritative(flag):
    args=fixture()
    args[0].provenance['coverage_validation']={'status':flag,'verified':True}
    args[0].spatial['coverage_status']=flag
    assert radius.build_result(*args)['structured_result']['coverage_status']=='UNKNOWN'


def test_positive_snapshot_observation_is_unchanged():
    result=radius.build_result(*fixture(1))
    assert result['status']=='COMPLETED'
    assert result['structured_result']['total_count']==1
    assert result['structured_result']['status']=='SUCCESS'


def test_execute_wrapper_preserves_empty_limitation(monkeypatch):
    # Isolate post-dispatch rendering; real scope denial is tested separately.
    monkeypatch.setattr(radius, "_preflight_spatial_scope", lambda qec: None)
    qec,layer,params,total,counts,rows,geometry=fixture()
    monkeypatch.setattr(radius,'prepare_radius_request',lambda state:(qec,layer,{},params))
    monkeypatch.setattr(radius,'_fetch_result',lambda *args:(total,counts,rows,geometry))
    result=radius.execute_radius_request({'task_id':'empty-audit','query':'wrecks'})
    assert result['status']=='PARTIAL'
    assert 'None' not in result['summary']
    assert result['summary']==result['claims'][0]['text']
