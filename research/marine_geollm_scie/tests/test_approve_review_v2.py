import copy
import json
from pathlib import Path

import pytest

from research.marine_geollm_scie.runners.approve_review_v2 import approve, explicit_slots, sha, verified_spatial


def fixture_inputs(tmp_path):
    rows=[{'case_id':f'c{i}','query':f'query{i}','annotation_status':'DRAFT','human_approval':False,
           'resolution':'조건부 후보 Wreck; 필수 정답집합 아님', 'evidence':'source text',
           'reviewer_A':{'필요 QEC 필드':'distance_m=5000; reference_geometry=REQUIRED; candidate_features=[Wreck]',
                         '기대 실행 행동':'조건부 실행'}, 'source_sha256':'workbook','source_locator':'A1'} for i in range(18)]
    source=tmp_path/'annotations_DRAFT.jsonl'
    source.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    (tmp_path/'manifest.json').write_text(json.dumps({'annotations_sha256':sha(source),'sources':[]}),encoding='utf-8')
    benchmark=tmp_path/'cases.jsonl'
    benchmark.write_text(''.join(json.dumps({'case_id':r['case_id'],'query':r['query'],'category':'Q4','equivalence_group':r['case_id']})+'\n' for r in rows),encoding='utf-8')
    return source,benchmark


def test_only_literal_slots_not_unknowns_or_candidates():
    assert explicit_slots('location=독도; distance_m=5000; reference_geometry=null; targets=[Wreck]; analysis_type=x')=={'slots.location_text':'독도','slots.distance_m':5000}


def test_user_approval_versions_without_reinterpreting(tmp_path):
    source,benchmark=fixture_inputs(tmp_path);before=source.read_bytes()
    event={'explicit_user_approval':True,'verbatim_user_request':'승인','event_timestamp':None}
    manifest=approve(source,benchmark,event,tmp_path/'v3')
    rows=[json.loads(x) for x in (tmp_path/'v3/evaluation_references.jsonl').read_text(encoding='utf-8').splitlines()]
    assert source.read_bytes()==before and len(rows)==18
    assert all(r['human_approval'] and r['annotation_status']=='GOLD' for r in rows)
    assert all(not r['independent_expert_review'] and not r['two_reviewers'] for r in rows)
    assert all(r['semantics']['labels'] is None and r['spatial'] is None for r in rows)
    assert all(r['approved_source_record']['human_approval'] is False for r in rows)
    assert manifest['event_timestamp_provided'] is False
    with pytest.raises(FileExistsError):approve(source,benchmark,event,tmp_path/'v3')


def test_missing_user_event_and_changed_source_rejected(tmp_path):
    source,benchmark=fixture_inputs(tmp_path)
    with pytest.raises(ValueError,match='Explicit'):approve(source,benchmark,{},tmp_path/'v3')
    source.write_text(source.read_text()+'\n',encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):
        approve(source,benchmark,{'explicit_user_approval':True,'verbatim_user_request':'승인'},tmp_path/'v3')


def test_oracle_hash_and_equivalence_checks(tmp_path):
    results=tmp_path/'oracle.jsonl'
    rows=[{'case_id':f'PILOT_Q4_0{i}','object_ids':['source:1'],'status':'VERIFIED'} for i in (1,2,3)]
    results.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    manifest=tmp_path/'manifest_oracle.json'
    manifest.write_text(json.dumps({'status':'VERIFIED','results_path':results.name,'results_sha256':sha(results),
                                   'dataset_snapshot_sha256':'source','reference_geometry_source':'approved anchor'}),encoding='utf-8')
    assert len(verified_spatial(manifest)[0])==3
    results.write_text(results.read_text()+'\n',encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):verified_spatial(manifest)


def test_actual_csv_oracle_rejects_nonfinite_distances(tmp_path):
    from research.marine_geollm_scie.runners.approve_review_v2 import computed_csv_spatial
    source=tmp_path/'source.csv';source.write_text('id\n1\n',encoding='utf-8')
    sql=tmp_path/'reference.sql';sql.write_text('SELECT 1;',encoding='utf-8')
    distances=tmp_path/'all_distances.jsonl'
    row={'object_id':'source:1','distance_vincenty_m':1.0,'distance_postgis_m':1.0}
    distances.write_text(json.dumps(row)+'\n',encoding='utf-8')
    path=tmp_path/'spatial_reference.json';path.write_text('{}',encoding='utf-8')
    anchor=Path(__file__).resolve().parents[3]/'data/public_place_anchors.json'
    manifest={'case_ids':['PILOT_Q4_01','PILOT_Q4_02','PILOT_Q4_03'],
              'user_scope_approval':'동도 기준점·2022 CSV로 고정','source_snapshot':{'path':str(source),'sha256':sha(source),'row_count':1},
              'snapshot_sha256':sha(source),'reference_query':str(sql),'reference_query_sha256':sha(sql),
              'anchor_source_sha256':sha(anchor),'parsed_rows':1,'parse_errors':[], 'radius_m':5000,
              'reference_crs':'EPSG:4326','object_ids':['source:1'],'objects':[row],
              'anchor':{},'distance_policy':'fixture','crs_policy':'fixture','scope':'fixture'}
    assert len(computed_csv_spatial(path,manifest)[0])==3
    row['distance_vincenty_m']=float('nan')
    distances.write_text(json.dumps(row)+'\n',encoding='utf-8')
    with pytest.raises(ValueError,match='distance verification'):computed_csv_spatial(path,manifest)
