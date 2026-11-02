import copy
import io
import json
from pathlib import Path

import pytest

from research.marine_geollm_scie.runners import structured_review as sr
from research.marine_geollm_scie.runners import eight_method_runner as runner
from research.marine_geollm_scie.runners.eight_fault_recovery import clean_plan
from research.marine_geollm_scie.runners.matched_branches import freeze_initial, run_branches
from research.marine_geollm_scie.runners.review_consistency import inspect_review


def review(plan, invalid=False):
    return {'initial_checks': dict.fromkeys(sr.CHECK_FIELDS, 'pass'),
            'invalid': invalid, 'reason': 'synthetic observation', 'plan': plan}


def transport(monkeypatch, value):
    raw = json.dumps(value)
    requests = []
    def reply(req, timeout):
        requests.append(json.loads(req.data))
        return io.BytesIO(json.dumps({'response': raw, 'done': True, 'done_reason': 'stop',
                                    'prompt_eval_count': 1, 'eval_count': 1}).encode())
    monkeypatch.setattr(sr.urllib.request, 'urlopen', reply)
    return raw, requests


@pytest.mark.parametrize('field,value', [('radius_m', 5000), ('crs', 'EPSG:3857'),
    ('source', 'other'), ('feature_types', ['Obstruction']), ('filters', {'depth': 2}),
    ('reference_geometry', None)])
def test_false_verdict_cannot_silently_replace_execution_arguments(monkeypatch, field, value):
    initial = clean_plan()
    initial['tool_calls'][0]['arguments'][field] = value
    before = copy.deepcopy(initial)
    raw, calls = transport(monkeypatch, review(clean_plan()))
    call, parsed, errors = sr.call_review('request', {}, initial, model='fake', seed=42)
    assert parsed is None and errors == ['REVIEW_UNDECLARED_PLAN_CHANGE']
    assert call['raw_response'] == raw and call['review_usable'] is False
    receipt = call['review_consistency']
    assert receipt['raw_initial_invalid'] is False and receipt['verdict_corrected'] is False
    assert receipt['undeclared_plan_change'] is True and receipt['changed_contract_paths']
    assert initial == before and len(calls) == 1


def test_answer_only_and_json_numeric_format_changes_do_not_reject(monkeypatch):
    initial = clean_plan(); proposed = copy.deepcopy(initial)
    proposed['answer'] = 'wording only'
    proposed['radius_m'] = 1000.0
    proposed['tool_calls'][0]['arguments']['radius_m'] = 1000.0
    transport(monkeypatch, review(proposed))
    call, parsed, errors = sr.call_review('request', {}, initial, model='fake', seed=42)
    assert parsed is not None and not errors
    assert call['review_consistency']['changed_contract_paths'] == []
    assert call['review_consistency']['initial_contract_sha256'] == call['review_consistency']['proposed_contract_sha256']


def test_declared_invalid_repair_is_not_semantically_approved(monkeypatch):
    initial = clean_plan(); initial['tool_calls'][0]['arguments']['radius_m'] = -1000
    value = review(clean_plan(), True); value['initial_checks']['distance'] = 'fail'
    transport(monkeypatch, value)
    call, parsed, errors = sr.call_review('request', {}, initial, model='fake', seed=42)
    assert parsed == value and not errors
    assert call['review_consistency']['semantic_correctness_assessed'] is False
    assert call['review_consistency']['changed_contract_paths'] == ['/tool_calls/0/arguments/radius_m']


def test_failed_checks_keep_raw_false_even_when_schema_consistency_rejects(monkeypatch):
    value = review(clean_plan()); value['initial_checks']['target'] = 'fail'
    transport(monkeypatch, value)
    call, parsed, errors = sr.call_review('request', {}, clean_plan(), model='fake', seed=42)
    assert parsed is None and 'REVIEW_VERDICT_CONTRADICTION' in errors
    assert call['review_consistency']['raw_initial_invalid'] is False
    assert call['review_consistency']['raw_initial_checks']['target'] == 'fail'


@pytest.mark.parametrize('raw', [None, 'bad', '[]', '{"invalid":false,"plan":{"radius_m":NaN}}'])
def test_missing_or_nonfinite_cannot_become_false_or_positive_detection(raw):
    receipt = inspect_review(clean_plan(), raw)
    assert receipt['raw_initial_invalid'] is None
    assert receipt['undeclared_plan_change'] is None


def test_type_and_absent_field_changes_are_not_normalized_away():
    initial = clean_plan(); proposed = copy.deepcopy(initial)
    proposed['tool_calls'][0]['arguments']['radius_m'] = '1000'
    assert inspect_review(initial, json.dumps(review(proposed)))['undeclared_plan_change'] is True
    proposed = copy.deepcopy(initial); proposed['tool_calls'][0]['arguments']['new'] = None
    assert inspect_review(initial, json.dumps(review(proposed)))['changed_contract_paths'] == ['/tool_calls/0/arguments/new']


def test_shared_b4_h_contract_failure_never_invokes_reviewed_execution(tmp_path, monkeypatch):
    initial = clean_plan(); initial['tool_calls'][0]['arguments']['radius_m'] = -1000
    raw, requests = transport(monkeypatch, review(clean_plan()))
    frozen = tmp_path / 'initial.json'; artifact = tmp_path / 'review.json'; calls = []
    freeze_initial(frozen, case_id='synthetic', repeat=0, plan=initial, generation={})
    rows = run_branches(frozen, tmp_path / 'branches',
        reviewer=lambda p: runner.review_candidate(p, case={'query': 'request'},
            packet={'evidence_text': ''}, profile={}, model='fake', seed=42,
            artifact=artifact, calls=calls), validator=lambda q: q,
        executor=lambda p: {}, query='request')
    branches = [r for r in rows if r['method'] in ('B4', 'H')]
    assert len(requests) == 1 and len(branches) == 2
    assert all(r['status'] == 'REVIEW_ERROR' and not r['execution_callback_invoked'] for r in branches)
    receipt = json.loads(artifact.read_text())
    assert receipt['review'] is None and receipt['call']['raw_response'] == raw
    assert receipt['errors'] == ['REVIEW_UNDECLARED_PLAN_CHANGE']


def test_new_protocol_and_consistency_source_are_in_fresh_freeze():
    from research.marine_geollm_scie.runners.freeze_comparison_sources import execution_files
    root = Path(__file__).resolve().parents[3]
    protocol = root / 'research/marine_geollm_scie/protocol/structured_review_v3.json'
    data = json.loads(protocol.read_text(encoding='utf-8'))
    assert data['version'] == sr.REVIEW_VERSION and data['schema_sha256'] == sr.SCHEMA_SHA256
    assert data['schema'] == sr.REVIEW_SCHEMA and data['budget'] == sr.REVIEW_BUDGET
    paths = execution_files(root)
    assert protocol in paths
    assert root / 'research/marine_geollm_scie/runners/review_consistency.py' in paths
