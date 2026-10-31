"""Bounded adapter tests; fixture DB is not an actual spatial oracle."""
import json
import hashlib
import copy
from pathlib import Path
import pytest
from research.marine_geollm_scie.baselines.v2_runtime import V2Executor,ObservedDatabase,spatial_statement,ToolBlocked
from research.marine_geollm_scie.baselines.v2_answer_projection import render
from research.marine_geollm_scie.runners.eight_method_runner import public_context,make_prompt,p1_costs,project_branch_answer,parse_candidate


class DB:
    def __init__(self):self.events=[];self.scope='metadata';self.requests=[]
    def query(self,body,args):
        self.requests.append((body,args))
        self.events.append({'scope':self.scope,'succeeded':True})
        if self.scope=='coverage_metadata':return [{'covered':True,'margin_m':6000}]
        return [{'source_id':'17','label':'Wreck','distance_m':2,'geometry':None,'attributes':{}}]


@pytest.fixture
def executor(tmp_path):
    path=tmp_path/'fc.json';path.write_text(json.dumps({'features':[{'code':'Wreck'}]}))
    return V2Executor(DB(),catalogue=path,catalogue_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),anchors=[],
        coverage={'s101':{'scope_verified':True,'bbox_epsg4326':[128,34,130,36],'source_sha256':'fixture'}},
        reference_geometries={'explicit':{'geometry_wkt':'POINT(129 35)','crs':'EPSG:4326'}})


def args(**overrides):
    return dict({'source':'s101','relation':'dwithin','radius_m':5000,'crs':'EPSG:4326',
        'feature_types':['Wreck'],'reference_geometry':'POINT(129 35)'},**overrides)


def test_nearest_has_no_hidden_radius(executor):
    result=executor.call('spatial.query',args(relation='nearest',radius_m=None))
    assert len(result['rows'])==1
    body,values=executor.db.requests[-1]
    assert 'ST_DWithin' not in body and values['radius_m'] is None
    assert 'LIMIT 1' in body


@pytest.mark.parametrize('relation,predicate',[('within','ST_Within'),('covers','ST_Covers'),('intersects','ST_Intersects')])
def test_distinct_boundary_predicates(relation,predicate):
    assert predicate in spatial_statement('s101',relation)


def test_missing_geometry_not_repaired_from_location(executor):
    with pytest.raises(ToolBlocked,match='MISSING_REFERENCE_GEOMETRY'):
        executor.call('spatial.query',args(reference_geometry=None,location_text='Busan'))
    assert not executor.db.requests


def test_only_explicit_registered_ref_dereferenced(executor):
    assert executor.reference(args(reference_geometry=None,geometry_ref='explicit'))=='POINT(129 35)'
    with pytest.raises(ToolBlocked,match='UNKNOWN_REFERENCE'):
        executor.reference(args(reference_geometry=None,geometry_ref='invented'))


def test_no_crs_inference(executor):
    with pytest.raises(ToolBlocked,match='CRS'):
        executor.call('spatial.query',args(crs=None))


def test_metadata_is_not_gis_execution(executor):
    executor.coverage['s101']['scope_verified']=False
    result=executor.execute({'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':args()}]})
    trace=result['execution_observation']
    assert trace['tool_called'] is True and trace['execution_attempted'] is True
    assert trace['sql_executed'] is False and trace['execution_started'] is False


def test_actual_tool_receipts_render_without_gold(executor):
    plan={'action':'search','answer':'Candidate unverified','tool_calls':[{'tool_id':'spatial.query','arguments':args()}]}
    out=render(plan,executor.execute(plan),coverage=executor.coverage)
    assert out['spatial_tasks']['Wreck']['object_ids']==['17']
    assert out['spatial_tasks']['Wreck']['object_evidence']['17']['source_snapshot_sha256']=='fixture'
    assert out['candidate_prose_is_unverified'] is True


def test_failed_sql_submission_is_not_fabricated_server_execution(executor):
    def fail(body,arguments):
        executor.db.events.append({'scope':executor.db.scope,'sql_executed':None,'succeeded':None})
        raise TimeoutError('fixture transport failure')
    executor.coverage['s101']={'scope_verified':True,'scope_type':'FULL_DECLARED_SOURCE'}
    executor.db.query=fail
    result=executor.execute({'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':args()}]})
    trace=result['execution_observation']
    assert trace['execution_attempted'] is True
    assert trace['sql_executed'] is None and trace['execution_started'] is None
    assert trace['execution_succeeded'] is None


def test_common_context_does_not_serialize_large_geometry_or_gold():
    profile={'reference_geometries':{'ref':{'geometry_wkt':'SECRET_WKT','name':'Source boundary','crs':'EPSG:4326'}}}
    context=public_context(profile,{'spatial_context':{}})
    assert 'SECRET_WKT' not in json.dumps(context)
    prompt=make_prompt({'query':'question'}, {'evidence_text':''},profile,tools=False)
    assert 'tool_calls MUST be []' in prompt


def test_p1_costs_use_observed_tokens_and_keep_missing_unknown():
    row={'latency_ms':1500,'_imported_model_calls':[
        {'path':'/api/generate','response':{'prompt_eval_count':12,'eval_count':8}},
        {'path':'/api/embed','response':{'prompt_eval_count':3}}],
        'execution_observation':{'observation_complete':True,'events':[{'kind':'spatial_tool_called'},{'kind':'sql_submitted'}]}}
    cost=p1_costs(row)
    assert cost['input_tokens']==12 and cost['output_tokens']==8
    assert cost['embedding_input_tokens']==3 and cost['spatial_tool_calls']==1
    assert cost['tool_calls'] is None
    row['_imported_model_calls'].append({'path':'/api/generate','response':{}})
    assert p1_costs(row)['input_tokens'] is None


def test_large_geometry_parameter_uses_stdin_not_windows_argv(monkeypatch):
    import subprocess
    received={}
    def run(command,**kwargs):
        received.update(command=command,**kwargs)
        return subprocess.CompletedProcess(command,0,stdout='[]',stderr='')
    monkeypatch.setattr(subprocess,'run',run)
    db=ObservedDatabase()
    db.query('SELECT 1',{'reference_geometry':'x'*300000})
    assert '-i' in received['command'] and '-c' not in received['command']
    assert len(received['input'])>300000
    assert sum(map(len,received['command']))<1000


def test_original_v1_q1_02_bad_source_preserved_without_projection_crash():
    fixture=json.loads((Path(__file__).parent/'fixtures/v1_q1_02_invalid_source.json').read_text(encoding='utf-8'))
    before=copy.deepcopy(fixture)
    answer=render(fixture['candidate_plan'],fixture['execution'],coverage={'s101':{'source_sha256':'fixture'}})
    assert answer['status']=='PARTIAL' and answer['error_code']=='ANSWER_PROJECTION_INPUT_INVALID'
    assert answer['projection_errors']==[{'call_index':2,'reason':'INVALID_SPATIAL_ARGUMENT_TYPES','fields':['source']}]
    assert answer['spatial_tasks']=={} and 'source_coverage' not in answer
    assert fixture==before


@pytest.mark.parametrize('bad_source',[['s101'],{'source':'s101'},True,7,None])
def test_bad_source_types_are_not_coerced_or_selected(executor,bad_source):
    plan={'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':args(source=bad_source)}]}
    before=copy.deepcopy(plan)
    execution=executor.execute(plan)
    assert execution['receipts'][0]['status']=='TOOL_POLICY_BLOCKED'
    assert execution['receipts'][0]['reason']=='SOURCE_OR_OPERATOR_TYPE_INVALID'
    assert not executor.db.requests
    answer=render(plan,execution,coverage=executor.coverage)
    assert answer['projection_errors'] and answer['spatial_tasks']=={}
    assert plan==before


@pytest.mark.parametrize('bad_targets',[['Wreck',{}],{'Wreck':True},'Wreck',42])
def test_bad_target_types_are_not_projected_to_object_keys(executor,bad_targets):
    plan={'action':'search','tool_calls':[{'tool_id':'spatial.query','arguments':args(feature_types=bad_targets)}]}
    execution=executor.execute(plan)
    assert execution['receipts'][0]['reason']=='FEATURE_TYPES_INVALID'
    result=render(plan,execution,coverage=executor.coverage)
    assert result['spatial_tasks']=={} and result['projection_errors']
    assert not executor.db.requests


@pytest.mark.parametrize('field,value',[('relation',[]),('relation',{}),('geometry_ref',[]),('geometry_ref',{})])
def test_unhashable_operator_and_geometry_ref_rejected_before_db(executor,field,value):
    with pytest.raises(ToolBlocked):
        executor.call('spatial.query',args(**{field:value}))
    assert not executor.db.requests


def test_unexpected_render_error_preserves_execution_and_does_not_abort_next_branch():
    branch={'status':'EXECUTOR_RETURNED','candidate_plan':{'answer':'unverified'},
            'execution':{'receipts':[]},'execution_observation':{'execution_attempted':False}}
    original_execution=copy.deepcopy(branch['execution'])
    def fail(*args,**kwargs):raise TypeError('fixture malformed renderer data')
    project_branch_answer(branch,{},renderer=fail)
    assert branch['status']=='ANSWER_PROJECTION_ERROR'
    assert branch['emitted_answer'] is None
    assert branch['answer_projection_error']['answer_repaired'] is False
    assert branch['execution']==original_execution
    following={'status':'VALIDATOR_BLOCKED','candidate_plan':{'action':'clarify','answer':'Provide geometry'},'execution':{}}
    project_branch_answer(following,{})
    assert following['emitted_answer']['status']=='NEEDS_USER_INPUT'


@pytest.mark.parametrize('value',['NaN','Infinity','-Infinity','1e999'])
def test_nonfinite_nested_model_value_rejected_before_plan_freeze(value):
    raw='{"tool_calls":[{"tool_id":"spatial.query","arguments":{"radius_m":'+value+'}}]}'
    plan,valid,errors=parse_candidate(raw)
    assert plan is None and valid is False
    assert errors==['INVALID_OR_NONFINITE_JSON']


def test_new_shared_output_schema_accepts_advertised_covers_without_changing_old_schema():
    from research.marine_geollm_scie.baselines.plan_comparison import parse_plan,PLAN_SCHEMA
    fixture=json.loads((Path(__file__).parent/'fixtures/v1_q1_02_invalid_source.json').read_text(encoding='utf-8'))
    plan=fixture['candidate_plan'];plan['spatial_relation']='covers'
    raw=json.dumps(plan)
    assert parse_candidate(raw)[1] is True
    assert parse_candidate(raw)[0]['spatial_relation']=='covers'
    assert parse_plan(raw)[1] is False
    assert 'covers' not in PLAN_SCHEMA['properties']['spatial_relation']['enum']
