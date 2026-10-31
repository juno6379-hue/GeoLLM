"""Observe deployed SSE empty/positive/invalid radius contracts; no GOLD scoring."""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--empty-geometry', default='POINT(150 0)')
    parser.add_argument('--empty-distance', type=float, default=1000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path('services/orchestrator/s101_radius_execution.py')
    cases = [
        ('empty', f'반경 {args.empty_distance:g}m 위험객체를 찾아줘', args.empty_geometry, args.empty_distance),
        ('positive', '반경 1km 위험객체를 찾아줘', 'POINT(129.075 35.075)', 1000),
        ('invalid', '반경 60km 위험객체를 찾아줘', 'POINT(129.075 35.075)', 60000),
    ]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    checks = []
    for i, (name, query, geometry, distance) in enumerate(cases):
        row = observe('http://localhost:8000', i, query,
            {'geometry': geometry, 'crs': 'EPSG:4326', 'base_location': '지도 기준점',
             'buffer_distance': distance}, socket_timeout=180, observation_timeout=300)
        (args.output / (name + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        final = (row.get('completion') or {}).get('final_result') or {}
        payload = final.get('structured_result') or {}
        if name == 'empty':
            ok = (final.get('status') == 'PARTIAL' and payload.get('status') == 'NO_EVIDENCE'
                  and payload.get('observed_total_count') == 0 and payload.get('total_count') is None
                  and payload.get('coverage_status') == 'UNKNOWN'
                  and payload.get('query_execution_succeeded') is True)
        elif name == 'positive':
            ok = final.get('status') == 'COMPLETED' and (payload.get('total_count') or 0) > 0
        else:
            qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
            ok = final.get('status') in ('BLOCKED', 'NEEDS_CLARIFICATION') and qec.get('readiness') != 'EXECUTION_READY'
        checks.append({'case': name, 'passed': ok, 'status': final.get('status'),
                       'structured_status': payload.get('status'), 'total_count': payload.get('total_count'),
                       'observed_total_count': payload.get('observed_total_count'), 'seconds': row['elapsed_seconds']})
        print(json.dumps(checks[-1], ensure_ascii=True), flush=True)
    report = {'checks': checks, 'source_sha256': source_hash,
              'source_unchanged': hashlib.sha256(source.read_bytes()).hexdigest() == source_hash,
              'browser_tested': False, 'paper_experiment': False}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if not all(x['passed'] for x in checks) or not report['source_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
