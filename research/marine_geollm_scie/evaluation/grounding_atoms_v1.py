"""Proposed atom-level grounding measurements; no model or GOLD synthesis.

This module scores only explicitly supplied atoms. A perfect atom score does not
assert full task semantics, spatial truth, independent review or publication
eligibility. Missing input is distinct from an observed empty prediction.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
import random
import re
import statistics


CONTRACT_VERSION = 'grounding_atoms.v1.proposed'
SCOPE = 'EXPLICIT_GROUNDING_ATOMS_ONLY_NOT_FULL_TASK_SEMANTICS'


def _string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value


def _json_value(value):
    """Typed exact JSON identity; no inference, aliases or unit repair."""
    def validate(item):
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            if not math.isfinite(item):
                raise ValueError('Nonfinite atom value')
            return
        if isinstance(item, list):
            for child in item:
                validate(child)
            return
        if isinstance(item, dict) and all(isinstance(k, str) for k in item):
            for child in item.values():
                validate(child)
            return
        raise ValueError('Atom values must be finite JSON with string object keys')
    validate(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _atoms(items, gold):
    if not isinstance(items, list):
        raise ValueError('Atoms must be an explicit list, or None when unobserved')
    id_key = 'atom_id' if gold else 'prediction_id'
    output = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Each atom must be an object')
        identity = _string(item.get(id_key), id_key)
        if identity in output:
            raise ValueError(f'Duplicate {id_key}')
        kind, task = _string(item.get('kind'), 'kind'), _string(item.get('task_id'), 'task_id')
        if gold:
            accepted = item.get('accepted_values')
            if not isinstance(accepted, list) or not accepted:
                raise ValueError('Each GOLD atom requires explicit nonempty accepted_values')
            values = {_json_value(value) for value in accepted}
        else:
            if 'value' not in item:
                raise ValueError('Prediction atom missing explicit value')
            values = {_json_value(item['value'])}
        output[identity] = (kind, task, values)
    return output


def score_atoms(gold_atoms, predicted_atoms):
    """Maximum one-to-one match, preserving repeated predictions as false positives.

    Atom schemas:
      GOLD: {atom_id, kind, task_id, accepted_values: [JSON, ...]}
      prediction: {prediction_id, kind, task_id, value: JSON}
    Accepted alternatives are provided by the caller's frozen contract. None is
    missing observation/GOLD; [] is an observed empty set. Empty/empty gives
    strict_atom_match=True but undefined F1 (zero denominator).
    """
    gold = _atoms(gold_atoms, True) if gold_atoms is not None else None
    predicted = _atoms(predicted_atoms, False) if predicted_atoms is not None else None
    base = dict(contract_version=CONTRACT_VERSION, scope=SCOPE, measured=False,
                tp=None, fp=None, fn=None, precision=None, recall=None, f1=None,
                strict_atom_match=None, matches=[], unmatched_gold=[], unmatched_predictions=[],
                expected_atoms=len(gold) if gold is not None else None,
                observed_atoms=len(predicted) if predicted is not None else None)
    if gold is None or predicted is None:
        base['status'] = 'NOT_MEASURED'
        base['missing_reasons'] = ([ 'GOLD_ATOMS_NOT_PROVIDED' ] if gold is None else []) + (
            [ 'PREDICTION_NOT_OBSERVED' ] if predicted is None else [])
        return base
    edges = {pid: [gid for gid in sorted(gold)
                   if predicted[pid][:2] == gold[gid][:2] and predicted[pid][2] & gold[gid][2]]
             for pid in sorted(predicted)}
    gold_to_prediction = {}

    def augment(pid, visited):
        for gid in edges[pid]:
            if gid in visited:
                continue
            visited.add(gid)
            owner = gold_to_prediction.get(gid)
            if owner is None or augment(owner, visited):
                gold_to_prediction[gid] = pid
                return True
        return False

    for pid in sorted(predicted):
        augment(pid, set())
    tp = len(gold_to_prediction)
    fp, fn = len(predicted)-tp, len(gold)-tp
    matched_predictions = set(gold_to_prediction.values())
    base.update(status='MEASURED_ATOM_COMPARISON', measured=True, tp=tp, fp=fp, fn=fn,
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                strict_atom_match=(fp == 0 and fn == 0),
                matches=[{'atom_id': gid, 'prediction_id': gold_to_prediction[gid]} for gid in sorted(gold_to_prediction)],
                unmatched_gold=sorted(set(gold)-gold_to_prediction.keys()),
                unmatched_predictions=sorted(set(predicted)-matched_predictions), missing_reasons=[])
    return base


def _quantile(values, probability):
    values = sorted(values)
    position = (len(values)-1)*probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return values[lower]+(values[upper]-values[lower])*(position-lower)


def _paired_rows(rows):
    index = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Paired observation must be an object')
        cid = _string(row.get('case_id'), 'case_id')
        group = _string(row.get('equivalence_group'), 'equivalence_group')
        repeat = row.get('repeat_id')
        if isinstance(repeat, bool) or not isinstance(repeat, (int, str)) or repeat == '':
            raise ValueError('Explicit integer/string repeat_id required')
        key = cid, _json_value(repeat)
        if key in index:
            raise ValueError('Duplicate case/repeat observation')
        hashes = tuple(row.get(k) for k in ('query_sha256', 'gold_sha256', 'contract_sha256'))
        if any(not isinstance(h, str) or re.fullmatch(r'[0-9a-f]{64}', h) is None for h in hashes):
            raise ValueError('Query, GOLD and contract SHA256 identities required')
        score = row.get('score')
        if not isinstance(score, dict) or type(score.get('measured')) is not bool:
            raise ValueError('Explicit score measurement state required')
        if score['measured']:
            if any(type(score.get(k)) is not int or score[k] < 0 for k in ('tp', 'fp', 'fn')):
                raise ValueError('Observed TP/FP/FN must be nonnegative integers')
            strict = score.get('strict_atom_match')
            if type(strict) is not bool or strict != (score['fp'] == 0 and score['fn'] == 0):
                raise ValueError('Strict atom verdict inconsistent with confusion counts')
        index[key] = (group, hashes, score)
    return index


def paired_cluster_bootstrap(a_rows, b_rows, *, samples=2000, seed=20261102):
    """Paired B−A micro-F1 CI, resampling equivalence groups with all their cases.

    Each record needs case_id, repeat_id, equivalence_group, query_sha256,
    gold_sha256, contract_sha256, and a score_atoms result. TP/FP/FN are averaged
    over repeats within each case, then summed before computing each micro F1.
    No missing pair/outcome is silently dropped. This is descriptive, not proof
    that the supplied GOLD was independently approved.
    """
    if type(samples) is not int or samples < 100 or type(seed) is not int:
        raise ValueError('Integer seed and at least 100 bootstrap samples required')
    a, b = _paired_rows(a_rows), _paired_rows(b_rows)
    if not a or a.keys() != b.keys():
        raise ValueError('Identical nonempty case/repeat cohorts required')
    if any(a[k][:2] != b[k][:2] for k in a):
        raise ValueError('Paired group/query/GOLD/contract identity mismatch')
    case_identity = {}
    for key, entry in a.items():
        previous = case_identity.setdefault(key[0], entry[:2])
        if previous != entry[:2]:
            raise ValueError('Case identity/group changed across repeats')
    result = dict(contract_version=CONTRACT_VERSION, status='NOT_MEASURED', scope=SCOPE,
                  cases=len(case_identity), clusters=len({v[0] for v in case_identity.values()}),
                  paired_observations=len(a), bootstrap_samples=samples, seed=seed,
                  a_micro_f1=None, b_micro_f1=None, difference_B_minus_A=None, ci95=None,
                  a_strict_rate=None, b_strict_rate=None, strict_difference_B_minus_A=None,
                  strict_ci95=None, missing_paired_outcomes=0,
                  resampling_unit='EQUIVALENCE_GROUP', repeat_policy='MEAN_COUNTS_WITHIN_CASE',
                  confidence_interpretation='DESCRIPTIVE_NOT_CONFIRMATORY')
    result['missing_paired_outcomes'] = sum(not (a[k][2]['measured'] and b[k][2]['measured']) for k in a)
    if result['missing_paired_outcomes']:
        result['reason'] = 'MISSING_PAIRED_OUTCOME_NOT_EXCLUDED'
        return result
    counts = defaultdict(lambda: [[], []])
    for key in sorted(a):
        for method, source in enumerate((a, b)):
            score = source[key][2]
            counts[key[0]][method].append(tuple(score[k] for k in ('tp', 'fp', 'fn'))+(int(score['strict_atom_match']),))
    case_vectors = {cid: tuple(tuple(statistics.mean(v[j] for v in method) for j in range(4))
                              for method in pair) for cid, pair in counts.items()}
    clusters = defaultdict(list)
    for cid in sorted(case_vectors):
        clusters[case_identity[cid][0]].append(case_vectors[cid])

    def aggregate(vectors):
        methods = []
        for method in (0, 1):
            tp, fp, fn = (sum(v[method][j] for v in vectors) for j in range(3))
            micro = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
            strict = statistics.mean(v[method][3] for v in vectors)
            methods.append((micro, strict))
        return methods

    point = aggregate(list(case_vectors.values()))
    result.update(a_micro_f1=point[0][0], b_micro_f1=point[1][0],
                  difference_B_minus_A=point[1][0]-point[0][0] if all(v[0] is not None for v in point) else None,
                  a_strict_rate=point[0][1], b_strict_rate=point[1][1],
                  strict_difference_B_minus_A=point[1][1]-point[0][1])
    if len(clusters) < 2:
        result.update(status='POINT_ONLY', reason='FEWER_THAN_TWO_EQUIVALENCE_GROUPS')
        return result
    rng = random.Random(seed)
    blocks = [clusters[key] for key in sorted(clusters)]
    differences, strict_differences = [], []
    zero_denominator = 0
    for _ in range(samples):
        selected = [vector for _ in blocks for vector in rng.choice(blocks)]
        outcomes = aggregate(selected)
        strict_differences.append(outcomes[1][1]-outcomes[0][1])
        if any(v[0] is None for v in outcomes):
            zero_denominator += 1
        else:
            differences.append(outcomes[1][0]-outcomes[0][0])
    result.update(status='DESCRIPTIVE_PILOT', zero_denominator_bootstrap_samples=zero_denominator,
                  strict_ci95=[_quantile(strict_differences, .025), _quantile(strict_differences, .975)],
                  limitation='Few independent groups; unstable CI' if len(clusters) < 10 else None)
    if zero_denominator:
        result.update(status='PARTIALLY_MEASURED', reason='ZERO_DENOMINATOR_SAMPLES_NOT_DISCARDED', ci95=None)
    else:
        result['ci95'] = [_quantile(differences, .025), _quantile(differences, .975)]
    return result
