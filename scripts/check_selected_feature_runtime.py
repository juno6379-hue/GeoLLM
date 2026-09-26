"""Live selected-object evidence contracts; source rows are never synthesized."""
import argparse
import json
import os
import time
from pathlib import Path
from urllib.request import urlopen
import psycopg2
from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new output path')
    for _ in range(180):
        try:
            with urlopen('http://localhost:8000/health', timeout=2) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError('API not ready')
    with psycopg2.connect(os.environ['S101_DB_URL']) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT feature_instance_id, feature_type_name FROM projection.s101_feature_valid ORDER BY feature_instance_id LIMIT 1')
            identifier, feature_type = cursor.fetchone()
    source = 'projection.s101_feature_valid'
    query = '지도에서 선택한 이 객체 정보를 설명해줘'
    cases = [
        (301, query, {'id': identifier, 'source_ref': source}, 'COMPLETED', None),
        (302, query+' 심볼 매칭도 설명해줘', {'id': identifier, 'source_ref': source}, 'PARTIAL', 'OUTPUT_OBLIGATIONS_UNMET'),
        (303, query, {}, 'NEEDS_CLARIFICATION', 'SELECTED_FEATURE_REQUIRED'),
        (304, query, {'id': identifier, 'source_ref': 'unknown'}, 'NEEDS_CLARIFICATION', 'SELECTED_FEATURE_SOURCE_REQUIRED'),
        (305, query, {'id': '1 OR 1=1', 'source_ref': source}, 'NEEDS_CLARIFICATION', 'INVALID_SELECTED_FEATURE_ID'),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    passed = 0
    with args.output.open('x', encoding='utf-8') as stream:
        for number, question, selection, status, code in cases:
            row = observe('http://localhost:8000', number, question, {'selected_feature': selection})
            final = (row.get('completion') or {}).get('final_result') or {}
            ok = final.get('status') == status and final.get('error_code') == code
            if number in (301, 302):
                evidence = (final.get('structured_result') or {}).get('selected_feature_evidence') or {}
                ok = ok and evidence.get('feature_id') == identifier and evidence.get('feature_type') == feature_type and bool(evidence.get('row_sha256'))
                qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
                ok = ok and qec.get('readiness') == 'EXECUTION_READY' and qec.get('execution_status') == 'EXECUTED'
                ok = ok and (qec.get('slots') or {}).get('feature_instance_id') == identifier
                ok = ok and ((qec.get('provenance') or {}).get('execution') or {}).get('query_execution_id') == evidence.get('query_execution_id')
            row['contract_check_passed'] = bool(ok)
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
            passed += bool(ok)
            print(json.dumps({'sample': number, 'passed': bool(ok), 'status': final.get('status'), 'code': final.get('error_code')}), flush=True)
    print(f'{passed}/{len(cases)} real API contracts')
    return passed != len(cases)


if __name__ == '__main__':
    raise SystemExit(main())
