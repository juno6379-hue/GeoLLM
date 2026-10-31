"""Verify controlled-fault raw evidence before writing RQ2/RQ4 diagnostics."""
import argparse
import json
from pathlib import Path
from research.marine_geollm_scie.runners.report_eight import sha,jsonl
from research.marine_geollm_scie.evaluation.v2_fault_results import summarize_faults
from research.marine_geollm_scie.runners.matched_branches import plan_hash


def load_verified_faults(folder, *, benchmark_sha256=None, execution_identity=None):
    folder=Path(folder)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('status')!='COMPLETED_CONTROLLED_DIAGNOSTICS':
        raise ValueError('Controlled fault run incomplete')
    if benchmark_sha256 is not None and manifest.get('benchmark_sha256')!=benchmark_sha256:
        raise ValueError('Fault GOLD identity differs')
    if execution_identity is not None and manifest.get('execution_identity')!=execution_identity:
        raise ValueError('Fault execution identity differs; new run required')
    for name,key in [('fault_contract.json','fault_contract_sha256'),('independent_oracle.json','independent_oracle_sha256'),('rows.jsonl','rows_sha256')]:
        if sha(folder/name)!=manifest.get(key):raise ValueError('Fault artifact changed: '+name)
    contract=json.loads((folder/'fault_contract.json').read_text(encoding='utf-8'))
    cases={c['case_id']:c for c in contract['cases']}
    rows=jsonl(folder/'rows.jsonl')
    expected={(case,method) for case in cases for method in ('B4','P0','H')}
    if len(rows)!=len(expected) or {(r['case_id'],r['method']) for r in rows}!=expected:
        raise ValueError('Fault observation set incomplete or duplicate')
    for row in rows:
        case=cases[row['case_id']]
        # Case and method values above are constrained to the frozen contract.
        directory=folder/row['case_id']
        if not directory.resolve().is_relative_to(folder.resolve()):raise ValueError('Invalid case path')
        if json.loads((directory/'initial_plan.json').read_text(encoding='utf-8'))!=case or plan_hash(case['plan'])!=case['initial_plan_sha256']:
            raise ValueError('Frozen initial fault plan changed')
        if json.loads((directory/(row['method']+'.json')).read_text(encoding='utf-8'))!=row:
            raise ValueError('Fault row differs from raw branch')
        if row.get('expected_invalid') is not case['expected_invalid'] or row.get('initial_plan_sha256')!=case['initial_plan_sha256']:
            raise ValueError('Fault initial condition/label differs')
        for key in ('fault_contract_sha256','independent_oracle_sha256','benchmark_sha256','execution_identity'):
            if row.get(key)!=manifest.get(key):raise ValueError('Fault row lineage differs: '+key)
        if row.get('review_artifact_sha256')!=sha(directory/'review.json'):
            raise ValueError('Shared reviewer raw changed')
    return rows,manifest


def run_report(folder,output):
    output=Path(output)
    if output.exists():raise FileExistsError('New report directory required')
    rows,manifest=load_verified_faults(folder)
    summary=summarize_faults(rows)
    output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 동일 오류 입력 검출·복구 비교', '',
           '원래18문항과 분리한 통제된 오류 진단입니다. 독립 전문가 GOLD 정확도가 아닙니다.', '',
           '| 방법 | 관측 | False Ready | False Block | 복구시도 | 의미보존·공간정답 공동성공(시도 기준) |',
           '|---|---:|---|---|---:|---|']
    def show(x):return '미측정' if x is None else f'{x:.4f}'
    for method,result in summary['overall_by_method'].items():
        lines.append(f"| {method} | {result['rows']} | {show(result['false_ready']['value'])} | {show(result['false_block']['value'])} | {result['recovery_attempted']} | {show(result['joint_recovery_given_attempt']['value'])} |")
    lines+=['','오류 유형별 결과·분모·미측정은 summary.json에 보존했습니다.',
            'P0는 추가 복구 추론이 없는 Validator 조건이므로 복구율 분모에서 제외합니다.',
            'Hybrid 초기 검출은 두 최초 verdict의 OR이며, 복구 실행은 동일 검토안에 Validator를 추가합니다.',
            '권한 분리 원천이 없어 permission fault는 미실행입니다. 이 cohort가 전체 reliability taxonomy를 완전히 검증한 것은 아닙니다.']
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({'source_run_manifest_sha256':sha(Path(folder)/'manifest.json'),
        'rows_sha256':manifest['rows_sha256'],'fault_contract_sha256':manifest['fault_contract_sha256'],
        'scientific_completion':False},indent=2),encoding='utf-8')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=run_report(a.run_dir,a.output)
    print(json.dumps({'status':result['status'],'methods':list(result['overall_by_method'])}))
