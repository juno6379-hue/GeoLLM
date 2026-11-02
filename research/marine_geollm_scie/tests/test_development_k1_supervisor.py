"""Supervisor lifecycle and completion gates; never start a model or child."""
import json
from pathlib import Path
import shutil
import pytest
from research.marine_geollm_scie.runners import supervise_development_k1 as supervisor


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')


def setup_workspace(tmp_path,monkeypatch):
    (tmp_path/'outputs').mkdir()
    contract=tmp_path/'contract.json';save(contract,{'base_observations':144,'fault_observations':207})
    monkeypatch.setattr(supervisor,'ROOT',tmp_path)
    monkeypatch.setattr(supervisor,'CONTRACT',contract)
    return tmp_path/'outputs/eight_comparison_active.lock'


@pytest.mark.parametrize('failure',['interrupt','nonzero','exception'])
def test_abnormal_exit_retains_lock_for_surviving_children_or_containers(tmp_path,monkeypatch,failure):
    lock=setup_workspace(tmp_path,monkeypatch)
    class Child:
        pid=424242
        def wait(self):
            if failure=='interrupt':raise KeyboardInterrupt('synthetic stop')
            if failure=='exception':raise RuntimeError('synthetic wait error')
            return 2
    monkeypatch.setattr(supervisor.subprocess,'Popen',lambda *a,**k:Child())
    with pytest.raises((KeyboardInterrupt,RuntimeError)):
        supervisor.run(tmp_path/'run',tmp_path/'snapshot')
    receipt=json.loads(lock.read_text(encoding='utf8'))
    status=json.loads((tmp_path/'run/status.json').read_text(encoding='utf8'))
    assert receipt['automatic_restart_allowed'] is False
    assert receipt['child_or_container_may_remain'] is True
    assert status['lock_retained'] is True
    if failure!='nonzero':assert receipt['child_pid']==424242
    # A second run cannot silently take the retained lock.
    with pytest.raises(FileExistsError):supervisor.run(tmp_path/'run2',tmp_path/'snapshot2')


def test_immutable_benchmark_file_change_rejected_even_if_manifest_unchanged(tmp_path):
    benchmark=tmp_path/'benchmark'
    shutil.copytree(supervisor.BENCHMARK,benchmark)
    snapshot=tmp_path/'snapshot.json';save(snapshot,{'relations':[],'files':[]})
    bundle={'snapshot_manifest':{'path':str(snapshot),'sha256':supervisor.sha(snapshot)},
        'measurement_files':[],'benchmark_path':str(benchmark),
        'benchmark_manifest_sha256':supervisor.sha(benchmark/'manifest.json')}
    supervisor.verify_frozen(bundle)
    with (benchmark/'queries.jsonl').open('a',encoding='utf8') as stream:stream.write('\n')
    with pytest.raises(ValueError,match='artifact changed'):supervisor.verify_frozen(bundle)


def write_expanded(output):
    from research.marine_geollm_scie.runners.expanded_fault_runner import load_contract
    contract,_,_=load_contract(supervisor.FAULTS)
    rows=[{'case_id':c['case_id'],'method':m} for c in contract['cases'] for m in ('B4','P0','H')]
    path=output/'expanded_faults/rows.jsonl';path.parent.mkdir(parents=True)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf8')
    manifest={'status':'COMPLETED_CONTROLLED_DIAGNOSTICS','rows':207,'expected_rows':207,
        'rows_sha256':supervisor.sha(path),'contract_manifest_sha256':supervisor.sha(supervisor.FAULTS/'manifest.json')}
    save(path.parent/'manifest.json',manifest)
    save(output/'expanded_report/summary.json',{'status':'CONTROLLED_PROTOCOL_DIAGNOSTICS','raw_observation_rows':207})
    save(output/'expanded_report/manifest.json',{'run_manifest_sha256':supervisor.sha(path.parent/'manifest.json'),
        'rows_sha256':supervisor.sha(path)})
    return rows


def test_207_gate_requires_exact_rows_and_report_lineage(tmp_path):
    rows=write_expanded(tmp_path)
    assert supervisor.verify_expanded_collection(tmp_path)['raw_rows']==207
    path=tmp_path/'expanded_faults/rows.jsonl'
    rows[-1]=rows[0]
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf8')
    manifest=json.loads((path.parent/'manifest.json').read_text(encoding='utf8'));manifest['rows_sha256']=supervisor.sha(path)
    save(path.parent/'manifest.json',manifest)
    with pytest.raises(ValueError,match='missing or duplicate'):supervisor.verify_expanded_collection(tmp_path)


def test_normal_collection_only_releases_lock_and_runs_rq5_then_review_template(tmp_path,monkeypatch):
    lock=setup_workspace(tmp_path,monkeypatch)
    output=tmp_path/'run';snapshot=tmp_path/'snapshot';stages=[]
    monkeypatch.setattr(supervisor,'verify_frozen',lambda bundle:None)
    from research.marine_geollm_scie.runners import supervise_eight
    monkeypatch.setattr(supervise_eight,'verify_execution_measurement',lambda summary:None)
    class Child:
        pid=424242
        def __init__(self,command,**kwargs):
            self.stage=Path(kwargs['stdout'].name).stem
            self.command=command;stages.append((self.stage,command))
        def wait(self):
            if self.stage=='freeze':save(snapshot/'snapshot_manifest.json',{'relations':[],'files':[]})
            elif self.stage=='profiles':save(output/'profiles/baseline_profile.json',{})
            elif self.stage=='rq3_contract':save(output/'rq3_contract/manifest.json',{})
            elif self.stage=='base_report':save(output/'base_report/summary.json',{'completion_gate':{'observation_comparison_complete':True}})
            elif self.stage=='expanded_faults':write_expanded(output)
            return 0
    monkeypatch.setattr(supervisor.subprocess,'Popen',Child)
    result=supervisor.run(output,snapshot)
    assert not lock.exists()
    assert result['status']=='COLLECTED_PENDING_RQ1_ANNOTATION_AND_FINAL_REPORT'
    names=[s[0] for s in stages]
    assert names.index('base_report') < names.index('rq3_method_report') < names.index('rq5_report') < names.index('expanded_faults')
    assert names[-1]=='rq1_review_template'
    assert result['expanded_collection_gate']['raw_rows']==207
    assert result['scientific_completion'] is False
    assert result['required_next']==['RQ1_new_36_raw_annotations','independent_final_gate']
