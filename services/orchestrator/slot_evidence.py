"""Original-text evidence and dimensional validation; never infer absent values."""
from __future__ import annotations

import hashlib
import math
import re
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

QUANTITY = re.compile(r'(?<![0-9A-Za-z.,+-])(?P<value>[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+))\s*(?P<unit>킬로미터|킬로|㎞|미터|개월|해리|km|nm|m|일|주|달|년)(?![A-Za-z])', re.I)
DISTANCE = {'km': Decimal(1000), '킬로미터': Decimal(1000), '킬로': Decimal(1000), '㎞': Decimal(1000), 'm': Decimal(1), '미터': Decimal(1), 'nm': Decimal(1852), '해리': Decimal(1852)}
DURATION = {'일': 'D', '주': 'W', '개월': 'M', '달': 'M', '년': 'Y'}


class SlotEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    slot_type: Literal['distance', 'duration', 'location', 'target', 'version', 'date']
    raw_text: str = Field(min_length=1)
    span: tuple[StrictInt, StrictInt] | None = None
    normalized_value: Any = None
    unit: str | None = None
    source_kind: Literal['query', 'conversation', 'map', 'registry', 'derived', 'default_policy'] = 'query'
    source_ref: str | None = None


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode('utf-8')).hexdigest()


def quantity_value(raw: str, kind: str) -> tuple[Any, str]:
    match = QUANTITY.fullmatch(raw)
    if not match:
        raise ValueError('EXPLICIT_UNIT_REQUIRED')
    number, unit = Decimal(match['value'].replace(',', '')), match['unit'].lower()
    if number <= 0:
        raise ValueError('NON_POSITIVE_QUANTITY')
    if kind == 'distance' and unit in DISTANCE:
        return float(number * DISTANCE[unit]), 'm'
    if kind == 'duration' and unit in DURATION:
        if number != number.to_integral_value():
            raise ValueError('FRACTIONAL_CALENDAR_DURATION_UNSUPPORTED')
        return f'P{int(number)}{DURATION[unit]}', 'iso8601_duration'
    raise ValueError('UNIT_DIMENSION_MISMATCH')


def validate_slot(query: str, proposal: SlotEvidence | dict, *, sources: dict | None = None) -> dict:
    """Non-query evidence requires exact equality with a caller-verified source.

    The caller, not the model, constructs sources. A source ID alone is not proof.
    Successful validation establishes grounding/type only, not world truth.
    """
    slot = SlotEvidence.model_validate(proposal)
    errors = []
    if slot.source_kind == 'query':
        span = slot.span
        if span is None or not (0 <= span[0] < span[1] <= len(query)) or query[span[0]:span[1]] != slot.raw_text:
            errors.append('SOURCE_SPAN_MISMATCH')
        if slot.source_ref not in (None, query_hash(query)):
            errors.append('SOURCE_QUERY_MISMATCH')
    else:
        reference = (sources or {}).get(slot.source_ref)
        expected = slot.model_dump(exclude={'source_ref', 'span'})
        if not reference or reference != expected:
            errors.append('UNVERIFIED_CONTEXT_SOURCE')
    value, unit = slot.normalized_value, slot.unit
    if slot.slot_type in {'distance', 'duration'}:
        try:
            value, unit = quantity_value(slot.raw_text, slot.slot_type)
            if slot.normalized_value is not None and (isinstance(slot.normalized_value, bool) or slot.normalized_value != value):
                errors.append('NORMALIZED_VALUE_MISMATCH')
            if slot.unit is not None and slot.unit != unit:
                errors.append('NORMALIZED_UNIT_MISMATCH')
        except ValueError as exc:
            errors.append(str(exc))
    elif slot.source_kind == 'query' and slot.normalized_value not in (None, slot.raw_text):
        errors.append('NORMALIZATION_REQUIRES_VERIFIED_DERIVATION')
    return {**slot.model_dump(mode='json'), 'normalized_value': value, 'unit': unit,
            'validation_status': 'REJECTED' if errors else 'GROUNDED', 'reason_codes': errors,
            'semantic_review_required': slot.slot_type not in {'distance', 'duration'},
            'index_unit': 'unicode_code_point', 'query_sha256': query_hash(query)}


def extract_quantities(query: str) -> list[dict]:
    slots = []
    for match in QUANTITY.finditer(query):
        kind = 'distance' if match['unit'].lower() in DISTANCE else 'duration'
        if match['unit'] == '년' and re.fullmatch(r'\d{4}', match['value']):
            kind = 'date'
        item = validate_slot(query, {'slot_type': kind, 'raw_text': match[0], 'span': match.span()})
        before, after = query[max(0, match.start()-8):match.start()], query[match.end():match.end()+8]
        item['quantity_role'] = ('radius' if kind == 'distance' and
                                 (re.search(r'반경\s*$', before) or re.match(r'\s*(?:이내|반경)', after))
                                 else 'duration' if kind == 'duration' else 'calendar_year' if kind == 'date' else 'length_unspecified')
        slots.append(item)
    return slots


def radius_quantities(query: str) -> list[dict]:
    """Prefer explicit radius scopes and exclude depth/draft/height dimensions."""
    distances = [s for s in extract_quantities(query) if s['slot_type'] == 'distance']
    scoped = [s for s in distances if s['quantity_role'] == 'radius']
    return scoped or [s for s in distances if not re.search(r'(?:수심|흘수|높이|고도)\s*$', query[max(0,s['span'][0]-8):s['span'][0]])]


def distance_m(query: str) -> float | None:
    """One unambiguous distance; preserves negative values for legacy error gates."""
    candidates = radius_quantities(query)
    if len(candidates) != 1:
        return None
    slot = candidates[0]
    if slot['validation_status'] == 'GROUNDED':
        return slot['normalized_value']
    if slot['reason_codes'] == ['NON_POSITIVE_QUANTITY']:
        match = QUANTITY.fullmatch(slot['raw_text'])
        return float(Decimal(match['value'].replace(',', '')) * DISTANCE[match['unit'].lower()])
    return None


def ground_distance_payload(query: str, payload: dict, context: dict | None = None) -> dict:
    """A parser/model number is not evidence; accept original quantity or explicit map input."""
    result = dict(payload)
    proposed = result.pop('distance_m', None)
    result.pop('distance_evidence', None)
    value = distance_m(query)
    if value is not None and value > 0 and math.isfinite(value):
        matches = [s for s in extract_quantities(query) if s['slot_type']=='distance'
                   and s['validation_status']=='GROUNDED' and s['normalized_value']==value]
        scoped = [s for s in matches if s['quantity_role']=='radius']
        result['distance_m'] = value
        result['distance_evidence'] = (scoped or matches)[0]
    elif not any(s['slot_type']=='distance' for s in extract_quantities(query)):
        raw = (context or {}).get('buffer_distance')
        try:
            supplied = float(raw) if raw is not None and not isinstance(raw,bool) else None
        except (TypeError,ValueError):
            supplied = None
        if supplied is not None and math.isfinite(supplied) and supplied > 0:
            result['distance_m'] = supplied
            result['distance_evidence'] = {'source_kind':'map','source_ref':'request.spatial_context.buffer_distance',
                                           'raw_value':raw,'normalized_value':supplied,'unit':'m',
                                           'validation_status':'EXPLICIT_REQUEST_INPUT','runtime_limits_required':True}
    if proposed is not None and proposed != result.get('distance_m'):
        result['rejected_distance_proposal'] = {'value':proposed,'reason':'NO_MATCHING_SOURCE_EVIDENCE'}
    return result
