import pytest
from research.marine_geollm_scie.evaluation.rq_metrics import (approved,derive,spatial_gap,fault_detection,
    recovery,costs,cluster_bootstrap,paired_mcnemar)

G={'annotation_status':'GOLD','human_approval':True,'adjudication_status':'APPROVED','annotator_ids':['expert'],
   'gold_sha256':'fixture-only','expected_behavior':'EXECUTE','semantics':{'labels':['Wreck']},'spatial':{'object_ids':[],
   'dataset_snapshot_sha256':'snapshot-fixture','oracle_sha256':'oracle-fixture'}}


def test_ai_pre_review_cannot_be_promoted_by_flags():
    assert approved(G)
    assert not approved({**G,'review_kind':'AI_PRE_REVIEW'})
    assert not approved({**G,'human_approval':False})
    assert derive({'semantic_correct':True,'spatial_correct':True},{'annotation_status':'DRAFT'})['semantic_correct'] is None


def test_label_match_is_not_full_semantic_accuracy_and_citations_not_evidence_truth():
    row={'predicted_semantics':{'labels':['Wreck']},'verified_evidence_refs':['FC:Wreck']}
    gold={**G,'evidence':{'required_refs':['FC:Wreck']}}
    score=derive(row,gold)
    assert score['semantic_label_exact'] is True and score['semantic_correct'] is None
    assert score['reference_completeness'] is True and score['evidence_correct'] is None
    row['evidence_verification']={'verification_artifact_sha256':'fixture','claim_support_verified':False,'source_version_verified':True}
    assert derive(row,gold)['evidence_correct'] is False


def test_gap_denominators_and_valid_empty():
    gold={'a':G,'b':G,'c':G}
    rows=[{'case_id':'a','execution_success':True,'returned_object_ids':[],'snapshot_sha256':'snapshot-fixture'},
          {'case_id':'b','execution_success':True,'returned_object_ids':['wrong'],'snapshot_sha256':'snapshot-fixture'},
          {'case_id':'c','execution_success':False}]
    score=spatial_gap(rows,gold)
    assert score['ESR']==pytest.approx(2/3)
    assert score['SCR']==pytest.approx(1/3)
    assert score['CGE']==.5 and score['SSFR']==.5
    assert score['execution_correctness_gap']==pytest.approx(1/3)
    rows[2]['execution_success']=None
    assert spatial_gap(rows,gold)['CGE'] is None
    rows[2]['execution_success']=False
    rows[0].pop('returned_object_ids')
    assert spatial_gap(rows,gold)['SSFR'] is None


def test_draft_faults_separate_and_missing_predictions_retained():
    rows=[{'case_id':'a','expected_invalid':True,'predicted_invalid':True},
          {'case_id':'b','expected_invalid':True,'predicted_invalid':None}]
    assert fault_detection(rows,{})['recall'] is None
    diagnostic=fault_detection(rows,{},diagnostic=True)
    assert diagnostic['TP']==1 and diagnostic['missing_predictions']==1 and diagnostic['recall'] is None


def test_recovery_rsc_conditional_denominator_and_drift():
    gold={k:{**G,'recovery_eligible':True,'semantics':{'labels':['Wreck'],'label_set_is_complete_semantic_contract':True}} for k in ('a','b')}
    rows=[{'case_id':'a','recovery_attempted':True,'recovery_success':True,'returned_object_ids':[],'snapshot_sha256':'snapshot-fixture',
           'predicted_semantics':{'labels':['Hazard']},'error_detected':True},
          {'case_id':'b','recovery_attempted':True,'recovery_success':False,'returned_object_ids':['wrong'],'snapshot_sha256':'snapshot-fixture',
           'predicted_semantics':{'labels':['Wreck']},'error_detected':True}]
    result=recovery(rows,gold)
    assert result['RSC']==1 and result['spatial_correct_all_attempts']==.5
    assert result['SPR']==.5 and result['SDR']==.5
    assert result['meaning_preserved_spatial_recovery_rate']==0


def test_cost_does_not_impute_tokens_and_executed_tool_calls():
    r=costs([{'latency_ms':10,'input_tokens':3,'output_tokens':None,'tool_calls':[{'plan':'only'}],'status':'timeout'},
             {'latency_ms':20,'input_tokens':4,'output_tokens':5,'tool_calls_executed':0}])
    assert r['total_tokens_missing']==1 and r['total_tokens_mean']==9
    assert r['tool_calls_measured']==1 and r['tool_calls_mean']==0
    assert r['timeout_rows']==1


def test_cluster_pairing_and_mcnemar_independence():
    a=[{'case_id':c,'repeat':j,'equivalence_group':c,'score':False} for c in ('a','b') for j in range(3)]
    b=[{**r,'score':True} for r in a]
    result=cluster_bootstrap(a,b,'score',samples=100)
    assert result['clusters']==2 and result['cases']==2 and result['paired_rows']==6
    assert result['difference_B_minus_A']==1 and result['ci95']==[1,1]
    assert paired_mcnemar(a,b,'score',repeat_id=0)['paired_cases']==2
    with pytest.raises(ValueError):cluster_bootstrap(a,b[:-1],'score',samples=100)
    for r in a+b:r['equivalence_group']='one'
    assert paired_mcnemar(a,b,'score',repeat_id=0)['status']=='NOT_READY'


def test_safe_abstention_not_execution_failure():
    result=derive({'validator_decision':'NEEDS_USER_INPUT','execution_success':False},{**G,'expected_behavior':'NEEDS_USER_INPUT'})
    assert result['safe_abstention_correct'] is True
    assert spatial_gap([{'case_id':'a','execution_success':False}],{'a':{**G,'expected_behavior':'NEEDS_USER_INPUT'}})['executable_rows']==0


def test_semantic_f1_only_declared_required_labels_and_no_missing_drop():
    from research.marine_geollm_scie.evaluation.rq_metrics import semantic_set_scores
    rows=[{'case_id':'a','predicted_semantics':{'labels':['Wreck','Rock']}}]
    result=semantic_set_scores(rows,{'a':G})
    assert result['micro_f1']==pytest.approx(2/3)
    assert result['macro_f1']==.5
    rows.append({'case_id':'b','predicted_semantics':None})
    result=semantic_set_scores(rows,{'a':G,'b':G})
    assert result['micro_f1'] is None and result['missing']==1
