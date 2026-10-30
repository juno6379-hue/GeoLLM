"""Freeze user-selected AI review workbooks and audit existing plans, research only.

Checks are post-hoc, narrow structural diagnostics, not semantic or execution accuracy.
The input workbooks and original model outputs are never modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

from .import_review_workbooks import read_workbook


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def records(workbook, sheet):
    rows = workbook['sheets'][sheet]
    headers = {re.sub(r'\d+', '', a): c['value'] for a, c in rows[0].items()}
    return [{headers[re.sub(r'\d+', '', a)]: c['value'] for a, c in row.items()} for row in rows[1:]]


def index_cases(rows):
    result = {}
    for row in rows:
        key = row['사례 ID']
        if key in result:
            raise ValueError(f'Duplicate case: {key}')
        result[key] = row
    return result


def validate_sources(consensus, a, b, cases):
    rows = records(consensus, '합의작성')
    ar = index_cases(records(a, '검수작성'))
    br = index_cases(records(b, 'AI 검토안'))
    cr = index_cases(rows)
    if len(cr) != 18 or set(cr) != set(ar) or set(cr) != set(br):
        raise ValueError('Expected the same 18 case IDs in all three files')
    for key, row in cr.items():
        if row['A 제출파일 SHA256'] != a['sha256'] or row['B 제출파일 SHA256'] != b['sha256']:
            raise ValueError(f'Source workbook hash mismatch: {key}')
        if key not in cases or any(x[key]['원문 질의'] != cases[key]['query'] for x in (ar, br, cr)):
            raise ValueError(f'Original query mismatch: {key}')
        if row['상태(유지)'] != 'DRAFT' or 'human_approval=false' not in row['수동 승인 기록']:
            raise ValueError('Approval changed: explicit review workflow required')
    return cr, ar, br


def plan_checks(case_id, plan):
    """Limited explicit slot checks; no keyword-based answer grading."""
    if not isinstance(plan, dict):
        return [{'field': 'plan', 'status': 'UNAVAILABLE', 'observed': plan}]
    expected = {}
    if case_id in {'PILOT_Q1_03', 'PILOT_Q2_03', 'PILOT_Q6_03'}:
        expected = {'spatial_relation': 'none', 'radius_m': None, 'location_text': None}
    elif case_id == 'PILOT_Q3_03':
        expected = {'spatial_relation': 'intersects', 'radius_m': None}
    elif case_id in {'PILOT_Q4_01', 'PILOT_Q5_03'}:
        expected = {'spatial_relation': 'dwithin', 'radius_m': 5000}
    return [{'field': field, 'expected': value, 'observed': plan.get(field),
             'status': 'MATCH' if field in plan and plan[field] == value else 'REVIEW_REQUIRED'}
            for field, value in expected.items()]


def run(root, input_dir, model_run, output):
    paths = [input_dir / name for name in (
        '합의검토_18사례_AI합의수정본_v2.xlsx',
        '검수자A_18사례_AI사전검토_Dataset근거_v2.xlsx',
        '검수자B_18사례_AI사전검토_v2.xlsx')]
    workbooks = [read_workbook(p) for p in paths]
    cases = {r['case_id']: r for r in map(json.loads, (root / 'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl').read_text(encoding='utf-8').splitlines())}
    consensus, ar, br = validate_sources(*workbooks, cases)
    manifest = json.loads((model_run / 'manifest.json').read_text(encoding='utf-8'))
    raw_path = model_run / 'comparison_rows.jsonl'
    raw = [json.loads(s) for s in raw_path.read_text(encoding='utf-8').splitlines()]
    if manifest['status'] != 'COMPLETED' or manifest['rows'] != len(raw) or manifest['rows_sha256'] != sha(raw_path):
        raise ValueError('Completed model run digest/row count mismatch')
    if len({(r['case_id'], r['method'], r['repeat']) for r in raw}) != len(raw):
        raise ValueError('Duplicate model observations')
    if not {r['case_id'] for r in raw} <= consensus.keys():
        raise ValueError('Model case absent from review')
    model_cases = json.loads((model_run / 'cases.json').read_text(encoding='utf-8'))
    if any(c['query'] != consensus[c['case_id']]['원문 질의'] for c in model_cases):
        raise ValueError('Model query differs from review')
    output.mkdir(parents=True, exist_ok=False)
    for path in paths:
        shutil.copy2(path, output / path.name)
    (output / 'workbook_cells.json').write_text(json.dumps(workbooks, ensure_ascii=False, indent=2), encoding='utf-8')
    annotations = []
    for key, row in consensus.items():
        full_b = [r for r in records(workbooks[2], '입력필드전체') if r['사례 ID'] == key]
        annotations.append({'case_id': key, 'query': row['원문 질의'],
            'annotation_status': 'DRAFT', 'review_kind': 'AI_PRE_REVIEW', 'human_approval': False,
            'resolution': row['합의 결과'], 'evidence': row['합의 근거·출처'],
            'disagreements': row['불일치 항목'], 'remaining_review': row['추가 검토사항'],
            'source_locator': f'합의작성!A{list(consensus).index(key)+2}:L{list(consensus).index(key)+2}',
            'reviewer_A': ar[key], 'reviewer_B_display': br[key], 'reviewer_B_full_fields': full_b,
            'source_sha256': workbooks[0]['sha256'], 'spatial_object_ids': None})
    write_jsonl(output / 'annotations_DRAFT.jsonl', annotations)
    diagnostics = []
    for row in raw:
        diagnostics.append({'case_id': row['case_id'], 'method': row['method'], 'repeat': row['repeat'],
            'status': row['status'], 'plan': row.get('plan'), 'checks': plan_checks(row['case_id'], row.get('plan')),
            'semantic_correct': None, 'execution_success': None, 'spatial_correct': None,
            'evidence_correct': None, 'human_approval': False, 'evaluation_kind': 'POST_HOC_DRAFT_DIAGNOSTIC'})
    write_jsonl(output / 'plan_diagnostics.jsonl', diagnostics)
    dataset_audit = []
    for path in (root / 'Dataset').glob('*.csv'):
        if path.name not in {'해양수산부_공동활용체계_해양지명_20221231.csv', '해양수산부 부산지방해양수산청_항로표지정보_20250623.csv'}:
            continue
        for encoding in ('utf-8-sig', 'cp949'):
            try:
                with path.open(encoding=encoding, newline='') as f:
                    rows = list(csv.DictReader(f))
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f'Unknown CSV encoding: {path.name}')
        dataset_audit.append({'path': str(path), 'sha256': sha(path), 'encoding': encoding,
            'rows': len(rows), 'columns': list(rows[0]) if rows else [],
            'dokdo_any_field_rows': sum(any('독도' in str(v) for v in r.values()) for r in rows),
            'dokdo_exact_any_field_rows': sum(any(str(v).strip() == '독도' for v in r.values()) for r in rows),
            'lighthouse_any_field_rows': sum(any('등대' in str(v) for v in r.values()) for r in rows),
            'scope': 'CSV content inventory only; no coordinate, coverage or spatial GOLD approval'})
    (output / 'dataset_audit.json').write_text(json.dumps(dataset_audit, ensure_ascii=False, indent=2), encoding='utf-8')
    counts = Counter(r['disagreements'].split(']')[0].lstrip('[') for r in annotations)
    info = {'status': 'DRAFT_REFERENCE_INTEGRATED', 'cases': len(annotations), 'model_rows': len(raw),
        'human_gold_cases': 0, 'review_groups': dict(counts), 'model_rows_sha256': sha(raw_path),
        'model_run': str(model_run), 'sources': [{'path': w['path'], 'sha256': w['sha256']} for w in workbooks],
        'source_hash_links_verified': True, 'accuracy': None, 'kappa': None,
        'protocol': 'Post-hoc structural slot diagnostics only, 6 pilot cases, 3 repeats, B0-B4 planning only',
        'code_sha256': sha(Path(__file__)), 'annotations_sha256': sha(output / 'annotations_DRAFT.jsonl')}
    (output / 'manifest.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# v2 검토안 반영 및 기존 모델 출력 대조', '',
        '사용자가 지정한 v2 세 파일을 보존하고 합의문에 기록된 A/B SHA256과 실제 파일 일치를 검증했다.',
        '18개 사례 원문·ID 일치, B의 요약 셀뿐 아니라 입력필드전체도 보존했다. 모두 DRAFT/human_approval=false다.',
        '기존 6문항 × 5방법 × 3반복 = 90개 출력에 대조했다. 신규 모델 호출 및 운영 변경은 없다.',
        '아래 값은 사후 슬롯 진단이며 의미 정확도·실행 성공률·인간 검수자 일치도가 아니다.',
        '비공간 질의의 공간슬롯 없음, 명시 5km의 5000m/dwithin, 선택 영역 질의의 intersects만 자동 확인한다.',
        'clarify의 타당성, 전체 의미, 근거의 주장 지지 여부, 실제 공간 객체집합은 자동 채점하지 않았다.', '',
        '| 방법 | 출력 수 | 슬롯 재검토 필요 출력 | plan 미제공 출력 |', '|---|---:|---:|---:|']
    for method in sorted({r['method'] for r in diagnostics}):
        rs = [r for r in diagnostics if r['method'] == method]
        lines.append(f"| {method} | {len(rs)} | {sum(any(c['status']=='REVIEW_REQUIRED' for c in r['checks']) for r in rs)} | {sum(any(c['status']=='UNAVAILABLE' for c in r['checks']) for r in rs)} |")
    lines += ['', '## 사례별 합의와 실제 출력', '']
    for key, row in consensus.items():
        lines += [f'### {key} — {row["원문 질의"]}', '', row['합의 결과'], '',
                  '남은 검토: ' + row['추가 검토사항'], '', '근거: ' + row['합의 근거·출처'], '']
        observed = [r for r in diagnostics if r['case_id'] == key]
        if not observed:
            lines += ['이번 90행 모델 비교에 포함되지 않은 사례. 미실행을 성공/실패로 집계하지 않는다.', '']
        for r in observed:
            lines += [f"**{r['method']} / 반복 {r['repeat']}**", '',
                '```json', json.dumps({'plan': r['plan'], 'slot_diagnostics': r['checks']}, ensure_ascii=False, indent=2), '```', '']
    (output / 'v2_comparison_KR.md').write_text('\n'.join(lines), encoding='utf-8')
    return info


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--model-run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(run(a.root, a.input_dir, a.model_run, a.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
