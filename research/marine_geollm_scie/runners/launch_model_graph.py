"""고정 모델과 연구 DB만 접근하는 전체 graph 연구 실행기."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from research.marine_geollm_scie.runners.binding_snapshot import verify_files
from research.marine_geollm_scie.runners.launch_production import isolation_metadata
from research.marine_geollm_scie.runners.model_graph_conditions import graph_condition,graph_condition_environment

ROOT=Path(__file__).resolve().parents[3]
DB='scie_model_v3'
PROXY='marine-scie-model-proxy'
NETWORK='marine-scie-graph-isolated'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def graph_source_files(root):
    return (list((root/'services').rglob('*.py'))+list((root/'shared').rglob('*.py'))
            +list((root/'research/marine_geollm_scie/runners').glob('*.py'))
            +[root/'data/tool_registry.yaml'])


def warmup_summary(calls):
    warmup=[r for r in calls if r.get('case',{}).get('case_id')=='IMPORT_WARMUP']
    failed=[r for r in warmup if r.get('status')!='RETURNED' or r.get('upstream_http_status')!=200]
    embeddings=[r for r in warmup if r.get('path') in {'/api/embed','/api/embeddings','/v1/embeddings'}]
    return {'status':'DEGRADED_WARMUP' if failed or not embeddings else 'WARMUP_OBSERVED_WITHOUT_PROXY_ERRORS',
            'observed_calls':len(warmup),'embedding_calls':len(embeddings),
            'failed_call_ids':[r.get('call_id') for r in failed],
            'identity_check_retries':sum(len(r.get('identity_checks',[]))>1 for r in warmup),
            'semantic_quality_verified':False}

def validate_observations(rows,cases):
    if len(rows)!=18 or len(cases)!=18 or {r['case_id'] for r in rows}!=cases:
        raise ValueError('Expected 18 distinct case observations')
    if any(r.get('status') not in {'GRAPH_RETURNED','GRAPH_ERROR'} for r in rows):
        raise ValueError('Invalid observation status')

def validate_profile(profile,snapshot):
    graph_condition(profile)
    if snapshot.get('db_identity')!={'container':'marine-scie-pilot-db','database':DB} or snapshot.get('status')!='LOADED_VERIFIED':raise ValueError('Loaded model research DB required')
    if profile.get('embedding_ready') is not True:raise ValueError('Embedding completion required before graph run')
    digests=profile.get('model_digests',{})
    if set(digests)!={'qwen2.5:1.5b','bge-m3:latest'} or any(not isinstance(v,str) or len(v)!=64 for v in digests.values()):raise ValueError('Full fixed model digests required')
    if profile.get('embedding_model_digest')!=digests['bge-m3:latest']:raise ValueError('Embedding digest mismatch')
    capabilities=next((r for r in snapshot.get('relations',[]) if r.get('relation')=='knowledge.capability_embeddings'),{})
    if not (capabilities.get('rows',0)>0 and capabilities.get('rows')==capabilities.get('embedding_rows')
            and capabilities.get('min_embedding_dimension')==1024 and capabilities.get('max_embedding_dimension')==1024):
        raise ValueError('Complete 1024-dimensional capability embedding snapshot required')

def main(output,snapshot_path,profile_path):
    out=Path(output).resolve(); snapshot_path=Path(snapshot_path).resolve();profile_path=Path(profile_path).resolve()
    snapshot=json.loads(snapshot_path.read_text(encoding='utf-8'));profile=json.loads(profile_path.read_text(encoding='utf-8'))
    validate_profile(profile,snapshot);verify_files(snapshot,snapshot_path.parent)
    if profile.get('snapshot_manifest_sha256') != sha(snapshot_path):
        raise ValueError('Embedding profile must bind the exact snapshot manifest hash')
    for name in (PROXY,'marine-scie-model-worker'):
        if subprocess.run(['docker','inspect',name],capture_output=True).returncode == 0:
            raise RuntimeError('Research container name already in use: '+name)
    out.mkdir(parents=True,exist_ok=False)
    mask=out/'isolation.empty.env';mask.write_text('')
    network=json.loads(subprocess.check_output(['docker','network','inspect',NETWORK]))[0]
    isolation=isolation_metadata(mask,network)
    image=subprocess.check_output(['docker','image','inspect','docker-backend','--format','{{.Id}}'],text=True).strip()
    benchmark=ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl'
    source_files=graph_source_files(ROOT)
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in source_files}
    manifest={'method':'P_current_production_model_enabled_restricted','scope':'Actual production graph entry, 18 original cases K1; capability pgvector enabled; external/coverage restrictions remain; not unrestricted Full P or equal planning budget', 'capability_retrieval':{'pgvector_enabled':True,'relation':'knowledge.capability_embeddings','snapshot_metadata':next(r for r in snapshot['relations'] if r['relation']=='knowledge.capability_embeddings'),'fallback':'production fallback only if actual retrieval fails; recorded in graph trace'},'snapshot_manifest_sha256':sha(snapshot_path),'profile_sha256':sha(profile_path),'model_profile':profile,'image_id':image,'benchmark_sha256':sha(benchmark),'source_hashes':source_hashes,'isolation':isolation,'cache_policy':'semantic answer cache reset per case; same production singleton other caches','network_policy':'worker only internal network; proxy dual network and endpoint/model allowlist; no ports published','conditions':{'LLM_MODEL':'qwen2.5:1.5b','EMBEDDING_MODEL':'bge-m3','model_budget':'production per-call settings preserved; proxy records actual requests','PGOPTIONS':'default_transaction_read_only=on','OLLAMA_BASE_URL':'http://marine-scie-model-proxy:11434'}}
    condition=graph_condition(profile)
    manifest['method']=condition['method']
    manifest['graph_condition']=condition
    manifest['conditions'].update(graph_condition_environment(profile))
    manifest['identity_check_policy']={'timeout_seconds':10,'max_attempts':2,'retry_scope':'transport error on read-only tags only; digest mismatch never retried','backoff_seconds':.5}
    manifest['registry_sha256']={'data/tool_registry.yaml':sha(ROOT/'data/tool_registry.yaml')}
    if condition['research_timeout_override']:
        manifest['conditions']['model_budget']='production settings except explicit research semantic-prior timeout override; not equal-compute baseline'
    (out/'model_graph_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    common=['--mount',f'type=bind,source={ROOT},target=/work,readonly','--mount',f'type=bind,source={out},target=/out','--mount',f'type=bind,source={mask},target=/work/.env,readonly','--mount',f'type=bind,source={profile_path},target=/model_profile.json,readonly','--workdir','/work','--env','PYTHONPATH=/work','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHON_DOTENV_DISABLED=1']
    proxy_started=False
    try:
        subprocess.run(['docker','run','-d','--rm','--name',PROXY,'--network','bridge','--label','marine.scie.research=true',*common,image,'python','-m','research.marine_geollm_scie.runners.model_proxy','--profile','/model_profile.json','--output','/out'],check=True,capture_output=True)
        proxy_started=True
        subprocess.run(['docker','network','connect',NETWORK,PROXY],check=True,capture_output=True)
        ready=False
        for _ in range(30):
            probe=subprocess.run(['docker','exec',PROXY,'python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=12).read()"],capture_output=True,timeout=20)
            if probe.returncode==0:
                ready=True;break
            time.sleep(1)
        if not ready:
            manifest['worker_status']='PROXY_NOT_READY'
            raise RuntimeError('Proxy readiness/model digest check failed')
        # The graph has only this internal network. The proxy is not an HTTP forward proxy.
        db='postgresql://postgres:scie_local_pilot@marine-scie-pilot-db:5432/'+DB
        env={'SCIE_MODEL_GRAPH':'1','DISABLE_LLM_API':'0','S101_DB_URL':db,'POSTGIS_URL':db,'PGOPTIONS':'-c default_transaction_read_only=on -c statement_timeout=10000','OLLAMA_BASE_URL':'http://'+PROXY+':11434','OPENAI_BASE_URL':'http://'+PROXY+':11434/v1','OPENAI_API_KEY':'research-local-ollama','LLM_MODEL':'qwen2.5:1.5b','GEOLLM_OLLAMA_MODEL':'qwen2.5:1.5b','OLLAMA_MODEL':'qwen2.5:1.5b','GEOLLM_WEB_SHADOW_MODEL':'qwen2.5:1.5b','EMBEDDING_MODEL':'bge-m3','GEOLLM_CAPABILITY_PGVECTOR':'true','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','APP_DATA_DIR':'/tmp'}
        env.update(graph_condition_environment(profile))
        cmd=['docker','run','--rm','--name','marine-scie-model-worker','--network',NETWORK,'--label','marine.scie.research=true',*common,'--mount',f'type=bind,source={snapshot_path},target=/snapshot.json,readonly','--tmpfs','/work/logs:rw','--tmpfs','/work/data/feedback:rw']
        for key,value in env.items():cmd+=['--env',key+'='+value]
        cmd += [image,'python','-m','research.marine_geollm_scie.runners.model_graph_session','--benchmark','/work/research/marine_geollm_scie/benchmark/query_cases_v1.jsonl','--output','/out','--profile','/model_profile.json','--snapshot','/snapshot.json']
        try:
            completed=subprocess.run(cmd,capture_output=True,timeout=13000)
        except subprocess.TimeoutExpired as exc:
            manifest['worker_status']='OBSERVATION_TIMEOUT'
            for name,content in [('stdout.log',exc.stdout or b''),('stderr.log',exc.stderr or b'')]:
                (out/name).write_bytes(content.replace(db.encode(),b'[REDACTED_RESEARCH_DSN]'))
            subprocess.run(['docker','stop','marine-scie-model-worker'],capture_output=True)
            raise
        for name,content in [('stdout.log',completed.stdout),('stderr.log',completed.stderr)]: (out/name).write_bytes(content.replace(db.encode(),b'[REDACTED_RESEARCH_DSN]'))
        manifest['worker_exit_code']=completed.returncode
        if completed.returncode != 0:
            manifest['worker_status']='WORKER_FAILED'
            raise RuntimeError('Research graph worker failed; raw logs preserved')
        raw=out/'production_rows.jsonl'
        rows=[json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines() if line.strip()]
        cases={json.loads(line)['case_id'] for line in benchmark.read_text(encoding='utf-8').splitlines() if line.strip()}
        try:
            validate_observations(rows,cases)
        except ValueError:
            manifest['worker_status']='INCOMPLETE_OBSERVATION'
            raise
        manifest['observed_rows']=len(rows)
        manifest['graph_status_counts']={status:sum(r.get('graph_status')==status for r in rows) for status in {r.get('graph_status') for r in rows}}
        calls=[json.loads(line) for line in (out/'model_calls.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        manifest['warmup_verification']=warmup_summary(calls)
        if manifest['warmup_verification']['status']=='DEGRADED_WARMUP':
            manifest['worker_status']='DEGRADED_WARMUP'
            raise RuntimeError('Research warmup failed; all raw observations preserved but healthy initialization not verified')
        manifest['worker_status']='EXECUTION_OBSERVED'
    finally:
        if proxy_started:subprocess.run(['docker','stop',PROXY],capture_output=True)
        verify_files(snapshot,snapshot_path.parent)
        unchanged=all(sha(ROOT/p)==digest for p,digest in source_hashes.items()) and sha(profile_path)==manifest['profile_sha256'] and sha(snapshot_path)==manifest['snapshot_manifest_sha256']
        manifest['source_unchanged_after']=unchanged
        (out/'model_graph_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        if not unchanged:raise RuntimeError('Research source/profile changed during run')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--snapshot',required=True);p.add_argument('--profile',required=True)
    a=p.parse_args();main(a.output,a.snapshot,a.profile)
