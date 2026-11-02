import hashlib
import json
from tools.scie_results_ui.rq1_grounding import METADATA, build_rq1_grounding


def setup(root, labels):
    path = root / METADATA
    path.parent.mkdir(parents=True)
    path.write_text('\n'.join(json.dumps(x) for x in labels), encoding='utf-8')


def annotation(cid, query, terms, complexity=None):
    return dict(case_id=cid, query_sha256=hashlib.sha256(query.encode()).hexdigest(),
                terminology_condition=terms, complexity=complexity or [],
                human_approval=False, post_hoc=True, annotation_status='DRAFT')


def test_conditions_are_hash_bound_overlapping_and_not_approved_gold(tmp_path):
    qs=[dict(case_id='a',query='query',equivalence_group='one'),dict(case_id='b',query='altered')]
    setup(tmp_path,[annotation('a','query',['DOMAIN_KOREAN','COLLOQUIAL'],['COMPOSITE_MULTI_TASK']),
                    annotation('b','old',['OFFICIAL_TERM'])])
    r=build_rq1_grounding(tmp_path,qs,'v6')
    rows={x['condition']:x for x in r['rows']}
    assert rows['DOMAIN_KOREAN']['n']==rows['COLLOQUIAL']['n']==rows['MIXED']['n']==1
    assert rows['OFFICIAL_TERM']['n']==0
    assert r['condition_metadata']['rejected_queries']==[{'case_id':'b','reason':'QUERY_HASH_MISMATCH'}]
    assert rows['MIXED']['label_human_approved_n']==0
    assert rows['MIXED']['cluster_count']==1


def test_no_score_substitution_or_prior_pilot_loading(tmp_path):
    setup(tmp_path,[annotation('a','q',['OFFICIAL_TERM'])])
    p=tmp_path/'research/marine_geollm_scie/runs/v6/report_with_faults/summary.json'
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'machine_contract_pass':1,'semantic_human_accuracy':1,'feature_f1':1,
                             'semantic_f1':1}),encoding='utf-8')
    r=build_rq1_grounding(tmp_path,[{'case_id':'a','query':'q'}],'v6')
    for row in r['rows']:
        assert all(row[k] is None for k in ['b1_semantic_f1','b2_semantic_f1','delta_b2_b1','ci95','strict_match'])
    assert r['selected_report']['candidate_metric_fields']==['semantic_f1']
    assert r['metric_contract']['status']=='NOT_DEFINED_FOR_SELECTED_RUN'


def test_unseen_cannot_be_claimed_from_posthoc_label(tmp_path):
    setup(tmp_path,[annotation('a','q',['UNSEEN_SYNONYM','MIXED_KO_EN'])])
    r=build_rq1_grounding(tmp_path,[{'case_id':'a','query':'q'}],'v6')
    assert all(row['n']==0 for row in r['rows'])
    assert r['condition_metadata']['unseen_labels_not_admitted']==1


def test_duplicate_and_outside_paths_are_not_admitted(tmp_path):
    item=annotation('a','q',['DOMAIN_KOREAN'])
    setup(tmp_path,[item,item])
    r=build_rq1_grounding(tmp_path,[{'case_id':'a','query':'q'}],'../../holdout')
    assert r['condition_metadata']['matched_queries']==0
    assert r['selected_report']['status']=='INVALID_RUN_ID'


def test_absent_artifacts_preserve_unknown_and_zero_is_not_accuracy(tmp_path):
    r=build_rq1_grounding(tmp_path,[{'case_id':'a','query':'q'}],None)
    assert r['condition_metadata']['status']=='UNAVAILABLE'
    assert all(x['b1_semantic_f1'] is None and x['n']==0 for x in r['rows'])
