import copy
import json
import pytest
from research.marine_geollm_scie.evaluation.prediction_contract_v1 import (
    sha,prepare_annotation,canonical_candidate,validate_complete_annotation,
)


def fixture():
    raw=json.dumps({'plan':{'target_features':['height'],'answer':'Wreck 5 km'}}).encode()
    pre={'case_id':'x','method':'B1','query':'query','query_sha256':sha(b'query'),
         'raw_sha256':sha(raw),'raw_path':'fixture.json','raw_status':'INVALID_RESPONSE','plan_observed':True,
         'structured_field_observations':[{'kind':'feature','value':'height','json_pointer':'/plan/target_features/0'}],
         'answer_span_preannotations':[{'kind':'feature','literal_value':'Wreck','json_pointer':'/plan/answer','spans':[[0,5]]}]}
    return pre,raw


def test_wrong_feature_field_stays_feature_and_failure_retained():
    pre,raw=fixture();result=prepare_annotation(pre,raw,feature_codes=['Wreck'])
    assert result['units'][0]['candidate']=={'kind':'feature','value':'height','normalization_rule':'PRESERVED_LITERAL'}
    assert result['prediction_atoms'] is None
    assert 'MODEL_SCHEMA_FAILURE_RETAINED' in result['retained_failures']
    assert not result['human_review_complete']


@pytest.mark.parametrize('mutation',['raw','span','value','pointer'])
def test_fabricated_witness_rejected(mutation):
    pre,raw=fixture()
    if mutation=='raw':raw+=b' '
    if mutation=='span':pre['answer_span_preannotations'][0]['spans']=[[1,6]]
    if mutation=='value':pre['structured_field_observations'][0]['value']='Wreck'
    if mutation=='pointer':pre['answer_span_preannotations'][0]['json_pointer']='/query'
    with pytest.raises((ValueError,KeyError)):prepare_annotation(pre,raw)


@pytest.mark.parametrize('literal,expected',[('5 km',5000),('1 kilometer',1000),('0.001 km',1),('1.5 m',None),('5',None)])
def test_explicit_distance_no_defaults_or_rounding(literal,expected):
    value=canonical_candidate('distance_mention',literal)
    assert (value[1] if value else None)==expected


def test_no_task_broadcast_or_scoring_partial_annotation():
    pre,raw=fixture();r=prepare_annotation(pre,raw)
    assert all(unit['task_id'] is None for unit in r['units'])
    with pytest.raises(ValueError,match='EXTRACTION_INCOMPLETE'):validate_complete_annotation(r)


def test_malformed_response_stays_unmeasured_not_empty():
    pre,raw=fixture();pre.update(plan_observed=False,structured_field_observations=[],answer_span_preannotations=[])
    r=prepare_annotation(pre,raw)
    assert r['prediction_atoms'] is None
    assert 'MALFORMED_JSON_RAW_RESPONSE_REVIEW_REQUIRED' in r['retained_failures']


def test_no_wrong_feature_correction_or_unknown_alias_expansion():
    assert canonical_candidate('feature','naval wreckage',['Wreck'])[1]=='naval wreckage'
    assert canonical_candidate('feature','Anchorage Area',['AnchorageArea'])[1]=='AnchorageArea'
    assert canonical_candidate('attribute_mention','height') is None
    assert canonical_candidate('source_mention','fc.xml') is None


def test_completion_cannot_invent_gold_value_from_valid_span():
    pre,raw=fixture();r=prepare_annotation(pre,raw)
    r.update(complete_grounding_extraction=True,missing_reviews=[],
        full_response_review={'raw_sha256':r['raw_sha256'],'status':'ALL_ASSERTIONS_REVIEWED'},
        unit_decisions=[{'unit_id':'structured:0','disposition':'ATOM','rationale':'explicit field'},
                        {'unit_id':'narrative:0','disposition':'OUTSIDE_RQ1_SCOPE','rationale':'fixture decision'}],
        prediction_atoms=[{'prediction_id':'p1','task_id':'query','kind':'feature','value':'Lighthouse',
                           'witness_unit_ids':['structured:0'],'task_binding_receipt':'single task'}])
    with pytest.raises(ValueError,match='ATOM_NOT_SUPPORTED'):validate_complete_annotation(r)
