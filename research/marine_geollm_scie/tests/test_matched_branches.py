import json
import pytest
from research.marine_geollm_scie.runners.matched_branches import freeze_initial,load_frozen,run_branches,plan_hash


def test_frozen_hash_is_order_independent_and_mutation_rejected(tmp_path):
    assert plan_hash({'b':2,'a':1})==plan_hash({'a':1,'b':2})
    p=tmp_path/'initial.json'
    freeze_initial(p,case_id='x',repeat=0,plan={'action':'search'},generation={'model':'fixture'})
    with pytest.raises(FileExistsError):
        freeze_initial(p,case_id='x',repeat=0,plan={},generation={})
    raw=json.loads(p.read_text());raw['plan']['action']='changed';p.write_text(json.dumps(raw))
    with pytest.raises(ValueError): load_frozen(p)


def test_branches_share_one_initial_and_one_review_but_cannot_mutate_each_other(tmp_path,monkeypatch):
    from services.orchestrator import execution_validator
    # Controller unit fixture, not proof that a real QEC is authorized.
    monkeypatch.setattr(execution_validator,'is_execution_authorized',lambda q:q.slots.target_features==['ReviewedFixture'])
    initial=tmp_path/'initial.json'
    frozen=freeze_initial(initial,case_id='x',repeat=0,plan={'feature':'OriginalFixture'},generation={'model':'fixture'})
    reviewed=[];executed=[]
    def reviewer(plan):
        reviewed.append(plan.copy());plan['feature']='ReviewedFixture'
        return {'plan':plan,'call':{'status':'fixture'}}
    def validator(qec):return qec
    def executor(plan):
        executed.append(plan.copy());plan['feature']='MutatedFixture'
        return {'status':'fixture'}
    rows=run_branches(initial,tmp_path/'branches',reviewer=reviewer,validator=validator,executor=executor)
    assert len(reviewed)==1
    assert [r['candidate_plan']['feature'] for r in rows]==['OriginalFixture','ReviewedFixture','OriginalFixture','ReviewedFixture']
    assert rows[2]['status']=='VALIDATOR_BLOCKED'
    assert [r['feature'] for r in executed]==['OriginalFixture','ReviewedFixture','ReviewedFixture']
    assert {r['initial_plan_hash'] for r in rows}=={frozen['plan_hash']}
    assert load_frozen(initial)['plan']=={'feature':'OriginalFixture'}
    assert all(r['execution_observation'] is None for r in rows)


def test_review_failure_is_preserved_without_dropping_other_branches(tmp_path,monkeypatch):
    from services.orchestrator import execution_validator
    monkeypatch.setattr(execution_validator,'is_execution_authorized',lambda q:False)
    p=tmp_path/'initial.json';freeze_initial(p,case_id='x',repeat=0,plan={},generation={})
    def failed(plan):raise TimeoutError()
    rows=run_branches(p,tmp_path/'out',reviewer=failed,validator=lambda q:q,executor=lambda p:{})
    assert [r['status'] for r in rows]==['EXECUTOR_RETURNED','REVIEW_ERROR','VALIDATOR_BLOCKED','REVIEW_ERROR']
