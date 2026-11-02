import copy,json
import pytest
from research.marine_geollm_scie.evaluation.rq5_costs import model_event,event_ledger
from research.marine_geollm_scie.runners.eight_method_runner import costs,p1_costs
from research.marine_geollm_scie.runners.report_rq5 import summarize,run,evidence_presence

def call(identity):return dict(event_id=identity,input_tokens=10,output_tokens=2,latency_ms=25,status='OK')
def row(method,case='Q1'):
    calls=[call(case+':shared' if method in ('B3','B4','P0','H') else case+':'+method)]
    if method in ('B4','H'):calls.append(call(case+':review'))
    return {'method':method,'case_id':case,'repeat':0,'costs':costs(calls,{},.2,sql_events=[],telemetry_complete=True),
            'raw_artifact_sha256':'a'*64,'emitted_answer':{'answer_text':'fixture'}}

def test_shared_physical_call_deduplication_and_allocation_conserve_cost():
    rows=[row(m) for m in ('B3','B4','P0','H')];ledger=event_ledger(rows)
    assert ledger['unique_observed_model_calls']==2
    assert ledger['physical_total']['input_tokens']==20
    assert sum(c['input_tokens'] for c in ledger['standalone_model_costs'].values())==60
    assert sum(c['input_tokens'] for c in ledger['allocated_model_costs'].values())==20
    rows[-1]['costs']['model_call_events'][0]['output_tokens']=999
    with pytest.raises(ValueError,match='payload mismatch'):event_ledger(rows)

def test_absent_telemetry_never_becomes_zero():
    assert costs([],{},.2)['sql_calls'] is None
    p1=p1_costs({'case_id':'Q1'})
    assert p1['sql_calls'] is None and p1['model_calls'] is None and p1['input_tokens'] is None
    ledger=event_ledger([{'method':'P1','case_id':'Q1','costs':p1}])
    assert ledger['total_sql_submissions'] is None and not ledger['complete']

def test_all_sql_includes_pre_execution_metadata():
    events=[{'scope':'metadata'},{'scope':'spatial'}]
    measured=costs([call('one')],{'execution_observation':{'db_events':[events[1]]}},.2,sql_events=events,telemetry_complete=True)
    assert measured['sql_calls']==2
    assert measured['all_sql_events']==events

def test_complete_144_synthetic_schema_does_not_invent_evqsr():
    rows=[row(m,'Q'+str(i)) for i in range(18) for m in ('B0','B1','B2','B3','B4','P0','H','P1')]
    report=summarize(rows)
    assert report['status']=='COMPLETE_OBSERVATION_COHORT'
    assert report['event_ledger']['unique_observed_model_calls']==108
    assert all(v['EVQSR']['value'] is None for v in report['methods'].values())
    assert all(v['False_Block']['value'] is None for v in report['methods'].values())

def test_presence_does_not_claim_source_correctness():
    r=row('B3');r['emitted_answer']={'spatial_tasks':{'Wreck':{'object_ids':['1'],'object_evidence':{
        '1':{'object_id':'1','source_snapshot_sha256':'f'*64}}}}}
    result=evidence_presence(r)
    assert result['value'] is True and result['end_to_end_provenance_correctness'] is None

def test_judgment_binds_exact_new_answer():
    r=row('B3');judgment={'method':'B3','case_id':'Q1','repeat':0,'raw_artifact_sha256':'b'*64}
    with pytest.raises(ValueError,match='exact raw'):summarize([r],judgments=[judgment],expected_cases=1)

def test_report_rejects_old_score_file(tmp_path):
    source=tmp_path/'rows.jsonl';source.write_text(json.dumps(row('B3'))+'\n')
    scores=tmp_path/'scores.json';scores.write_text(json.dumps({'observations_sha256':'f'*64,'rows':[]}))
    with pytest.raises(ValueError,match='not bound'):run(source,tmp_path/'report',scores=scores)

def test_branch_metadata_is_included_even_when_validator_blocks(tmp_path,monkeypatch):
    from research.marine_geollm_scie.runners.matched_branches import freeze_initial,run_branches
    from services.orchestrator import execution_validator
    monkeypatch.setattr(execution_validator,'is_execution_authorized',lambda q:False)
    source=tmp_path/'initial.json';freeze_initial(source,case_id='Q',repeat=0,plan={'feature':'Wreck'},generation={})
    events=[]
    def validator(q):events.append({'scope':'metadata','stage':'binding'});return q
    def executor(p):events.append({'scope':'spatial'});return {'execution_observation':{}}
    rows=run_branches(source,tmp_path/'branches',reviewer=lambda p:{'plan':p},validator=validator,
                      executor=executor,sql_events=lambda:events)
    assert rows[2]['status']=='VALIDATOR_BLOCKED'
    assert rows[2]['all_sql_events']==[{'scope':'metadata','stage':'binding'}]
    assert rows[3]['all_sql_events']==[{'scope':'metadata','stage':'binding'}]

def test_old_spatial_only_sql_count_not_presented_as_all_sql():
    r=row('B3');del r['costs']['all_sql_events'];r['costs']['sql_calls']=9
    report=summarize([r],expected_cases=1)
    assert report['methods']['B3']['costs']['sql_calls']['measured']==0
