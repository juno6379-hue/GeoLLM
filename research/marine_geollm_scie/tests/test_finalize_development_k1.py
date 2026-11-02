"""Offline finalization gates: no model, database, API or holdout access."""
import copy
import json
from pathlib import Path

import pytest

from research.marine_geollm_scie.runners import finalize_development_k1 as f


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


def lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf8')


@pytest.fixture
def base(tmp_path, monkeypatch):
    run=tmp_path/'run'; benchmark=tmp_path/'benchmark'
    monkeypatch.setattr(f, 'BENCHMARK', benchmark)
    cases=[{'case_id':f'C{i}', 'query':f'query {i}'} for i in range(18)]
    lines(benchmark/'answer_contracts.jsonl', cases)
    lines(benchmark/'queries.jsonl', cases)
    ident={k:'new-'+k for k in ('system_source_sha256','adapter_sha256','model_profile_sha256',
        'source_snapshot_sha256','benchmark_inputs_sha256','method_definitions_sha256')}
    pin={'path':str(tmp_path/'snapshot.json'),'sha256':ident['source_snapshot_sha256']}
    profile={'execution_identity':ident, 'snapshot_manifest':pin}
    put(run/'profiles/baseline_profile.json',profile)
    put(run/'measurement_freeze.json',{'snapshot_manifest':pin,'benchmark_manifest_sha256':'gold-new',
        'measurement_files':[{'path':str(run/'profiles/baseline_profile.json'),'sha256':f.sha(run/'profiles/baseline_profile.json')}]})
    manifest={'execution_identity':ident,'benchmark_sha256':'gold-new','repeats':[0],
        'status':'COMPLETED_OBSERVATIONS','expected_rows':144,'profile_sha256':f.sha(run/'profiles/baseline_profile.json')}
    put(run/'comparison/manifest.json',manifest)
    rows=[]
    for c in cases:
        for method in ('B0','B1','B2','B3','B4','P0','H','P1'):
            row={**c,'method':method,'repeat':0,'benchmark_sha256':'gold-new','execution_identity':ident,
                'initial_plan_sha256':'shared-'+c['case_id'],'review_artifact_sha256':'review-'+c['case_id'],
                'lossless_compilation_verified':True,'domain_tools_enabled':method!='B0','status':'INVALID_RESPONSE'}
            path=run/'comparison/raw'/f'{c["case_id"]}_{method}.json';put(path,row)
            row={**row,'raw_artifact_path':path.relative_to(run/'comparison').as_posix(),'raw_artifact_sha256':f.sha(path)}
            rows.append(row)
    summary={'completion_gate':{'observation_comparison_complete':True}}
    put(run/'base_report/summary.json',summary)
    def save():
        lines(run/'comparison/observations.jsonl',rows)
        put(run/'base_report/manifest.json',{'observations_sha256':f.sha(run/'comparison/observations.jsonl'),
            'run_manifest_sha256':f.sha(run/'comparison/manifest.json'),'benchmark_sha256':'gold-new',
            'report_files':{'summary.json':f.sha(run/'base_report/summary.json')}})
    save()
    def replace_row(index, **changes):
        rows[index].update(changes)
        path=run/'comparison'/rows[index]['raw_artifact_path']
        put(path,{k:v for k,v in rows[index].items() if k not in ('raw_artifact_path','raw_artifact_sha256')})
        rows[index]['raw_artifact_sha256']=f.sha(path);save()
    return run,rows,save,replace_row


def test_failed_model_rows_are_valid_observations(base):
    run,rows,_,_=base
    assert len(f.verify_base(run)[0])==144
    assert all(r['status']=='INVALID_RESPONSE' for r in rows)


@pytest.mark.parametrize('change,match',[
    ({'case_id':'C1','query':'query 1'},'Recomputed base gate'),
    ({'query':'wrong query'},'Frozen query'),
    ({'repeat':1},'Recomputed base gate'),
    ({'execution_identity':{'source_snapshot_sha256':'old'}},'Recomputed base gate'),
    ({'benchmark_sha256':'old-gold'},'Recomputed base gate'),
    ({'domain_tools_enabled':True},'Recomputed base gate'),
])
def test_same_counts_do_not_bypass_identity_or_case_gates(base,change,match):
    run,_,_,replace=base;replace(0,**change)
    with pytest.raises(ValueError,match=match):f.verify_base(run)


@pytest.mark.parametrize('index,change',[
    (3,{'initial_plan_sha256':'different'}),
    (6,{'review_artifact_sha256':'different'}),
    (5,{'lossless_compilation_verified':False}),
])
def test_shared_plan_review_lossless_gates_recomputed(base,index,change):
    run,_,_,replace=base;replace(index,**change)
    with pytest.raises(ValueError,match='Recomputed base gate'):f.verify_base(run)


def test_preserved_old_run_cannot_claim_new_snapshot(base):
    run,_,save,_=base
    profile=f.read(run/'profiles/baseline_profile.json')
    profile['snapshot_manifest']['sha256']='different'
    put(run/'profiles/baseline_profile.json',profile);save()
    with pytest.raises(ValueError,match='measurement freeze'):f.verify_base(run)


def test_preserved_summary_cannot_allow_report_path_escape(base):
    run,_,_,_=base
    path=run/'base_report/manifest.json';manifest=f.read(path)
    manifest['report_files']['../measurement_freeze.json']=f.sha(run/'measurement_freeze.json');put(path,manifest)
    with pytest.raises(ValueError,match='escapes'):f.verify_base(run)


def test_raw_query_must_match_projection_even_when_digest_matches(base):
    run,rows,save,_=base
    path=run/'comparison'/rows[0]['raw_artifact_path'];raw=f.read(path)
    raw['query']='an old different question';put(path,raw)
    rows[0]['raw_artifact_sha256']=f.sha(path);save()
    with pytest.raises(ValueError,match='Raw query projection'):f.verify_base(run)


@pytest.mark.parametrize('mutation',['missing_profile_pin','partial_collection','wrong_profile_sha','extra_repeat'])
def test_collection_and_profile_freeze_are_required(base,mutation):
    run,_,save,_=base
    if mutation=='missing_profile_pin':
        path=run/'measurement_freeze.json';value=f.read(path);value['measurement_files']=[]
    else:
        path=run/'comparison/manifest.json';value=f.read(path)
        if mutation=='partial_collection':value['status']='RUNNING'
        elif mutation=='wrong_profile_sha':value['profile_sha256']='old'
        else:value['repeats']=[0,1]
    put(path,value);save()
    with pytest.raises(ValueError):f.verify_base(run)


@pytest.fixture
def diagnostics(tmp_path):
    from research.marine_geollm_scie.runners.rq3_execution_faults import score_execution, REF
    run=tmp_path/'diagnostic_run';folder=run/'rq3_contract'
    cases=[];rows=[]
    for i in range(8):
        case={'case_id':f'D{i}','fault':'clean' if i==0 else 'truncation','plan':{'action':'spatial'},'oracle_file':f'{i}.json'}
        oracle={'objects':[{'source_id':'a','geometry_ewkb':'0101'}], 'relation':'intersects',
            'reference_geometry':'POLYGON ((0 0,1 0,1 1,0 0))','distance_m':None}
        put(folder/case['oracle_file'],oracle);cases.append(case)
        objects=oracle['objects'] if i==0 else []
        result={'execution_observation':{'execution_succeeded':True},'receipts':[{'result':{'rows':objects}}]}
        injection={'executed_sql':REF+' geom) r ST_Intersects(p.geometry,r.geom)',
            'arguments':{'reference_geometry':oracle['reference_geometry'],'relation':'intersects','radius_m':None}}
        rows.append({'case_id':case['case_id'],'method':'COMMON_EXECUTOR_DIAGNOSTIC','repeat_id':1,
            'fault':case['fault'],'execution':result,'injections':[injection],
            **score_execution(case,oracle,result,[injection])})
    contract={'cases':cases,'frozen_code':{'source.py':'sourcehash'}}
    put(folder/'contract.json',contract);digest=f.sha(folder/'contract.json')
    put(folder/'manifest.json',{'contract_sha256':digest,
        'files':{p.name:f.sha(p) for p in folder.iterdir() if p.is_file()}})
    for i,row in enumerate(rows):
        row['contract_sha256']=digest
        raw=run/'rq3_diagnostics'/f'{i}.json'
        put(raw,{'job':{'method':row['method'],'case_id':row['case_id'],'repeat_id':1,'plan':cases[i]['plan']},'observation':row})
        row.update(raw_file=raw.name,raw_sha256=f.sha(raw))
    put(run/'rq3_diagnostics/observations.json',rows)
    put(run/'rq3_diagnostics/summary.json',{'status':'COMPLETED','observations':8,'sources_unchanged':True,
        'contract_sha256':digest,'source_before':contract['frozen_code'],'source_after':contract['frozen_code']})
    return run,rows


def test_actual_sql_diagnostics_rescore_without_database(diagnostics):
    run,_=diagnostics
    assert len(f.verify_diagnostics(run))==8


@pytest.mark.parametrize('mutation',['empty','duplicate','projection','raw_hash','fake_success','source','job'])
def test_diagnostic_summary_alone_never_proves_completion(diagnostics,mutation):
    run,rows=diagnostics;folder=run/'rq3_diagnostics'
    if mutation=='empty':rows=[]
    elif mutation=='duplicate':rows[1]=copy.deepcopy(rows[0])
    elif mutation=='projection':rows[0]['execution_success']=False
    elif mutation=='raw_hash':rows[0]['raw_sha256']='wrong'
    elif mutation=='source':
        summary=f.read(folder/'summary.json');summary['source_after']={};put(folder/'summary.json',summary)
    else:
        raw=f.read(folder/rows[0]['raw_file'])
        if mutation=='fake_success':
            rows[0]['execution']['execution_observation']['execution_succeeded']=False
            raw['observation']['execution']=rows[0]['execution']
        else:raw['job']['plan']={'action':'old-plan'}
        put(folder/rows[0]['raw_file'],raw);rows[0]['raw_sha256']=f.sha(folder/rows[0]['raw_file'])
    put(folder/'observations.json',rows)
    with pytest.raises(ValueError):f.verify_diagnostics(run)


@pytest.fixture
def finalizer_env(base,monkeypatch):
    from research.marine_geollm_scie.runners import expanded_fault_runner,report_rq5,report_rq3_methods
    run,_,_,_=base
    put(run/'status.json',{'status':'COLLECTED_PENDING_RQ1_ANNOTATION_AND_FINAL_REPORT'})
    put(run/'profiles/model_profile.json',{'profile':'new'})
    lines(run/'profiles/common_inputs.jsonl',[{'query':'new'}])
    put(run/'graph/model_graph_manifest.json',{'observed_rows':18,'source_unchanged_after':True,
        'snapshot_manifest_sha256':f.read(run/'measurement_freeze.json')['snapshot_manifest']['sha256'],
        'profile_sha256':f.sha(run/'profiles/model_profile.json'),'benchmark_sha256':f.sha(run/'profiles/common_inputs.jsonl')})
    put(run/'expanded_faults/manifest.json',{'execution_identity':f.read(run/'profiles/baseline_profile.json')['execution_identity']})
    reviews=run.parent/'new_reviews.jsonl';reviews.write_text('new reviewed answers',encoding='utf8')
    monkeypatch.setattr(f,'verify_frozen',lambda b:None)
    monkeypatch.setattr(f,'verify_diagnostics',lambda p:[])
    monkeypatch.setattr(expanded_fault_runner,'report',lambda *a:{'raw_observation_rows':207})
    monkeypatch.setattr(report_rq5,'run',lambda *a,**k:{'status':'COMPLETE_OBSERVATION_COHORT'})
    monkeypatch.setattr(report_rq3_methods,'run',lambda *a,**k:{})
    def measure(*args,**kwargs):
        put(args[1]/'status.json',{'measured':True,'observations':36,'contract_sha256':f.CONTRACT_SHA256})
    monkeypatch.setattr(f,'measure_rq1',measure)
    return run,reviews,run.parent/'final_report'


def test_success_is_observation_completion_not_human_or_holdout(finalizer_env):
    run,reviews,output=finalizer_env
    result=f.finalize(run,reviews,output)
    assert result['base_observations']==144
    assert result['scientific_completion'] is False
    assert result['human_new_answer_accuracy_complete'] is False
    assert result['holdout_used'] is False
    assert result['k5_complete'] is False
    assert f.read(run/'status.json')['stage']=='FINALIZED'


@pytest.mark.parametrize('mutation',['rq1_missing','rq1_old_contract','rq3_exception','rq5_partial','fault_old_identity','raw_changed','reviews_changed','snapshot_changed'])
def test_finalization_failures_never_promote_status(finalizer_env,monkeypatch,mutation):
    from research.marine_geollm_scie.runners import report_rq5,report_rq3_methods
    run,reviews,output=finalizer_env
    if mutation.startswith('rq1_'):
        def measure(*args,**kwargs):
            put(args[1]/'status.json',{'measured':mutation!='rq1_missing','observations':36,
                'contract_sha256':'old' if mutation=='rq1_old_contract' else f.CONTRACT_SHA256})
        monkeypatch.setattr(f,'measure_rq1',measure)
    elif mutation=='rq3_exception':
        def fail(*a,**k):raise ValueError('incomplete denominator')
        monkeypatch.setattr(report_rq3_methods,'run',fail)
    elif mutation=='rq5_partial':monkeypatch.setattr(report_rq5,'run',lambda *a,**k:{'status':'PARTIAL'})
    elif mutation=='fault_old_identity':put(run/'expanded_faults/manifest.json',{'execution_identity':{'source_snapshot_sha256':'old'}})
    else:
        original=f.measure_rq1
        def measure(*args,**kwargs):
            original(*args,**kwargs)
            target={'raw_changed':run/'comparison/raw/C0_B0.json','reviews_changed':reviews,
                'snapshot_changed':run/'measurement_freeze.json'}[mutation]
            target.write_text('{}',encoding='utf8')
        monkeypatch.setattr(f,'measure_rq1',measure)
    with pytest.raises((ValueError,KeyError)):f.finalize(run,reviews,output)
    assert f.read(run/'status.json')['status']=='COLLECTED_PENDING_RQ1_ANNOTATION_AND_FINAL_REPORT'
    assert not (output/'manifest.json').exists()
