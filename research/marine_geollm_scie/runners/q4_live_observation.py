"""Actual Q4 API observations. No GOLD file is loaded or sent to the service."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
TERMINAL={'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'}


def request(path,payload=None):
    body=json.dumps(payload,ensure_ascii=False).encode('utf-8') if payload is not None else None
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=body,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)


def run(output):
    source=ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl'
    cases=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines() if s.strip()]
    selected=[c for c in cases if c['case_id'] in {'PILOT_Q4_01','PILOT_Q4_02','PILOT_Q4_03'}]
    if len(selected)!=3:raise ValueError('Three original Q4 queries required')
    output.mkdir(parents=True,exist_ok=False)
    source_paths=['services/orchestrator/semantic_router.py','services/orchestrator/request_obligations.py',
                  'services/orchestrator/graph.py','services/orchestrator/execution_validator.py',
                  'data/spatial_layer_registry.yaml','data/public_place_anchors.json']
    hashes_before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths}
    with (output/'api_rows.jsonl').open('x',encoding='utf-8') as stream:
        for case in selected:
            row={'case_id':case['case_id'],'query':case['query'],'method':'P_current_production_live',
                'repeat':0,'scope':'LIVE_API_Q4_ONLY_NOT_MATCHED_BASELINE','gold_used_for_generation':False}
            start=time.perf_counter()
            try:
                row['accepted']=request('/api/v1/tasks',{'query':case['query'],
                    'organization_id':'scie_q4_observation','user_id':'scie_q4_observation'})
                deadline=time.monotonic()+120
                while True:
                    row['final']=request('/api/v1/tasks/'+row['accepted']['task_id'])
                    if row['final'].get('status') in TERMINAL:
                        row['status']='CAPTURED';break
                    if time.monotonic()>=deadline:
                        row['status']='OBSERVATION_TIMEOUT';break
                    time.sleep(1)
            except Exception as exc:
                row.update(status='TRANSPORT_ERROR',error=f'{type(exc).__name__}: {exc}')
            row['total_latency_ms']=(time.perf_counter()-start)*1000
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            print(row['case_id'],row['status'],row.get('final',{}).get('status'),flush=True)
    manifest={'benchmark_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'production_source_hashes_before':hashes_before,
        'production_source_hashes_after':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},
        'gold_used_for_generation':False,'endpoint':'POST /api/v1/tasks; GET /api/v1/tasks/{id}',
        'scope':'live production observation; data snapshot alignment must be checked separately',
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rows_sha256':hashlib.sha256((output/'api_rows.jsonl').read_bytes()).hexdigest()}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
