"""Live positive/negative nearby-place request checks."""
import json
from datetime import datetime
from pathlib import Path
from scripts.check_geollm_web_samples import observe


def main():
    cases = [
        ('독도구근해저지명', 'COMPLETED', 10000),
        ('독도 부근 해양지명을 찾아줘', 'COMPLETED', 10000),
        ('독도 1km 이내 해양지명을 찾아줘', 'COMPLETED', 1000),
        ('없는항구 주변 해양지명을 찾아줘', 'NEEDS_CLARIFICATION', None),
        ('독도 60km 이내 해양지명을 찾아줘', 'NEEDS_CLARIFICATION', None),
    ]
    path = Path('outputs') / ('nearby_names_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jsonl')
    failures = []
    with path.open('w', encoding='utf-8') as stream:
        for i, (query, status, radius) in enumerate(cases):
            row = observe('http://localhost:8000', i, query, {}, socket_timeout=180, observation_timeout=240)
            final = (row.get('completion') or {}).get('final_result') or {}
            result = final.get('structured_result') or {}
            ok = final.get('status') == status
            if radius:
                ok = ok and result.get('distance_m') == radius and result.get('count', 0) > 0
                receipt = (((final.get('orchestrator_v2') or {}).get('query_execution_context') or {}).get('provenance') or {}).get('execution_validation') or {}
                ok = ok and receipt.get('authority') == 'ExecutionValidator'
            row['passed'] = bool(ok)
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
            print(json.dumps({'query':query,'status':final.get('status'),'radius':result.get('distance_m'),
                              'count':result.get('count'),'passed':ok,'answer':final.get('answer_text')},ensure_ascii=True),flush=True)
            if not ok:
                failures.append(query)
    assert not failures, failures


if __name__ == '__main__':
    main()
