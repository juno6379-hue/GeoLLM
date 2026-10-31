"""Fail-closed structural checks for research specifications, not runtime authorization."""
from pathlib import Path
import yaml

DETECTORS = {'LLM_REVIEW_PRIMARY', 'DETERMINISTIC_PRIMARY', 'HYBRID', 'POST_EXECUTION_PRIMARY'}


def load(root=None):
    root = Path(root) if root else Path(__file__).resolve().parent
    return tuple(yaml.safe_load((root / name).read_text(encoding='utf-8')) for name in
                 ('reliability_case_registry.yaml', 'reliability_policy_registry.yaml'))


def validate(cases, policies):
    """Raise ValueError for invalid specifications; never returns EXECUTION_READY."""
    errors = []
    rows = cases.get('cases', [])
    ids = [r.get('case_id') for r in rows]
    if not ids or len(ids) != len(set(ids)):
        errors.append('duplicate or missing case IDs')
    if cases.get('production_enabled') is not False or policies.get('production_enabled') is not False:
        errors.append('research registry must not activate production')
    if policies.get('example_is_adopted_policy') is not False or policies.get('default_distance_m') is not None:
        errors.append('example default must not silently become policy')
    rules = {p['policy_id']: p for p in policies.get('policies', [])}
    if len(rules) != len(policies.get('policies', [])):
        errors.append('duplicate policy IDs')
    for row in rows:
        cid = row.get('case_id')
        if row.get('proposed_primary_detector') not in DETECTORS:
            errors.append(f'{cid}: detector missing')
        if row.get('detector_superiority_measured') is not False:
            errors.append(f'{cid}: unmeasured superiority claim')
        if not row.get('rq') or not set(row['rq']) <= {f'RQ{i}' for i in range(1, 6)}:
            errors.append(f'{cid}: invalid RQ mapping')
        if row.get('policy_id') not in rules or cid not in rules[row['policy_id']]['case_ids']:
            errors.append(f'{cid}: broken policy reference')
        if row.get('production_status') is not None and not row.get('implementation_evidence'):
            errors.append(f'{cid}: implementation claim without evidence')
        for key in ('query_example','failure_scenario','risk_ko','required_qec_information',
                    'expected_decision','forbidden_behavior','related_code','metrics'):
            if not row.get(key):
                errors.append(f'{cid}: missing {key}')
    specs = cases.get('representative_test_specs', [])
    if {t['test_id'] for t in specs} != {f'RC-T{i:02d}' for i in range(1, 31)} or len(specs) != 30:
        errors.append('30 distinct representative specifications required')
    for spec in specs:
        if not set(spec.get('case_ids', [])) <= set(ids) or not spec.get('case_ids'):
            errors.append('unresolved representative case reference')
    if policies.get('methods') != ['B0','B1','B2','B3','B4','P0','H','P1']:
        errors.append('eight-method identity changed')
    paired = policies.get('matched_plan', {})
    if paired.get('same_initial_plan_hash') is not True or paired.get('p0_compilation') != 'LOSSLESS_NO_INFERENCE':
        errors.append('paired-plan / lossless constraint missing')
    if errors:
        raise ValueError('; '.join(errors))
    return {'case_count': len(ids), 'representative_spec_count': len(specs), 'production_enabled': False}


if __name__ == '__main__':
    print(validate(*load()))
