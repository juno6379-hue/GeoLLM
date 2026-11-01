import copy
import pytest
from research.marine_geollm_scie.runners.supervise_eight import verify_execution_measurement


def summary():
    return {'execution_semantics_version':'spatial_execution_semantics_v3',
        'overall_by_method':{m:{'spatial_eligible_case_ids':['A','B'],
            'execution_success_all_eligible':{'denominator':2,'value':None}}
            for m in ('B0','B1','B2','B3','B4','P0','H','P1')}}


def test_shared_missing_outcomes_do_not_bypass_or_fail_measurement_parity():
    verify_execution_measurement(summary())


@pytest.mark.parametrize('mutation',['old_version','missing_method','different_cases','different_denominator'])
def test_rejects_complete_rows_with_inconsistent_measurement(mutation):
    s=copy.deepcopy(summary())
    if mutation=='old_version':s['execution_semantics_version']='v2'
    elif mutation=='missing_method':del s['overall_by_method']['P1']
    elif mutation=='different_cases':s['overall_by_method']['P1']['spatial_eligible_case_ids']=['A','C']
    else:s['overall_by_method']['P1']['execution_success_all_eligible']['denominator']=1
    with pytest.raises(RuntimeError):verify_execution_measurement(s)
