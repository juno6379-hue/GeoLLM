"""Fresh source freeze and RQ1-RQ5 Development K1, never holdout access.

Model collection ends with an explicit pending AI annotation gate. Finalization
requires the new raw-answer RQ1 measurement, never old development labels.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
RESEARCH=ROOT/'research/marine_geollm_scie'
CONTRACT=RESEARCH/'protocol/development_k1_rq_contract_20261103.json'
BENCHMARK=RESEARCH/'benchmark/gold_v2_immutable_20261101_v1'
FAULTS=RESEARCH/'fixtures/rq2_rq4_expanded_20261103_v3'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def verify_frozen(bundle):
    from .binding_snapshot import verify_files
    from .freeze_v2_benchmark import verify as verify_benchmark
    snapshot=Path(bundle['snapshot_manifest']['path'])
    if sha(snapshot)!=bundle['snapshot_manifest']['sha256']:raise ValueError('Snapshot pin changed')
    verify_files(json.loads(snapshot.read_text(encoding='utf-8')),snapshot.parent)
    for entry in bundle['measurement_files']:
        if sha(entry['path'])!=entry['sha256']:raise ValueError('Measurement asset changed: '+entry['path'])
    verify_benchmark(Path(bundle['benchmark_path']),expected_manifest_sha256=bundle['benchmark_manifest_sha256'])


def verify_expanded_collection(output,expected_rows=207):
    """Require the exact raw set and matching verified report, including failures."""
    from .expanded_fault_runner import load_contract
    contract,_,_=load_contract(FAULTS)
    output=Path(output);run=output/'expanded_faults'
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf8'))
    rows_path=run/'rows.jsonl'
    if manifest.get('status')!='COMPLETED_CONTROLLED_DIAGNOSTICS' or manifest.get('rows')!=expected_rows or manifest.get('expected_rows')!=expected_rows:
        raise ValueError('207 fault observation gate failed')
    if sha(rows_path)!=manifest.get('rows_sha256'):raise ValueError('Fault raw hash mismatch')
    if sha(FAULTS/'manifest.json')!=manifest.get('contract_manifest_sha256'):raise ValueError('Fault contract lineage mismatch')
    rows=[json.loads(line) for line in rows_path.read_text(encoding='utf8').splitlines() if line.strip()]
    expected={(case['case_id'],method) for case in contract['cases'] for method in ('B4','P0','H')}
    if len(expected)!=expected_rows or len(rows)!=expected_rows or {(r['case_id'],r['method']) for r in rows}!=expected:
        raise ValueError('Fault rows missing or duplicate')
    report=output/'expanded_report'
    summary=json.loads((report/'summary.json').read_text(encoding='utf8'))
    provenance=json.loads((report/'manifest.json').read_text(encoding='utf8'))
    if summary.get('raw_observation_rows')!=expected_rows or summary.get('status')!='CONTROLLED_PROTOCOL_DIAGNOSTICS':
        raise ValueError('Fault report incomplete')
    if provenance.get('run_manifest_sha256')!=sha(run/'manifest.json') or provenance.get('rows_sha256')!=sha(rows_path):
        raise ValueError('Fault report provenance mismatch')
    return {'raw_rows':len(rows),'expected_rows':expected_rows,'raw_hash_verified':True,'exact_case_method_set_verified':True}


def run(output,snapshot_output):
    output=Path(output).resolve();snapshot_output=Path(snapshot_output).resolve()
    if output.exists() or snapshot_output.exists():raise FileExistsError('Fresh output/snapshot required')
    # Exclusive lock also respected by the earlier eight-method supervisor.
    lock=ROOT/'outputs/eight_comparison_active.lock'
    with lock.open('x',encoding='utf-8') as stream:
        json.dump({'pid':os.getpid(),'run':str(output),'kind':'RQ1_RQ5_DEVELOPMENT_K1'},stream)
    output.mkdir(parents=True)
    status={'status':'PREPARING','pid':os.getpid(),'stage':None,'stages':[],
        'created_at':datetime.now(timezone.utc).isoformat(),'scientific_completion':False,
        'expected_base_rows':144,'expected_fault_rows':207,'holdout_used':False}
    bundle=None;collection_complete=False
    def save():
        status['observed_at']=datetime.now(timezone.utc).isoformat();write(output/'status.json',status)
    def stage(name,module,*args):
        if bundle:verify_frozen(bundle)
        status.update(status='RUNNING',stage=name);save();print(name,flush=True)
        with (output/(name+'.log')).open('xb') as stream:
            child=subprocess.Popen([sys.executable,'-X','utf8','-m',module,*map(str,args)],
                cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            status['child_pid']=child.pid;status['last_child_pid']=child.pid;save();code=child.wait()
        status['child_pid']=None
        status['stages'].append({'stage':name,'exit_code':code,'finished_at':datetime.now(timezone.utc).isoformat()});save()
        if code:raise RuntimeError('Stage failed: '+name)
        if bundle:verify_frozen(bundle)
    profiles=output/'profiles';snapshot=snapshot_output/'snapshot_manifest.json'
    try:
        from .freeze_v2_benchmark import verify as verify_benchmark
        verify_benchmark(BENCHMARK)
        contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
        if contract['base_observations']!=144 or contract['fault_observations']!=207:
            raise ValueError('Unexpected measurement cohort')
        stage('freeze','research.marine_geollm_scie.runners.freeze_comparison_sources',
            '--parent',ROOT/'outputs/scie_model_snapshot_20261031_execution_v1/snapshot_manifest.json','--output',snapshot_output)
        stage('profiles','research.marine_geollm_scie.runners.prepare_eight_profiles',
            '--snapshot',snapshot,'--output',profiles,'--benchmark',BENCHMARK)
        stage('rq3_contract','research.marine_geollm_scie.runners.rq3_execution_faults',
            '--prepare-profile',profiles/'baseline_profile.json','--contract',output/'rq3_contract')
        assets=[CONTRACT,*profiles.glob('*'),*FAULTS.glob('*'),*(output/'rq3_contract').glob('*')]
        bundle={'version':'development_k1_frozen_measurements_v1','snapshot_manifest':{'path':str(snapshot),'sha256':sha(snapshot)},
            'measurement_files':[{'path':str(p),'sha256':sha(p)} for p in assets if p.is_file()],
            'benchmark_manifest_sha256':sha(BENCHMARK/'manifest.json'),
            'benchmark_path':str(BENCHMARK),
            'holdout_read':False,'annotation_policy':'New raw-linked AI annotation after collection under frozen extraction contract',
            'ablation_claim':False}
        write(output/'measurement_freeze.json',bundle);verify_frozen(bundle)
        stage('rq3_diagnostics','research.marine_geollm_scie.runners.rq3_execution_faults',
            '--contract',output/'rq3_contract','--output',output/'rq3_diagnostics')
        stage('graph','research.marine_geollm_scie.runners.launch_model_graph',
            '--snapshot',snapshot,'--profile',profiles/'model_profile.json','--benchmark',profiles/'common_inputs.jsonl','--output',output/'graph')
        stage('comparison','research.marine_geollm_scie.runners.eight_method_runner',
            '--profile',profiles/'baseline_profile.json','--benchmark',BENCHMARK,
            '--inputs',profiles/'common_inputs.jsonl','--p1-rows',output/'graph/production_rows.jsonl',
            '--output',output/'comparison','--execute')
        stage('base_report','research.marine_geollm_scie.runners.report_eight',
            '--run-dir',output/'comparison','--benchmark',BENCHMARK,'--output',output/'base_report')
        from .supervise_eight import verify_execution_measurement
        summary=json.loads((output/'base_report/summary.json').read_text(encoding='utf-8'))
        if not summary['completion_gate']['observation_comparison_complete']:raise ValueError('144 observation gate failed')
        verify_execution_measurement(summary)
        stage('rq3_method_report','research.marine_geollm_scie.runners.report_rq3_methods',
            '--observations',output/'comparison/observations.jsonl','--scores',output/'base_report',
            '--benchmark',BENCHMARK,'--output',output/'rq3_method_report')
        stage('rq5_report','research.marine_geollm_scie.runners.report_rq5',
            '--observations',output/'comparison/observations.jsonl','--scores',output/'base_report',
            '--output',output/'rq5_report')
        stage('expanded_faults','research.marine_geollm_scie.runners.expanded_fault_runner',
            '--contract-dir',FAULTS,'--profile',profiles/'baseline_profile.json','--benchmark',BENCHMARK,
            '--output',output/'expanded_faults','--execute')
        stage('expanded_report','research.marine_geollm_scie.runners.expanded_fault_runner',
            '--contract-dir',FAULTS,'--report-run',output/'expanded_faults','--output',output/'expanded_report')
        status['expanded_collection_gate']=verify_expanded_collection(output,contract['fault_observations'])
        stage('rq1_review_template','research.marine_geollm_scie.runners.rq1_reviewed_measurement',
            '--observations',output/'comparison/observations.jsonl','--output',output/'rq1_review_template')
        # Finalization still requires actual new-answer annotations and independent review.
        status.update(status='COLLECTED_PENDING_RQ1_ANNOTATION_AND_FINAL_REPORT',stage='POST_COLLECTION',
            required_next=['RQ1_new_36_raw_annotations','independent_final_gate'],
            lock_retained=False)
        save()
        collection_complete=True
    except BaseException as exc:
        status.update(status='STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error=str(exc),
            lock_retained=True,child_or_container_may_remain=True,
            restart_policy='DO_NOT_RESTART: inspect recorded child PID and research worker/proxy containers; preserve lock until absence or owned termination is verified')
        save();raise
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding='utf8')).get('pid')==os.getpid():
            if collection_complete:lock.unlink()
            else:
                # An exited launcher does not prove its child tree/containers are gone.
                # Never release on interrupt, nonzero exit, or validation failure.
                write(lock,{'pid':os.getpid(),'run':str(output),'kind':'RQ1_RQ5_DEVELOPMENT_K1',
                    'status':'REVIEW_REQUIRED_LOCK_RETAINED','child_pid':status.get('child_pid'),
                    'last_child_pid':status.get('last_child_pid'),
                    'stage':status.get('stage'),'child_or_container_may_remain':True,
                    'automatic_restart_allowed':False})
    return status


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--snapshot-output',required=True)
    args=parser.parse_args();print(json.dumps(run(args.output,args.snapshot_output)))
