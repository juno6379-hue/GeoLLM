import io
import json
import pytest
from research.marine_geollm_scie.runners import structured_review as sr
from research.marine_geollm_scie.runners.eight_fault_recovery import clean_plan


def envelope():
    return {'invalid':False,'reason':'explicit input matches','plan':clean_plan()}


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
