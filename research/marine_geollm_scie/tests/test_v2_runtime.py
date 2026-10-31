"""Bounded adapter tests; fixture DB is not an actual spatial oracle."""
import json
import hashlib
import pytest
from research.marine_geollm_scie.baselines.v2_runtime import V2Executor,ObservedDatabase,spatial_statement,ToolBlocked
from research.marine_geollm_scie.baselines.v2_answer_projection import render
from research.marine_geollm_scie.runners.eight_method_runner import public_context,make_prompt,p1_costs


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
