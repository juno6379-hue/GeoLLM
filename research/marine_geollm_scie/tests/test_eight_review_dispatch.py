"""Exercise the typed-plan prompt to shared reviewer path without model calls."""
import json
import pytest
from research.marine_geollm_scie.runners import eight_method_runner as runner
from research.marine_geollm_scie.runners.matched_branches import freeze_initial, run_branches

CASE = {'case_id':'development','query':'Find Wreck','spatial_context':{}}
PACKET = {'evidence_text':'Public feature definition'}
PLAN = {'action':'clarify','tool_calls':[],'missing_inputs':['reference_geometry']}


def test_typed_prompt_uses_same_explicit_contract_for_shared_review(tmp_path, monkeypatch):
    prompt=runner.make_prompt(CASE,PACKET,{},tools=True)
    assert 'Available read-only tools, each explicit call executes once:' not in prompt
    seen=[]
    def model(query, context, plan, **kw):
        seen.append(context)
        return {'status':'completed'}, {'plan':plan}, []
    monkeypatch.setattr(runner,'call_review',model)
    artifact=tmp_path/'review.json';calls=[]
    result=runner.review_candidate(PLAN,case=CASE,packet=PACKET,profile={},
        model='not-called',seed=42,artifact=artifact,calls=calls)
    assert len(seen)==1 and seen[0]['tool_contract']==runner.TOOL_INSTRUCTIONS
    assert runner.TOOL_INSTRUCTIONS in prompt
    assert result['plan']==PLAN and len(calls)==1
    assert json.loads(artifact.read_text())['review']['plan']==PLAN


@pytest.mark.parametrize('failure', ['context', 'transport', 'invalid_response'])
def test_failed_review_has_shared_receipt_and_never_executes_reviewed_branches(tmp_path, monkeypatch, failure):
    def broken(*args, **kwargs):
        raise IndexError('development callback failure')
    if failure=='context':
        monkeypatch.setattr(runner,'public_context',broken)
    elif failure=='transport':
        monkeypatch.setattr(runner,'call_review',broken)
    else:
        monkeypatch.setattr(runner,'call_review',lambda *a,**k: (
            {'status':'completed','raw_response':'malformed'},None,['ValidationError']))
    artifact=tmp_path/'review.json';calls=[]
    initial=tmp_path/'initial.json'
    freeze_initial(initial,case_id=CASE['case_id'],repeat=0,plan=PLAN,generation={})
    rows=run_branches(initial,tmp_path/'paired',
        reviewer=lambda candidate:runner.review_candidate(candidate,case=CASE,packet=PACKET,
            profile={},model='not-called',seed=42,artifact=artifact,calls=calls),
        validator=lambda q:q,executor=lambda p:{},query=CASE['query'])
    reviewed=[r for r in rows if r['method'] in ('B4','H')]
    assert len(reviewed)==2
    assert all(r['status']=='REVIEW_ERROR' and r['execution_callback_invoked'] is False for r in reviewed)
    receipt=json.loads(artifact.read_text())
    assert receipt['review'] is None and receipt['errors']
    assert runner.digest(artifact)
    assert len(calls)==(1 if failure=='invalid_response' else 0)
    if failure!='invalid_response':
        assert receipt['call'] is None and receipt['error_type']=='IndexError'


@pytest.mark.parametrize('callback_fails', [False, True])
def test_actual_runner_persists_equal_review_hashes_with_fake_external_adapters(tmp_path, monkeypatch, callback_fails):
    """Keep runner/branch controller/serialization real, stub DB and models only.

    Identity verification is a separate tested gate; fixture inputs are deliberately
    not real research data. This catches wiring errors beyond helper-only tests.
    """
    benchmark=tmp_path/'benchmark';benchmark.mkdir()
    cases=[dict(CASE,case_id=f'DEV_{i}') for i in range(18)]
    inputs=benchmark/'queries.jsonl'
    inputs.write_text(''.join(json.dumps(c)+'\n' for c in cases),encoding='utf-8')
    profile=tmp_path/'profile.json'
    profile.write_text(json.dumps({'model':'fake','benchmark_sha256':'fixture',
        'execution_identity':{'benchmark_inputs_sha256':runner.digest(inputs)},
        'catalogue':{'path':'unused','sha256':'unused'}}))
    plan={'action':'clarify','intent':'spatial_search','target_features':['Wreck'],
        'attributes':[],'spatial_relation':'intersects','location_text':None,'radius_m':None,
        'crs':None,'tool_calls':[],'evidence_refs':[],'missing_inputs':['reference_geometry'],'answer':''}
    call={'status':'completed','raw_response':json.dumps(plan),'latency_ms':1,
          'input_tokens':1,'output_tokens':1,'done_reason':'stop'}
    monkeypatch.setattr(runner,'ensure_identity',lambda *a:None)
    monkeypatch.setattr(runner,'model_digest',lambda *a:None)
    monkeypatch.setattr(runner,'build_packet',lambda *a,**k:PACKET)
    monkeypatch.setattr(runner,'call_model',lambda *a,**k:dict(call))
    class FakeExecutor:
        def __init__(self,*a,**k):pass
        def execute(self,plan):
            return {'status':'NOT_EXECUTED','receipts':[],
                    'execution_observation':dict(runner.NO_SPATIAL)}
    monkeypatch.setattr(runner,'V2Executor',FakeExecutor)
    monkeypatch.setattr(runner,'ObservedDatabase',lambda:None)
    monkeypatch.setattr(runner,'validator_for',lambda *a,**k:lambda q:q)
    contexts=[]
    def model(query,context,candidate,**kwargs):
        contexts.append(context)
        if callback_fails:raise RuntimeError('simulated model transport failure')
        return dict(call),{'plan':candidate},[]
    monkeypatch.setattr(runner,'call_review',model)
    output=tmp_path/'run'
    result=runner.run(output,profile,benchmark,execute=True)
    assert result['rows']==126 and len(contexts)==18
    assert all(c['tool_contract']==runner.TOOL_INSTRUCTIONS for c in contexts)
    rows=[json.loads(x) for x in (output/'observations.jsonl').read_text().splitlines()]
    for case in cases:
        pair={r['method']:r for r in rows if r['case_id']==case['case_id'] and r['method'] in ('B4','H')}
        artifact=output/case['case_id']/'review_call_raw.json'
        assert pair['B4']['review_artifact_sha256']==pair['H']['review_artifact_sha256']==runner.digest(artifact)
        if callback_fails:
            assert all(r['status']=='REVIEW_ERROR' and not r['execution_callback_invoked'] for r in pair.values())
