"""Independent contract-boundary checks; synthetic inputs, no model calls."""
import copy
import json

import pytest

from research.marine_geollm_scie.runners.review_consistency import inspect_review
from research.marine_geollm_scie.runners.eight_fault_recovery import clean_plan
from research.marine_geollm_scie.evaluation.v2_fault_results import metrics


@pytest.mark.parametrize('change', ['remove_call', 'duplicate_call', 'change_evidence',
                                    'remove_reference', 'bool_distance', 'action'])
def test_executable_change_never_becomes_positive_llm_detection(change):
    before = clean_plan()
    after = copy.deepcopy(before)
    if change == 'remove_call':
        after['tool_calls'] = []
    elif change == 'duplicate_call':
        after['tool_calls'].append(copy.deepcopy(after['tool_calls'][0]))
    elif change == 'change_evidence':
        after['evidence_refs'] = ['invented_ref']
    elif change == 'remove_reference':
        del after['tool_calls'][0]['arguments']['reference_geometry']
    elif change == 'bool_distance':
        after['tool_calls'][0]['arguments']['radius_m'] = True
    else:
        after['action'] = 'clarify'
    receipt = inspect_review(before, json.dumps({'invalid': False, 'plan': after}))
    assert receipt['undeclared_plan_change'] is True
    assert receipt['raw_initial_invalid'] is False
    assert receipt['verdict_corrected'] is False
    assert receipt['semantic_correctness_assessed'] is False
    assert receipt['initial_contract_sha256'] != receipt['proposed_contract_sha256']


def test_rejected_predictions_keep_all_faults_in_denominator():
    rows = [dict(expected_invalid=True, predicted_invalid=False) for _ in range(5)]
    rows += [dict(expected_invalid=True, predicted_invalid=None,
                  raw_review_invalid=False, review_usable=False) for _ in range(3)]
    result = metrics(rows)
    assert result['rows'] == 8
    assert result['missing_predictions'] == 3
    assert result['false_ready'] == dict(value=None, denominator=8, measured=5, missing=3)
    assert result['confusion'] == {'FN': 5}


def test_unchanged_invalid_plan_is_not_implicitly_semantically_checked():
    plan = clean_plan()
    plan['tool_calls'][0]['arguments']['radius_m'] = -1000
    receipt = inspect_review(plan, json.dumps({'invalid': False, 'plan': plan}))
    assert receipt['undeclared_plan_change'] is False
    assert receipt['raw_initial_invalid'] is False
    assert receipt['semantic_correctness_assessed'] is False
