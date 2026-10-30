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
        for key in ('review_status','annotation_status','label_status','annotator_ids','adjudication_status',
                    'review_kind','human_approval'):
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
        state_names={'error':'오류','completed':'완료','COMPONENT_RETURNED':'컴포넌트 반환',
                     'COMPLETED':'완료','NEEDS_CLARIFICATION':'추가 확인 필요','BLOCKED':'실행 차단'}
        state_text=', '.join(f'{state_names.get(state,state)} {count}회' for state,count in counts.items())
        operational_notes.append(f'- `{method}`: 실행 기록 {len(group)}개; {state_text}.'
            +(f' 독립 SQL 객체 집합과 {sum(checks)}/{len(checks)} 일치(동일 스냅샷의 정합성 검사이며 전문가 정답 평가는 아님).' if checks else ''))
    (root/'metrics'/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (root/'metrics'/'fault_diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (root/'reports'/'results_summary.md').write_text(
        '# 논문 실험 파일럿 결과 요약\n\n논문 본실험 준비 상태: **미완료(NOT_READY)**\n\n'
        f'평가 사례: {len(cases)}개; 전문가 승인 정답(GOLD): {summary["verified_gold_cases"]}개; 실행 기록: {len(rows)}개.\n\n'
        '- 논문 성능 주장에는 전문가 검수·최종 판정과 고정된 독립 평가셋이 필요합니다.\n'
        '- 반복 실행을 독립 표본으로 세거나 통계적 유의성을 주장하지 않습니다.\n'
        '- 미측정 값은 null입니다. 실행 완료가 의미 해석·공간 결과의 정확성을 보장하지 않습니다.\n'
        '- R6는 관측한 실행 구성입니다. 구성요소 제거 효과에는 동일 조건의 통제 실험이 필요합니다.\n\n'
        '처리시간은 실제 관측값과 누락 수를 함께 기록합니다. 인위적 오류 진단과 전문가 정답 기반 평가는 구분합니다.\n\n'
        +'## 실제 관측 결과\n\n'+'\n'.join(operational_notes)+'\n\n'
        +'운영 언어 분석, 실행 검증기(ExecutionValidator), 반경 공간조회는 서로 다른 컴포넌트 실험이며 전체 제안 파이프라인(P)의 결과가 아닙니다. 현재 B4는 제공된 계획을 검토하며 직접 생성·수정하지 않습니다. B0–B3, 전체 P, 통제된 구성요소 제거 실험과 오류 복구 실험은 아직 수행하지 않았습니다.\n', encoding='utf-8')
    from .build_figures import build_figures
    build_figures(root, tables)
    from .build_figures import build_operational_figure
    build_operational_figure(root, joined)
    return summary
