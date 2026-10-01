"""Verify understood place, unresolved anchor, missing radius, and live layer search via HTTP."""
import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen
from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for attempt in range(90):
        try:
            with urlopen('http://localhost:8000/health', timeout=2) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError('Backend readiness timed out')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cases = [
        ('울릉도 주변 지명을 찾아줘', 'LOCATION_UNCONFIRMED'),
        ('울릉항 주변 지명을 찾아줘', 'DISTANCE_REQUIRED'),
        ('울릉항 반경 5km 지명을 찾아줘', None),
    ]
    failures = []
    with args.output.open('x', encoding='utf-8') as output:
        for number, (query, error) in enumerate(cases):
            row = observe('http://localhost:8000', number, query, socket_timeout=180, observation_timeout=300)
            final = (row.get('completion') or {}).get('final_result') or {}
            structured = final.get('structured_result') or {}
            qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
            if error:
                passed = (final.get('status') == 'NEEDS_CLARIFICATION' and final.get('error_code') == error
                          and structured.get('search_execution', {}).get('status') == 'NOT_RUN'
                          and bool(qec.get('slots', {}).get('location_text'))
                          and qec.get('readiness') != 'EXECUTION_READY')
            else:
                passed = (final.get('status') == 'COMPLETED'
                          and qec.get('provenance', {}).get('execution_validation', {}).get('authority') == 'ExecutionValidator')
            row['contract_check_passed'] = passed
            output.write(json.dumps(row, ensure_ascii=False) + '\n')
            output.flush()
            print(json.dumps({'query': query, 'status': final.get('status'), 'error': final.get('error_code'),
                              'count': structured.get('count'), 'passed': passed}, ensure_ascii=False), flush=True)
            if not passed:
                failures.append(number)
    assert not failures, failures


if __name__ == '__main__':
    main()
