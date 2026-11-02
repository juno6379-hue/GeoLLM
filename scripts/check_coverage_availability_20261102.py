"""Development-only coverage availability regression; never loads research cases.

Raw SSE and source hashes are preserved in a new directory. Assertions inspect
server receipts, not independent DB instrumentation or human semantic accuracy.
"""
import argparse
import hashlib
import json
import time
from urllib.request import urlopen
from pathlib import Path

from scripts.check_geollm_web_samples import observe

CASES = (
    ('q4_explicit', '독도 주변 반경 5km의 해양지명을 찾아줘.', {}, 'corpus'),
    ('q4_english', 'Find marine place names within 5 km of Dokdo.', {}, 'corpus'),
    ('q4_meters', '독도 주변 반경 5000m의 해양지명을 찾아줘.', {}, 'corpus'),
    ('gazetteer_completeness_negative', '독도 주변 반경 5km의 모든 해양지명을 빠짐없이 찾아줘.', {}, 'corpus_blocked'),
    ('s101_dokdo', '독도 5km 이내 침선을 찾아줘', {}, 'blocked'),
    ('s101_busan_unverified', '반경 1km 침선을 찾아줘',
     {'geometry': 'POINT(129.075 35.075)', 'crs': 'EPSG:4326',
      'base_location': '지도 기준점', 'buffer_distance': 1000}, 'blocked'),
    ('s101_missing_area', 'Find wrecks intersecting the selected area.', {}, 'missing'),
    ('s101_definition', 'Wreck의 S-101 정의를 알려줘', {}, 'document'),
)
EXECUTION_FIELDS = ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed')
SOURCE_PATHS = (
    'services/orchestrator/spatial_coverage.py',
    'services/orchestrator/execution_validator.py',
    'services/orchestrator/s101_radius_execution.py',
    'services/orchestrator/graph.py',
    'services/orchestrator/gazetteer_corpus.py',
    'services/orchestrator/schema_binding_adapter.py',
    'data/source_inventory/marine_gazetteer_20221231.csv',
    'data/spatial_layer_registry.yaml',
    'services/orchestrator/dataset_answer.py',
    'services/orchestrator/dataset_verification.py',
    'services/orchestrator/coastal_knowledge.py',
    'services/standard_rag_agent/vdb.py',
    'data/source_verification/current.json',
)


def hashes():
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SOURCE_PATHS}


def inspect_case(row, expectation):
    final = (row.get('completion') or {}).get('final_result') or {}
    result = final.get('structured_result') or {}
    qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
    provenance = qec.get('provenance') or {}
    coverage = provenance.get('coverage_validation') or {}
    execution = provenance.get('spatial_preflight') or provenance.get('spatial_execution') or result.get('search_execution') or {}
    checks = {'completion_received': row.get('observation') == 'COMPLETED_EVENT_RECEIVED'}
    if expectation == 'blocked':
        checks.update(
            blocked=final.get('status') == 'BLOCKED',
            coverage_error=final.get('error_code') in ('DATA_COVERAGE_UNVERIFIED', 'DATA_OUT_OF_SCOPE'),
            readiness=qec.get('readiness') == 'BLOCKED_DATA',
            coverage_required=coverage.get('required') is True,
            no_absence_certified=coverage.get('absence_certified') is False,
            count_unknown='count' in result and result['count'] is None,
            preflight=execution.get('status') == 'BLOCKED_BEFORE_DISPATCH',
            no_target_execution=all(execution.get(k) is False for k in EXECUTION_FIELDS),
        )
    elif expectation == 'corpus_blocked':
        checks.update(blocked=final.get('status') == 'BLOCKED',
                      readiness=qec.get('readiness') == 'BLOCKED_DATA',
                      no_corpus_exception=coverage.get('status') == 'UNKNOWN',
                      coverage_required=coverage.get('required') is True,
                      not_run=execution.get('status') == 'NOT_RUN',
                      count_unknown=result.get('count') is None)
    elif expectation == 'missing':
        checks.update(clarification=final.get('status') == 'NEEDS_CLARIFICATION',
                      readiness=qec.get('readiness') == 'NEEDS_USER_INPUT',
                      not_success=qec.get('execution_status') == 'NOT_RUN' or provenance.get('execution_status') == 'NOT_RUN' or result.get('execution_status') == 'NOT_RUN' or
                      (result.get('search_execution') or {}).get('status') == 'NOT_RUN')
    elif expectation == 'document':
        checks.update(completed=final.get('status') == 'COMPLETED',
                      document_operation=(qec.get('route_plan') or {}).get('analysis_type') == 'public_catalogue_document_lookup')
    elif expectation == 'corpus':
        features = result.get('features') or []
        count = result.get('returned_count')
        checks.update(
            completed=final.get('status') == 'COMPLETED',
            ready=qec.get('readiness') == 'EXECUTION_READY',
            nonempty_source_results=isinstance(count, int) and count > 0 and count == len(features),
            corpus_receipt=coverage.get('status') == 'CORPUS_VERIFIED',
            no_fake_adequacy=coverage.get('geographic_coverage') == 'UNKNOWN',
            source_count_scope=result.get('count_scope') == 'SOURCE_CORPUS_RETURNED_ROWS',
            execution_recorded=all(execution.get(k) is True for k in ('attempted', 'started', 'tool_called', 'sql_executed')),
            disclosure='수록' in str(final.get('summary')) and '실제 해역' in str(final.get('summary')) and '보증하지' in str(final.get('summary')),
            no_absence_certified=coverage.get('absence_certified') is False,
            no_global_total=result.get('total_count') is None,
            source_bound=bool(features) and all(x.get('source_id') is not None and
                x.get('source') == 'serving.marine_gazetteer_current' for x in features),
            distance_preserved=result.get('distance_m') == 5000,
        )
    else:
        raise ValueError(expectation)
    return {'passed': all(checks.values()), 'checks': checks, 'status': final.get('status'),
            'error_code': final.get('error_code'), 'summary': final.get('summary'),
            'coverage': coverage, 'execution_receipt': execution,
            'count': result.get('count'), 'returned_count': result.get('returned_count'),
            'total_count': result.get('total_count'),
            'limitation': 'Receipt assertions; not independent SQL instrumentation or human semantic grading.'}


def wait_for_health(base_url, timeout=60):
    deadline = time.monotonic() + timeout
    attempts = []
    while time.monotonic() < deadline:
        try:
            with urlopen(base_url + '/health', timeout=5) as response:
                ready = response.status == 200
            attempts.append({'status': 200, 'ready': ready})
            if ready:
                return {'ready': True, 'attempts': attempts}
        except Exception as exc:
            attempts.append({'ready': False, 'error_type': type(exc).__name__})
        time.sleep(min(2, max(0, deadline - time.monotonic())))
    return {'ready': False, 'attempts': attempts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--cases', nargs='+', choices=[c[0] for c in CASES])
    parser.add_argument('--verify-only', action='store_true', help='Read existing raw observations; no network calls.')
    args = parser.parse_args()
    selected = [c for c in CASES if not args.cases or c[0] in args.cases]
    if not args.verify_only:
        args.output.mkdir(parents=True, exist_ok=False)
        readiness = wait_for_health(args.base_url)
        (args.output / 'readiness.json').write_text(json.dumps(readiness, indent=2), encoding='utf-8')
        if not readiness['ready']:
            raise SystemExit('Readiness timeout; no task requests sent.')
        before = hashes()
        (args.output / 'source_hashes.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    else:
        before = json.loads((args.output / 'source_hashes.json').read_text(encoding='utf-8'))
    checks = []
    for index, (name, query, context, expectation) in enumerate(selected):
        path = args.output / (name + '.json')
        if args.verify_only:
            row = json.loads(path.read_text(encoding='utf-8'))
        else:
            row = observe(args.base_url, index, query, context, socket_timeout=180, observation_timeout=300)
            path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        check = {'case': name, 'raw_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 **inspect_case(row, expectation)}
        checks.append(check)
        print(json.dumps(check, ensure_ascii=True), flush=True)
    unchanged = before == hashes()
    report = {'observations': checks, 'source_unchanged': unchanged,
              'passed': unchanged and all(c['passed'] for c in checks),
              'operational_negative_cases': ['gazetteer_completeness_negative'],
              'paper_experiment': False, 'holdout_loaded': False, 'browser_tested': False}
    target = args.output / ('verification_recheck.json' if args.verify_only else 'verification.json')
    if target.exists():
        raise FileExistsError('Preserve existing verification; use a fresh output directory.')
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
