import copy
import json
from pathlib import Path
import pytest
from research.marine_geollm_scie.runners.expanded_fault_contract import cases,BASES,VERSION
from research.marine_geollm_scie.runners import expanded_fault_runner as runner
from research.marine_geollm_scie.runners.matched_branches import plan_hash


def test_cohort_pairing_preserves_old_cohort_and_has_predeclared_codes():
    from research.marine_geollm_scie.runners.eight_fault_recovery import cohort
    assert len(cohort())==9
    rows=cases();assert len(rows)==69
    assert sum(r['expected_invalid'] for r in rows)==33
    assert len({r['base_scenario_id'] for r in rows})==3
    for row in rows:
        clean=next(r for r in rows if r['pair_id']==row['pair_id'] and r['pair_role']=='clean')
        assert row['clean_plan_sha256']==clean['initial_plan_sha256']
        assert row['initial_plan_sha256']==plan_hash(row['plan'])
        assert bool(row['expected_fault_codes'])==row['expected_invalid']
        assert row['changed_paths'] or not row['expected_invalid']
    assert {'semantic_ambiguity','wrong_valid_attribute','evidence_mismatch','semantic_expansion'} <= {r['error_type'] for r in rows}
    clarifications=[r for r in rows if r['pair_role']=='clean' and r['expected_behavior']=='NEEDS_USER_INPUT']
    assert len(clarifications)==6
    assert all(not r['false_block_eligible'] and not r['binary_diagnosis_eligible'] and not r['execution_eligible'] for r in clarifications)
    assert sum(r['false_block_eligible'] for r in rows)==30
    from research.marine_geollm_scie.baselines.lossless_qec import explicit_distance
    for row in rows:
        if row['error_type']=='unit' and row['pair_role']=='fault':
            value=row['plan']['tool_calls'][0]['arguments']['radius_m']
            assert isinstance(value,str)
            assert explicit_distance(value)==row['clean_plan']['tool_calls'][0]['arguments']['radius_m']


@pytest.mark.parametrize('invalid,codes,expected,result',[
    (True,['REQUEST_CRS_MISMATCH'],['REQUEST_CRS_MISMATCH'],True),
    (True,['DATA_COVERAGE_UNVERIFIED'],['REQUEST_CRS_MISMATCH'],False),
    (False,[],['REQUEST_CRS_MISMATCH'],False),
    (None,None,['REQUEST_CRS_MISMATCH'],None),
    (True,None,['REQUEST_CRS_MISMATCH'],None),
    (False,[],[],None)])
def test_binary_is_not_target_code(invalid,codes,expected,result):
    assert runner.target_diagnosis(invalid,codes,expected) is result


def test_native_code_extraction_never_uses_expected_labels():
    receipt={'invalid':True,'qecs':[{'blockers':['BLOCKED_CONFIG: REQUEST_CRS_MISMATCH',{'code':'UNSUPPORTED'}]}],
             'compilation_traces':[{'errors':['DISTANCE_VALUE_TYPE_INVALID']}]}
    assert runner.native_codes(receipt)==['DISTANCE_VALUE_TYPE_INVALID','REQUEST_CRS_MISMATCH','UNSUPPORTED']
    assert runner.native_codes({'invalid':False,'qecs':[]})==[]
    assert runner.native_codes({'invalid':None}) is None
    messages={'invalid':True,'qecs':[{'blockers':['BLOCKED_INPUT: reference geometry is unresolved',
        'distance_m must be positive','explicit research source required','BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED']} ]}
    assert runner.native_codes(messages)==['DATA_COVERAGE_UNVERIFIED','DISTANCE_NOT_POSITIVE','EXPLICIT_SOURCE_REQUIRED','MISSING_REFERENCE_GEOMETRY']
    assert 'distance_m must be positive' in runner.raw_native_codes(messages)


@pytest.mark.parametrize('failed_review',[False,True])
def test_actual_runner_and_report_with_no_model_or_db(tmp_path,monkeypatch,failed_review):
    fixture=Path(__file__).resolve().parents[1]/'fixtures/rq2_rq4_expanded_20261103_v3'
    contract,oracles,_=runner.load_contract(fixture)
    # Complete 207-row control flow; mocks do not count as actual measured performance.
    profile={'snapshot_manifest':contract['snapshot_manifest'],'execution_identity':{'fixture':'test'},
             'catalogue':{'path':'unused','sha256':'unused'},'coverage':{},'model':'fixture'}
    profile_path=tmp_path/'profile.json';profile_path.write_text(json.dumps(profile),encoding='utf8')
    class Executor:
        def __init__(self,*a,**k):pass
        def execute(self,plan):
            geometry=plan['tool_calls'][0]['arguments']['reference_geometry']
            base=next(b[0] for b in BASES if b[2]==geometry)
            return {'execution_observation':{'observation_complete':True,'execution_started':True,'execution_succeeded':True},
                'receipts':[{'tool_id':'spatial.query','status':'TOOL_RETURNED','result':{'rows':[{'source_id':i} for i in oracles[base]['object_ids']]}}],
                'tool_calls_attempted':1}
    monkeypatch.setattr(runner,'ensure_identity',lambda *a:None)
    monkeypatch.setattr(runner,'model_digest',lambda *a:None)
    monkeypatch.setattr(runner,'V2Executor',Executor)
    monkeypatch.setattr(runner,'ObservedDatabase',lambda:None)
    monkeypatch.setattr(runner,'validator_for',lambda *a,**k:None)
    monkeypatch.setattr(runner,'public_context',lambda *a:{})
    monkeypatch.setattr(runner.old,'detect',lambda plan,*a,**k:{'invalid':plan.get('action')=='clarify','qecs':[]})
    called=[]
    def review(query,context,plan,**kwargs):
        called.append(plan_hash(plan))
        candidate=next(c for c in contract['cases'] if c['query']==query and c['plan']==plan)
        if failed_review and candidate['case_id']=='WRECK_A_UNKNOWN_SOURCE_FAULT':
            return {'input_tokens':None,'output_tokens':None,'latency_ms':1},None,['SYNTHETIC_MODEL_FAILURE']
        # Test-only oracle-driven repair, not an experimental branch implementation.
        return {'input_tokens':1,'output_tokens':1,'latency_ms':1}, {'invalid':candidate['expected_invalid'],
            'detected_fault_codes':candidate['expected_fault_codes'],'plan':copy.deepcopy(candidate['clean_plan'])},[]
    monkeypatch.setattr(runner,'call_review',review)
    run=tmp_path/'run';manifest=runner.run(fixture,profile_path,tmp_path,run,execute=True)
    assert manifest['rows']==207 and len(called)==69
    summary=runner.report(run,fixture,tmp_path/'report')
    assert summary['rq2_target_codes']['B4']['binary_recall']['denominator']==33
    assert summary['rq2_target_codes']['B4']['target_fault_code_recall']['value']==(None if failed_review else 1)
    assert summary['rq2_target_codes']['P0']['target_fault_code_recall']['value']==0
    assert summary['rq4_recovery']['status']=='NONEMPTY_CONTROLLED_DIAGNOSTICS'
    assert summary['rq2_target_codes']['P0']['paired_control_false_block']['denominator']==30
    assert summary['rq2_target_codes']['P0']['paired_control_false_block']['value']==0
    assert summary['safe_abstention']['rows_excluded_from_binary_and_false_block']==18
    assert summary['safe_abstention']['value'] is None
    assert summary['overall_by_method']['B4']['forbidden_recovery_proposals']==(None if failed_review else 3)
    if failed_review:
        assert summary['rq4_detailed_metrics']['B4']['forbidden_recovery']['missing']==1
        assert summary['rq2_paired_cluster_comparison']['P0']['binary_recall']['ci95'] is None
    assert summary['overall_by_method']['P0']['forbidden_recovery_proposals'] is None
    assert summary['rq4_detailed_metrics']['B4']['human_escalation']['value'] is None
    assert summary['rq2_paired_cluster_comparison']['P0']['binary_recall']['independent_base_clusters']==3
    rows=[json.loads(x) for x in (run/'rows.jsonl').read_text(encoding='utf8').splitlines()]
    recovered=[r for r in rows if r['recovery_eligible']]
    assert recovered and all(r['joint_success'] is True for r in recovered)
    assert all(r['recovery_attempted'] is False for r in rows if r['error_type']=='semantic_ambiguity')
    clean_clarify=[r for r in rows if r['method']=='P0' and not r['binary_diagnosis_eligible']]
    assert len(clean_clarify)==6 and all(r['raw_native_invalid'] is True for r in clean_clarify)
    (run/'WRECK_A_CONTROL_CLEAN'/'B4.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='ROW_CHANGED'):runner.report(run,fixture,tmp_path/'tampered_report')
