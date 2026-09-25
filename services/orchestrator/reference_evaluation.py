"""Offline evidence contracts; never grants model or tool execution authority."""
import hashlib
import json
from pathlib import Path


def load_reference_index(path):
    path=Path(path)
    manifest=json.loads((path.parent/'manifest.json').read_text(encoding='utf-8'))
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['units_sha256']:
        raise ValueError('Reference index snapshot hash mismatch')
    return [json.loads(line) for line in raw.decode('utf-8').splitlines()]


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def make_unit(source, locator, text, canonical_ids=()):
    text_hash=digest(text)
    identifier=digest(json.dumps([source['sha256'],locator,text_hash],ensure_ascii=False,sort_keys=True))
    return {'unit_id':identifier,'source_id':source['artifact_id'],
            'source_sha256':source['sha256'],'edition':source['edition'],
            'locator':locator,'text':text,'text_sha256':text_hash,
            'canonical_ids':list(canonical_ids),
            'source_review_status':source.get('source_review_status','UNREVIEWED'),
            'current_law_status':source.get('current_law_status','NOT_VERIFIED'),
            'execution_authorized':False}


def validate_reference_gold(gold, units):
    indexed={u['unit_id']:u for u in units}
    if len(indexed)!=len(units):
        raise ValueError('Duplicate reference unit IDs')
    for unit in units:
        if digest(unit['text'])!=unit['text_sha256']:
            raise ValueError('Reference text hash mismatch')
        expected=make_unit({'artifact_id':unit['source_id'],'sha256':unit['source_sha256'],
                            'edition':unit['edition']},unit['locator'],unit['text'])
        if expected['unit_id']!=unit['unit_id']:
            raise ValueError('Reference locator/identity mismatch')
    for case in gold:
        if case.get('reference_review_status')!='HUMAN_VERIFIED':
            raise ValueError('Human reference review is required for maritime gold')
        bindings=case.get('reference_bindings')
        if not bindings:
            raise ValueError('Reference bindings are required for maritime gold')
        for binding in bindings:
            unit=indexed.get(binding.get('unit_id'))
            if not unit:
                raise ValueError('Unknown reference unit')
            if unit['source_review_status']=='GOLD_APPROVAL_BLOCKED':
                raise ValueError('Source edition is blocked for gold approval')
            if unit.get('extraction_flags'):
                raise ValueError('Reference extraction needs correction before gold approval')
            if any(binding.get(k)!=unit[k] for k in ('source_id','source_sha256','edition','text_sha256','locator')):
                raise ValueError('Reference binding does not match frozen source')
            quote=binding.get('quote')
            if not isinstance(quote,str) or not quote or quote not in unit['text']:
                raise ValueError('Reference quote is not present in the unit')
            if not binding.get('claim') or not binding.get('applicability') or not binding.get('reviewer_ids'):
                raise ValueError('Claim, applicability and reviewer attribution are required')
            if binding.get('review_status')!='HUMAN_VERIFIED':
                raise ValueError('Each reference binding needs human review')
            if binding.get('use_as_current_law') and unit['current_law_status']!='VERIFIED_CURRENT':
                raise ValueError('Current legal applicability is not verified')
    return {'cases':len(gold),'bindings':sum(len(g['reference_bindings']) for g in gold),
            'status':'SOURCE_CONTRACT_VALIDATED',
            'limitation':'Hash/quote checks cannot establish semantic correctness or reviewer identity.'}
