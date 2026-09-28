"""Verify the deployed web UI, persisted review API and positive/negative execution gates."""
import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen
from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = 'http://localhost:8000'
    for _ in range(120):
        try:
            with urlopen(base + '/health', timeout=2) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        time.sleep(1)
    with urlopen(base + '/') as response:
        html = response.read().decode()
    assert 'id="evidenceMenu"' in html and '--map-panel-height' in html
    with urlopen(base + '/evidence-workspace.js') as response:
        assert '질의 해석·실행 비교 이력' in response.read().decode()
    with urlopen(base + '/api/v1/intent-comparisons?limit=2') as response:
        assert len(json.load(response)['items']) <= 2
    spatial = {'geometry': 'POINT(129.075 35.075)', 'crs': 'EPSG:4326', 'base_location': '지도 기준점'}
    cases = [
        ('해운대구로 이동', {}, 'COMPLETED', True),
        ('Wreck 정의를 알려줘', {}, 'COMPLETED', True),
        ('반경 1km 위험객체를 찾아줘', {**spatial, 'buffer_distance': 1000}, 'COMPLETED', True),
        ('주변 위험객체를 찾아줘', spatial, 'NEEDS_CLARIFICATION', False),
        ('반경 60km 위험객체를 찾아줘', {**spatial, 'buffer_distance': 60000}, 'BLOCKED', False),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    with args.output.open('x', encoding='utf-8') as stream:
        for index, (query, context, expected, allowed) in enumerate(cases):
            row = observe(base, index, query, context, socket_timeout=180, observation_timeout=300)
            final = (row.get('completion') or {}).get('final_result') or {}
            orch = final.get('orchestrator_v2') or {}
            plan = orch.get('route_plan') or {}
            qec = orch.get('query_execution_context') or {}
            receipt = (qec.get('provenance') or {}).get('execution_validation') or {}
            ok = final.get('status') == expected and bool(plan.get('execution_ready')) == allowed
            if allowed:
                ok = ok and receipt.get('authority') == 'ExecutionValidator' and bool(receipt.get('input_hash'))
            row['contract_check_passed'] = bool(ok)
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            print(json.dumps({'query': query, 'status': final.get('status'), 'ready': plan.get('execution_ready'), 'authority': receipt.get('authority'), 'passed': bool(ok)}, ensure_ascii=False), flush=True)
            if not ok:
                failures.append(index)
    assert not failures, failures
    print('UI assets + review API + 5/5 execution contracts passed', flush=True)


if __name__ == '__main__':
    main()
