"""원문 복합 요청의 실제 API 응답을 보존한다. GOLD를 사용하지 않는다."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from research.marine_geollm_scie.issues.reproduce_radius_api_rq_v2 import request, ROOT


def run(output):
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    queries=[('simple_en','Find wrecks within 5 km of Dokdo.'),
        ('composite_en','Find wrecks within 5 km of Dokdo and explain their S-101 attributes.'),
        ('composite_ko','독도 주변 5km의 침선을 찾고 S-101 속성을 설명해줘.')]
    with (out/'api_rows.jsonl').open('x',encoding='utf-8') as stream:
        for name,query in queries:
            row={'case_id':name,'query':query,'gold_used':False,'source_hash':hashlib.sha256((ROOT/'services/orchestrator/request_obligations.py').read_bytes()).hexdigest()}
            start=time.perf_counter()
            try:
                row['accepted']=request('/api/v1/tasks',{'query':query,'organization_id':'scie_contract_audit','user_id':'scie_contract_audit'})
                deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    final=request('/api/v1/tasks/'+row['accepted']['task_id'])
                    if final.get('status') in {'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'}:break
                    time.sleep(1)
                row.update(status='CAPTURED' if final.get('status') in {'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'} else 'OBSERVATION_TIMEOUT',final=final)
            except Exception as exc:row.update(status='TRANSPORT_ERROR',error=f'{type(exc).__name__}: {exc}')
            row['latency_ms']=(time.perf_counter()-start)*1000
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            print(name,row['status'],row.get('final',{}).get('status'),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True)
    run(parser.parse_args().output_dir)
