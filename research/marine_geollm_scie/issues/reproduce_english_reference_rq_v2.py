"""영어 참조위치 추출의 실제 API 정상/부정 관측. GOLD 미사용."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from research.marine_geollm_scie.issues.reproduce_radius_api_rq_v2 import request, ROOT


def run(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    for _ in range(90):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8000/',timeout=1) as response:
                if response.status==200:break
        except OSError:pass
        time.sleep(1)
    else:raise RuntimeError('Backend readiness deadline exceeded')
    cases=[('dokdo','Find marine place names within 5 km of Dokdo.'),
        ('busan','Find marine place names within 2 km of 부산항.'),
        ('busan_source_alias','Find marine place names within 2 km of BUSAN HANG.'),
        ('ulleungdo','Find marine place names within 2 km of 울릉도.'),
        ('missing','Find marine place names within 5 km of.'),
        ('multiple','Find marine place names within 5 km of Dokdo and Ulleungdo.'),
        ('unknown','Find marine place names within 5 km of SCIE_UNKNOWN_LOCATION_8301.'),
        ('over_limit','Find marine place names within 60 km of Dokdo.')]
    with (out/'api_rows.jsonl').open('x',encoding='utf-8') as stream:
        for name,query in cases:
            row={'case_id':name,'query':query,'gold_used':False,
                'source_hash':hashlib.sha256((ROOT/'services/orchestrator/semantic_router.py').read_bytes()).hexdigest()}
            start=time.perf_counter()
            try:
                row['accepted']=request('/api/v1/tasks',{'query':query,'organization_id':'scie_reference_audit','user_id':'scie_reference_audit'})
                deadline=time.monotonic()+120
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
