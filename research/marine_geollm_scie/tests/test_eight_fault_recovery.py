import copy
import json
import jsonschema
import pytest
from research.marine_geollm_scie.runners.eight_fault_recovery import (
    clean_plan,cohort,semantic_signature,detect,hybrid_invalid,returned_ids,joint_recovery,REVIEW_SCHEMA)
from research.marine_geollm_scie.runners.eight_fault_recovery import parse_review_response


def test_cohort_is_fixed_and_missing_geometry_not_supplied_to_reviewer():
    rows=cohort()
    assert len(rows)==9 and len({r['case_id'] for r in rows})==9
    assert rows[0]['expected_invalid'] is False
    missing=next(r for r in rows if r['error_type']=='geometry')
    assert 'geometry' not in missing['spatial_context']
    assert 'reference_geometry' not in missing['plan']['tool_calls'][0]['arguments']
    assert missing['forbidden_recovery'] and not missing['recovery_eligible']
    source=next(r for r in rows if r['error_type']=='source')
    assert source['forbidden_recovery']


def test_unit_compilation_rejection_is_not_native_validator_call():
    unit=next(r for r in cohort() if r['error_type']=='unit')
    def forbidden(qec):raise AssertionError('must not call')
    receipt=detect(unit['plan'],forbidden)
    assert receipt['compiler_rejected'] is True
    assert receipt['native_validator_called'] is False
    assert receipt['invalid'] is True


def test_native_validator_failure_is_unknown_not_successful_detection():
    def unavailable(qec):raise ConnectionError()
    receipt=detect(clean_plan(),unavailable)
    assert receipt['native_validator_called'] is True
    assert receipt['invalid'] is None
    assert receipt['error_type']=='ConnectionError'


@pytest.mark.parametrize('a,b,expected',[(True,None,True),(False,None,None),(False,False,False),(None,None,None)])
def test_hybrid_components_keep_missing(a,b,expected):
    assert hybrid_invalid(a,b) is expected


def test_semantics_detects_feature_expansion_and_source_drift():
    original=clean_plan();new=copy.deepcopy(original)
    new['tool_calls'][0]['arguments']['feature_types'].append('Rock')
    assert semantic_signature(new)!=semantic_signature(original)
    new=copy.deepcopy(original);new['tool_calls'][0]['arguments']['source']='navigation_aids'
    assert semantic_signature(new)!=semantic_signature(original)
    new=copy.deepcopy(original);new['tool_calls'][0]['arguments']['radius_m']='1 km'
    assert semantic_signature(new)==semantic_signature(original)


def test_semantics_rejects_hidden_filters_or_top_level_target_drift():
    original=clean_plan();new=copy.deepcopy(original)
    new['tool_calls'][0]['arguments']['filters']={'depth':3}
    assert semantic_signature(new) is None
    new=copy.deepcopy(original);new['target_features']=['Rock']
    assert semantic_signature(new)!=semantic_signature(original)


def test_semantic_faults_preserve_same_clean_reference_and_are_invalid():
    rows=[r for r in cohort() if r['error_type'] in {'wrong_feature','semantic_expansion','semantic_distance'}]
    assert len(rows)==3
    for row in rows:
        assert row['expected_invalid'] and row['recovery_eligible']
        assert semantic_signature(row['plan'])!=semantic_signature(clean_plan())


def test_document_result_is_not_empty_spatial_result():
    assert returned_ids({'receipts':[{'tool_id':'documents.search','status':'TOOL_RETURNED','result':{'rows':[]}}]}) is None
    assert returned_ids({'receipts':[{'tool_id':'spatial.query','status':'TOOL_RETURNED','result':{'rows':[]}}]})==[]


def test_joint_recovery_retains_unknown():
    assert joint_recovery(True,True,None) is None
    assert joint_recovery(True,False,None) is False
    assert joint_recovery(True,True,True) is True


def test_review_schema_requires_explicit_initial_verdict_and_full_plan():
    valid = {'initial_checks': {name: 'pass' for name in
        ('target', 'distance', 'crs', 'reference', 'source', 'tool_contract')},
        'invalid':False,'reason':'control','plan':clean_plan()}
    jsonschema.validate(valid,REVIEW_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({k: v for k, v in valid.items() if k != 'invalid'},REVIEW_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({k: v for k, v in valid.items() if k != 'initial_checks'},REVIEW_SCHEMA)


@pytest.mark.parametrize('response',[None,{},[],True,'null','[]','invalid'])
def test_malformed_review_response_is_retained_as_failed_parse(response):
    review,errors=parse_review_response(response)
    assert review is None and errors


@pytest.mark.parametrize('nonfinite',['NaN','Infinity','1e999'])
def test_nonfinite_review_plan_rejected_before_artifact_serialization(nonfinite):
    plan=clean_plan();plan['radius_m']='NUMERIC_SENTINEL'
    text=json.dumps({'invalid':True,'reason':'test','plan':plan}).replace('"NUMERIC_SENTINEL"',nonfinite)
    review,errors=parse_review_response(text)
    assert review is None and errors==['ValueError']
