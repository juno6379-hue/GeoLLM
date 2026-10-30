import json
from research.marine_geollm_scie.baselines import plan_comparison as pc


def plan():
    return {'action':'clarify','intent':'spatial_search','target_features':['Wreck'],'attributes':[],
            'spatial_relation':'intersects','location_text':None,'radius_m':None,'crs':None,
            'tool_calls':[],'evidence_refs':[],'missing_inputs':['selected area'],'answer':'Select an area.'}


def packet():
    return {'evidence_text':'','sources':[],'packet_sha256':'test-packet'}


def test_schema_is_not_execution_approval():
    value,valid,errors=pc.parse_plan(json.dumps(plan()))
    assert valid and not errors
    qec=pc.capture_qec('Find wrecks in selected area.',value,'B3',packet())
    assert qec['readiness']=='DRAFT'
    assert qec['route_plan']['execution_ready'] is False
    assert not qec['data_bindings']
    assert qec['semantic_resolution']['verification_status']=='UNVERIFIED_LLM_CANDIDATE'
    value['unexpected']='must reject'
    assert pc.parse_plan(json.dumps(value))[1] is False


def test_self_review_has_same_total_generation_ceiling(monkeypatch):
    ceilings=[]
    def fake(prompt,*,model,seed,max_tokens):
        ceilings.append(max_tokens)
        answer=plan() if len(ceilings)==1 else {'verdict':'valid','issues':[],'revised_plan':plan()}
        return {'status':'completed','raw_response':json.dumps(answer),'input_tokens':20,'output_tokens':10,'latency_ms':1}
    monkeypatch.setattr(pc,'call_model',fake)
    result=pc.run_condition({'query':'Find wrecks'},'B4',packet(),model='test',seed=42)
    assert ceilings==[384,384]
    assert result['model_calls']==2 and result['output_tokens']==20
    assert result['execution_success'] is None
    assert result['review']['verdict']=='valid'
    assert result['full_qec']['readiness']=='DRAFT'


def test_failed_review_is_not_successful_self_review(monkeypatch):
    outputs=iter([{'status':'completed','raw_response':json.dumps(plan()),'input_tokens':20,'output_tokens':10,'latency_ms':1},
                  {'status':'timeout','raw_response':None,'input_tokens':None,'output_tokens':None,'latency_ms':180000}])
    monkeypatch.setattr(pc,'call_model',lambda *args,**kwargs:next(outputs))
    result=pc.run_condition({'query':'Find wrecks'},'B4',packet(),model='test',seed=42)
    assert result['status']=='timeout' and result['schema_valid'] is None
    assert result['full_qec'] is None and result['output_tokens'] is None
    assert result['initial_plan']==plan()
