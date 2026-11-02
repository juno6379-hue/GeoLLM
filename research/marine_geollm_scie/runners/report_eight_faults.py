"""Verify controlled-fault raw evidence before writing RQ2/RQ4 diagnostics."""
import argparse
import json
from pathlib import Path
from research.marine_geollm_scie.runners.report_eight import sha,jsonl
from research.marine_geollm_scie.evaluation.v2_fault_results import summarize_faults
from research.marine_geollm_scie.runners.matched_branches import plan_hash


def verify_recovery_measurement(row, case, oracle_scope):
    from research.marine_geollm_scie.runners.eight_fault_recovery import recovery_eligibility
    expected=recovery_eligibility(case,row['method'],oracle_scope)
    if any(row.get(key)!=value for key,value in expected.items()):
        raise ValueError('Recovery eligibility differs from nonempty Oracle contract')
    if not expected['recovery_eligible'] and (row.get('recovery_attempted') is not False
            or any(row.get(key) is not None for key in ('recovery_success','semantic_preservation','spatial_correct','joint_success'))):
        raise ValueError('Excluded or unmeasured Oracle cannot claim recovery/restoration')


def recovery_measurement_coverage(rows):
    """Publish exclusions separately, never relabel old raw observations."""
    from collections import Counter
    result={}
    for method in sorted({r['method'] for r in rows}):
        group=[r for r in rows if r['method']==method]
        known=[r for r in group if r.get('recovery_measurement_version')=='nonempty_object_restoration_v1']
        protocol=[r for r in known if r.get('recovery_protocol_eligible') is True]
        result[method]={'rows':len(group),'measurement_contract_observed':len(known),
            'legacy_or_missing_contract':len(group)-len(known),
            'protocol_eligible_denominator':len(protocol),
            'nonempty_eligible_denominator':sum(r.get('recovery_eligible') is True for r in protocol),
            'excluded_or_unmeasured_reasons':dict(Counter(r['recovery_exclusion_reason'] for r in protocol if r.get('recovery_eligible') is not True)),
            'scope':'Nonempty object restoration only; initial binary fault diagnosis uses all original rows'}
    return result


def recovery_measurement_summary(rows):
    coverage=recovery_measurement_coverage(rows)
    known=sum(v['measurement_contract_observed'] for v in coverage.values())
    legacy=sum(v['legacy_or_missing_contract'] for v in coverage.values())
    eligible=sum(v['nonempty_eligible_denominator'] for v in coverage.values())
    missing=sum(v['excluded_or_unmeasured_reasons'].get('RECOVERY_ORACLE_MISSING_OR_INVALID',0) for v in coverage.values())
    status=('LEGACY_PROTOCOL_NOT_NONEMPTY_VERIFIED' if not known else
            'MIXED_CONTRACTS_NOT_COMPARABLE' if legacy else
            'UNMEASURED_ORACLE' if missing else
            'NO_NONEMPTY_ELIGIBLE_CASES' if not eligible else 'NONEMPTY_CONTROLLED_DIAGNOSTICS')
    return {'status':status,'measurement_version':'nonempty_object_restoration_v1' if known and not legacy else None,
            'coverage_by_method':coverage,
            'scope':'Fixed task tuple and nonempty source SQL object restoration; independent expert semantics unmeasured; legacy metrics retain their original contract'}


def recovery_measurement_lines(measurement):
    lines=['','## 실제 객체 복원 측정 분모', '',
           '측정 상태: '+measurement['status']+'.', '',
           '| 방법 | 프로토콜상 복구대상 | non-empty 복원 적격 | 제외·미측정 이유 | 계약 미관측 |',
           '|---|---:|---:|---|---:|']
    for method,item in measurement['coverage_by_method'].items():
        # Unknown legacy eligibility is not a measured zero.
        observed=item['measurement_contract_observed']>0
        protocol=item['protocol_eligible_denominator'] if observed else '미측정(구계약)'
        eligible=item['nonempty_eligible_denominator'] if observed else '미측정(구계약)'
        lines.append(f"| {method} | {protocol} | {eligible} | {json.dumps(item['excluded_or_unmeasured_reasons'],ensure_ascii=False)} | {item['legacy_or_missing_contract']} |")
    lines+=['','빈 Oracle는 RECOVERY_ORACLE_EMPTY로 제외, Oracle 미관측은 RECOVERY_ORACLE_MISSING_OR_INVALID로 미측정입니다. 이 행들도 초기 오류 검출 분모에는 유지합니다. 적격 0건의 복구율은 0%가 아니라 정의되지 않음(null)입니다. 기존 계약 결과와 복구율은 원래 조건 그대로 보존하며 새로운 non-empty 복구 결과로 소급 해석하지 않습니다.']
    return lines


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
    oracle_scope=None
    if contract.get('recovery_measurement_version')=='nonempty_object_restoration_v1':
        from research.marine_geollm_scie.runners.eight_fault_recovery import recovery_oracle_scope
        oracle=json.loads((folder/'independent_oracle.json').read_text(encoding='utf-8'))
        oracle_scope=recovery_oracle_scope(oracle.get('object_ids'))
        if oracle.get('recovery_oracle_scope')!=oracle_scope or manifest.get('recovery_oracle_scope')!=oracle_scope:
            raise ValueError('Recovery Oracle eligibility receipt differs')
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
        if oracle_scope is not None:
            verify_recovery_measurement(row,case,oracle_scope)
    return rows,manifest


def run_report(folder,output):
    output=Path(output)
    if output.exists():raise FileExistsError('New report directory required')
    rows,manifest=load_verified_faults(folder)
    summary=summarize_faults(rows)
    summary['recovery_measurement_coverage']=recovery_measurement_coverage(rows)
    summary['rq4_recovery']=recovery_measurement_summary(rows)
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
    lines+=recovery_measurement_lines(summary['rq4_recovery'])
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({'source_run_manifest_sha256':sha(Path(folder)/'manifest.json'),
        'rows_sha256':manifest['rows_sha256'],'fault_contract_sha256':manifest['fault_contract_sha256'],
        'scientific_completion':False},indent=2),encoding='utf-8')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=run_report(a.run_dir,a.output)
    print(json.dumps({'status':result['status'],'methods':list(result['overall_by_method'])}))
