"""Validate source-backed lexical interpretations against FC attribute constraints."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from services.orchestrator.reference_evaluation import make_unit
from services.orchestrator.marine_terminology import match_terminology

DATA=Path(__file__).resolve().parents[2]/'data'


def validate_mappings(document, catalogue):
    if document['fc_sha256']!=catalogue['metadata']['sha256']:
        raise ValueError('FC snapshot mismatch')
    units={u['unit_id']:u for u in document['units']}
    for u in units.values():
        expected=make_unit({'artifact_id':u['source_id'],'sha256':u['source_sha256'],'edition':u['edition']},u['locator'],u['text'])
        if expected['unit_id']!=u['unit_id'] or expected['text_sha256']!=u['text_sha256']:
            raise ValueError('Source identity mismatch')
    features={f['code']:f for f in catalogue['features']}
    attributes={a['code']:a for a in catalogue['attributes']}
    for m in document['mappings']:
        if not set(m['references'])<=units.keys(): raise ValueError('Missing source reference')
        if m['search_enabled'] and (not m['references'] or m['status']!='SOURCE_BACKED_SEARCH_SUBSET'):
            raise ValueError('Unqualified search mapping')
        if m['feature'] is None:
            if m['search_enabled']: raise ValueError('Missing Feature')
            continue
        feature=features.get(m['feature'])
        if not feature: raise ValueError('Unknown Feature')
        bindings={b['ref']:b for b in feature['bindings'] if b['kind']=='attributeBinding' and b['type']=='attribute'}
        for attr,values in m['filters'].items():
            if attr not in bindings or not values: raise ValueError('Attribute not bound to Feature')
            allowed=set(bindings[attr]['permitted_values']) or {v['value'] for v in attributes[attr]['listed_values']}
            if not set(values)<=allowed: raise ValueError('Invalid enumeration')
    return document


@lru_cache(maxsize=1)
def registry():
    raw=(DATA/'marine_s101_bindings.json').read_bytes()
    document=validate_mappings(json.loads(raw),json.loads((DATA/'s101_feature_catalogue_v2_parsed.json').read_text(encoding='utf-8')))
    return document,hashlib.sha256(raw).hexdigest()


def resolve_mappings(query, constraints=()):
    document,digest=registry()
    by_term={m['term']:m for m in document['mappings']}
    return [{**by_term[t['original_label']], 'raw_text':t['raw_text'], 'span':t['span'],
             'registry_sha256':digest,'fc_sha256':document['fc_sha256'],'human_gold':False}
            for t in match_terminology(query,constraints)['candidates']
            if t['original_label'] in by_term and not t['excluded'] and not t['quoted']]
