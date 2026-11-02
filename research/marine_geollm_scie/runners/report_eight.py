"""Verify immutable raw receipts and write a new eight-method GOLD v2 report."""
import argparse
import hashlib
import json
from pathlib import Path
from research.marine_geollm_scie.runners.freeze_v2_benchmark import verify
from research.marine_geollm_scie.reliability.research_release_gate import report_gate
from research.marine_geollm_scie.evaluation.v2_results import score_row, summarize


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def verify_raw(run, row):
    path = (run / row['raw_artifact_path']).resolve()
    if not path.is_relative_to(run) or not path.is_file() or sha(path) != row['raw_artifact_sha256']:
        raise ValueError('Raw artifact path/hash mismatch: '+str(row.get('case_id')))
    raw = json.loads(path.read_text(encoding='utf-8'))
    # The artifact is the receipt row before its own path/hash was attached.
    for key in ('case_id', 'method', 'repeat', 'emitted_answer', 'final_state',
                'execution_observation', 'costs', 'execution_identity', 'benchmark_sha256',
                'initial_plan_sha256', 'review_artifact_sha256','lossless_compilation_verified',
                'compilation_status','compilation_failure_reason','execution_callback_invoked',
                'status','error_type','domain_tools_enabled','answer_projection_error',
                'execution_status_before_projection','expected_error_type'):
        if row.get(key) != raw.get(key):
            raise ValueError('Observation differs from raw artifact: '+key)
    return path


def run_report(run_dir, benchmark, output, *, faults=None):
    run = Path(run_dir).resolve(); benchmark = Path(benchmark).resolve(); output = Path(output)
    if output.exists():
        raise FileExistsError('New report directory required')
    manifest = json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    verify(benchmark, expected_manifest_sha256=manifest.get('benchmark_sha256'))
    if not manifest.get('benchmark_sha256'):
        raise ValueError('Pinned benchmark SHA256 required')
    contracts = jsonl(benchmark/'answer_contracts.jsonl')
    by_case = {c['case_id']: c for c in contracts}
    rows_path = run/'observations.jsonl'
    rows = jsonl(rows_path)
    for row in rows:
        verify_raw(run, row)
        if row['case_id'] not in by_case:
            raise ValueError('Unknown benchmark case')
    gate = report_gate(case_ids=list(by_case), repeats=manifest.get('repeats', []),
        observations=rows, execution_identity=manifest.get('execution_identity', {}),
        benchmark_sha256=manifest['benchmark_sha256'], raw_integrity_verified=True)
    # Missing observations remain a partial report, not completed benchmark.
    scores = [score_row(r, by_case[r['case_id']]) for r in rows]
    summary = summarize(scores)
    if faults is not None:
        from research.marine_geollm_scie.runners.report_eight_faults import (
            load_verified_faults,recovery_measurement_summary,recovery_measurement_lines)
        from research.marine_geollm_scie.evaluation.v2_fault_results import summarize_faults
        fault_rows,fault_manifest=load_verified_faults(faults,
            benchmark_sha256=manifest['benchmark_sha256'],execution_identity=manifest.get('execution_identity'))
        diagnostic=summarize_faults(fault_rows)
        measurement=recovery_measurement_summary(fault_rows)
        diagnostic['recovery_measurement_coverage']=measurement['coverage_by_method']
        summary['controlled_fault_recovery']=diagnostic
        summary['rq2_fault_comparison']={'status':diagnostic['status'],'artifact':str(Path(faults).resolve()),
            'rows':len(fault_rows),'fault_contract_sha256':fault_manifest['fault_contract_sha256']}
        summary['rq4_recovery']=measurement
        summary['rq5_false_ready_false_block']={'status':diagnostic['status'],'scope':'Controlled fault labels and one valid control, not full benchmark correctness'}
    summary['completion_gate'] = gate
    summary['expected_observations'] = 18*8*len(manifest.get('repeats', []))
    summary['observed_rows'] = len(rows)
    summary['scientific_completion'] = False
    output.mkdir(parents=True, exist_ok=False)
    (output/'scores.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in scores), encoding='utf-8')
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# GOLD v2 8방법 공통 평가', '',
             '기계 계약·실제 공간 관측의 평가이며 독립 인간 의미 정확도가 아닙니다.', '',
             f"관측 {len(rows)}/{summary['expected_observations']}; 관측 완료 gate: {gate['observation_comparison_complete']}.", '',
             '| 방법 | 행 | 기계 계약 통과/측정/전체 | 공간 실행 성공(전체 적격) | 공간 실행 성공(시도 조건부) | 공간 정확성 | Silent Spatial Failure |',
             '|---|---:|---|---|---|---|---|']
    def display(v):
        return '미측정' if v is None else f'{v:.4f}'
    for method, group in summary['overall_by_method'].items():
        p=group['machine_contract_pass']
        values=[display(group[k]['value'])+f" (측정 {group[k]['measured']}/{group[k]['denominator']})" for k in ('execution_success_all_eligible','execution_success_given_attempt','spatial_correctness','silent_spatial_failure_given_success')]
        passed=sum(r['all_applicable_checks_pass'] is True for r in scores if r['method']==method)
        lines.append(f"| {method} | {group['observations']} | {passed}/{p['measured']}/{p['denominator']} | {' | '.join(values)} |")
    lines += ['', '실행 성공은 공통 v3 정의입니다. 관측 완료·실제 미실행은 false, 관측 중단·누락·모순은 null입니다. SQL 성공과 공간 정답을 분리합니다.',
              '전체 적격 ESR은 GOLD로 선택한 동일 공간 문항을 분모로 하며 출력 누락도 제외하지 않습니다. 조건부 ESR은 실제 공간 시도 문항만 사용합니다.',
              '영역 요청·coverage 중단이 정답인 문항은 공간 ESR 분모에서 제외하며 별도 행동 계약으로 평가합니다. 동일 equivalence_group의 표현 변형은 독립 공간 문제로 세지 않습니다.',
              '전체 평균과 별도로 summary.json의 by_method_query_condition 및 error_types를 확인하세요.',
              '누락은 0점 또는 비실행으로 채우지 않습니다. 공간 기준이 없는 coverage 문항은 Safe Abstention으로 분리합니다.',
              ('RQ2·RQ4 및 False Ready/False Block은 summary.json의 controlled_fault_recovery에서 별도 통제된 오류 cohort로 확인합니다. 독립 전문가 의미 정확도가 아닙니다.' if faults is not None else
               'RQ2 fault 검출, RQ4 복구·의미 보존, False Ready/False Block은 실제 별도 대조 관측이 없어 미측정입니다.'),
              '반복 행을 독립 표본으로 세지 않으며, 현재 결과로 전체 의미 정확도나 논문 결론을 선언하지 않습니다.']
    if faults is not None:
        lines+=recovery_measurement_lines(summary['rq4_recovery'])
    if gate['errors']:
        lines += ['', '## 완료 gate 미충족', *['- '+e for e in gate['errors']]]
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    provenance={'run_manifest_sha256':sha(run/'manifest.json'), 'observations_sha256':sha(rows_path),
                'benchmark_sha256':sha(benchmark/'manifest.json'), 'raw_files_verified':len(rows),
                'report_files':{p.name:sha(p) for p in output.iterdir() if p.is_file()},
                'source_hashes': {str(p.relative_to(Path(__file__).resolve().parents[3])): sha(p) for p in (
                    Path(__file__), Path(__file__).resolve().parents[1]/'evaluation/v2_results.py',
                    Path(__file__).resolve().parents[1]/'evaluation/v2_observations.py',
                    Path(__file__).resolve().parents[1]/'evaluation/execution_semantics.py')},
                'scientific_completion':False}
    (output/'manifest.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',required=True,type=Path)
    parser.add_argument('--benchmark',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--faults',type=Path)
    args=parser.parse_args()
    result=run_report(args.run_dir,args.benchmark,args.output,faults=args.faults)
    print(json.dumps({'rows':result['observed_rows'],'gate':result['completion_gate']},ensure_ascii=True))
