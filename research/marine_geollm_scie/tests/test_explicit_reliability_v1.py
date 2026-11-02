import pytest

from research.marine_geollm_scie.evaluation.grounding_atoms_v1 import score_atoms, paired_cluster_bootstrap
from research.marine_geollm_scie.evaluation.execution_reliability_v1 import summarize_execution


def gold(identity, values):
    return dict(atom_id=identity, kind='feature', task_id='t', accepted_values=values)


def pred(identity, value):
    return dict(prediction_id=identity, kind='feature', task_id='t', value=value)


def pair(cid, score, group=None, repeat=1):
    return dict(case_id=cid, equivalence_group=group or cid, repeat_id=repeat,
                query_sha256='a'*64, gold_sha256='b'*64, contract_sha256='c'*64, score=score)


def obs(cid, e, s, eligible=True):
    return dict(case_id=cid, repeat_id=1, equivalence_group=cid, eligible=eligible,
                execution_success=e, spatial_correct=s)


def test_maximum_matching_not_greedy():
    result = score_atoms([gold('a', ['X', 'Y']), gold('b', ['X'])],
                         [pred('a', 'X'), pred('b', 'Y')])
    assert result['tp'] == 2 and result['f1'] == 1 and result['strict_atom_match']


def test_duplicate_predictions_are_false_positives():
    result = score_atoms([gold('a', ['X'])], [pred('a', 'X'), pred('b', 'X')])
    assert (result['tp'], result['fp'], result['fn']) == (1, 1, 0)


def test_missing_distinct_from_observed_empty():
    assert score_atoms(None, [])['f1'] is None
    assert not score_atoms([], None)['measured']
    assert score_atoms([gold('a', ['X'])], [])['f1'] == 0
    empty = score_atoms([], [])
    assert empty['strict_atom_match'] is True and empty['f1'] is None


@pytest.mark.parametrize('value', ['5000m', True, 1.0])
def test_no_unit_or_type_inference(value):
    assert score_atoms([gold('a', [1])], [pred('a', value)])['tp'] == 0


def test_task_identity_and_invalid_atoms():
    p = pred('a', 'X'); p['task_id'] = 'another'
    assert score_atoms([gold('a', ['X'])], [p])['tp'] == 0
    with pytest.raises(ValueError):
        score_atoms([], [pred('a', float('nan'))])
    with pytest.raises(ValueError):
        score_atoms([], [pred('a', 'X'), pred('a', 'X')])


def test_bootstrap_paired_seed_order_and_repeat_weight():
    yes = score_atoms([gold('a', ['X'])], [pred('a', 'X')])
    no = score_atoms([gold('a', ['X'])], [])
    a = [pair('a', no), pair('a', yes, repeat=2), pair('b', no)]
    b = [pair('a', yes), pair('a', yes, repeat=2), pair('b', yes)]
    r = paired_cluster_bootstrap(a, b, samples=100, seed=7)
    assert r == paired_cluster_bootstrap(a[::-1], b[::-1], samples=100, seed=7)
    assert r['a_micro_f1'] == pytest.approx(.4)
    assert r['difference_B_minus_A'] == pytest.approx(.6)
    assert r['cases'] == 2 and r['paired_observations'] == 3


def test_bootstrap_missing_and_identity_fail_closed():
    yes = score_atoms([gold('a', ['X'])], [pred('a', 'X')])
    a = [pair('a', yes), pair('b', yes)]
    b = [pair('a', yes), pair('b', score_atoms(None, []))]
    assert paired_cluster_bootstrap(a, b, samples=100)['ci95'] is None
    b[1] = pair('b', yes); b[1]['gold_sha256'] = 'd'*64
    with pytest.raises(ValueError):
        paired_cluster_bootstrap(a, b, samples=100)


def test_empty_denominator_draws_not_dropped():
    rows = [pair('a', score_atoms([], [])),
            pair('b', score_atoms([gold('a', ['X'])], []))]
    r = paired_cluster_bootstrap(rows, rows, samples=100)
    assert r['zero_denominator_bootstrap_samples'] > 0
    assert r['ci95'] is None and r['strict_ci95'] == [0, 0]


def test_rq3_conditional_not_gap():
    r = summarize_execution([obs('a', True, True), obs('b', True, False), obs('c', False, None)])
    assert r['ESR']['value'] == pytest.approx(2/3)
    assert r['SCR_joint']['value'] == pytest.approx(1/3)
    assert r['CGE']['value'] == .5 and r['SSFR']['value'] == .5
    assert r['execution_correctness_gap'] == pytest.approx(1/3)
    assert r['raw_spatial_correctness']['value'] is None


def test_unknown_membership_and_zero_success_not_zero_accuracy():
    r = summarize_execution([obs('a', True, True), obs('b', None, False)])
    assert r['ESR']['value'] is None and r['CGE']['value'] is None
    r = summarize_execution([obs('a', False, None)])
    assert r['SCR_joint']['value'] == 0
    assert r['SSFR']['value'] is None and r['CGE']['denominator'] == 0


def test_exclusions_and_invalid_observations():
    r = summarize_execution([obs('a', True, True), obs('b', None, None, False)])
    assert r['observations'] == 1 and r['excluded_observations'] == 1
    with pytest.raises(ValueError):
        summarize_execution([obs('a', 'false', None)])
    with pytest.raises(ValueError):
        summarize_execution([obs('a', True, True), obs('a', True, True)])
