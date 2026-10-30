"""Bounded counterbalanced B0–B4 planning pilot. No production API or DB writes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import urllib.request

from ..baselines.evidence_packets import build_packet
from ..baselines.plan_comparison import run_condition, PLAN_SCHEMA

ROOT=Path(__file__).resolve().parents[3]
RESEARCH=ROOT/'research/marine_geollm_scie'
CASE_IDS=['PILOT_Q1_03','PILOT_Q2_03','PILOT_Q3_03','PILOT_Q4_01','PILOT_Q5_03','PILOT_Q6_03']

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def run(output, repeats=3, model='qwen2.5:1.5b'):
    output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists() or (output/'comparison_rows.jsonl').exists():
        raise FileExistsError('Use a new run ID; existing baseline is immutable')
    benchmark=RESEARCH/'benchmark/query_cases_v1.jsonl'
    cases=[json.loads(x) for x in benchmark.read_text(encoding='utf-8').splitlines() if x.strip()]
    cases=[c for c in cases if c['case_id'] in CASE_IDS]
    assert len(cases)==6
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=30) as response:
        tags=json.load(response)
    metadata=next(m for m in tags['models'] if m['name']==model)
    packets={c['case_id']:{m:build_packet(c['query'],'B2' if m=='B4' else 'B0' if m=='B3' else m,max_chars=6000) for m in ('B0','B1','B2','B3','B4')} for c in cases}
    write(output/'evidence_packets.json',packets)
    write(output/'cases.json',cases)
    methods=['B0','B1','B2','B3','B4']
    schedule=[]
    for repeat in range(repeats):
        for index,case in enumerate(cases):
            rotation=(repeat+index)%5
            for method in methods[rotation:]+methods[:rotation]:
                schedule.append({'case_id':case['case_id'],'method':method,'repeat':repeat,'seed':42+repeat})
    source_paths=[p for p in (RESEARCH/'baselines').glob('*.py')]+[Path(__file__),ROOT/'shared/schemas/agent.py']
    manifest={'run_id':output.name,'started_at':datetime.now(timezone.utc).isoformat(),'status':'RUNNING',
              'publication_status':'NOT_READY','scope':'B0-B4 observable planning only; no GIS execution',
              'git_commit_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'git_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
              'model_metadata':metadata,'temperature':0.2,'repeats':repeats,'random_seeds':[42+i for i in range(repeats)],
              'generation_budget':{'per_condition_total_max_tokens':768,'B4_initial':384,'B4_review':384,'other_single_call':768},
              'context_tokens':8192,'evidence_max_chars':6000,'timeout_seconds_per_call':180,
              'warmup':'none; initial load latency and failures retained','schedule':schedule,
              'benchmark_sha256':digest(benchmark),'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in source_paths},
              'packet_file_sha256':digest(output/'evidence_packets.json'),'plan_output_schema':PLAN_SCHEMA,
              'human_gold_cases':0,'python_version':platform.python_version(),
              'limitations':['Convenience pilot subset, not representative benchmark','No semantic gold or execution accuracy',
                             'B3 is typed tool planning, not an executing tool agent','B4 self-review does not grant execution authority',
                             'P condition uses a separate unchanged production adapter; its conditions must be reported separately']}
    write(output/'manifest.json',manifest)
    case_map={c['case_id']:c for c in cases}
    with (output/'comparison_rows.jsonl').open('x',encoding='utf-8') as stream:
        for number,item in enumerate(schedule):
            case=case_map[item['case_id']]
            packet=packets[item['case_id']][item['method']]
            started=datetime.now(timezone.utc).isoformat()
            try:
                result=run_condition(case,item['method'],packet,model=model,seed=item['seed'])
            except Exception as exc:
                result={'status':'runner_error','error_type':type(exc).__name__,'error':str(exc),'schema_valid':None,
                        'execution_success':None,'scope':'PLAN_ONLY','review_status':'DRAFT'}
            row={**item,**result,'category':case['category'],'query':case['query'],'annotation_status':'DRAFT',
                 'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
                 'evidence_packet_sha256':packet['packet_sha256'],'retrieval_status':packet['status']}
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            print(f"{number+1}/{len(schedule)} {item['case_id']} {item['method']} {row['status']}",flush=True)
    manifest.update(status='COMPLETED',ended_at=datetime.now(timezone.utc).isoformat(),rows=len(schedule),
                    rows_sha256=digest(output/'comparison_rows.jsonl'))
    write(output/'manifest.json',manifest)
    from .comparison_report import report_comparison
    report_comparison(output)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--repeats',type=int,choices=range(1,6),default=3)
    args=parser.parse_args()
    run(args.output_dir,args.repeats)
