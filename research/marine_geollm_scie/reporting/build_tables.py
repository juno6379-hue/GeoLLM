"""Reproducible pilot tables; absent measurements remain null."""
import csv
import json
from collections import Counter
from pathlib import Path
from ..evaluation.metrics import (is_gold, semantic_metrics, evqsr, validator_metrics,
                                  recovery_metrics, distribution, mean_complete)

NAMES = ['R1_benchmark_composition','R2_semantic_grounding','R3_planning_execution',
         'R4_validator_comparison','R5_recovery','R6_ablation','R7_operational_overhead']


def write_table(path, records):
    fields = list(dict.fromkeys(k for r in records for k in r)) or ['status']
    with path.with_suffix('.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    def value(x):
        return 'NOT_READY' if x is None else str(x).replace('|', '\\|').replace('\n', ' ')
    lines = ['PILOT — NOT FINAL PAPER RESULT', '', '| ' + ' | '.join(fields) + ' |',
             '| ' + ' | '.join('---' for _ in fields) + ' |']
    lines += ['| ' + ' | '.join(value(r.get(k)) for k in fields) + ' |' for r in records]
    path.with_suffix('.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def report(run_dir, cases, rows):
    root = Path(run_dir)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    for name in ('tables','metrics','reports','figures'):
        (root/name).mkdir(parents=True, exist_ok=True)
    # Review provenance comes from the case; runtime predictions can never promote it.
    case_map = {c['case_id']: c for c in cases}
    joined = []
    for raw in rows:
        c = case_map.get(raw.get('case_id'), {})
        r = {**c, **raw}
        for key in ('review_status','annotation_status','label_status','annotator_ids','adjudication_status'):
            r.pop(key, None)
            if key in c:
                r[key] = c[key]
        for key in ('expected_behavior','gold_semantic_set','expected_invalid'):
            if key in c:
                r[key] = c[key]
        joined.append(r)
    categories = sorted({c.get('category','UNSPECIFIED') for c in cases})
    tables = [[{'category': cat, 'candidate_cases': sum(c.get('category','UNSPECIFIED')==cat for c in cases),
                'verified_gold_cases': sum(c.get('category','UNSPECIFIED')==cat and is_gold(c) for c in cases)}
               for cat in categories], [], [], [], [], [], []]
    diagnostics = []
    for method in sorted({r.get('method','UNSPECIFIED') for r in joined}):
        group = [r for r in joined if r.get('method','UNSPECIFIED')==method]
        semantic = semantic_metrics(group)
        end = evqsr(group)
        validator = validator_metrics(group)
        recovery = recovery_metrics(group)
        tables[1].append({'method':method, 'gold_rows':sum(is_gold(r) for r in group), **semantic})
        tables[2].append({'method':method,'gold_execute_rows':end['eligible'], **end['components'],
                          'evqsr':end['value'],'status':end['status']})
        tables[3].append({'method':method, **validator})
        tables[4].append({'method':method, **{k:v for k,v in recovery.items() if k!='iterations'},
                          'mean_repair_iterations':recovery['iterations']['mean']})
        tables[5].append({'profile':method,'semantic_micro_f1':semantic['micro_f1'],
                          'execution_success':end['components']['execution_success'],
                          'spatial_correct':end['components']['spatial_correct'], 'evqsr':end['value'],
                          'status':end['status']})
        latency = distribution([r.get('latency_ms') for r in group])
        operational = {'method':method,'runs':len(group),'distinct_cases':len({r.get('case_id') for r in group}),
                       **{'latency_ms_'+k:v for k,v in latency.items()},
                       'failure_rows':sum(str(r.get('status','')).upper() in ('ERROR','FAILED','TIMEOUT') for r in group)}
        for field in ('input_tokens','output_tokens','tool_calls','validator_ms','repair_ms'):
            operational.update({field+'_'+k:v for k,v in distribution([r.get(field) for r in group]).items()
                                if k in ('measured','missing','mean')})
        tables[6].append(operational)
        diagnostics.append({'method':method, 'warning':'AUTOMATED FAULT DIAGNOSTIC; NOT PUBLICATION GOLD',
                            **validator_metrics(group, require_gold=False)})
    for name, records in zip(NAMES, tables):
        write_table(root/'tables'/name, records)
    summary = {'result_class':'PILOT — NOT FINAL PAPER RESULT','publication_status':'NOT_READY',
               'cases':len(cases), 'verified_gold_cases':sum(is_gold(c) for c in cases),
               'rows':len(rows), 'status_counts':dict(Counter(r.get('status','UNKNOWN') for r in rows)),
               'tables':dict(zip(NAMES,tables)),
               'limitations':['No final-paper claims: expert adjudication and locked holdout are required.',
                              'Repeated trials are descriptive only; no unpaired significance test is reported.',
                              'Missing predictions remain null; runtime completion is not semantic or spatial truth.',
                              'R6 contains observed profiles only; causal ablation requires controlled matched runs.']}
    operational_notes=[]
    for method in sorted({r.get('method','UNSPECIFIED') for r in joined}):
        group=[r for r in joined if r.get('method','UNSPECIFIED')==method]
        counts=dict(Counter(r.get('status','UNKNOWN') for r in group))
        checks=[r['sql_object_set_consistent'] for r in group if isinstance(r.get('sql_object_set_consistent'),bool)]
        operational_notes.append(f'- `{method}`: {len(group)} rows; states {counts}.'
            +(f' Independent SQL object-set consistency: {sum(checks)}/{len(checks)} (same snapshot, not expert gold).' if checks else ''))
    (root/'metrics'/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (root/'metrics'/'fault_diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (root/'reports'/'results_summary.md').write_text(
        '# PILOT — NOT FINAL PAPER RESULT\n\nPublication status: **NOT_READY**\n\n'
        f'Cases: {len(cases)}; verified expert GOLD: {summary["verified_gold_cases"]}; run rows: {len(rows)}.\n\n'
        + '\n'.join('- '+s for s in summary['limitations'])+'\n\n'
        'Operational latency uses observed samples and lists missing counts. Fault diagnostics are separate from expert-scored results.\n\n'
        +'## Observed diagnostic runs\n\n'+'\n'.join(operational_notes)+'\n\n'
        +'Production linguistic analysis, ExecutionValidator and radius execution are separate component cohorts, not the full proposed pipeline. B4 reviews supplied fixtures; it does not generate and repair its own plans. B0–B3, full P, controlled ablations and recovery are not executed.\n', encoding='utf-8')
    from .build_figures import build_figures
    build_figures(root, tables)
    from .build_figures import build_operational_figure
    build_operational_figure(root, joined)
    return summary
