from copy import deepcopy
from research.marine_geollm_scie.evaluation.v2_fault_results import summarize_faults


def row():
    return {'method':'H','error_type':'wrong_feature','expected_invalid':True,'predicted_invalid':False,
        'recovery_eligible':True,'recovery_attempted':True,'recovery_success':True,
        'semantic_preservation':False,'spatial_correct':True,'joint_success':False}


def test_successful_execution_with_semantic_drift_is_not_joint_success():
    result=summarize_faults([row()])['overall_by_method']['H']
    assert result['recovery_success_given_attempt']['value']==1
    assert result['semantic_preservation_given_attempt']['value']==0
    assert result['joint_recovery_given_attempt']['value']==0
    assert result['false_ready']['value']==1


def test_detection_missingness_not_hidden_by_other_verdicts():
    a=row();b=deepcopy(a);b['predicted_invalid']=None
    result=summarize_faults([a,b])['overall_by_method']['H']
    assert result['false_ready']['value'] is None
    assert result['false_ready']['missing']==1


def test_validation_only_method_has_no_recovery_denominator():
    a=row();a.update(method='P0',recovery_eligible=False,recovery_attempted=False)
    result=summarize_faults([a])['overall_by_method']['P0']
    assert result['recovery_eligible']==0
    assert result['joint_recovery_given_attempt']['value'] is None


def test_failed_attempt_is_preserved_in_eligible_denominator():
    a=row();a.update(recovery_attempted=False,recovery_success=None,joint_success=None,semantic_preservation=None)
    result=summarize_faults([a])['overall_by_method']['H']
    assert result['joint_recovery_all_eligible']['value']==0
    assert result['joint_recovery_given_attempt']['value'] is None
