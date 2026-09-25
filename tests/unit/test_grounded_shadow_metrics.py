import pytest
from scripts.run_grounded_intent_shadow import slot_reviews
from scripts.evaluate_grounded_shadow import summarize


def test_unfaithful_and_wrong_dimension_model_slots_are_rejected():
    rows=slot_reviews('최근 12개월 AIS',{'target':'AIS','place':'부산항','radius':'12개월','time':None})
    assert [r['status'] for r in rows] == ['GROUNDED_SEMANTIC_REVIEW_REQUIRED','REJECTED','REJECTED','ABSENT_REQUIRES_GOLD_REVIEW']


def test_absent_gold_does_not_produce_accuracy():
    result=summarize([{'called':True,'elapsed_s':2,'accepted':True}])
    assert result['semantic_metrics'] is None
    assert result['gold_status']=='UNAVAILABLE'


def test_completed_sse_event_can_still_be_a_failed_task():
    from scripts.check_geollm_web_samples import observed_status
    assert observed_status({'observation':'COMPLETED_EVENT_RECEIVED', 'completion':{'status':'FAILED'}})=='FAILED'


def test_ai_review_cannot_be_used_as_gold():
    with pytest.raises(ValueError):
        summarize([], [{'sample':1,'review_status':'AI_REVIEW_REQUIRED'}])


def test_failed_response_kept_in_gold_denominator():
    gold=[{'sample':1,'review_status':'HUMAN_VERIFIED','reviewer_ids':['test-fixture'],
           'required_tasks':[{'allowed_capability_sets':[['tool.a'],['tool.b','tool.c']]}],
           'slots':{'radius':None},'needs_clarification':True,'forbidden_capabilities':[]}]
    result=summarize([{'sample':1,'called':True,'elapsed_s':120,'accepted':False}],gold)
    assert result['semantic_metrics']['required_task_plan_coverage']==0
    assert result['semantic_metrics']['slot_raw_exact_match']==0
    assert result['semantic_metrics']['missing_clarification_rate']==1


def test_empty_capability_alternative_cannot_earn_vacuous_credit():
    gold=[{'sample':1,'review_status':'HUMAN_VERIFIED','reviewer_ids':['fixture'],
           'required_tasks':[{'allowed_capability_sets':[[]]}], 'slots':{}, 'needs_clarification':False}]
    with pytest.raises(ValueError, match='non-empty'):
        summarize([],gold)


def test_review_form_is_blind_and_cannot_be_mistaken_for_holdout():
    from scripts.export_korean_review_pack import review_forms
    forms=list(review_forms({'cases':[{'sample':1,'query':'침선','context':{},'candidate_issue':None,
                                      'inputs':{'capability_contracts':{}},'candidates':['hidden-scores']}]}))
    assert forms[0]['review_status']=='UNREVIEWED'
    assert forms[0]['needs_clarification'] is None
    assert forms[0]['dataset_role']=='DEVELOPMENT_NOT_INDEPENDENT_HOLDOUT'
    assert 'candidates' not in forms[0]


def test_f1_penalizes_missing_work_and_excess_tools():
    from scripts.grounded_metrics import classification_metrics
    metrics=classification_metrics([{'locate','search'},{'search'}],[{'locate','accident'},set()])
    assert metrics['micro']['tp']==1
    assert metrics['micro']['fp']==1
    assert metrics['micro']['fn']==2
    assert metrics['micro']['f1']==pytest.approx(.4)
    assert metrics['exact_match_accuracy']==0


def test_alternative_plans_do_not_require_all_equivalent_tools():
    from scripts.grounded_metrics import closest_allowed_plan
    tasks=[{'allowed_capability_sets':[['lookup_and_search'],['locate','search']]}]
    assert closest_allowed_plan(tasks,{'locate','search'}) == {'locate','search'}


def test_f1_without_cases_is_unmeasured():
    from scripts.grounded_metrics import classification_metrics
    result=classification_metrics([],[])
    assert result['micro']['f1'] is None
    assert result['macro_f1'] is None
    assert result['exact_match_accuracy'] is None


def test_gold_f1_keeps_failed_predictions_and_does_not_award_empty_slot_accuracy():
    gold=[{'sample':1,'review_status':'HUMAN_VERIFIED','reviewer_ids':['fixture'],'intent':'SPATIAL',
           'required_tasks':[{'allowed_capability_sets':[['search']]}],
           'slots':{'target':'침선'},'needs_clarification':False}]
    result=summarize([{'sample':1,'called':True,'accepted':False,'elapsed_s':120}],gold)['semantic_metrics']['classification']
    assert result['intent']['macro_f1']==0
    assert result['tool_plan']['micro']['f1']==0
    assert result['slot_raw_value']['micro']['f1']==0
    assert result['clarification']['macro_f1']==0
