"""Table 9 readiness projection. Never substitutes other scores for Semantic F1.

Uses query-hash-bound, explicitly post-hoc condition annotations and the selected
run's public summary only. It does not read holdout material or run an evaluator.
"""
from __future__ import annotations

from research.marine_geollm_scie.evaluation.grounding_annotation_validation import validate_annotation_package

from collections import Counter
import hashlib
import json
from pathlib import Path
import re


CONDITIONS = (
    ('OFFICIAL_TERM', '공식 용어'),
    ('DOMAIN_KOREAN', '한국어 도메인 용어'),
    ('COLLOQUIAL', '구어체'),
    ('UNSEEN_SYNONYM', '미관측 동의어'),
    ('MIXED', '복합 요청'),
)
METADATA = Path('outputs/scie_rq_v2_audit_20261030/condition_metadata.jsonl')
METRIC_NAMES = {'semantic_f1', 'semantic_grounding_f1', 'strict_match', 'strict_match_rate', 'ci95'}


def _read(root: Path, relative: Path):
    path = (root / relative).resolve()
    receipt = {'path': relative.as_posix(), 'sha256': None, 'status': 'UNAVAILABLE'}
    if not path.is_relative_to(root) or not path.is_file():
        return None, receipt
    try:
        raw = path.read_bytes()
        receipt['sha256'] = hashlib.sha256(raw).hexdigest()
        text = raw.decode('utf-8-sig')
        value = ([json.loads(line) for line in text.splitlines() if line.strip()]
                 if path.suffix == '.jsonl' else json.loads(text))
        receipt['status'] = 'AVAILABLE'
        return value, receipt
    except (OSError, ValueError, UnicodeError):
        receipt['status'] = 'UNREADABLE'
        return None, receipt


def _metric_paths(value, prefix=''):
    result = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f'{prefix}.{key}' if prefix else key
            if key in METRIC_NAMES:
                result.append(path)
            result.extend(_metric_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.extend(_metric_paths(item, f'{prefix}[{index}]'))
    return result


def build_rq1_grounding(root, queries, selected_run_id):
    root = Path(root).resolve()
    annotations, metadata_receipt = _read(root, METADATA)
    annotations = annotations if isinstance(annotations, list) else []
    annotations = [x for x in annotations if isinstance(x, dict) and isinstance(x.get('case_id'), str)]
    annotation_counts = Counter(x.get('case_id') for x in annotations)
    annotation_by_id = {x.get('case_id'): x for x in annotations}
    valid_queries = [q for q in queries if isinstance(q, dict)
                     and isinstance(q.get('case_id'), str) and isinstance(q.get('query'), str)]
    query_counts = Counter(q['case_id'] for q in valid_queries)
    admitted, rejected = [], []
    for query in valid_queries:
        cid = query['case_id']
        annotation = annotation_by_id.get(cid)
        reason = None
        if query_counts[cid] != 1 or annotation_counts[cid] > 1:
            reason = 'DUPLICATE_CASE_ID'
        elif not annotation:
            reason = 'CONDITION_ANNOTATION_MISSING'
        elif annotation.get('query_sha256') != hashlib.sha256(query['query'].encode()).hexdigest():
            reason = 'QUERY_HASH_MISMATCH'
        if reason:
            rejected.append({'case_id': cid, 'reason': reason})
            continue
        labels = annotation.get('terminology_condition')
        labels = labels if isinstance(labels, list) else []
        complexity = annotation.get('complexity')
        complexity = complexity if isinstance(complexity, list) else []
        # UNSEEN is not inferable from language or wording. It requires a frozen
        # training/retrieval-dictionary exposure check, absent in this protocol.
        conditions = {label for label in labels if isinstance(label, str) and label in {'OFFICIAL_TERM', 'DOMAIN_KOREAN', 'COLLOQUIAL'}}
        if 'COMPOSITE_MULTI_TASK' in complexity:
            conditions.add('MIXED')
        admitted.append({'case_id': cid, 'conditions': conditions,
                         'cluster': query.get('equivalence_group') or None,
                         'annotation_status': annotation.get('annotation_status', 'UNKNOWN'),
                         'human_approval': annotation.get('human_approval') is True,
                         'post_hoc': annotation.get('post_hoc'),
                         'excluded_unseen_label': 'UNSEEN_SYNONYM' in labels})
    report = None
    report_receipt = {'path': None, 'sha256': None, 'status': 'INVALID_RUN_ID'}
    if isinstance(selected_run_id, str) and re.fullmatch(r'[A-Za-z0-9_-]+', selected_run_id):
        report, report_receipt = _read(root, Path('research/marine_geollm_scie/runs') /
                                     selected_run_id / 'report_with_faults/summary.json')
    fields = _metric_paths(report)
    rows = []
    for condition, label in CONDITIONS:
        matched = [q for q in admitted if condition in q['conditions']]
        reasons = ['선택 실행의 Semantic Grounding F1·Strict Match 평가계약과 대응 결과가 연결되지 않았습니다.']
        if not matched:
            reasons.append('이 조건의 검증된 문항 분류가 없습니다. 0점이 아닙니다.')
        if condition == 'UNSEEN_SYNONYM':
            reasons.append('훈련 자료·검색 사전의 동결 및 미노출 확인 근거가 없어 UNSEEN을 부여하지 않습니다.')
        rows.append(dict(condition=condition, label=label, n=len(matched),
                         case_ids=[q['case_id'] for q in matched],
                         cluster_count=len({q['cluster'] for q in matched if q['cluster']}),
                         missing_cluster_ids=sum(q['cluster'] is None for q in matched),
                         b1_semantic_f1=None, b2_semantic_f1=None, delta_b2_b1=None,
                         ci95=None, strict_match=None, measurement_status='NOT_MEASURED',
                         label_status='POST_HOC_DESCRIPTIVE_NOT_PRE_REGISTERED' if matched else 'NOT_ESTABLISHED',
                         annotation_statuses=dict(Counter(q['annotation_status'] for q in matched)),
                         label_human_approved_n=sum(q['human_approval'] for q in matched),
                         label_post_hoc_n=sum(q['post_hoc'] is True for q in matched),
                         missing_reasons=reasons,
                         ci_missing_reason='동일 문항의 B1/B2 Semantic F1 및 동등 질의군 단위 paired CI 계약이 없습니다.',
                         strict_interpretation='동일 GOLD의 필수 grounding 전체 일치를 평가해야 하며, 부분 F1·기계계약 통과로 대체하지 않습니다.'))
    return dict(table_id='TABLE_9', title='조건별 Semantic Grounding 비교', status='NOT_MEASURED',
                gold_atom_annotation=validate_annotation_package(root, valid_queries),
                selected_run_id=selected_run_id, methods={'B1': 'Text-RAG', 'B2': 'Ontology/KG'}, rows=rows,
                condition_metadata={**metadata_receipt, 'matched_queries': len(admitted),
                                    'rejected_queries': rejected,
                                    'post_hoc': True, 'human_approval': all(q['human_approval'] for q in admitted) if admitted else False,
                                    'annotation_approval_distinct_from_gold': True,
                                    'matched_queries_without_table_condition': [q['case_id'] for q in admitted if not q['conditions']],
                                    'unseen_labels_not_admitted': sum(q['excluded_unseen_label'] for q in admitted)},
                selected_report={**report_receipt, 'candidate_metric_fields': fields,
                                 'candidate_fields_are_not_validated_metric_contract': True},
                metric_contract={'status': 'NOT_DEFINED_FOR_SELECTED_RUN', 'requirements': [
                    '동일 GOLD의 grounding 단위·정규화·별칭·허용 매칭과 micro/macro F1 분모를 먼저 고정합니다.',
                    'B1/B2 동일 case_id·query/GOLD/raw hash로 실제 예측과 정답 집합을 대응합니다.',
                    'Strict Match의 필수 작업 전체 일치·미응답·실패·부분 응답 처리 기준을 고정합니다.',
                    'Δ는 같은 문항의 B2−B1이며, 95% CI는 동등 질의군을 묶은 paired cluster 방법·seed·반복·소표본 제한을 사전 고정합니다.',
                    'UNSEEN은 훈련/검색 사전 노출 확인으로 별도 승인하며, 개발 결과나 홀드아웃 정답에서 추론하지 않습니다.',
                ]},
                limitations=[
                    '기계계약 통과율, AI 보조 인간 확인 이진 정확도, Feature F1, 과거 pilot F1을 이 표의 Semantic F1로 대체하지 않습니다.',
                    '조건별 N은 관측 점수 분모가 아닌 query hash가 일치하는 사후 분류 문항 수입니다.',
                    '조건은 중첩될 수 있으므로 N을 합산하여 독립 문항 수로 해석하지 않습니다.',
                    'MIXED는 COMPOSITE_MULTI_TASK에서 파생한 복합 요청 조건이며 MIXED_KO_EN 언어 혼합과 다릅니다.',
                    'GOLD 승인과 사후 조건 라벨 승인은 별개입니다. 홀드아웃을 읽거나 평가를 실행하지 않습니다.',
                ])
