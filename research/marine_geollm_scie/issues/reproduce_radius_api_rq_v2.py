"""실제 POST /tasks 경로의 정상/부정 입력 감사. 공간 DB에는 조회만 요청한다."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]


def request(path, payload=None):
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request('http://127.0.0.1:8000'+path, data=body,
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=25) as response: return json.load(response)


def run(output):
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    raw = out/'api_rows.jsonl'
    source_paths = ['services/orchestrator/execution_validator.py', 'services/orchestrator/s101_radius_execution.py',
        'services/orchestrator/graph.py', 'services/orchestrator/router.py']
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths}
    rows = []
    with raw.open('x', encoding='utf-8') as stream:
        for name in ['control', 'invalid_feature', 'invalid_crs', 'operator_conflict']:
            spatial = {'geometry':'POINT(129.05 35.1)', 'crs':'EPSG:4326', 'target_features':['Wreck'], 'result_limit': 5}
            if name == 'invalid_feature': spatial['target_features'] = ['NOT_A_REAL_S101_FEATURE_SCIE']
            if name == 'invalid_crs': spatial['crs'] = 'EPSG:INVALID_SCIE'
            if name == 'operator_conflict': spatial['spatial_relation'] = 'within'
            payload = {'query':'침선 반경 3000m', 'spatial_context':spatial,
                'organization_id':'scie_contract_audit', 'user_id':'scie_contract_audit'}
            row = {'case_id': name, 'input':payload, 'point_basis':'합성 명시점; 검증된 부산항 기준점 아님',
                'gold_used':False, 'spatial_correct':None, 'source_hashes_before':hashes}
            start = time.perf_counter()
            try:
                accepted = request('/api/v1/tasks', payload); row['accepted'] = accepted
                deadline = time.monotonic()+90
                history = []
                while time.monotonic() < deadline:
                    final = request('/api/v1/tasks/'+accepted['task_id'])
                    history.append({'status':final.get('status'), 'time_s':time.perf_counter()-start})
                    if final.get('status') in {'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'}: break
                    time.sleep(1)
                row.update(final=final, poll_history=history, status='CAPTURED' if final.get('status') in {'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'} else 'OBSERVATION_TIMEOUT')
            except Exception as exc:
                row.update(status='TRANSPORT_ERROR', error=f'{type(exc).__name__}: {exc}')
            row['latency_ms'] = (time.perf_counter()-start)*1000
            rows.append(row); stream.write(json.dumps(row, ensure_ascii=False)+'\n'); stream.flush()
            print(name,row['status'],row.get('final',{}).get('status'),flush=True)
    (out/'manifest.json').write_text(json.dumps({'source_hashes_before':hashes,
        'source_hashes_after':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},
        'endpoint':'POST /api/v1/tasks; GET /api/v1/tasks/{id}', 'writes':'일반 task 이력만 생성; 업무 DB 변경은 요청하지 않음',
        'gold_used':False, 'source_changes':False},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True)
    run(parser.parse_args().output_dir)
