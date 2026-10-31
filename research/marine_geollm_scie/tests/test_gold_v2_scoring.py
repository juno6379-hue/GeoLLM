from research.marine_geollm_scie.evaluation.gold_v2 import score, distances_match, all_known


def abstention_contract():
    return {'case_id':'PILOT_Q5_01','evaluation_stratum':'OUT_OF_COVERAGE_SAFE_ABSTENTION',
        'coverage_reference':{'source_relation_sha256':{'s101':'hash'}},
        'expected_spatial_behavior':{'accepted_states':['BLOCKED_DATA','DATA_OUT_OF_SCOPE'],
                                    'per_target':{'Lighthouse':{},'Wreck':{}}}}


def answer():
    return {'spatial_tasks':{t:{'status':'BLOCKED_DATA','object_ids':None} for t in ('Lighthouse','Wreck')},
        'source_coverage':{'source_snapshot_sha256':'hash','requested_extent_covered':False,'explanation':'Outside source coverage'}}


def test_oos_is_not_a_zero_object_or_spatial_accuracy_case():
    a=answer();trace={'observation_complete':True,'execution_attempted':False}
    r=score(abstention_contract(),a,trace)
    assert r['safe_abstention_correct'] is True
    assert r['spatial_correctness'] is None
    assert not r['execution_correctness_gap_applicable']
    a['spatial_tasks']['Wreck']['object_ids']=[]
    assert score(abstention_contract(),a,trace)['safe_abstention_correct'] is False


def test_both_subtasks_required_and_missing_trace_not_false():
    a=answer()
    assert score(abstention_contract(),a,{})['safe_abstention_correct'] is None
    del a['spatial_tasks']['Wreck']
    assert score(abstention_contract(),a,{})['safe_abstention_correct'] is False


def test_wrong_coverage_hash_and_attempted_execution_fail():
    a=answer();a['source_coverage']['source_snapshot_sha256']='invented'
    assert score(abstention_contract(),a,{'execution_attempted':True})['safe_abstention_correct'] is False


def test_distance_tolerance_is_explicit_and_nan_cannot_pass():
    expected={'Wreck':{'minimum':0.,'maximum':1999.}}
    assert distances_match({'Wreck':{'minimum':.001,'maximum':1999.001}},expected,.01)
    assert not distances_match({'Wreck':{'minimum':float('nan'),'maximum':1999.}},expected,.01)
    assert not distances_match({},expected,.01)


def test_known_failure_is_not_hidden_by_unmeasured_check():
    assert all_known({'failed':False,'unknown':None}) is False
    assert all_known({'passed':True,'unknown':None}) is None
