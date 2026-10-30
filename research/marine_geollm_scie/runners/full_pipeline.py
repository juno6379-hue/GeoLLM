"""Unattended, gated research continuation after real dataset embedding completion."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
RESEARCH=ROOT/'research/marine_geollm_scie'
QWEN='65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b'
BGE='7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab'
WORKER='geollm-dataset-embedding-completion'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');t.replace(p)


def require_embedding_complete(progress):
    if (progress.get('status')!='COMPLETED' or progress.get('pending')!=0 or
        progress.get('total')!=progress.get('embedded') or progress.get('total',0)<=0 or
        progress.get('min_dim')!=1024 or progress.get('max_dim')!=1024 or
        progress.get('model_digest_unchanged') is not True):
        raise ValueError('Embedding completion/dimension/digest verification required')


def build_profiles(snapshot_path,embedding_manifest,run_dir):
    snapshot=read(snapshot_path);embedding=read(embedding_manifest)
    require_embedding_complete(embedding)
    if embedding.get('model_digest')!=BGE:raise ValueError('Unexpected completed embedding digest')
    if snapshot.get('status')!='LOADED_VERIFIED' or snapshot.get('db_identity')!={'container':'marine-scie-pilot-db','database':'scie_model_v3'}:
        raise ValueError('New verified research snapshot required')
    docs=next(r for r in snapshot['relations'] if r['relation']=='knowledge.document_chunks')
    if docs['rows']!=docs.get('embedding_rows') or docs['rows']!=embedding['total']:
        raise ValueError('Frozen corpus embedding count mismatch')
    cap=next((r for r in snapshot['relations'] if r['relation']=='knowledge.capability_embeddings'),{})
    if not cap.get('rows') or cap.get('embedding_rows')!=cap['rows'] or cap.get('min_embedding_dimension')!=1024 or cap.get('max_embedding_dimension')!=1024:
        raise ValueError('Capability vectors must be captured and complete')
    catalogue=ROOT/'data/s101_feature_catalogue_v2_parsed.json'
    anchors=read(ROOT/'data/public_place_anchors.json')['places']
    anchor=next(a for a in anchors if a['place_id']=='mof:dokdo:east-island')
    common={'contains_gold_answers':False,'snapshot_manifest':{'path':str(snapshot_path.resolve()),'sha256':sha(snapshot_path)},
        'catalogue':{'path':str(catalogue),'sha256':sha(catalogue)},
        'anchors':[{'source_id':anchor['place_id'],'name':anchor['label'],'aliases':anchor['aliases'],
            'geometry':{'type':'Point','coordinates':[anchor['longitude'],anchor['latitude']]}}],
        'coverage':{'marine_places':{'scope_verified':True,'max_radius_m_by_anchor':{anchor['place_id']:5000}},
            's101':{'scope_verified':False},'navigation_aids':{'scope_verified':False}},
        'coverage_interpretation':'Fixed 2022 source corpus within user-selected radius; not real-world completeness',
        'historical_embedding_digest_unverified':True,'historical_vectors_preserved_and_same_corpus_used_for_all_methods':True,
        'embedding_completion_manifest':{'path':str(embedding_manifest.resolve()),'sha256':sha(embedding_manifest)}}
    baseline={**common,'model':'qwen2.5:1.5b','model_digest':QWEN,
        'temperature':0.2,'seed':42,'context_tokens':8192,'generation_budget_per_condition':768}
    model={**common,'model_digests':{'qwen2.5:1.5b':QWEN,'bge-m3:latest':BGE},'embedding_ready':True,
        'embedding_model':'bge-m3:latest','embedding_model_digest':BGE,'snapshot_manifest_sha256':sha(snapshot_path),
        'graph_internal_prompts_and_budgets':'unchanged production defaults; not equal-compute baseline'}
    run_dir.mkdir(parents=True,exist_ok=True)
    write(run_dir/'baseline_profile.json',baseline);write(run_dir/'model_profile.json',model)
    return baseline,model


def run(output,embedding_dir,snapshot_dir,run_dir):
    output.mkdir(parents=True,exist_ok=True)
    # Exclusive guard; never run two supervisors against the same corpus/run.
    lock=output/'supervisor.lock'
    with lock.open('x',encoding='utf-8') as f:f.write(str(os.getpid()))
    started=datetime.now(timezone.utc).isoformat()
    frozen_paths=list((RESEARCH/'runners').glob('*.py'))+list((RESEARCH/'baselines').glob('*.py'))+[ROOT/'scripts/complete_dataset_embeddings.py']
    frozen_paths += list((ROOT/'services').rglob('*.py'))+list((ROOT/'shared').rglob('*.py'))
    frozen_paths += list((ROOT/'data').glob('*.json'))+list((ROOT/'data').glob('*.yaml'))
    frozen_paths += list((RESEARCH/'benchmark/frozen_v5').glob('*'))+[RESEARCH/'benchmark/query_cases_v1.jsonl']
    frozen_paths = [p for p in frozen_paths if p.is_file()]
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in frozen_paths}
    state={'status':'RUNNING','stage':'WAITING_FOR_EMBEDDINGS','pid':os.getpid(),'started_at':started,
        'planned_graph_cases':18,'planned_baseline_cases':18,'planned_baseline_methods':5,'repeats':1,
        'scientific_completion':False,'source_hashes':source_hashes,'events':[]}

    def save():
        state['observed_at']=datetime.now(timezone.utc).isoformat();write(output/'status.json',state)

    def unchanged():
        if any(sha(ROOT/p)!=h for p,h in source_hashes.items()):raise ValueError('Research code changed after pipeline freeze')

    def stage(name,module,args,timeout):
        unchanged();state['stage']=name;save()
        with (output/(name.lower()+'.log')).open('xb') as log:
            result=subprocess.run([sys.executable,'-u','-m',module,*map(str,args)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        state['events'].append({'stage':name,'exit_code':result.returncode,'finished_at':datetime.now(timezone.utc).isoformat()});save()
        if result.returncode:raise RuntimeError(name+' failed; logs and committed work preserved')
        unchanged()

    try:
        save();absent=0
        while True:
            progress=read(embedding_dir/'progress.json') if (embedding_dir/'progress.json').exists() else {}
            state['embedding_progress']=progress;save()
            if progress.get('status')=='COMPLETED':require_embedding_complete(progress);break
            active=subprocess.run(['docker','inspect',WORKER,'--format','{{.State.Running}}'],capture_output=True,text=True)
            if active.returncode==0 and active.stdout.strip()=='true':absent=0
            else:absent+=1
            if absent>=3:raise RuntimeError('Embedding worker exited without verified completion; resume pending rows first')
            time.sleep(30)
        unchanged()
        # Fresh fixed source snapshot only after source completion, not the old partial DB.
        stage('FREEZE_COMPLETED_DATA','research.marine_geollm_scie.runners.binding_snapshot',
            ['--output',snapshot_dir,'--database','scie_model_v3'],7200)
        snapshot_path=snapshot_dir/'snapshot_manifest.json'
        build_profiles(snapshot_path,embedding_dir/'manifest.json',run_dir)
        # Verify installed digests again before any new generation calls.
        with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=30) as response:tags=json.load(response)
        installed={m['name']:m['digest'] for m in tags['models']}
        if installed.get('qwen2.5:1.5b')!=QWEN or installed.get('bge-m3:latest')!=BGE:raise ValueError('Pinned model changed')
        stage('FULL_GRAPH_18','research.marine_geollm_scie.runners.launch_model_graph',
            ['--output',run_dir/'graph','--snapshot',snapshot_path,'--profile',run_dir/'model_profile.json'],14400)
        stage('BASELINES_90','research.marine_geollm_scie.runners.compare_execution',
            ['--output-dir',run_dir/'baselines','--profile',run_dir/'baseline_profile.json','--execute','--repeats','1'],43200)
        stage('COMPARE_OBSERVATIONS','research.marine_geollm_scie.runners.execution_report',
            ['--baselines',run_dir/'baselines','--graph',run_dir/'graph','--contracts',RESEARCH/'benchmark/frozen_v5/answer_contracts.jsonl','--output-dir',run_dir/'report'],600)
        state.update(status='EXECUTION_COMPARISON_FINISHED',stage='DONE',finished_at=datetime.now(timezone.utc).isoformat(),
            report_path=str(run_dir/'report'),scientific_completion=False,
            remaining='K5, independent holdout, complete spatial/evidence gold, controlled recovery/ablation; review actual failures')
        save()
    except Exception as exc:
        state.update(status='STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error=str(exc));save();raise
    finally:
        # Preserve the lock as a completion/failed-run identity rather than silently rerun stages.
        pass


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--embedding-dir',type=Path,required=True)
    p.add_argument('--snapshot-dir',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    if not a.execute:raise SystemExit('Explicit --execute required')
    run(a.output.resolve(),a.embedding_dir.resolve(),a.snapshot_dir.resolve(),a.run_dir.resolve())
