"""Descriptive within-case repeat variability, never repeated-row pseudo replication."""
import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
import statistics

from .execution_report import load, score, sha
from .repeat_experiment import validate_stage, require_unchanged


def summarize(scores, contracts, expected_repeats=5):
    groups = defaultdict(list)
    keys = set()
    for row in scores:
        key = (row['method'], row['case_id'], row['external_repeat'])
        if key in keys:
            raise ValueError('Duplicate method/case/external repeat observation')
        keys.add(key)
        groups[key[:2]].append(row)
    cases = []
    for (method, case), rows in sorted(groups.items()):
        values = [r['all_applicable_checks_pass'] for r in rows]
        measured = [float(v) for v in values if type(v) is bool]
        latencies = [r['latency_ms'] for r in rows if isinstance(r.get('latency_ms'), (int, float))]
        complete = len(rows) == expected_repeats and {r['external_repeat'] for r in rows} == set(range(expected_repeats))
        cases.append({'method': method, 'case_id': case,
            'equivalence_group': contracts[case]['equivalence_group'],
            'observed_repeats': len(rows), 'expected_repeats': expected_repeats,
            'repeat_schedule_complete': complete, 'measured_repeats': len(measured),
            'unmeasured_repeats': len(values)-len(measured),
            'component_pass_fraction_measured_only': statistics.mean(measured) if measured else None,
            'component_pass_fraction_complete': statistics.mean(measured) if complete and len(measured) == expected_repeats else None,
            'component_outcome_changed': len(set(measured)) > 1 if len(measured) > 1 else None,
            'latency_ms_mean': statistics.mean(latencies) if latencies else None,
            'latency_ms_sample_sd': statistics.stdev(latencies) if len(latencies) > 1 else None,
            'latency_ms_min': min(latencies) if latencies else None,
            'latency_ms_max': max(latencies) if latencies else None,
            'observed_statuses': dict(Counter(str(r.get('observed_status')) for r in rows)),
            'semantic_accuracy': None})
    clusters = defaultdict(list)
    for case in cases:
        clusters[(case['method'], case['equivalence_group'])].append(case)
    for method in {r['method'] for r in cases}:
        for group in {r['equivalence_group'] for r in contracts.values()}:
            clusters.setdefault((method, group), [])
    cluster_rows = []
    for (method, group), rows in sorted(clusters.items()):
        values = [r['component_pass_fraction_complete'] for r in rows]
        expected_cases = {k for k, v in contracts.items() if v['equivalence_group'] == group}
        complete = {r['case_id'] for r in rows} == expected_cases and all(v is not None for v in values)
        cluster_rows.append({'method': method, 'equivalence_group': group, 'case_count': len(rows),
            'component_pass_fraction': statistics.mean(values) if complete else None,
            'complete_case_repeat_measurement': complete})
    methods = []
    for method in sorted({r['method'] for r in cases}):
        group_rows = [r for r in cluster_rows if r['method'] == method]
        values = [r['component_pass_fraction'] for r in group_rows if r['component_pass_fraction'] is not None]
        methods.append({'method': method, 'observed_unique_cases': sum(r['method'] == method for r in cases),
            'observed_equivalence_clusters': sum(r['case_count'] > 0 for r in group_rows),
            'expected_equivalence_clusters': len(group_rows), 'fully_measured_clusters': len(values),
            'unmeasured_clusters': len(group_rows)-len(values),
            'component_cluster_macro_measured_only': statistics.mean(values) if values else None,
            'full_semantic_accuracy': None, 'confidence_interval': None,
            'inference_policy': 'Descriptive development cohort only; repeated rows are not independent cases; no independent GOLD or holdout.'})
    return {'case_repeats': cases, 'equivalence_clusters': cluster_rows, 'methods': methods}


def run(run_dir, contracts_path, output):
    run_dir, contracts_path, output = map(Path, (run_dir, contracts_path, output))
    if output.exists():
        raise FileExistsError('New report directory required')
    state = json.loads((run_dir/'status.json').read_text(encoding='utf-8'))
    require_unchanged(state['source_hashes'])
    frozen_contract = str(Path(state['contracts']).resolve())
    if (str(contracts_path.resolve()) != frozen_contract
            or sha(contracts_path) != state['source_hashes'].get(frozen_contract)):
        raise ValueError('Scoring must use the contracts frozen before execution')
    contracts = {r['case_id']: r for r in load(contracts_path)}
    if len(contracts) != 18:
        raise ValueError('18 frozen contracts required')
    sources = [(run_dir/'baselines', 'baseline', None)] + [(run_dir/f'graph_repeat_{i}', 'graph', i) for i in range(5)]
    scores, provenance = [], []
    for folder, kind, external in sources:
        verified = validate_stage(folder, kind)
        provenance.append(verified)
        for row in load(verified['raw_path']):
            if row['case_id'] not in contracts:
                raise ValueError('Unknown case')
            observed = score(row, contracts[row['case_id']], 'BASELINE_EXECUTION_ADAPTER' if kind == 'baseline' else 'P_PRODUCTION_GRAPH')
            observed.update(external_repeat=row['repeat'] if external is None else external,
                raw_repeat=row.get('repeat'), raw_source=verified['raw_path'], raw_source_sha256=verified['raw_sha256'],
                latency_ms=row.get('total_latency_ms', row.get('latency_ms')),
                observed_status=row.get('graph_status', row.get('status')))
            scores.append(observed)
    result = summarize(scores, contracts)
    output.mkdir(parents=True)
    for name, rows in [('component_scores', scores), *result.items()]:
        (output/(name+'.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')
    manifest = {'rows': len(scores), 'expected_rows': 540, 'contract_sha256': sha(contracts_path),
                'sources': provenance, 'independent_human_gold': False, 'holdout': False,
                'scientific_completion': False, 'semantic_accuracy': None,
                'scope': 'Frozen K5 component audit and within-case stability; not independent case accuracy',
                'frozen_sources_digest': __import__('hashlib').sha256(json.dumps(state['source_hashes'], sort_keys=True).encode()).hexdigest(),
                'evaluator_sha256': sha(Path(__file__).with_name('execution_report.py'))}
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# K5 반복 실험: 구성요소 검사와 변동성', '',
        '독립 검수 전 개발 사례의 잠정 구성요소 검사입니다. 540행을 540개 독립 사례로 취급하지 않습니다.',
        '각 사례의 5회 반복을 먼저 평균하고, 동등표현은 같은 군집으로 묶습니다. 미측정 반복이 있으면 완전 측정 평균은 null입니다.',
        'P는 기존 생성 옵션을 유지한 fresh-process 반복이며 baseline은 seed 42~46입니다. 동일 계산예산·순서 무작위 실험이 아닙니다.', '',
        '| 방법 | 고유 사례 | 동등표현 군집 | 완전 측정 군집 | 구성요소 군집 평균(측정분만) |', '|---|---:|---:|---:|---:|']
    for r in result['methods']:
        value = r['component_cluster_macro_measured_only']
        lines.append(f"| {r['method']} | {r['observed_unique_cases']} | {r['observed_equivalence_clusters']} | {r['fully_measured_clusters']} | {value if value is not None else '미측정'} |")
    lines += ['', '위 값은 전체 의미 정답률이 아닙니다. 군집별 결측 분모가 다른 방법을 승률로 순위화하지 않습니다.',
              'case_repeats.jsonl에 사례별 검사 변동, 상태 분포와 지연 평균·표준편차·범위를 보존했습니다.',
              '독립 검수 A/B와 합의 결과를 받은 뒤 별도 확정 참조 버전으로 재채점해야 합니다. 개발셋은 검수 후에도 holdout이 되지 않습니다.']
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', required=True); p.add_argument('--contracts', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); run(a.run, a.contracts, a.output)
