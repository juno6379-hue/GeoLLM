import hashlib
import json
from pathlib import Path

from tools.scie_results_ui.adapter import GOLD, RESEARCH, ResultsAdapter


def put(root, name, obj):
    path = root / RESEARCH / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding='utf-8')
    return path


def fixture(root):
    v5 = '20261101_gold_v2_eight_k1_v5'
    v6 = '20261102_gold_v2_eight_k1_v6'
    put(root, 'RESULTS_INDEX_KR.md', f'| 실행 중 v6 | runs/{v6}/status.json |\n| 최신 완료 v5 | runs/{v5}/report_with_faults/comparison_KR.md |')
    put(root, GOLD + '/manifest.json', {'case_count': 1, 'methods':['B3','B4','P0','H'], 'independent_expert_review_complete':False})
    put(root, GOLD + '/comparison_protocol.json', {'approved_scope_partition': {'out_of_coverage_safe_abstention':['PILOT_Q3_01']}})
    put(root, GOLD + '/answer_contracts.jsonl', json.dumps({'case_id':'PILOT_Q3_01','category':'Q3','holdout_eligible':False,'independent_expert_review':False,'spatial_object_scoring_enabled':False})+'\n')
    for rid in (v5,v6):
        put(root, f'runs/{rid}/status.json', {'status':'COMPLETED_OBSERVATIONS','repeats':1})
        put(root, f'runs/{rid}/report_with_faults/summary.json', {'observed_rows':4,'scientific_completion':False,'completion_gate':{'observation_comparison_complete':True}, 'overall_by_method':{'B3':{'semantic_human_accuracy':None,'safe_abstention':{'value':None,'denominator':1},'spatial_eligible_case_ids':[]}}})
    put(root, f'runs/{v5}/comparison/observations.jsonl', '\n'.join(json.dumps({'case_id':'PILOT_Q3_01','method':m,'initial_plan_hash':'same','review_artifact_sha256':'review' if m in ('B4','H') else None}) for m in ('B3','B4','P0','H'))+'\n')
    return v5, v6


def test_precedence_even_when_new_run_finishes(tmp_path):
    v5,v6=fixture(tmp_path)
    put(tmp_path,'results/latest/summary.json',{'observed_rows':999})
    result=ResultsAdapter(tmp_path).dashboard()
    assert result['overview']['selected_run_id']==v5
    assert result['overview']['latest_run_id']==v6
    assert result['overview']['observed_rows']==4
    assert all('results/latest' not in s['source_path'] for s in result['sources'])


def test_null_gold_and_abstention_preserved(tmp_path):
    fixture(tmp_path)
    x=ResultsAdapter(tmp_path).dashboard()
    assert x['overview']['independent_expert_review_complete'] is False
    assert x['methods'][0]['metrics']['semantic_human_accuracy'] is None
    assert x['rq']['3']['overall_by_method']['B3']['safe_abstention']['value'] is None
    assert x['rq']['3']['overall_by_method']['B3']['spatial_eligible_case_ids']==[]
    assert x['benchmark']['cases'][0]['safe_abstention_expected'] is True


def test_shared_hashes_are_artifact_values(tmp_path):
    fixture(tmp_path)
    x=ResultsAdapter(tmp_path).dashboard()
    rows=x['benchmark']['cases'][0]['results']
    assert {r['initial_plan_hash'] for r in rows}=={'same'}
    assert {r['review_artifact_sha256'] for r in rows if r['method'] in ('B4','H')}=={'review'}


def test_missing_artifacts_are_not_zero(tmp_path):
    x=ResultsAdapter(tmp_path).dashboard()
    assert x['overview']['holdout_count'] is None
    assert x['overview']['observed_rows'] is None
    assert x['overview']['case_count'] is None
    assert x['status']=='UNAVAILABLE_LOCAL_ARTIFACT'


def test_provenance_hash_and_allowlist(tmp_path):
    fixture(tmp_path)
    adapter=ResultsAdapter(tmp_path)
    x=adapter.dashboard()
    source=next(s for s in x['sources'] if s['source_path'].endswith('RESULTS_INDEX_KR.md'))
    assert source['source_sha256']==hashlib.sha256((tmp_path/source['source_path']).read_bytes()).hexdigest()
    assert '../secret' not in adapter.allowed
    assert all(p.resolve().is_relative_to((tmp_path/RESEARCH).resolve()) for p in adapter.allowed.values())


def test_stopped_run_never_complete(tmp_path):
    v5,_=fixture(tmp_path)
    put(tmp_path,f'runs/{v5}/status.json',{'status':'STOPPED_REQUIRES_REVIEW'})
    x=ResultsAdapter(tmp_path).dashboard()
    assert x['overview']['status']!='OBSERVATION_COMPLETE'
    assert not next(r for r in x['runs'] if r['run_id']==v5)['can_be_cited']


def test_partial_jsonl_preserves_complete_records(tmp_path):
    put(tmp_path,'partial.jsonl','{"case_id":"a"}\n{"case_id":')
    adapter=ResultsAdapter(tmp_path)
    assert adapter.load('partial.jsonl')==[{'case_id':'a'}]
    assert next(iter(adapter.sources.values()))['status']=='PARTIAL'


def test_spatial_gold_not_legacy_scoring_flag(tmp_path):
    fixture(tmp_path)
    rows=[{'case_id':'PILOT_Q3_02','category':'Q3','spatial_object_scoring_enabled':False,
           'spatial_correctness_applicable':True,'spatial_gold':{'AnchorageArea':{'object_ids':[],'source_snapshot_sha256':'hash'}}},
          {'case_id':'PILOT_Q4_01','category':'Q4','spatial_object_scoring_enabled':True,
           'equivalence_group':'dokdo_radius_5km','spatial_reference':{'object_ids':['original:1']}}]
    put(tmp_path,GOLD+'/answer_contracts.jsonl','\n'.join(json.dumps(r) for r in rows)+'\n')
    cases=ResultsAdapter(tmp_path).dashboard()['benchmark']['cases']
    assert cases[0]['spatial_gold_available'] is True
    assert cases[0]['spatial_object_scoring_enabled'] is False
    assert cases[0]['spatial_gold_summary']['AnchorageArea']['object_count']==0
    assert cases[1]['evaluation_stratum']=='SOURCE_BOUND_CORPUS_SPATIAL'
    assert cases[1]['equivalence_group']=='dokdo_radius_5km'
