"""Read-only, filename-bounded discovery of annotation inputs; never grants GOLD."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from research.marine_geollm_scie.evaluation.metrics import is_gold
from research.marine_geollm_scie.runners.import_review_workbooks import read_workbook

COMPONENTS = ('semantic', 'qec', 'spatial', 'evidence', 'fault')
MARKERS = ('gold', 'annotation', 'adjudication', 'reference', '승인', '검수', '합의')
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'graph', 'rag', 'staging'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def discover(roots):
    """Do not follow symlinks/junctions; read only likely annotation file names."""
    seen = set()
    for root in roots:
        for directory, folders, files in os.walk(root, followlinks=False):
            folders[:] = [n for n in folders if n not in SKIP_DIRS
                          and not Path(directory, n).is_symlink()
                          and not getattr(Path(directory, n), 'is_junction', lambda: False)()]
            for name in sorted(files):
                path = Path(directory, name)
                if path.suffix.lower() not in {'.json', '.jsonl', '.csv', '.xlsx'}:
                    continue
                if not any(marker in name.lower() for marker in MARKERS):
                    continue
                if path.is_symlink() or path.resolve() in seen:
                    continue
                seen.add(path.resolve())
                yield path


def approval_eligible(row):
    """Reuse existing approval gate; an AI identity is not an independent expert."""
    if not is_gold(row) or row.get('human_approval') is not True:
        return False
    annotators = row.get('annotator_ids')
    if not isinstance(annotators, list) or not annotators:
        return False
    return all(isinstance(x, str) and x.strip() and not x.upper().startswith('AI') for x in annotators)


def _present(value):
    return value is not None and value != '' and value != {} and value != []


def component_coverage(row):
    """Structural coverage, not factual correctness of an annotation."""
    sem = row.get('semantics') or row.get('gold_semantics') or {}
    qec = row.get('qec_fields') or row.get('gold_qec') or {}
    spatial = row.get('spatial') or row.get('spatial_oracle') or row.get('gold_spatial_results') or row
    evid = row.get('evidence') or row.get('required_evidence') or row.get('gold_evidence') or {}
    ids = spatial.get('expected_object_ids', spatial.get('object_ids')) if isinstance(spatial, dict) else None
    snapshot = spatial.get('dataset_snapshot_sha256', spatial.get('snapshot_sha256', spatial.get('database_snapshot'))) if isinstance(spatial, dict) else None
    oracle = spatial.get('oracle_sha256', spatial.get('reference_query', spatial.get('oracle_reference'))) if isinstance(spatial, dict) else None
    semantic_ok = (isinstance(sem, dict) and any(_present(sem.get(k)) for k in
                   ('intent', 'canonical_concept_candidates', 'canonical_concept_id', 'feature')))
    semantic_ok = semantic_ok or _present(row.get('gold_semantic_set')) or _present(row.get('canonical_concept_id'))
    semantic_ok = semantic_ok or (isinstance(sem, dict) and isinstance(sem.get('labels'), list))
    qec_ok = isinstance(qec, dict) and any(_present(qec.get(k)) for k in ('proposed_fields', 'slots', 'expected_fields'))
    qec_ok = qec_ok or (isinstance(qec, dict) and any('.' in k for k in qec))
    spatial_ok = isinstance(ids, list) and _present(snapshot) and _present(oracle)
    evidence_ok = isinstance(evid, dict) and any(_present(evid.get(k)) for k in ('verified_local_sources', 'references', 'required_references'))
    evidence_ok = evidence_ok or (isinstance(evid, dict) and isinstance(evid.get('required_refs'), list))
    evidence_ok = evidence_ok or _present(row.get('required_evidence_reference'))
    fault_ok = isinstance(row.get('expected_invalid'), bool) and _present(row.get('fault_type', row.get('error_code')))
    return dict(zip(COMPONENTS, map(bool, (semantic_ok, qec_ok, spatial_ok, evidence_ok, fault_ok))))


def load_rows(path):
    if path.suffix.lower() == '.xlsx':
        workbook = read_workbook(path)
        rows = []
        for name, sheet in workbook['sheets'].items():
            if not sheet:
                continue
            headers = {re.sub(r'\d+', '', a): c['value'] for a, c in sheet[0].items()}
            if '사례 ID' not in headers.values() or '원문 질의' not in headers.values():
                continue
            for cells in sheet[1:]:
                row = {headers.get(re.sub(r'\d+', '', a), a): c['value'] for a, c in cells.items()}
                if not row.get('사례 ID'):
                    continue
                # Preserve observations; spreadsheets are not silently mapped to approved labels.
                state = row.get('상태(유지)', row.get('AI 상태', row.get('상태')))
                state = 'DRAFT' if state and 'DRAFT' in state else state
                rows.append({'case_id': row['사례 ID'], 'annotation_status': state,
                             'review_kind': 'WORKBOOK_REQUIRES_EXPLICIT_IMPORT',
                             'human_approval': False if 'human_approval=false' in str(row.get('수동 승인 기록', '')) else None,
                             'source_sheet': name})
        return rows
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as file:
            return list(csv.DictReader(file))
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.jsonl':
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        rows = payload if isinstance(payload, list) else payload.get('annotations', payload.get('rows', [payload]))
    return [r for r in rows if isinstance(r, dict) and ('case_id' in r or 'annotation_status' in r)]


def audit(roots, max_bytes=32 * 1024 * 1024):
    files = []
    eligible_ids = {key: set() for key in COMPONENTS}
    approval_cohorts = {'user_approved_ai_assisted': set(), 'independent_expert_explicit': set(), 'other_approved': set()}
    for path in discover(roots):
        info = {'path': str(path.resolve()), 'sha256': sha(path), 'bytes': path.stat().st_size}
        if info['bytes'] > max_bytes:
            files.append({**info, 'status': 'NOT_READ_SIZE_LIMIT'})
            continue
        try:
            rows = load_rows(path)
            eligible = [r for r in rows if approval_eligible(r)]
            for row in eligible:
                cohort = ('user_approved_ai_assisted' if row.get('review_kind') == 'USER_APPROVED_AI_ASSISTED'
                          else 'independent_expert_explicit' if row.get('independent_expert_review') is True else 'other_approved')
                if row.get('case_id'): approval_cohorts[cohort].add(row['case_id'])
            counts = Counter()
            draft_counts = Counter()
            for row in rows:
                coverage = component_coverage(row)
                for component, covered in coverage.items():
                    draft_counts[component] += int(covered)
                    if covered and approval_eligible(row):
                        counts[component] += 1
                        if row.get('case_id'):
                            eligible_ids[component].add(row['case_id'])
            info.update(status='READ', row_count=len(rows), unique_case_count=len({r.get('case_id') for r in rows if r.get('case_id')}),
                        approval_eligible_count=len(eligible), annotation_status_counts=dict(Counter(str(r.get('annotation_status', r.get('review_status'))) for r in rows)),
                        component_counts={k: counts[k] for k in COMPONENTS},
                        draft_or_unapproved_component_counts={k: draft_counts[k]-counts[k] for k in COMPONENTS})
        except (OSError, ValueError, KeyError, TypeError, UnicodeError, BadZipFile, ParseError) as exc:
            info.update(status='UNREADABLE', error_type=type(exc).__name__)
        files.append(info)
    return {'schema_version': 'gold_audit.v1', 'read_only': True,
            'scan_roots': [str(Path(x).resolve()) for x in roots], 'filename_markers': list(MARKERS),
            'scope_note': 'Filename-bounded scan, not proof that no unlabelled external gold exists. No annotation text copied into audit.',
            'approval_gate': 'existing is_gold + human_approval is True + non-AI annotator_ids; factual validation still required',
            'audit_code_sha256': sha(__file__),
            'files': files, 'components': {k: {'eligible_unique_cases': len(ids), 'status': 'CANDIDATES_REQUIRE_REVIEW' if ids else 'NOT_READY'} for k, ids in eligible_ids.items()},
            'approval_cohorts_unique_cases': {k: len(v) for k, v in approval_cohorts.items()},
            'paper_ready': False, 'gold_modified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots', type=Path, nargs='+', default=[Path('research'), Path('outputs')])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.roots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    print(json.dumps({'files': len(result['files']), 'components': result['components'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
