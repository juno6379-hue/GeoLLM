import json
import pytest
from research.marine_geollm_scie.evaluation.metrics import (is_gold, object_sets, distance_error,
    validator_metrics, evqsr, distribution, semantic_metrics, COMPONENTS)
from research.marine_geollm_scie.evaluation.statistics import paired_bootstrap, mcnemar_exact
from research.marine_geollm_scie.reporting.build_tables import report, NAMES


GOLD = {'review_status':'GOLD','annotator_ids':['expert-a','expert-b'],'adjudication_status':'APPROVED'}


def test_gold_requires_human_provenance():
    assert not is_gold({'review_status':'GOLD'})
    assert not is_gold({**GOLD,'adjudication_status':'PENDING'})
    assert is_gold(GOLD)
    assert not is_gold({**GOLD,'review_kind':'AI_PRE_REVIEW'})
    assert not is_gold({**GOLD,'human_approval':False})


def test_missing_is_not_empty_or_zero():
    assert object_sets(None,[])['f1'] is None
    assert object_sets([],[])['f1'] == 1
    assert object_sets(['a'],[])['f1'] == 0
    assert object_sets(['a','b'],['b','c'])['f1'] == .5
    assert distance_error(0,0,.1)['relative_error'] is None
    assert distance_error(1,None,.1)['within_tolerance'] is None


def test_invalid_is_positive_and_missing_does_not_disappear():
    rows=[{**GOLD,'expected_invalid':a,'predicted_invalid':b} for a,b in
          [(True,True),(True,False),(False,True),(False,False)]]
    result=validator_metrics(rows)
    assert [result[k] for k in ('TP','FP','FN','TN')] == [1,1,1,1]
    assert result['false_ready_rate']==.5
    assert result['false_block_rate']==.5
    rows.append({**GOLD,'expected_invalid':True,'predicted_invalid':None})
    assert validator_metrics(rows)['f1'] is None
    assert validator_metrics([{'expected_invalid':True,'predicted_invalid':True}])['f1'] is None


def test_evqsr_joint_success_and_missing():
    good={**GOLD,'expected_behavior':'EXECUTE',**dict.fromkeys(COMPONENTS,True)}
    bad={**good,'spatial_correct':False}
    assert evqsr([good,bad])['value']==.5
    assert evqsr([good,{**bad,'spatial_correct':None}])['value'] is None
    assert evqsr([{**good,'review_status':'DRAFT'}])['value'] is None
    assert semantic_metrics([{'semantic_correct':True}])['semantic_correct'] is None


def test_operational_missing_counts():
    assert distribution([10,None,30,float('nan')]) == {
        'measured':2,'missing':2,'mean':20,'p50':20,'p95':29,'iqr':10}


def test_paired_statistics_do_not_count_repeats_as_cases():
    a=[{'case_id':k,'score':1} for k in ('a','a','b','b')]
    b=[{'case_id':k,'score':0} for k in ('a','a','b','b')]
    result=paired_bootstrap(a,b,field='score',samples=100)
    assert result['paired_cases']==2
    assert result['ci95']==[1,1]
    with pytest.raises(ValueError):
        paired_bootstrap(a,[{'case_id':'a','score':None}],field='score')
    assert mcnemar_exact({'a':True},{'a':True})['p_value']==1


def test_report_never_promotes_runtime_gold(tmp_path):
    (tmp_path/'manifest.json').write_text('{}')
    cases=[{'case_id':'c','category':'Q1','review_status':'DRAFT','expected_behavior':'EXECUTE'},
           {'case_id':'ai','category':'Q1',**GOLD,'expected_behavior':'EXECUTE',
            'review_kind':'AI_PRE_REVIEW','human_approval':False}]
    rows=[{'case_id':'c','method':'B0','status':'error','latency_ms':12,**GOLD,
           **dict.fromkeys(COMPONENTS,True)},
          {'case_id':'ai','method':'B0','status':'completed','latency_ms':12,**GOLD,
           'review_kind':'HUMAN_REVIEW','human_approval':True,**dict.fromkeys(COMPONENTS,True)}]
    result=report(tmp_path,cases,rows)
    assert result['verified_gold_cases']==0
    assert result['tables'][NAMES[2]][0]['evqsr'] is None
    assert result['tables'][NAMES[6]][0]['latency_ms_mean']==12
    assert result['tables'][NAMES[6]][0]['failure_rows']==1
    assert (tmp_path/'figures'/'D1_pilot_operational.png').exists()
    assert len(list((tmp_path/'figures').glob('F*.png')))==7
    assert len(list((tmp_path/'tables').glob('R*.csv')))==7
    assert json.loads((tmp_path/'metrics'/'summary.json').read_text(encoding='utf-8'))['publication_status']=='NOT_READY'


def test_manifest_required(tmp_path):
    with pytest.raises(FileNotFoundError):
        report(tmp_path,[],[])


def test_finalize_refuses_partial_pilot(tmp_path):
    from research.marine_geollm_scie.runners.finalize import finalize
    with pytest.raises(RuntimeError,match='Pilot inputs not complete'):
        finalize(tmp_path)
    assert not (tmp_path/'manifest.json').exists()
