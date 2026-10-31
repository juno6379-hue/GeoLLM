"""모델 활성화 실제 production graph: 연구 DB/고정 모델, 전체18문항 K1."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import signal
import time
from urllib.parse import urlsplit
import uuid
from research.marine_geollm_scie.baselines.production_adapter import observable,extract_artifacts
from research.marine_geollm_scie.runners.model_graph_conditions import graph_condition,validate_condition_environment
from research.marine_geollm_scie.runners.execution_observer import ExecutionObserver

METHOD='P_current_production_model_enabled_restricted'

def require_profile(profile, snapshot):
    validate_condition_environment(profile,os.environ)
    if os.getenv('SCIE_MODEL_GRAPH')!='1' or not Path('/.dockerenv').exists():raise RuntimeError('Isolated model worker required')
    if os.getenv('DISABLE_LLM_API')!='0':raise RuntimeError('Explicit model-enabled profile required')
    for key in ['S101_DB_URL','POSTGIS_URL']:
        url=urlsplit(os.getenv(key,''))
        if url.hostname!='marine-scie-pilot-db' or url.path!='/scie_model_v3':raise RuntimeError('Research DB mismatch')
    if 'default_transaction_read_only=on' not in os.getenv('PGOPTIONS',''):raise RuntimeError('Read-only required')
    if profile.get('embedding_ready') is not True:raise RuntimeError('Embedding completion not verified')
    if set(profile.get('model_digests',{}))!={'qwen2.5:1.5b','bge-m3:latest'}:raise RuntimeError('Pinned model identities required')
    if profile.get('embedding_model_digest')!=profile['model_digests']['bge-m3:latest']:raise RuntimeError('Embedding model mismatch')
    if snapshot.get('db_identity')!={'container':'marine-scie-pilot-db','database':'scie_model_v3'} or snapshot.get('status')!='LOADED_VERIFIED':raise RuntimeError('Loaded research snapshot required')
    if os.getenv('OLLAMA_BASE_URL')!='http://marine-scie-model-proxy:11434':raise RuntimeError('Proxy-only model access required')

def current_case(out, payload):
    pending=out/'current_case.pending.json'
    pending.write_text(json.dumps(payload))
    pending.replace(out/'current_case.json')

def main(benchmark,output,profile_path,snapshot_path):
    out=Path(output); profile=json.loads(Path(profile_path).read_text());snapshot=json.loads(Path(snapshot_path).read_text())
    require_profile(profile,snapshot)
    condition=graph_condition(profile)
    rows=[json.loads(x) for x in Path(benchmark).read_text(encoding='utf-8').splitlines() if x.strip()]
    if len(rows)!=18 or len({r['case_id'] for r in rows})!=18:raise ValueError('Immutable 18-case benchmark required')
    start=time.perf_counter()
    from services.orchestrator.graph import orchestrator_graph,cache
    from shared.schemas.agent import AgentStatus
    (out/'warmup.json').write_text(json.dumps({'latency_ms':(time.perf_counter()-start)*1000,'cache_policy':'fresh process startup, per-case semantic cache reset; other read-only production caches reused'}))
    def expired(signum, frame):raise TimeoutError('Research case 600s deadline')
    signal.signal(signal.SIGALRM,expired)
    with (out/'production_rows.jsonl').open('x',encoding='utf-8') as stream:
        for case in rows:
            identifier=str(uuid.uuid4()); start=time.perf_counter()
            current_case(out, {'case_id':case['case_id'],'task_id':identifier,'repeat':0})
            # Prevent earlier benchmark answers from becoming semantic-cache hits.
            cache.vectorstore=None
            state={'task_id':identifier,'query':case['query'],'organization_id':'scie_isolated','user_id':'scie_research','status':AgentStatus.RECEIVED,'spatial_context':case.get('spatial_context') or {},'state_history':[]}
            row={'method':METHOD,'case_id':case['case_id'],'query':case['query'],'source_case':case,'repeat':0,'initial_state':observable(state),'semantic_correct':None,'spatial_correct':None,'execution_success':None,'comparison_condition':'actual production graph with its own prompts and budgets; not planning-baseline equivalent'}
            row['method']=condition['method']
            row['graph_condition']=condition
            signal.alarm(600)
            observer = ExecutionObserver(identifier)
            try:
                with observer:
                    final=observable(asyncio.run(orchestrator_graph.ainvoke(state,config={'configurable':{'thread_id':identifier},'recursion_limit':30})))
                row.update(status='GRAPH_RETURNED',graph_status=final.get('status'),final_state=final,**extract_artifacts(final))
            except Exception as exc:row.update(status='GRAPH_ERROR',error_type=type(exc).__name__)
            finally:signal.alarm(0)
            row['execution_observation'] = observer.result()
            row['latency_ms']=(time.perf_counter()-start)*1000
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            print(case['case_id'],row['status'],row.get('graph_status'),flush=True)
    current_case(out, {'case_id':'SESSION_COMPLETE'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--benchmark',required=True);p.add_argument('--output',required=True);p.add_argument('--profile',required=True);p.add_argument('--snapshot',required=True)
    a=p.parse_args();main(a.benchmark,a.output,a.profile,a.snapshot)
