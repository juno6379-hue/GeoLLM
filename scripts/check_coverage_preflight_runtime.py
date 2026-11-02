"""Observe production coverage denials and document/place controls over real SSE."""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = [Path('services/orchestrator') / name for name in
             ('spatial_coverage.py', 'execution_validator.py', 's101_radius_execution.py')]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    cases = [
        ('dokdo_attributes', 'Find wrecks within 5 km of Dokdo and explain their S-101 attributes.', {}),
        ('dokdo_radius', '독도 5km 이내 침선을 찾아줘', {}),
        ('busan_unknown', '반경 1km 침선을 찾아줘',
         {'geometry': 'POINT(129.075 35.075)', 'crs': 'EPSG:4326', 'base_location': '지도 기준점', 'buffer_distance': 1000}),
        ('missing_area', 'Find wrecks intersecting the selected area.', {}),
        ('definition', 'Wreck의 S-101 정의를 알려줘', {}),
        ('place_names', '독도 부근 5km 이내 해양지명을 알려줘', {}),
    ]
    checks = []
    for i, (name, query, context) in enumerate(cases):
        row = observe('http://localhost:8000', i, query, context,
                      socket_timeout=180, observation_timeout=300)
        (args.output / f'{name}.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        final = (row.get('completion') or {}).get('final_result') or {}
        qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
        result = final.get('structured_result') or {}
        check = {'case': name, 'observation': row.get('observation'), 'status': final.get('status'),
                 'error_code': final.get('error_code'), 'readiness': qec.get('readiness'),
                 'coverage': (qec.get('provenance') or {}).get('coverage_validation'),
                 'summary': final.get('summary'), 'structured_status': result.get('status'),
                 'seconds': row['elapsed_seconds']}
        checks.append(check)
        print(json.dumps(check, ensure_ascii=True), flush=True)
    report = {'observations': checks, 'source_hashes': hashes,
              'source_unchanged': all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()),
              'paper_experiment': False, 'browser_tested': False,
              'note': 'Raw SSE requires independent contract and execution-trace review; no automatic success claim.'}
    (args.output / 'observations.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
