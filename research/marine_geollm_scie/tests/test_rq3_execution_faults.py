import csv,json
from types import SimpleNamespace
from shapely.geometry import Point,MultiPoint,mapping
import pytest
from research.marine_geollm_scie.runners.rq3_execution_faults import (
    REF,mutate_sql,FaultDatabase,source_oracle,score_execution,sha,verify_contract)
from research.marine_geollm_scie.baselines.v2_runtime import spatial_statement,ToolBlocked
from research.marine_geollm_scie.evaluation.rq3_contract import summarize,method_table,paired_ci


@pytest.mark.parametrize('fault',['wrong_reference','wrong_distance_method','wrong_crs','truncation'])
def test_radius_mutation_changes_sql_without_plan_repair(fault):
    body=spatial_statement('marine_places','dwithin')
    assert mutate_sql(body,fault)!=body
    assert 'serving.marine_gazetteer_current' in mutate_sql(body,fault)


def test_fault_requires_correct_injection_point():
    with pytest.raises(ToolBlocked):mutate_sql('SELECT 1','wrong_reference')
    with pytest.raises(ToolBlocked):mutate_sql(spatial_statement('marine_places','dwithin'),'wrong_predicate')


def test_wrapper_retains_atomic_guard_and_metadata_unmutated(monkeypatch):
    captured=[]
    def process(*args,**kwargs):captured.append(kwargs['input']);return SimpleNamespace(returncode=0,stdout='[]',stderr='')
    monkeypatch.setattr('research.marine_geollm_scie.baselines.v2_runtime.subprocess.run',process)
    db=FaultDatabase('truncation');db.scope='metadata';db.query('SELECT 1',{})
    assert not db.injections
    db.source_guard={'relation':'serving.marine_gazetteer_current','columns':[['source_id','text']], 'rows':1,'sha256':'a'*64}
    db.scope='spatial';db.query(spatial_statement('marine_places','dwithin'),{})
    assert db.injections[0]['source_guard_retained']
    assert 'RESEARCH_SNAPSHOT_IDENTITY_MISMATCH' in captured[1] and 'LIMIT 1001' not in captured[1]
    assert captured[1].index('RESEARCH_SNAPSHOT_IDENTITY_MISMATCH')<captured[1].index('LIMIT 1')


def test_independent_oracle_points_and_nonempty_gate(tmp_path):
    source=tmp_path/'source.csv'
    with source.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['source_id','geometry']);writer.writeheader()
        writer.writerow({'source_id':'near','geometry':MultiPoint([(129.05,35.1)]).wkb_hex})
        writer.writerow({'source_id':'far','geometry':MultiPoint([(130,36)]).wkb_hex})
    args={'reference_geometry':'POINT(129.05 35.1)','radius_m':1000,'relation':'dwithin'}
    assert [r['source_id'] for r in source_oracle(source,args)]==['near']
    with pytest.raises(ValueError,match='Nonempty'):source_oracle(source,dict(args,reference_geometry='POINT(0 0)'))


def test_spatial_score_checks_geometry_not_only_ids():
    expected=MultiPoint([(129.05,35.1)])
    oracle={'objects':[{'source_id':'one','geometry_ewkb':expected.wkb_hex}]}
    result={'execution_observation':{'execution_succeeded':True},'receipts':[{'result':{'rows':[{'source_id':'one','geometry':mapping(Point(0,0)),'geometry_ewkb':Point(0,0).wkb_hex}]}}]}
    score=score_execution({},oracle,result,[])
    assert score['object_set_match'] and not score['geometry_match'] and not score['spatial_correct']
    result['execution_observation']['execution_succeeded']=False
    assert score_execution({},oracle,result,[])['spatial_correct'] is None


def test_original_geometry_telemetry_avoids_display_precision_false_failure():
    expected=MultiPoint([(131.8713972229871,37.2387138879871)])
    args={'reference_geometry':'POINT(131.87 37.24)','radius_m':5000,'relation':'dwithin','crs':'EPSG:4326'}
    oracle={'objects':[{'source_id':'one','geometry_ewkb':expected.wkb_hex}],
            'reference_geometry':args['reference_geometry'],'distance_m':5000,'relation':'dwithin'}
    result={'execution_observation':{'execution_succeeded':True},'receipts':[{'result':{'rows':[{
        'source_id':'one','geometry':mapping(MultiPoint([(131.871397223,37.238713888)])),
        'geometry_ewkb':expected.wkb_hex}]}}]}
    injection={'executed_sql':spatial_statement('marine_places','dwithin'),'arguments':args}
    assert score_execution({},oracle,result,[injection])['spatial_correct'] is True
    del args['crs'] # Real executor validates CRS before producing SQL arguments.
    assert score_execution({},oracle,result,[injection])['spatial_correct'] is True
    injection['executed_sql']=mutate_sql(injection['executed_sql'],'wrong_distance_method')
    assert score_execution({},oracle,result,[injection])['relation_match'] is False


def test_method_table_requires_same_frozen_contract():
    case=dict(row(),query_sha256='a'*64,oracle_sha256='b'*64)
    with pytest.raises(ValueError):method_table([dict(row(),method='B3')],[case])
    table=method_table([dict(row(),method='B3')],[case],contract_sha256='c'*64)
    assert table['B3']['ESR']['value']==1


def row(cid='a',group='g',e=True,s=True):
    return dict(case_id=cid,equivalence_group=group,repeat_id=1,eligible=True,
                execution_success=e,spatial_correct=s,semantic_correct=True,evidence_correct=True,
                query_sha256='a'*64,oracle_sha256='b'*64,contract_sha256='c'*64)


def test_zero_success_conditional_metrics_unmeasured():
    out=summarize([row(e=False,s=None)])
    assert out['ESR']['value']==0 and out['Spatial_Correct']['value']==0
    assert out['CGE']['value'] is None and out['SSFR']['value'] is None
    assert out['EVQSR']['value'] is None


def test_missing_methods_preserve_denominator():
    table=method_table([], [{'case_id':'a','equivalence_group':'g','eligible':True}])
    assert len(table)==8
    assert all(v['ESR']['denominator']==1 and v['ESR']['missing']==1 for v in table.values())


def test_paired_cohort_and_small_group_ci():
    a=[row()];b=[row(s=False)]
    assert paired_ci(a,b,samples=100)['metrics']['Spatial_Correct']['ci95'] is None
    with pytest.raises(ValueError):paired_ci(a,[dict(b[0],oracle_sha256='d'*64)],samples=100)
    a.append(row('b','h'));b.append(row('b','h',s=False))
    out=paired_ci(a,b,samples=100)
    assert out['metrics']['Spatial_Correct']['difference_B_minus_A']==-1
    assert out['metrics']['SSFR']['difference_B_minus_A']==1
    b[1]['execution_success']=None
    assert paired_ci(a,b,samples=100)['metrics']['SSFR']['ci95'] is None


def test_contract_tamper_fails(tmp_path):
    data=b'{}';(tmp_path/'contract.json').write_bytes(data)
    (tmp_path/'manifest.json').write_text(json.dumps({'files':{'contract.json':sha(data)},'contract_sha256':sha(data)}))
    assert verify_contract(tmp_path)[0]=={}
    (tmp_path/'contract.json').write_text('{"mutated":true}')
    with pytest.raises(ValueError):verify_contract(tmp_path)
