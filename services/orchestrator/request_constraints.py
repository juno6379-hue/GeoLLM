"""Read-only checks against explicit request inputs, never plan repair.

Only unambiguous literal constraints are checked. This is not a general natural
language equivalence oracle. A caller may supply an immutable snapshot of the
original request; plan/provenance claims are never trusted as request evidence.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re

import yaml

from services.orchestrator.slot_evidence import radius_quantities

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RequestConstraints:
    query: str
    context_json: str


def capture_request_constraints(query, spatial_context=None):
    """Call at the request boundary, never with a model's proposed plan/slots."""
    if not isinstance(query, str):
        raise TypeError('Original request query must be text')
    context = spatial_context or {}
    if hasattr(context, 'model_dump'):
        context = context.model_dump(mode='json')
    if not isinstance(context, dict):
        raise TypeError('Original request context must be an object')
    return RequestConstraints(query, json.dumps(context, ensure_ascii=False, sort_keys=True, allow_nan=False))


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _crs(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'\s*EPSG\s*:\s*(\d+)\s*', value, re.I)
    return 'EPSG:' + str(int(match[1])) if match else value.strip()


@lru_cache(maxsize=1)
def _feature_literals():
    path = ROOT / 'data/s101_feature_dictionary.yaml'
    raw = path.read_bytes()
    entries = (yaml.safe_load(raw) or {}).get('s101_features') or {}
    names = {name for entry in entries.values() for name in entry.get('feature_candidates', [])}
    # Only unambiguous dictionary aliases; multi-candidate terms need resolution.
    aliases = {alias: entry['feature_candidates'][0] for alias, entry in entries.items()
               if len(entry.get('feature_candidates', [])) == 1}
    aliases.update({name: name for name in names})
    return aliases, hashlib.sha256(raw).hexdigest()


def _query_features(query):
    aliases, digest = _feature_literals()
    # Do not collapse exclusions, generic category expansion, alternatives, or
    # source-attribute mappings into an exact target set. Their own gates apply.
    if re.search(r'제외|빼고|\b(?:except|exclude|excluding|without|or)\b|또는|위험\s*객체|항행위험|\bhazards?\b', query, re.I):
        return None, digest
    found = set()
    for alias, canonical in aliases.items():
        for match in re.finditer(r'(?<![A-Za-z0-9가-힣])' + re.escape(alias) +
                                 r'(?:s(?=$|[^A-Za-z]))?(?=$|[^A-Za-z0-9가-힣]|[를을의은는와과이]|에서|만)', query, re.I):
            before, after = query[max(0, match.start()-25):match.start()], query[match.end():match.end()+12]
            if (re.search(r'\b(?:near|around|from|at)\s+(?:the\s+)?$', before, re.I)
                    or re.match(r'\s*(?:주변|부근|근처|기준)', after)):
                continue  # Reference object mention is not a requested target.
            found.add(canonical)
    return found or None, digest


def _request_radius_quantities(query):
    """Only explicit spatial-distance scopes, never a generic length value."""
    selected = []
    for item in radius_quantities(query):
        start, end = item['span']
        before, after = query[max(0, start-32):start], query[end:end+20]
        if (re.search(r'(?:\b(?:depth|draft|draught|height|length|width|altitude)|수심|흘수|높이|길이|폭|고도)\s*(?:of\s*)?$', before, re.I)
                or re.match(r'\s*(?:deep|tall|high|wide|long)\b', after, re.I)):
            continue
        if (item['quantity_role'] == 'radius'
                or re.search(r'(?:\b(?:within|radius|buffer|distance)(?:\s+of)?|반경|주변|부근|근처|인근|거리)\s*$', before, re.I)
                or re.match(r'\s*(?:이내|반경|\b(?:radius|buffer)\b)', after, re.I)):
            selected.append(item)
    return selected


def check_request_constraints(qec, trusted=None):
    """Return violations and a hash-bound receipt; never write semantic slots."""
    blockers, warnings, checks = [], [], {}
    source = 'original_query_only'
    if trusted is not None and not isinstance(trusted, RequestConstraints):
        return ['BLOCKED_CONFIG: UNTRUSTED_REQUEST_CONSTRAINTS'], [], {'status': 'REJECTED', 'source': 'invalid_caller_object'}
    if trusted is None:
        trusted = capture_request_constraints(qec.original_query or '')
    else:
        source = 'caller_captured_original_request'
    if trusted.query != (qec.original_query or ''):
        blockers.append('BLOCKED_CONFIG: REQUEST_QUERY_MISMATCH')
    query = trusted.query
    context = json.loads(trusted.context_json)
    slots = qec.slots
    query_crs = {_crs(m[0]) for m in re.finditer(r'(?<![A-Za-z0-9])EPSG\s*:\s*\d+(?![A-Za-z0-9])', query, re.I)}
    expected_crs = next(iter(query_crs)) if len(query_crs) == 1 else None
    if not query_crs and context.get('crs') is not None:
        expected_crs = _crs(context['crs'])
    if expected_crs is not None:
        checks['crs'] = {'expected': expected_crs, 'actual': slots.crs,
                         'source': 'query' if query_crs else 'request_context'}
        if _crs(slots.crs) != expected_crs:
            blockers.append('BLOCKED_CONFIG: REQUEST_CRS_MISMATCH')
    if query_crs and context.get('crs') is not None and _crs(context['crs']) not in query_crs:
        blockers.append('NEEDS_USER_INPUT: REQUEST_CRS_CONFLICT')

    quantities = _request_radius_quantities(query)
    distances = {item['normalized_value'] for item in quantities if item['validation_status'] == 'GROUNDED'}
    expected_distance = next(iter(distances)) if len(distances) == 1 else None
    if not quantities and type(context.get('buffer_distance')) in (int, float):
        value = context['buffer_distance']
        if math.isfinite(value) and value > 0:
            expected_distance = value
    if expected_distance is not None:
        checks['distance_m'] = {'expected': expected_distance, 'actual': slots.distance_m,
                               'source': 'query' if quantities else 'request_context'}
        if slots.distance_m is None or not math.isclose(slots.distance_m, expected_distance, rel_tol=1e-12, abs_tol=1e-9):
            blockers.append('BLOCKED_CONFIG: REQUEST_DISTANCE_MISMATCH')
    elif len(distances) > 1:
        warnings.append('Multiple explicit request distances: per-subtask distance preservation is not measured')

    requested, registry_hash = _query_features(query)
    explicit_context_targets = context.get('target_features')
    if requested is None and isinstance(explicit_context_targets, list) and explicit_context_targets and all(isinstance(x, str) for x in explicit_context_targets):
        requested = set(explicit_context_targets)
    # Feature and layer identifiers are different namespaces. Do not guess a
    # layer-to-feature mapping. Missing targets remain subject to native gates.
    actual_targets = set(slots.target_features) | set(slots.resolved_target_set)
    if requested is not None and actual_targets:
        unexpected = actual_targets - requested
        checks['target_features'] = {'allowed': sorted(requested), 'actual': sorted(actual_targets),
                                     'unexpected': sorted(unexpected), 'comparison': 'subtask_subset'}
        if unexpected:
            blockers.append('BLOCKED_CONFIG: REQUEST_TARGET_MISMATCH')
    receipt = {'version': 'explicit_request_constraints_v1', 'source': source,
               'request_sha256': _hash({'query': trusted.query, 'context': context}),
               'feature_registry_sha256': registry_hash, 'checks': checks,
               'status': 'REJECTED' if blockers else 'CHECKED' if checks else 'NOT_MEASURED',
               'limitations': ['literal_unambiguous_constraints_only', 'subtask_union_completeness_not_measured',
                              'request_context_unavailable' if source == 'original_query_only' else 'caller_owns_request_boundary'],
               'semantic_repair_performed': False}
    return blockers, warnings, receipt
