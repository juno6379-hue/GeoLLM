"""Research review-envelope consistency, not semantic error detection.

Never turn a model's false/unknown verdict into a positive detection. Changes to
the proposed execution contract need an explicit initial-invalid model verdict.
"""
import hashlib
import json

VERSION = 'review_initial_plan_consistency_v1'


def _normal(value):
    # JSON numbers 1000 and 1000.0 have the same numeric value. Do not coerce
    # strings, booleans, units, CRS, aliases or absent fields.
    if type(value) is float and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _normal(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normal(v) for v in value]
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _paths(before, after, path=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            pointer = path + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in before or key not in after:
                result.append(pointer)
            else:
                result.extend(_paths(before[key], after[key], pointer))
        return result
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return [path]
        return [p for i, (a, b) in enumerate(zip(before, after))
                for p in _paths(a, b, path + '/' + str(i))]
    return [] if _json(before) == _json(after) else [path]


def inspect_review(initial_plan, raw_response):
    """Return a receipt even when schema/transport later rejects the response.

    Only ``answer`` is presentation text. Every other explicit plan field,
    including arguments, evidence bindings and missing inputs, is contract data.
    Array order is retained; no semantic equivalence is guessed.
    """
    receipt = {'version': VERSION, 'initial_plan_sha256': _hash(initial_plan),
               'raw_response_sha256': hashlib.sha256(raw_response.encode()).hexdigest()
                   if isinstance(raw_response, str) else None,
               'raw_initial_invalid': None, 'raw_initial_checks': None,
               'proposed_plan_sha256': None, 'changed_contract_paths': None,
               'undeclared_plan_change': None, 'semantic_correctness_assessed': False,
               'verdict_corrected': False}
    try:
        value = json.loads(raw_response)
        _json(value)  # Non-finite output is not admissible evidence.
    except (ValueError, TypeError, RecursionError):
        return receipt
    if not isinstance(value, dict):
        return receipt
    if type(value.get('invalid')) is bool:
        receipt['raw_initial_invalid'] = value['invalid']
    if isinstance(value.get('initial_checks'), dict):
        receipt['raw_initial_checks'] = value['initial_checks']
    proposed = value.get('plan')
    if not isinstance(initial_plan, dict) or not isinstance(proposed, dict):
        return receipt
    receipt['proposed_plan_sha256'] = _hash(proposed)
    original_contract = _normal({k: v for k, v in initial_plan.items() if k != 'answer'})
    proposed_contract = _normal({k: v for k, v in proposed.items() if k != 'answer'})
    changes = _paths(original_contract, proposed_contract)
    receipt.update(initial_contract_sha256=_hash(original_contract),
                   proposed_contract_sha256=_hash(proposed_contract),
                   changed_contract_paths=changes,
                   undeclared_plan_change=bool(changes) if value.get('invalid') is False else False)
    return receipt
