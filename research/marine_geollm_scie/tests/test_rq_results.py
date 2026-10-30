import json
from research.marine_geollm_scie.runners.rq_results import tables_for,load_references
from research.marine_geollm_scie.evaluation.rq_metrics import approved,derive


def test_scope_and_conditions_are_not_pooled_or_imputed():
    rows=[{'cohort':'PLAN_ONLY','method':'B0','case_id':'a','latency_ms':10,'schema_valid':True},
          {'cohort':'GRAPH_SMOKE','method':'GRAPH','case_id':'a','status':'GRAPH_RETURNED','latency_ms':20}]
    metadata={'a':{'terminology_condition':['COLLOQUIAL','DOMAIN_KOREAN'],'information_availability':[]}}
    tables=tables_for(rows,metadata,{})
    assert len(tables['RQ5_reliability_cost'])==2
    graph=next(r for r in tables['RQ3_execution_spatial_gap'] if r['method']=='GRAPH')
    assert graph['operational_execution_true']==0 and graph['ESR'] is None
    assert all(r['semantic_f1'] is None for r in tables['RQ1_condition_effectiveness'])
    assert any(r['axis']=='information_availability' and r['condition']=='UNMEASURED' for r in tables['RQ1_condition_effectiveness'])


def test_user_approval_is_internal_reference_not_expert_gold(tmp_path):
    row={'case_id':'a','annotation_status':'GOLD','human_approval':True,'adjudication_status':'APPROVED',
        'annotator_ids':['AI_SYNTHESIS','USER_APPROVAL'],'review_kind':'USER_APPROVED_AI_ASSISTED','independent_expert_review':False,
        'semantics':{'labels':None},'qec_fields':{'slots.distance_m':5000}}
    path=tmp_path/'reference.jsonl';path.write_text(json.dumps(row)+'\n')
    ref=load_references(path)['a']
    assert approved(ref)
    score=derive({'full_qec':{'slots':{'distance_m':5000}}},ref)
    assert score['qec_field_accuracy']==1 and score['plan_valid'] is None
    assert score['semantic_correct'] is None and score['full_success'] is None


def test_spatial_reference_snapshot_mismatch_is_unmeasured():
    ref={'annotation_status':'GOLD','human_approval':True,'adjudication_status':'APPROVED','annotator_ids':['expert'],
        'gold_sha256':'fixture','spatial':{'object_ids':[],'dataset_snapshot_sha256':'a','oracle_sha256':'oracle'}}
    assert derive({'returned_object_ids':[],'snapshot_sha256':'b'},ref)['spatial_correct'] is None
