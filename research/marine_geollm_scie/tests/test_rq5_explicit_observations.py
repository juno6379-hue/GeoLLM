import copy
import pytest
from research.marine_geollm_scie.evaluation import rq5_explicit_observations as m


def test_evqsr_requires_all_boolean_components_and_membership():
    row=dict(evqsr_eligible=True,**{k:True for k in m.COMPONENTS})
    assert m.reliability_summary([row])['evqsr']['value']==1
    row.pop('evidence_correct')
    assert m.reliability_summary([row])['evqsr']['value'] is None
    row['execution_success']=False
    assert m.reliability_summary([row])['evqsr']['value'] is None
    assert m.reliability_summary([{}])['evqsr']['unknown_membership']==1
    assert m.reliability_summary([{'evqsr_eligible':False}])['evqsr']['status']=='UNDEFINED'


def test_false_ready_missing_is_not_false_or_true():
    result=m.reliability_summary([{'expected_invalid':True}])
    assert result['false_ready']['value'] is None
    assert result['false_ready']['missing']==1
    result=m.reliability_summary([{'expected_invalid':True,'predicted_invalid':False},{'expected_invalid':False,'predicted_invalid':True}])
    assert result['false_ready']['value']==result['false_block']['value']==1


def costs():
    rows=[dict(observation_id=x,event_ids=['shared'],cost_events_complete=True,latency_seconds=t) for x,t in [('B4',2),('H',4)]]
    events=[dict(event_id='shared',input_tokens=100,output_tokens=20,tool_calls=0)]
    return rows,events


def test_shared_event_once_and_unattributed_per_observation_missing():
    rows,events=costs();result=m.cost_summary(rows,events+events)
    assert result['actual_unique_event_totals']['input_tokens']['value']==100
    assert result['allocated_observation_costs']['input_tokens']['mean'] is None
    assert result['latency_seconds']['p50']==3
    assert result['latency_seconds']['p95']==pytest.approx(3.9)


def test_explicit_cost_allocation_preserves_actual_total():
    rows,events=costs()
    contract=dict(contract_id='frozen-v1',weights={'B4':{'shared':.5},'H':{'shared':.5}})
    result=m.cost_summary(rows,events,contract)
    assert result['allocated_observation_costs']['input_tokens']['mean']==50
    contract['weights']['H']['shared']=1
    with pytest.raises(ValueError,match='once'):m.cost_summary(rows,events,contract)


def test_conflicting_receipt_and_incomplete_calls_fail_closed():
    rows,events=costs();changed={**events[0],'input_tokens':101}
    with pytest.raises(ValueError,match='Conflicting'):m.cost_summary(rows,events+[changed])
    rows[1]['cost_events_complete']=False;rows[1]['latency_seconds']=None
    result=m.cost_summary(rows,events)
    assert result['actual_unique_event_totals']['input_tokens']['value'] is None
    assert result['latency_seconds']['p95'] is None


@pytest.mark.parametrize('bad',[None,True,-1,float('nan'),float('inf'),1.5])
def test_invalid_cost_counters_are_missing(bad):
    rows,events=costs();events[0]['input_tokens']=bad
    assert m.cost_summary(rows,events)['actual_unique_event_totals']['input_tokens']['value'] is None


def profiles():
    full=dict(execution_kind='MODULE_ABLATION',configuration_id='full',modules={k:True for k in m.MODULES},**{k:'frozen-'+k for k in m.FROZEN_KEYS})
    variant=copy.deepcopy(full);variant['configuration_id']='without_kg';variant['modules']['bounded_kg']=False
    return full,variant


def observations(profile):
    return [dict(configuration_id=profile['configuration_id'],case_id='a',repeat=i,equivalence_group='a-group',metric_eligible=True,evqsr=True) for i in range(2)]


def test_ablation_pair_delta_not_repeated_sample_count_or_fake_ci():
    full,variant=profiles();a,b=observations(full),observations(variant)
    b[0]['evqsr']=False
    result=m.paired_ablation_delta(a,b,full,variant,field='evqsr')
    assert result['value']==-.5 and result['paired_cases']==1 and result['paired_observations']==2
    assert result['ci95'] is None


def test_absent_ablation_not_inferred_from_baselines():
    full,variant=profiles()
    assert m.paired_ablation_delta([],[],None,None,field='evqsr')['value'] is None
    variant['execution_kind']='B2'
    with pytest.raises(ValueError,match='ablation profile'):m.paired_ablation_delta(observations(full),observations(variant),full,variant,field='evqsr')


@pytest.mark.parametrize('case',['frozen','two_modules','duplicate','missing_pair','missing_outcome','eligibility'])
def test_ablation_rejects_uncontrolled_or_incomplete_comparison(case):
    full,variant=profiles();a,b=observations(full),observations(variant)
    if case=='frozen':variant['snapshot_sha256']='changed'
    if case=='two_modules':variant['modules']['qec']=False
    if case=='duplicate':b.append(b[0])
    if case=='missing_pair':b.pop()
    if case=='missing_outcome':b[0]['evqsr']=None
    if case=='eligibility':b[0].pop('metric_eligible')
    if case in ('frozen','two_modules','duplicate'):
        with pytest.raises(ValueError):m.paired_ablation_delta(a,b,full,variant,field='evqsr')
    else:
        result=m.paired_ablation_delta(a,b,full,variant,field='evqsr')
        assert result['value'] is None and result['status']=='UNMEASURED'
