import copy
import hashlib
import json
import pytest
from research.marine_geollm_scie.runners.score_q4_observations import score, validate_capture


def fixture():
    ref={'snapshot_sha256':'snapshot','anchor':{'longitude':131.8,'latitude':37.2},
        'objects':[{'source_id':'44','distance_postgis_m':100.004}],
        'object_ids':['mof_marine_names_20221231:44']}
    row={'case_id':'PILOT_Q4_01','query':'query','method':'production','repeat':0,'status':'CAPTURED','total_latency_ms':3,
        'final':{'status':'COMPLETED','final_result':{'structured_result':{
            'search_execution':{'status':'COMPLETED','authority':'ExecutionValidator'},
            'features':[{'공간정보일련번호':'44','feature_id':'opaque-production-id','distance_m':100,
                         'provenance':{'source_sha256':'snapshot'}}],
            'total_count':1,'distance_m':5000,'reference_geometry':'POINT(131.8 37.2)'}}}}
    return row,ref


def test_actual_source_id_is_bound_to_fixed_snapshot():
    row,ref=fixture();result=score(row,ref,'oracle')
    assert result['spatial_correct'] is True
    assert result['returned_object_ids']==ref['object_ids']
    assert result['full_success'] is None
    assert result['distance_max_abs_error_m']<.01
    assert result['source_id_mapping'][0]['returned_feature_id']=='opaque-production-id'


def test_unexecuted_empty_is_not_correct_empty():
    row,ref=fixture();s=row['final']['final_result']['structured_result']
    s['search_execution']={'status':'NOT_RUN'};s['features']=[];s['total_count']=0
    result=score(row,ref,'oracle')
    assert result['execution_success'] is False
    assert result['spatial_correct'] is None and result['returned_object_ids'] is None


def test_wrong_source_or_incomplete_result_not_silently_scored():
    row,ref=fixture();s=row['final']['final_result']['structured_result']
    s['features'][0]['provenance']['source_sha256']='other-version'
    assert score(row,ref,'oracle')['spatial_correct'] is None
    row,ref=fixture();row['final']['final_result']['structured_result']['total_count']=2
    result=score(row,ref,'oracle')
    assert result['spatial_correct'] is None and 'INCOMPLETE_RETURNED_OBJECT_SET' in result['binding_errors']


@pytest.mark.parametrize('status,graph_status',[('TRANSPORT_ERROR','COMPLETED'),('OBSERVATION_TIMEOUT','COMPLETED'),('CAPTURED','RUNNING')])
def test_stale_completed_search_is_not_execution_success(status,graph_status):
    row,ref=fixture();row['status']=status;row['final']['status']=graph_status
    result=score(row,ref,'oracle')
    assert result['execution_success'] is None and result['spatial_correct'] is None


def test_distance_accuracy_is_separate_from_object_set():
    row,ref=fixture()
    row['final']['final_result']['structured_result']['features'][0]['distance_m']=120
    result=score(row,ref,'oracle')
    assert result['spatial_correct'] is True and result['distance_correct'] is False
    assert result['distance_evaluated_object_count']==1
    row['final']['final_result']['structured_result']['features'][0]['distance_m']=None
    assert score(row,ref,'oracle')['distance_correct'] is None


def capture_fixture(tmp_path):
    raw_path=tmp_path/'api_rows.jsonl';benchmark=tmp_path/'benchmark.jsonl'
    raw=[{'case_id':'case','query':'original'}]
    raw_path.write_text(json.dumps(raw[0])+'\n',encoding='utf-8')
    benchmark.write_text(json.dumps(raw[0])+'\n',encoding='utf-8')
    manifest={'rows_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
              'benchmark_sha256':hashlib.sha256(benchmark.read_bytes()).hexdigest()}
    return raw_path,benchmark,raw,manifest


def test_capture_hashes_original_queries_and_optional_stability(tmp_path):
    raw_path,benchmark,raw,manifest=capture_fixture(tmp_path)
    def save(): (tmp_path/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    save()
    assert validate_capture(raw_path,raw,benchmark)=='UNVERIFIED_NOT_CAPTURED'
    manifest.update(production_source_hashes_before={'a':'hash'},production_source_hashes_after={'a':'hash'});save()
    assert validate_capture(raw_path,raw,benchmark)=='CAPTURE_BEFORE_AFTER_MATCH'
    manifest['production_source_hashes_after']={'a':'changed'};save()
    with pytest.raises(ValueError,match='Production sources'):validate_capture(raw_path,raw,benchmark)
    manifest['production_source_hashes_after']={'a':'hash'};save()
    raw[0]['query']='replacement'
    with pytest.raises(ValueError,match='case/query'):validate_capture(raw_path,raw,benchmark)


@pytest.mark.parametrize('which',['rows_sha256','benchmark_sha256'])
def test_reject_changed_capture_bytes(tmp_path,which):
    raw_path,benchmark,raw,manifest=capture_fixture(tmp_path)
    manifest[which]='wrong'
    (tmp_path/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):validate_capture(raw_path,raw,benchmark)
