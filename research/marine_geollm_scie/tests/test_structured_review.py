import io
import json
import pytest
from research.marine_geollm_scie.runners import structured_review as sr
from research.marine_geollm_scie.runners.eight_fault_recovery import clean_plan


def envelope():
    return {'initial_checks':dict.fromkeys(sr.CHECK_FIELDS,'pass'),
            'invalid':False,'reason':'explicit input matches','plan':clean_plan()}


@pytest.mark.parametrize('value',[None,[],{},True,clean_plan(),dict(envelope(),invalid='false'),
                                dict(envelope(),plan=[]),dict(envelope(),extra=1)])
def test_malformed_no_wrapper_or_verdict_fabrication(value):
    review,errors=sr.parse_review_response(json.dumps(value))
    assert review is None and errors


def test_valid_covers_and_nonfinite_boundary():
    value=envelope();value['plan']['spatial_relation']='covers'
    assert sr.parse_review_response(json.dumps(value))==(value,[])
    value['plan']['tool_calls'][0]['arguments']['bad']=float('nan')
    assert sr.parse_review_response(json.dumps(value))[0] is None


@pytest.mark.parametrize('reason,done,accepted',[('stop',True,True),('length',True,False),('stop',False,False)])
def test_schema_transport_and_completion_gate(monkeypatch,reason,done,accepted):
    requests=[]
    def respond(request,timeout):
        requests.append(json.loads(request.data));assert timeout==180
        return io.BytesIO(json.dumps({'response':json.dumps(envelope()),'done':done,
            'done_reason':reason,'prompt_eval_count':33,'eval_count':44}).encode())
    monkeypatch.setattr(sr.urllib.request,'urlopen',respond)
    call,review,errors=sr.call_review('explicit request',{},clean_plan(),model='test',seed=42)
    assert len(requests)==1 and requests[0]['format']==sr.REVIEW_SCHEMA
    assert requests[0]['options']=={'temperature':.2,'seed':42,'num_predict':768,'num_ctx':8192}
    assert (review is not None)==accepted
    assert call['input_tokens']==33 and call['output_tokens']==44
    assert call['schema_sha256']==sr.SCHEMA_SHA256


def test_timeout_kept_without_retry(monkeypatch):
    requests=[]
    def timeout(*args,**kwargs):
        requests.append(1);raise TimeoutError('probe timeout')
    monkeypatch.setattr(sr.urllib.request,'urlopen',timeout)
    call,review,errors=sr.call_review('request',{},clean_plan(),model='test',seed=42)
    assert len(requests)==1 and call['status']=='timeout' and review is None and errors


def test_model_check_contradiction_is_missing_not_corrected_detection():
    value=envelope();value['initial_checks']['target']='fail'
    original=json.dumps(value)
    assert sr.parse_review_response(original)==(None,['REVIEW_VERDICT_CONTRADICTION'])
    assert json.dumps(value)==original and value['invalid'] is False
    value['invalid']=True
    assert sr.parse_review_response(json.dumps(value))==(value,[])


def test_unknown_model_check_not_promoted_to_deterministic_failure():
    value=envelope();value['initial_checks']['source']='unknown'
    assert sr.parse_review_response(json.dumps(value))==(value,[])


@pytest.mark.parametrize('change',[{}, {'target':'valid'}, {'extra':'pass'}])
def test_initial_checks_are_complete_typed_model_output(change):
    value=envelope();value['initial_checks']=change
    assert sr.parse_review_response(json.dumps(value))[0] is None


def test_public_inputs_kept_without_gold_or_verdict_injection():
    plan=clean_plan();plan['tool_calls'][0]['arguments']['feature_types']=['Obstruction']
    prompt=sr.review_prompt('Find Wreck',{'map':{'crs':'EPSG:4326'}},plan)
    # The evidence is serialized intact, not pre-judged by a deterministic checker.
    assert json.loads(prompt.split('\nINITIAL_PLAN:',1)[1])==plan
    assert 'expected_invalid' not in prompt and 'FAULT_V2_' not in prompt
    assert 'initial_checks' in sr.REVIEW_SCHEMA['required']
