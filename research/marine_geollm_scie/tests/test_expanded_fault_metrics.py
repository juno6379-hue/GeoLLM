from research.marine_geollm_scie.evaluation.expanded_fault_metrics import (
    recovery_metrics,paired_cluster_comparison,summarize_paired)
import pytest


def test_missing_forbidden_review_is_not_zero_proposals():
    rows=[{'forbidden_recovery_eligible':True,'forbidden_recovery_proposed':None},
          {'forbidden_recovery_eligible':True,'forbidden_recovery_proposed':False}]
    report=recovery_metrics(rows)['forbidden_recovery']
    assert report['complete_positive_count'] is None
    assert (report['denominator'],report['measured'],report['missing'])==(2,1,1)
    assert report['observed_positive_count']==0
    assert recovery_metrics([])['forbidden_recovery']['complete_positive_count'] is None


def test_first_repair_execution_joint_and_drift_are_separate():
    rows=[{'recovery_eligible':True,'recovery_attempted':True,'recovery_success':True,
           'semantic_preservation':good,'joint_success':good,'human_escalation_observed':None}
          for good in (True,False)]
    metrics=recovery_metrics(rows)
    assert metrics['first_repair_execution_success_given_attempt']['value']==1
    assert metrics['first_repair_joint_success_given_attempt']['value']==.5
    assert metrics['semantic_drift_given_attempt']['value']==.5
    assert metrics['human_escalation']['value'] is None
    assert metrics['human_escalation']['denominator']==2
    assert metrics['human_escalation']['missing']==2


def rows():
    return [{'case_id':f'{base}_{i}','base_scenario_id':base,'method':method,'expected_invalid':True,
             'predicted_invalid':method!='B4','target_fault_code_detected':method!='B4'}
            for base in ('A','B','C') for i in range(2) for method in ('B4','P0','H')]


def test_paired_cluster_interval_uses_bases_not_fault_rows():
    value=paired_cluster_comparison(rows(),'P0','predicted_invalid')
    assert value['paired_cases']==6 and value['independent_base_clusters']==3
    assert value['paired_delta']==1 and value['ci95']==[1,1]
    assert value==paired_cluster_comparison(rows(),'P0','predicted_invalid')


def test_missing_pair_keeps_denominator_and_ci_unmeasured():
    data=rows();next(r for r in data if r['method']=='H')['target_fault_code_detected']=None
    metrics=summarize_paired(data)
    value=metrics['H']['target_fault_code_recall']
    assert (value['paired_cases'],value['measured_pairs'],value['missing_pairs'])==(6,5,1)
    assert value['paired_delta'] is None and value['ci95'] is None
    assert metrics['H']['binary_recall']['paired_delta']==1


def test_repetitions_cannot_silently_become_independent_pairs():
    data=rows();data.append(dict(data[0]))
    with pytest.raises(ValueError,match='UNDECLARED_REPEAT'):
        paired_cluster_comparison(data,'P0','predicted_invalid')
