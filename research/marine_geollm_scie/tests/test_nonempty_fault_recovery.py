"""Exercise actual runner/report control flow with no models or database calls."""
import json
from types import SimpleNamespace
import pytest
from research.marine_geollm_scie.runners import eight_fault_recovery as runner
from research.marine_geollm_scie.runners.report_eight_faults import (
    load_verified_faults, recovery_measurement_coverage, verify_recovery_measurement,
    recovery_measurement_summary, recovery_measurement_lines)
from research.marine_geollm_scie.evaluation.v2_fault_results import summarize_faults


@pytest.mark.parametrize('ids,status,reason', [(['11'],'ELIGIBLE',None),([], 'EXCLUDED','RECOVERY_ORACLE_EMPTY'),
    (None,'UNMEASURED','RECOVERY_ORACLE_MISSING_OR_INVALID'),([None],'UNMEASURED','RECOVERY_ORACLE_MISSING_OR_INVALID')])
def test_oracle_scope(ids,status,reason):
    scope=runner.recovery_oracle_scope(ids)
    assert scope['status']==status and scope['reason']==reason
    assert scope['nonempty_eligible'] is (status=='ELIGIBLE')


@pytest.mark.parametrize('ids', [['11'], [], None])
def test_runner_keeps_fault_rows_but_excludes_empty_or_missing_restoration(tmp_path,monkeypatch,ids):
    profile={'benchmark_sha256':'fixture_gold','execution_identity':{'source_snapshot_sha256':'fixture_snapshot'},
             'catalogue':{'path':'fixture','sha256':'fixture'},'model':'fixture',
             'snapshot_manifest':{'path':'fixture_manifest','sha256':'fixture'},
             'coverage':{'s101':{'source_sha256':'fixture'}}}
    profile_path=tmp_path/'profile.json';profile_path.write_text(json.dumps(profile),encoding='utf8')
    calls=[]; executions=[]
    class FakeExecutor:
        def __init__(self,*args,**kwargs):
            assert kwargs['snapshot_manifest']==profile['snapshot_manifest']
            self.db=SimpleNamespace(query=lambda *a:[{'source_id':i} for i in ids] if ids is not None else None)
        def execute(self,plan):
            executions.append(plan)
            return {'execution_observation':{'observation_complete':True,'execution_started':True,'execution_succeeded':True},
                    'receipts':[{'tool_id':'spatial.query','status':'TOOL_RETURNED','result':{'rows':[{'source_id':i} for i in (ids or [])]}}],
                    'tool_calls_attempted':1,'latency_ms':1}
    monkeypatch.setattr(runner,'ensure_identity',lambda *a:None)
    monkeypatch.setattr(runner,'model_digest',lambda *a:None)
    monkeypatch.setattr(runner,'ObservedDatabase',lambda:None)
    monkeypatch.setattr(runner,'V2Executor',FakeExecutor)
    monkeypatch.setattr(runner,'validator_for',lambda *a,**k:None)
    monkeypatch.setattr(runner,'detect',lambda *a,**k:{'invalid':False,'latency_ms':0})
    monkeypatch.setattr(runner,'public_context',lambda *a:{})
    def review(*a,**k):
        calls.append(1)
        return {'input_tokens':1,'output_tokens':1,'latency_ms':1},{'invalid':False,'plan':runner.clean_plan()},[]
    monkeypatch.setattr(runner,'call_review',review)
    folder=tmp_path/'run'
    manifest=runner.run(folder,profile_path,tmp_path,execute=True)
    rows,_=load_verified_faults(folder)
    assert manifest['status']=='COMPLETED_CONTROLLED_DIAGNOSTICS'
    assert len(rows)==27 and len(calls)==9
    assert len(executions)==(13 if ids else 1)
    report=summarize_faults(rows)
    coverage=recovery_measurement_coverage(rows)
    for method in ('B4','H'):
        metric=report['overall_by_method'][method]
        assert metric['rows']==9 and metric['missing_predictions']==0
        assert coverage[method]['protocol_eligible_denominator']==6
        assert coverage[method]['nonempty_eligible_denominator']==(6 if ids else 0)
        assert metric['joint_recovery_given_attempt']['value']==(1 if ids else None)
    if not ids:
        assert all(r['recovery_success'] is None and r['spatial_correct'] is None and r['joint_success'] is None for r in rows)
        reason='RECOVERY_ORACLE_EMPTY' if ids==[] else 'RECOVERY_ORACLE_MISSING_OR_INVALID'
        assert coverage['B4']['excluded_or_unmeasured_reasons']=={reason:6}
    assert coverage['P0']['nonempty_eligible_denominator']==0
    # Exercise the actual combined-report path, using no model/database or old run.
    from research.marine_geollm_scie.runners import report_eight
    benchmark=tmp_path/'benchmark';benchmark.mkdir()
    (benchmark/'manifest.json').write_text('{}',encoding='utf8')
    (benchmark/'answer_contracts.jsonl').write_text('',encoding='utf8')
    comparison=tmp_path/'comparison';comparison.mkdir()
    (comparison/'manifest.json').write_text(json.dumps({'benchmark_sha256':'fixture_gold',
        'execution_identity':profile['execution_identity'],'repeats':[1]}),encoding='utf8')
    (comparison/'observations.jsonl').write_text('',encoding='utf8')
    monkeypatch.setattr(report_eight,'verify',lambda *a,**k:None)
    combined=report_eight.run_report(comparison,benchmark,tmp_path/'combined_report',faults=folder)
    expected=('NONEMPTY_CONTROLLED_DIAGNOSTICS' if ids else
              'NO_NONEMPTY_ELIGIBLE_CASES' if ids==[] else 'UNMEASURED_ORACLE')
    assert combined['rq4_recovery']['status']==expected
    assert combined['controlled_fault_recovery']['overall_by_method']['B4']['rows']==9
    rendered=(tmp_path/'combined_report'/'comparison_KR.md').read_text(encoding='utf8')
    assert expected in rendered
    if not ids:
        assert reason in rendered


@pytest.mark.parametrize('ids',[[],None])
def test_report_rejects_success_claim_for_ineligible_oracle(ids):
    case={'recovery_eligible':True};scope=runner.recovery_oracle_scope(ids)
    row={'method':'H',**runner.recovery_eligibility(case,'H',scope),
         'recovery_attempted':False,'recovery_success':True,'semantic_preservation':None,'spatial_correct':True,'joint_success':True}
    with pytest.raises(ValueError,match='cannot claim'):
        verify_recovery_measurement(row,case,scope)


def test_old_rows_are_not_reinterpreted_as_nonempty_measurement():
    rows=[{'method':'H','recovery_eligible':True,'joint_success':True}]
    coverage=recovery_measurement_coverage(rows)['H']
    assert coverage['legacy_or_missing_contract']==1
    assert coverage['measurement_contract_observed']==0
    measurement=recovery_measurement_summary(rows)
    assert measurement['status']=='LEGACY_PROTOCOL_NOT_NONEMPTY_VERIFIED'
    assert '미측정(구계약)' in '\n'.join(recovery_measurement_lines(measurement))
    assert rows[0]['joint_success'] is True
