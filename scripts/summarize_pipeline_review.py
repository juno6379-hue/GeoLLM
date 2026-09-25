"""Produce a stage-observation matrix; statuses and model labels are not accuracy."""
import argparse
from collections import Counter
import json
from pathlib import Path


def rows(path):
    return {r['sample']: r for r in map(json.loads, path.read_text(encoding='utf-8').splitlines())}


def final(row):
    return (row.get('completion') or {}).get('final_result') or {}


def stage(row):
    result = final(row)
    orch = result.get('orchestrator_v2') or {}
    plan = orch.get('route_plan') or {}
    context = orch.get('query_execution_context') or {}
    return {'task_id': row.get('task_id'), 'status': result.get('status', row.get('observation')),
            'error': result.get('error_code'), 'intent': plan.get('intent'), 'analysis_type': plan.get('analysis_type'),
            'slots': plan.get('slots'), 'tools': context.get('tool_bindings'), 'data_bindings': context.get('data_bindings'),
            'candidate_routes': (orch.get('candidate_trace') or {}).get('route_candidates'),
            'execution_selection': (orch.get('candidate_trace') or {}).get('execution_selection'),
            'answer': result.get('answer_text'), 'result_fields': sorted((result.get('structured_result') or {}).keys())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--current', type=Path, required=True)
    p.add_argument('--shadow', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    before, after, shadow = rows(args.baseline), rows(args.current), rows(args.shadow)
    combined = []
    for sample, row in sorted(before.items()):
        model = shadow.get(sample) or {}
        combined.append({'sample': sample, 'query': row['query'], 'before': stage(row),
                        'after': stage(after[sample]) if sample in after else None,
                        'ollama': {'accepted_structure_only': model.get('accepted'), 'judgement': model.get('judgement'),
                                   'rejected_reason': model.get('rejected_reason'), 'used': False},
                        'human_gold': False, 'semantic_correctness': 'REVIEW_REQUIRED'})
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'stage_matrix.json').write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 실제 웹 샘플 단계별 관측', '', '상태/route 일치는 정확도가 아니다. AI의 판단 근거는 pipeline_repair_review_20260925.md를 참조한다.', '',
             '|번호|질의|수정 전 상태/분석|수정 후 상태/분석|Ollama 기본 검사/선택|', '|---|---|---|---|---|']
    for r in combined:
        b, a, m = r['before'], r['after'] or {}, r['ollama']
        selection = (m.get('judgement') or {}).get('primary') if m['accepted_structure_only'] else 'REJECTED'
        lines.append(f"|{r['sample']}|{r['query'].replace('|','/')}|{b['status']} / {b['analysis_type']}|{a.get('status')} / {a.get('analysis_type')}|{selection}|")
    (args.output/'stage_matrix.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'observed_after': len(after), 'statuses': dict(Counter(stage(r)['status'] for r in after.values())), 'matrix_rows': len(combined)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
