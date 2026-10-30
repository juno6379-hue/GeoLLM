import hashlib
import json

import pytest

from research.marine_geollm_scie.runners.export_annotation_review import export_review


def inputs(tmp_path):
    cases = tmp_path / 'cases.jsonl'
    cases.write_text(json.dumps({'case_id': 'q1', 'query': '질의', 'category': 'Q1',
                                 'equivalence_group': 'g1', 'expected_behavior': 'SECRET_EXPECTED',
                                 'annotation_status': 'GOLD'}) + '\n', encoding='utf-8')
    packets = tmp_path / 'packets.jsonl'
    rows = [{'case_id': 'q1', 'method': method, 'evidence': 'SOURCE_ONLY',
             'evidence_sha256': hashlib.sha256(b'SOURCE_ONLY').hexdigest(),
             'sources': [{'path': 'fc.json', 'sha256': 'a' * 64}],
             'model_answer': 'SECRET_MODEL', 'retrieval_trace': 'SECRET_RANKING'} for method in ('B1', 'B2')]
    packets.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    return cases, packets


def test_blinding_draft_and_separate_reviewers(tmp_path):
    cases, packets = inputs(tmp_path)
    out = tmp_path / 'export'
    result = export_review(cases, packets, out)
    assert result['gold_written'] is False
    for reviewer in ('reviewer_A', 'reviewer_B'):
        text = (out / reviewer / 'annotations_DRAFT.jsonl').read_text(encoding='utf-8')
        assert 'SECRET_' not in text
        row = json.loads(text)
        assert row['annotation_status'] == 'DRAFT'
        assert row['annotator_id'] is None and row['semantics'] is None
        assert row['expected_execution_behavior'] is None
        assert row['split_eligibility'] == 'PILOT_EXPOSED_NOT_HOLDOUT'
        assert len(row['source_materials']) == 2
        assert row['provenance']['benchmark_sha256'] == hashlib.sha256(cases.read_bytes()).hexdigest()
    assert json.loads((out / 'adjudication_DRAFT.jsonl').read_text(encoding='utf-8'))['resolution'] is None


def test_refuses_existing_export(tmp_path):
    cases, packets = inputs(tmp_path)
    out = tmp_path / 'export'
    export_review(cases, packets, out)
    with pytest.raises(FileExistsError): export_review(cases, packets, out)


def test_detects_changed_material_before_writing(tmp_path):
    cases, packets = inputs(tmp_path)
    packets.write_text(packets.read_text().replace('SOURCE_ONLY', 'CHANGED'), encoding='utf-8')
    with pytest.raises(ValueError, match='hash mismatch'): export_review(cases, packets, tmp_path / 'export')
    assert not (tmp_path / 'export').exists()


def test_missing_pair_not_silently_empty(tmp_path):
    cases, packets = inputs(tmp_path)
    packets.write_text(packets.read_text().splitlines()[0] + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Missing'): export_review(cases, packets, tmp_path / 'export')
