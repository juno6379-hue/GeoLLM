"""Development-only real-DB authority probe; no model, GOLD or holdout reads."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ..baselines.v2_runtime import ObservedDatabase, V2Executor, validator_for
from ..baselines.lossless_qec import compile_plan, validate_without_repair
from services.orchestrator.execution_validator import is_execution_authorized

ROOT = Path(__file__).resolve().parents[3]
FILES = ['services/orchestrator/spatial_coverage.py', 'services/orchestrator/execution_validator.py',
         'research/marine_geollm_scie/baselines/v2_runtime.py',
         'research/marine_geollm_scie/baselines/lossless_qec.py',
         'research/marine_geollm_scie/runners/source_authority_probe.py']


def hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}


def cases():
    base = {'source':'s101', 'feature_types':['Wreck'], 'reference_geometry':'POINT(129.05 35.1)',
            'crs':'EPSG:4326', 'radius_m':1000, 'relation':'dwithin', 'analysis_type':'feature_search_by_radius'}
    q4 = dict(base, source='marine_places', feature_types=[], radius_m=5000,
              reference_geometry='POINT(131.86955555555556 37.24077777777778)')
    return [
        ('q4', '독도 반경 5km 해양지명을 찾아줘', q4, True, 11),
        ('control', '주어진 기준점에서 반경 1000m 이내 Wreck를 찾아줘. 입력 좌표의 CRS는 EPSG:4326이다.', base, True, 0),
        ('outside', '주어진 독도 기준점 반경 1000m 이내 Wreck를 찾아줘', dict(base, reference_geometry=q4['reference_geometry']), False, None),
        ('partial', '주어진 기준점 반경 1000m 이내 Wreck를 찾아줘', dict(base, reference_geometry='POINT(128.9001 35.1)'), False, None),
        ('world', '독도 반경 5km 실제 존재하는 모든 해양지명을 빠짐없이 찾아줘', q4, False, None),
        ('missing_geometry', '선택된 영역의 Wreck를 찾아줘', dict(base, reference_geometry=None), False, None),
        ('invalid_crs', '주어진 기준점에서 반경 1000m 이내 Wreck를 찾아줘', dict(base, crs='EPSG:3857'), False, None),
    ]


def run(profile_path, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    profile = json.loads(Path(profile_path).read_text(encoding='utf-8'))
    before = hashes()
    executor = V2Executor(ObservedDatabase(), catalogue=ROOT/profile['catalogue']['path'],
        catalogue_sha256=profile['catalogue']['sha256'], anchors=profile.get('anchors', []),
        coverage=profile['coverage'], reference_geometries=profile.get('reference_geometries', {}),
        snapshot_manifest=profile['snapshot_manifest'])
    results = []
    for name, query, args, expected_ready, expected_count in cases():
        plan = {'action':'search', 'tool_calls':[{'tool_id':'spatial.query', 'arguments':copy.deepcopy(args)}]}
        start = len(executor.db.events)
        checked = [validate_without_repair(item, validator_for(executor, query=query))
                   for item in compile_plan(plan, query=query)]
        ready = bool(checked) and all(is_execution_authorized(q) for q in checked)
        execution = executor.execute(plan) if ready else None
        count = sum(len(r.get('result', {}).get('rows', []))
                    for r in (execution or {}).get('receipts', [])) if ready else None
        row = {'case':name, 'query':query, 'ready':ready, 'count':count,
               'expected_ready':expected_ready, 'expected_count':expected_count,
               'qecs':[q.model_dump(mode='json') for q in checked], 'execution':execution,
               'db_events':copy.deepcopy(executor.db.events[start:])}
        execution_ok = ((execution or {}).get('execution_observation', {}).get('execution_succeeded') is True
                        if ready else not any(e['scope'] == 'spatial' for e in row['db_events']))
        row['passed'] = ready == expected_ready and count == expected_count and execution_ok
        (output/(name+'.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        results.append({k:row[k] for k in ('case','ready','count','passed')})
    after = hashes()
    summary = {'kind':'DEVELOPMENT_AUTHORITY_PROBE_NOT_MODEL_COMPARISON',
        'model_calls':0, 'holdout_used':False, 'original_runs_modified':False,
        'profile_path':str(profile_path), 'source_before':before, 'source_after':after,
        'sources_unchanged':before == after, 'cases':results,
        'passed':before == after and all(r['passed'] for r in results)}
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--profile', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = run(args.profile, args.output)
    print(json.dumps({'passed':result['passed'], 'cases':result['cases']}))
    raise SystemExit(0 if result['passed'] else 1)
