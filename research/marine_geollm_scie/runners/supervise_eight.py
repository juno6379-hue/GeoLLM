"""Sequential fresh freeze -> P1 -> seven paired branches -> report.

No resume across code changes. A failed stage leaves the complete original
directory and stops; retries require a new output and newly verified freeze.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]


def run(output, snapshot_output, *, include_faults=False):
    output=Path(output).resolve();snapshot_output=Path(snapshot_output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    lock=ROOT/'outputs/eight_comparison_active.lock'
    with lock.open('x',encoding='utf-8') as stream:
        json.dump({'pid':os.getpid(),'run':str(output)},stream)
    status={'status':'PREPARING','pid':os.getpid(),'stage':None,'stages':[],
            'created_at':datetime.now(timezone.utc).isoformat(),'scientific_completion':False,
            'expected_comparison_rows':144,'repeats':1}
    def save():
        status['observed_at']=datetime.now(timezone.utc).isoformat()
        (output/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    def stage(name,module,*args):
        status.update(status='RUNNING',stage=name);save()
        print(name,flush=True)
        with (output/(name+'.log')).open('xb') as log:
            child=subprocess.Popen([sys.executable,'-m',module,*map(str,args)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            status['child_pid']=child.pid;save()
            code=child.wait()
        status['child_pid']=None
        status['stages'].append({'stage':name,'exit_code':code,'finished_at':datetime.now(timezone.utc).isoformat()});save()
        if code:raise RuntimeError('Stage failed: '+name)
    benchmark=ROOT/'research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1'
    profiles=output/'profiles';snapshot=snapshot_output/'snapshot_manifest.json'
    try:
        stage('freeze','research.marine_geollm_scie.runners.freeze_comparison_sources',
              '--parent',ROOT/'outputs/scie_model_snapshot_20261031_execution_v1/snapshot_manifest.json','--output',snapshot_output)
        stage('profiles','research.marine_geollm_scie.runners.prepare_eight_profiles',
              '--snapshot',snapshot,'--output',profiles,'--benchmark',benchmark)
        stage('graph','research.marine_geollm_scie.runners.launch_model_graph',
              '--snapshot',snapshot,'--profile',profiles/'model_profile.json','--benchmark',profiles/'common_inputs.jsonl','--output',output/'graph')
        stage('comparison','research.marine_geollm_scie.runners.eight_method_runner',
              '--profile',profiles/'baseline_profile.json','--benchmark',benchmark,
              '--inputs',profiles/'common_inputs.jsonl','--p1-rows',output/'graph/production_rows.jsonl',
              '--output',output/'comparison','--execute')
        stage('report','research.marine_geollm_scie.runners.report_eight',
              '--run-dir',output/'comparison','--benchmark',benchmark,'--output',output/'report')
        summary=json.loads((output/'report/summary.json').read_text(encoding='utf-8'))
        if not summary['completion_gate']['observation_comparison_complete']:
            raise RuntimeError('Observation/report completion gate failed; preserve all rows')
        if include_faults:
            stage('faults','research.marine_geollm_scie.runners.eight_fault_recovery',
                  '--profile',profiles/'baseline_profile.json','--benchmark',benchmark,'--output',output/'faults','--execute')
            stage('fault_report','research.marine_geollm_scie.runners.report_eight_faults',
                  '--run-dir',output/'faults','--output',output/'fault_report')
            stage('combined_report','research.marine_geollm_scie.runners.report_eight',
                  '--run-dir',output/'comparison','--benchmark',benchmark,'--faults',output/'faults',
                  '--output',output/'report_with_faults')
        status.update(status='COMPLETED_OBSERVATIONS',stage='DONE',
                      comparison_report=str(output/('report_with_faults' if include_faults else 'report')/'comparison_KR.md'));save()
    except BaseException as exc:
        status.update(status='STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error=str(exc));save();raise
    finally:
        if lock.exists() and json.loads(lock.read_text())['pid']==os.getpid():lock.unlink()
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--snapshot-output',required=True);p.add_argument('--include-faults',action='store_true')
    a=p.parse_args();print(json.dumps(run(a.output,a.snapshot_output,include_faults=a.include_faults)))
