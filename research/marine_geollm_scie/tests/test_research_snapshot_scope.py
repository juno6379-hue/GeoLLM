"""Research source authority tests; fixture rows are not spatial GOLD."""
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from research.marine_geollm_scie.baselines.v2_runtime import (
    V2Executor, ObservedDatabase, ResearchBindingAdapter, ToolBlocked,
    snapshot_identity_sql,
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FixtureDatabase:
    container='marine-scie-pilot-db'
    database='scie_model_v3'
    scope='metadata'
    events=[]
    def query(self, body, args):
        if self.scope=='binding_metadata':
            return [{'present':True,'selectable':True,'columns':['geometry']}]
        return [{'source_sha256':self.expected, 'row_count':1, 'schema_matches':True}]


@pytest.fixture
def subject(tmp_path):
    data=b'feature_instance_id,geometry\n1,0101\n'
    (tmp_path/'rows.csv').write_bytes(data)
    record={'relation':'projection.s101_feature_current',
            'columns':[['feature_instance_id','bigint'],['geometry','geometry']],
            'rows':1,'sha256':sha(data),'csv_path':'rows.csv',
            'coverage':{'selection':'BOUNDED_SUBSET','bbox_epsg4326':[128.9,34.9,129.3,35.3]}}
    manifest={'status':'LOADED_VERIFIED','db_identity':{'container':FixtureDatabase.container,
              'database':FixtureDatabase.database},'relations':[record]}
    pin=tmp_path/'manifest.json';pin.write_text(json.dumps(manifest))
    catalogue=tmp_path/'catalogue.json';catalogue.write_text(json.dumps({'features':[{'code':'Wreck'}]}))
    db=FixtureDatabase();db.expected=record['sha256']
    executor=V2Executor(db,catalogue=catalogue,catalogue_sha256=sha(catalogue.read_bytes()),anchors=[],
        snapshot_manifest={'path':str(pin),'sha256':sha(pin.read_bytes())},
        coverage={'s101':{'scope_verified':True,'bbox_epsg4326':[128.9,34.9,129.3,35.3],
                         'source_sha256':record['sha256']}})
    return executor,record,pin


def test_exact_snapshot_and_live_identity_receipt(subject):
    executor,record,_=subject
    adapter=ResearchBindingAdapter(executor)
    adapter._register_source('s101')
    binding=SimpleNamespace(dataset_id='s101',relation=record['relation'])
    contract=adapter.layer_registry['layers']['s101']['corpus_contract']
    receipt=adapter.verify_corpus_identity(binding,contract)
    assert receipt['status']=='VERIFIED'
    assert receipt['source_scope']['kind']=='RESEARCH_SNAPSHOT_DOMAIN'
    assert receipt['authority_scope']=='RESEARCH_FROZEN_SOURCE_ONLY'
    assert receipt['real_world_completeness']=='UNKNOWN' and receipt['absence_certified'] is False
    assert 'nearest_feature' not in contract['allowed_operations']


@pytest.mark.parametrize('change',['manifest','csv','database','scope_hash','bounds','missing_pin'])
def test_unverified_inputs_fail_closed(subject,change):
    executor,record,pin=subject
    if change=='manifest':pin.write_text('{}')
    if change=='csv':(pin.parent/'rows.csv').write_text('modified')
    if change=='database':executor.db.database='production'
    if change=='scope_hash':executor.coverage['s101']['source_sha256']='f'*64
    if change=='bounds':executor.coverage['s101']['bbox_epsg4326']=[120,30,140,40]
    if change=='missing_pin':executor.snapshot_manifest=None
    with pytest.raises((ToolBlocked, ValueError)):
        ResearchBindingAdapter(executor)._register_source('s101')


def test_live_db_mismatch_is_not_verified(subject):
    executor,record,_=subject
    adapter=ResearchBindingAdapter(executor);adapter._register_source('s101')
    executor.db.expected='0'*64
    assert adapter.verify_corpus_identity(SimpleNamespace(dataset_id='s101',relation=record['relation']),
        adapter.layer_registry['layers']['s101']['corpus_contract'])=={'status':'UNVERIFIED'}


def test_common_executor_rejects_scope_expansion_before_any_sql(subject):
    executor, _, _ = subject
    executor.coverage['s101']['bbox_epsg4326'] = [120,30,140,40]
    executor.db.events = []
    with pytest.raises(ToolBlocked, match='RESEARCH_SUBSET_SCOPE_MISMATCH'):
        executor.call('spatial.query', {'source':'s101', 'relation':'dwithin', 'radius_m':1000,
            'feature_types':['Wreck'], 'reference_geometry':'POINT(131.87 37.24)', 'crs':'EPSG:4326'})
    assert executor.db.events == []


def test_atomic_guard_precedes_query_same_readonly_transaction(subject,monkeypatch):
    _,record,_=subject
    commands=[]
    def process(command,**kwargs):
        commands.append(kwargs['input'])
        return SimpleNamespace(returncode=0,stdout='[]',stderr='')
    monkeypatch.setattr('research.marine_geollm_scie.baselines.v2_runtime.subprocess.run',process)
    db=ObservedDatabase();db.source_guard=record;db.scope='spatial'
    assert db.query('SELECT 17 AS source_id',{})==[]
    sql=commands[0]
    assert sql.startswith('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;')
    assert sql.index('RESEARCH_SNAPSHOT_IDENTITY_MISMATCH')<sql.index('SELECT 17 AS source_id')
    assert sql.endswith('ROLLBACK;') and record['sha256'] in sql


def test_atomic_mismatch_does_not_claim_spatial_execution(subject,monkeypatch):
    _,record,_=subject
    monkeypatch.setattr('research.marine_geollm_scie.baselines.v2_runtime.subprocess.run',
        lambda *a,**k:SimpleNamespace(returncode=1,stdout='',stderr='ERROR: RESEARCH_SNAPSHOT_IDENTITY_MISMATCH'))
    db=ObservedDatabase();db.source_guard=record;db.scope='spatial'
    with pytest.raises(RuntimeError):db.query('SELECT 17',{})
    assert db.events[-1]['sql_executed'] is False
    assert db.events[-1]['source_identity_status']=='MISMATCH_BEFORE_SPATIAL_SQL'


def test_sql_only_fixed_identifiers(subject):
    _,record,_=subject
    record['columns'][0][0]='id; DROP TABLE x'
    with pytest.raises(ValueError):snapshot_identity_sql(record)


def test_copy_boolean_encoding_and_exact_schema_guard():
    sql = snapshot_identity_sql({'relation':'serving.navigation_aid_current',
        'columns':[['source_id','text'],['active','boolean']]})
    assert "THEN 't'" in sql and "THEN 'f'" in sql
    assert "ARRAY['source_id','active'] AS schema_matches" in sql


def test_control_binding_keeps_explicit_source(subject):
    executor,_,_=subject
    adapter=ResearchBindingAdapter(executor)
    result=adapter.build_bindings({'analysis_type':'feature_search_by_radius'},
        {'filters':{'source':'s101'},'tool':'spatial.query'})
    assert not result.blockers
    assert result.data_bindings[0].dataset_id=='s101'
    assert result.data_bindings[0].snapshot_version.startswith('sha256:')


@pytest.mark.parametrize('sql_executed,succeeded,expected',[(False,False,False),(None,None,None),(True,True,True)])
def test_executor_preserves_confirmed_guard_block_vs_unknown_transport(subject,monkeypatch,sql_executed,succeeded,expected):
    executor,_,_=subject
    executor.db.events=[]
    def invoke(tool,args):
        executor.db.events.append({'scope':'spatial','sql_executed':sql_executed,'succeeded':succeeded})
        if succeeded is not True:
            raise RuntimeError('guard or transport failure')
        return {'rows':[]}
    monkeypatch.setattr(executor,'call',invoke)
    result=executor.execute({'tool_calls':[{'tool_id':'spatial.query','arguments':{}}]})
    trace=result['execution_observation']
    assert trace['sql_executed'] is expected
    assert trace['execution_started'] is expected
    assert trace['execution_succeeded'] is expected


def test_real_executor_requires_pin_before_starting(subject):
    executor,_,pin=subject
    catalogue=pin.parent/'catalogue.json'
    with pytest.raises(ToolBlocked,match='RESEARCH_SNAPSHOT_PIN_REQUIRED'):
        V2Executor(ObservedDatabase(),catalogue=catalogue,catalogue_sha256=sha(catalogue.read_bytes()),
                   anchors=[],coverage=executor.coverage)


def test_real_database_rejects_direct_unguarded_spatial_query(monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('No subprocess may start without the spatial source guard')
    monkeypatch.setattr('research.marine_geollm_scie.baselines.v2_runtime.subprocess.run',forbidden)
    db=ObservedDatabase();db.scope='spatial'
    with pytest.raises(ToolBlocked,match='RESEARCH_ATOMIC_SOURCE_GUARD_REQUIRED'):
        db.query('SELECT 1',{})
    assert db.events==[]


def test_real_executor_rechecks_pin_if_removed_after_construction(subject,monkeypatch):
    executor,_,_=subject
    executor.db=ObservedDatabase()
    executor.snapshot_manifest=None
    with pytest.raises(ToolBlocked,match='RESEARCH_SNAPSHOT_PIN_REQUIRED'):
        executor.call('spatial.query',{'source':'s101','relation':'dwithin','radius_m':1000,
            'crs':'EPSG:4326','feature_types':['Wreck'],'reference_geometry':'POINT(129.05 35.1)'})
    assert executor.db.events==[]
