"""Common GOLD v2 machine-contract scoring and explicitly scoped RQ summaries."""
from collections import Counter, defaultdict
from research.marine_geollm_scie.evaluation.gold_v2 import score, all_known
from research.marine_geollm_scie.evaluation.metrics import distribution
from research.marine_geollm_scie.evaluation.rq_metrics import rate
from research.marine_geollm_scie.evaluation.v2_observations import normalize
from research.marine_geollm_scie.runners.execution_report import check_contract


def score_row(row, contract):
    observation = normalize(row)
    trace = observation['trace']
    base = {'case_id': row['case_id'], 'method': row['method'], 'repeat': row['repeat'],
            'query_condition': contract.get('category'), 'equivalence_group': contract.get('equivalence_group', row['case_id']),
            'stratum': contract['evaluation_stratum'], 'run_status': row.get('status'),
            'execution_succeeded': trace.get('execution_succeeded'), 'spatial_correctness': None,
            'safe_abstention_correct': None, 'silent_spatial_failure': None,
            'execution_correctness_gap_applicable': False, 'all_applicable_checks_pass': None,
            'checks': {}, 'semantic_human_accuracy': None, 'observation': observation,
            'costs': row.get('costs') or {}}
    if not observation['output_available']:
        base['scoring_status'] = 'OUTPUT_UNAVAILABLE'
        base['error_types'] = [row.get('error_type') or row.get('status') or 'OUTPUT_UNAVAILABLE']
        return base
    answer = observation['answer']
    if contract['evaluation_stratum'] == 'SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4':
        checks = {c['id']: check_contract(answer, c) for c in contract.get('machine_checks', [])}
        base.update(checks=checks, all_applicable_checks_pass=all_known(checks))
        spatial_checks = [c for c in contract.get('machine_checks', []) if c['kind'] == 'source_bound_set_equality']
        if spatial_checks:
            base['spatial_correctness'] = all_known({c['id']: checks[c['id']] for c in spatial_checks})
            base['execution_correctness_gap_applicable'] = True
    else:
        base.update(score(contract, answer, trace))
        if contract['evaluation_stratum'] == 'MISSING_REQUIRED_INPUT':
            for key in ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed'):
                value = trace.get(key)
                base['checks'][key+'_false'] = False if value is True else True if value is False and trace.get('observation_complete') else None
            base['all_applicable_checks_pass'] = all_known(base['checks'])
    base['scoring_status'] = 'MACHINE_CONTRACT_ONLY'
    if base['execution_correctness_gap_applicable'] and base['execution_succeeded'] is True and isinstance(base['spatial_correctness'], bool):
        base['silent_spatial_failure'] = not base['spatial_correctness']
    errors = [name for name, value in base['checks'].items() if value is False]
    if any(value is None for value in base['checks'].values()):
        errors.append('UNMEASURED_COMPONENT')
    if row.get('error_type'):
        errors.append(row['error_type'])
    base['error_types'] = errors or ['NO_MACHINE_FAILURE_OBSERVED']
    return base


def group_summary(rows):
    spatial = [r for r in rows if r['execution_correctness_gap_applicable']]
    executed = [r for r in spatial if r['execution_succeeded'] is True]
    execution = rate([r['execution_succeeded'] for r in spatial])
    correctness = rate([r['spatial_correctness'] for r in spatial])
    joint = rate([False if r['execution_succeeded'] is False else r['spatial_correctness']
                  if r['execution_succeeded'] is True else None for r in spatial])
    silent = rate([r['silent_spatial_failure'] for r in executed])
    if execution['missing']:
        silent['value'] = None
    result = {'observations': len(rows), 'distinct_cases': len({r['case_id'] for r in rows}),
              'equivalence_groups': len({r['equivalence_group'] for r in rows}),
              'machine_contract_pass': rate([r['all_applicable_checks_pass'] for r in rows]),
              'safe_abstention': rate([r['safe_abstention_correct'] for r in rows if r['stratum'] == 'OUT_OF_COVERAGE_SAFE_ABSTENTION']),
              'execution_success': execution, 'spatial_correctness': correctness,
              'joint_execution_spatial_success': joint, 'silent_spatial_failure_given_success': silent,
              'execution_correctness_gap': execution['value']-joint['value'] if execution['value'] is not None and joint['value'] is not None else None,
              'error_types': dict(Counter(e for r in rows for e in r['error_types'])),
              'semantic_human_accuracy': None, 'costs': {}}
    for key in ('latency_seconds', 'input_tokens', 'output_tokens', 'tool_calls', 'sql_calls', 'model_calls'):
        values = [(r.get('costs') or {}).get(key) for r in rows]
        values = [v if isinstance(v, (int,float)) and not isinstance(v,bool) and v >= 0 else None for v in values]
        result['costs'][key] = distribution(values)
    return result


def summarize(rows):
    groups = defaultdict(list)
    strata = defaultdict(list)
    errors = defaultdict(list)
    for row in rows:
        groups[(row['method'], row['query_condition'])].append(row)
        strata[(row['method'], row['stratum'])].append(row)
        for error in row['error_types']:
            errors[(row['method'], error)].append(row)
    methods = sorted({r['method'] for r in rows})
    return {'scope': 'FROZEN_DEVELOPMENT_BENCHMARK_MACHINE_CONTRACTS_NOT_HUMAN_SEMANTIC_ACCURACY',
            'overall_by_method': {m: group_summary([r for r in rows if r['method'] == m]) for m in methods},
            'by_method_query_condition': {m+'|'+str(c): group_summary(v) for (m,c),v in groups.items()},
            'by_method_stratum': {m+'|'+str(c): group_summary(v) for (m,c),v in strata.items()},
            'by_method_error_type': {m+'|'+str(c): group_summary(v) for (m,c),v in errors.items()},
            'rq2_fault_comparison': {'status': 'NOT_MEASURED', 'reason': 'No separately frozen matched fault observations supplied'},
            'rq4_recovery': {'status': 'NOT_MEASURED', 'reason': 'No separately frozen recovery and semantic-preservation observations supplied'},
            'rq5_false_ready_false_block': {'status': 'NOT_MEASURED', 'reason': 'Needs independent executable/invalid labels, not inferred from spatial failure'},
            'repeated_rows_are_independent_samples': False, 'independent_gold_review_complete': False}
