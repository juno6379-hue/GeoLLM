"""Finite source permission requires pinned inventory and declared scope."""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.orchestrator.s101_corpus import verify_s101_corpus, inventory_digest, FIELDS
from services.orchestrator.spatial_coverage import assess_source_corpus
from shared.schemas.agent import DataBinding, ExecutionSlots, QueryExecutionContext


def request(query='기준점에서 반경 1000m 이내 Wreck를 찾아줘'):
    return QueryExecutionContext(original_query=query,
        route_plan={'analysis_type': 'feature_search_by_radius'},
        slots=ExecutionSlots(crs='EPSG:4326', reference_geometry='POINT(129.05 35.1)',
                             distance_m=1000, target_features=['Wreck']),
        data_bindings=[DataBinding(dataset_id='GBENC_S101_feature',
            relation='projection.s101_feature_current', geometry_column='geometry', srid=4326)])


def fixture(tmp_path):
    rows=[dict(feature_instance_id='1',dataset_id='cell1',dataset_version_id='v1',
               feature_type_name='Wreck',attributes={'name':'source wreck'},geometry_identity='0101000020e6100000')]
    scope=dict(kind='SOURCE_DECLARED_DATA_COVERAGE',crs='EPSG:4326',source_locator='fixture-only DataCoverage object dc1',
               geometry_wkt='POLYGON((129 35,129.2 35,129.2 35.2,129 35.2,129 35))')
    source=dict(schema_version='s101_exact_inventory_v1',dataset_id='GBENC_S101_feature',
                relation='projection.s101_feature_current',rows=rows,source_scope=scope,
                snapshot_version='sha256:'+inventory_digest(rows))
    path=tmp_path/'data/source_inventory/fixture.json';path.parent.mkdir(parents=True)
    raw=json.dumps(source).encode();path.write_bytes(raw)
    contract=dict(kind='s101_exact_inventory_v1',source_asset='data/source_inventory/fixture.json',
                  source_sha256=hashlib.sha256(raw).hexdigest(),snapshot_version=source['snapshot_version'],
                  allowed_operations=['feature_search_by_radius'],target_features=['Wreck'],
                  default_inventory_listing=True)
    registry={'layers':{'GBENC_S101_feature':dict(physical_table=source['relation'],
                  geometry_column='geometry',corpus_contract=contract)}}
    cursor=Mock();cursor.description=[(name,) for name in (*FIELDS,'geometry_valid')]
    cursor.fetchall.return_value=[{**rows[0],'geometry_valid':True}]
    return contract,registry,cursor,path


def test_verified_inventory_is_not_geographic_approval(tmp_path):
    contract,registry,cur,_=fixture(tmp_path);qec=request()
    verifier=lambda binding,c: verify_s101_corpus(cur,binding,c,root=tmp_path)
    result=assess_source_corpus(qec,registry,verifier)
    assert result['status']=='CORPUS_VERIFIED'
    assert result['absence_certified'] is False
    assert result['geographic_coverage']=='UNKNOWN'
    assert result['query_scope']=='SOURCE_CORPUS'


@pytest.mark.parametrize('query', ['모든 Wreck를 찾아줘','가장 가까운 Wreck를 찾아줘',
                                  'Find all wrecks','Find real-world wrecks'])
def test_default_inventory_cannot_narrow_complete_requests(tmp_path,query):
    _,registry,_,_=fixture(tmp_path);verifier=Mock()
    assert assess_source_corpus(request(query),registry,verifier) is None
    verifier.assert_not_called()


@pytest.mark.parametrize('change',['outside','partial','unknown_kind','invalid_polygon','unbound_source',
                                  'snapshot','missing_feature','no_default','missing_scope','scope_crs','scope_world'])
def test_no_permission_without_scope_and_identity(tmp_path,change):
    contract,registry,cur,_=fixture(tmp_path);qec=request()
    observed=verify_s101_corpus(cur,qec.data_bindings[0],contract,root=tmp_path)
    if change=='outside':qec.slots.reference_geometry='POINT(131.87 37.24)'
    elif change=='partial':qec.slots.reference_geometry='POINT(129.199 35.1)'
    elif change=='unknown_kind':observed['source_scope']['kind']='OBJECT_EXTENT'
    elif change=='invalid_polygon':observed['source_scope']['geometry_wkt']='POINT(129.05 35.1)'
    elif change=='unbound_source':observed['source_scope']['source_sha256']='a'*64
    elif change=='snapshot':observed['snapshot_version']='sha256:'+'a'*64
    elif change=='missing_feature':observed['target_features']=[]
    elif change=='no_default':contract['default_inventory_listing']=False
    elif change=='scope_crs':observed['source_scope']['crs']='EPSG:3857'
    elif change=='scope_world':observed['source_scope']['geometry_wkt']='POLYGON((-200 -90,200 -90,200 90,-200 90,-200 -90))'
    else:observed.pop('source_scope')
    receipt = assess_source_corpus(qec,registry,Mock(return_value=observed))
    if change in ('outside', 'partial'):
        assert receipt['status'] == ('OUT_OF_COVERAGE' if change == 'outside' else 'PARTIAL')
        assert receipt['source_corpus_status'] == 'VERIFIED'
        assert receipt['geographic_coverage_status'] == ('SOURCE_DECLARED_DOMAIN_OUTSIDE' if change == 'outside' else 'SOURCE_DECLARED_DOMAIN_PARTIAL')
        assert receipt['real_world_completeness'] == 'UNKNOWN'
        assert receipt['absence_certified'] is False
        assert receipt['sources'][0]['status'] == 'VERIFIED'
    else:
        assert receipt is None


@pytest.mark.parametrize('change',['changed_bytes','path_escape','live_attribute','live_membership',
                                  'invalid_geometry','missing_snapshot','missing_target'])
def test_source_verifier_fails_closed(tmp_path,change):
    contract,_,cur,path=fixture(tmp_path);qec=request()
    if change=='changed_bytes':path.write_text('{}')
    elif change=='path_escape':contract['source_asset']='../../outside.json'
    elif change=='live_attribute':cur.fetchall.return_value[0]['attributes']={}
    elif change=='live_membership':cur.fetchall.return_value=[]
    elif change=='invalid_geometry':cur.fetchall.return_value[0]['geometry_valid']=False
    elif change=='missing_snapshot':contract.pop('snapshot_version')
    else:contract['target_features']=['Obstruction']
    assert verify_s101_corpus(cur,qec.data_bindings[0],contract,root=tmp_path)['status']=='UNVERIFIED'


def test_unregistered_s101_remains_blocked(tmp_path):
    _,registry,_,_=fixture(tmp_path);registry['layers']['GBENC_S101_feature'].pop('corpus_contract')
    verifier=Mock()
    assert assess_source_corpus(request(),registry,verifier) is None
    verifier.assert_not_called()


@pytest.mark.parametrize('total',[0,2])
def test_source_count_is_not_world_absence_on_all_result_surfaces(total):
    from services.orchestrator.s101_radius_execution import _qualify_unverified_empty
    qec=request();qec.provenance['coverage_validation']={
        'authority':'ServerSourceCoverage','sources':[{'status':'VERIFIED'}],
        'status':'CORPUS_VERIFIED','query_scope':'SOURCE_CORPUS','absence_certified':False}
    result=dict(status='COMPLETED',summary=f'{total}건',structured_result={'total_count':total},
                spatial_result_summary={'total_count':total},map_layers=[{'metadata':{}}],
                evidence_bundle={'spatial_layer_evidence':[{'data':{}}]},claims=[{}],task_results=[{}])
    result=_qualify_unverified_empty(result,total,qec)
    assert result['status']=='COMPLETED'
    assert result['structured_result']['total_count']==total
    assert '실제 해역의 전체 객체나 부재를 보증하지 않습니다' in result['summary']
    for surface in [result['structured_result'], result['spatial_result_summary'],
                    result['map_layers'][0]['metadata'],result['evidence_bundle']['spatial_layer_evidence'][0]['data']]:
        assert surface['count_scope']=='SOURCE_CORPUS_MATCHED_ROWS'
        assert surface['absence_confirmed'] is False


def test_final_radius_wrapper_preserves_source_scope(monkeypatch):
    from services.orchestrator import s101_radius_execution as module
    qec=request();qec.slots.location_text='부산 기준점'
    qec.provenance['coverage_validation']={
        'authority':'ServerSourceCoverage','sources':[{'status':'VERIFIED'}],
        'status':'CORPUS_VERIFIED','query_scope':'SOURCE_CORPUS','absence_certified':False}
    monkeypatch.setattr(module,'prepare_radius_request',lambda state:(qec,{}, {}, {}))
    monkeypatch.setattr(module,'_preflight_spatial_scope',lambda *a:None)
    monkeypatch.setattr(module,'_fetch_result',lambda *a:(2,{},[],None))
    monkeypatch.setattr(module,'build_result',lambda *a:dict(status='COMPLETED',summary='old',
        structured_result={'total_count':2,'returned_count':2},claims=[{}]))
    result=module.execute_radius_request({'task_id':'fixture','spatial_context':{}})
    assert '검증된 S-101 원천 목록' in result['answer_text']
    assert '부재를 보증하지 않습니다' in result['claims'][0]['text']
    assert result['structured_result']['query_scope']=='SOURCE_CORPUS'


def test_malformed_corpus_receipt_does_not_bypass_empty_qualification():
    from services.orchestrator.s101_radius_execution import _qualify_unverified_empty
    qec=request();qec.provenance['coverage_validation']={'status':'CORPUS_VERIFIED'}
    result=_qualify_unverified_empty(dict(status='COMPLETED',structured_result={'total_count':0}),0,qec)
    assert result['status']=='PARTIAL'
    assert result['structured_result']['absence_confirmed'] is False
    assert result['structured_result']['total_count'] is None
