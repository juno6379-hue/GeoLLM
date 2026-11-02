"""Source-bound AI prediction annotation preparation, with no GOLD access.

This intentionally does not score partial candidate extraction as Semantic F1.
Every candidate keeps its raw witness; unresolved task/claim reviews block export.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

VERSION = 'rq1_prediction_extraction.v1.review_draft'
POLICY = {
    'version': VERSION,
    'authority': 'AI_MEASUREMENT_ANNOTATION_NOT_INDEPENDENT_HUMAN_REVIEW',
    'inputs': 'RAW_MODEL_RESPONSE_ONLY; QUERY_FOR_TASK_LABELS_NOT_ANSWER_VALUES',
    'channels': 'STRUCTURED_AND_NARRATIVE_UNION; NO_CHANNEL_AUTOMATICALLY_WINS',
    'wrong_field': 'PRESERVE_DECLARED_KIND; ATTRIBUTE_IN_FEATURE_IS_NOT_REPAIRED',
    'conflicts': 'KEEP_ALL_CONFLICTING_ASSERTIONS; NEVER_SELECT_GOLD_MATCH',
    'duplicates': 'MERGE_ONLY_EXPLICIT_SAME_ASSERTION_WITNESSES; SEPARATE_ASSERTIONS_REMAIN_FP',
    'composites': 'REQUIRE_EXPLICIT_TASK_BINDING; DO_NOT_BROADCAST_FLAT_FIELDS',
    'invalid_schema': 'RETAIN_VALID_JSON_FIELDS_AND_TEXT; DO_NOT_DROP_CASE',
    'malformed_json': 'NO_REPAIR; RAW_TEXT_REVIEW_REQUIRED; NO_AUTOMATIC_EMPTY_ATOMS',
    'unknown_values': 'KEEP_LITERAL_AS_CANDIDATE_FP; NO_SPELLING_OR_FEATURE_CORRECTION',
    'source_binding': 'SOURCE_MENTION_NOT_BINDING; OWNER_SOURCE_LOCATOR_MUST_BE_EXPLICIT',
    'scope': 'GROUNDING_ATOMS_ONLY; OTHER_CLAIMS_PRESERVED_IN_SIDECAR',
}
CONTRACT_SHA256 = hashlib.sha256(json.dumps(POLICY,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pointer(document, value):
    if not isinstance(value,str) or not value.startswith('/'):
        raise ValueError('INVALID_JSON_POINTER')
    for part in value[1:].split('/'):
        part=part.replace('~1','/').replace('~0','~')
        document=document[int(part)] if isinstance(document,list) else document[part]
    return document


def exact_json(a,b):
    return json.dumps(a,sort_keys=True,ensure_ascii=False,allow_nan=False)==json.dumps(b,sort_keys=True,ensure_ascii=False,allow_nan=False)


def canonical_candidate(kind,value,feature_codes=()):
    """Lossless conversions only. Returns (kind,value,rule) or None for review."""
    if kind=='feature':
        # Only case/word-spacing changes matching a unique FC code. Unknown
        # code, attribute-as-feature, or broader object labels stay unchanged.
        normalized=re.sub(r'\s+','',str(value)).casefold()
        matches=[code for code in feature_codes if code.casefold()==normalized]
        return ('feature',matches[0],'EXACT_FC_CASE_SPACE') if len(matches)==1 else ('feature',value,'PRESERVED_LITERAL')
    if kind in {'operator','reference','reference_crs','standard'}:
        if kind=='operator' and value in (None,'none','NONE',''):
            return None
        if kind=='reference_crs' and value in ('EPSG:4326',4326,'4326'):
            return kind,'EPSG:4326','EXPLICIT_CRS_IDENTIFIER'
        if kind=='standard' and isinstance(value,str) and re.fullmatch(r'S-?101',value,re.I):
            return kind,'S-101','EXPLICIT_STANDARD_IDENTIFIER'
        return kind,value,'PRESERVED_LITERAL'
    if kind in {'distance_m','distance_mention'}:
        try:
            if kind=='distance_m':
                if type(value) not in (int,float):return None
                number=Decimal(str(value))
            else:
                match=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(km|kilometers?|kilometres?|m|meters?|metres?)\s*',str(value),re.I)
                if not match:return None
                number=Decimal(match[1])*(1000 if match[2].casefold().startswith(('kilo','km')) else 1)
            if number.is_finite() and number==number.to_integral_value():
                return 'distance_m',int(number),'EXACT_EXPLICIT_METRES'
        except (InvalidOperation,ValueError):pass
    return None


def prepare_annotation(preannotation,raw_bytes,*,feature_codes=()):
    """Verify every old witness and prepare candidates, never complete a review."""
    if sha(raw_bytes)!=preannotation['raw_sha256']:
        raise ValueError('RAW_HASH_MISMATCH')
    raw=json.loads(raw_bytes)
    if sha(preannotation['query'].encode())!=preannotation['query_sha256']:
        raise ValueError('QUERY_HASH_MISMATCH')
    units=[]
    for channel,key in [('structured','structured_field_observations'),('narrative','answer_span_preannotations')]:
        for index,item in enumerate(preannotation.get(key,[])):
            value=item.get('value') if channel=='structured' else item['literal_value']
            actual=pointer(raw,item['json_pointer'])
            if channel=='structured':
                if not exact_json(actual,value):raise ValueError('FIELD_WITNESS_MISMATCH')
            else:
                if not isinstance(actual,str) or not item.get('spans'):raise ValueError('TEXT_WITNESS_REQUIRED')
                for bounds in item['spans']:
                    if (not isinstance(bounds,list) or len(bounds)!=2 or any(type(x) is not int for x in bounds)
                            or not 0<=bounds[0]<bounds[1]<=len(actual) or actual[bounds[0]:bounds[1]]!=value):
                        raise ValueError('SPAN_WITNESS_MISMATCH')
            candidate=canonical_candidate(item['kind'],value,feature_codes)
            unit={'unit_id':f'{channel}:{index}','channel':channel,'original_kind':item['kind'],
                  'literal_value':value,'json_pointer':item['json_pointer'],'spans':item.get('spans'),
                  'candidate':({'kind':candidate[0],'value':candidate[1],'normalization_rule':candidate[2]}
                               if candidate else None),
                  'task_id':None,'task_review':'REQUIRED_NO_QUERY_BROADCAST',
                  'assertion_review':'REQUIRED_POLARITY_CONFLICT_DUPLICATE_AND_FP',
                  'author_type':'AI_MEASUREMENT_PREANNOTATION'}
            units.append(unit)
    failures=[]
    if not preannotation.get('plan_observed'):failures.append('MALFORMED_JSON_RAW_RESPONSE_REVIEW_REQUIRED')
    if preannotation.get('raw_status')=='INVALID_RESPONSE':failures.append('MODEL_SCHEMA_FAILURE_RETAINED')
    return {key:preannotation[key] for key in ('case_id','method','query','query_sha256','raw_path','raw_sha256','raw_status')} | {
        'contract_version':VERSION,'contract_sha256':CONTRACT_SHA256,'author_type':'AI_MEASUREMENT_PREANNOTATION',
        'human_review_complete':False,'gold_read':False,'holdout_read':False,
        'units':units,'prediction_atoms':None,'complete_grounding_extraction':False,
        'measurement_status':'NOT_MEASURED','retained_failures':failures,
        'missing_reviews':['FULL_NARRATIVE_ASSERTION_COVERAGE','TASK_BINDING','CONFLICT_AND_DUPLICATE_ADJUDICATION',
                           'ATTRIBUTE_OWNER_AND_SOURCE_BINDING','ADDITIONAL_FP_CLAIMS']}


def validate_complete_annotation(record):
    """Fail closed before handing a reviewed prediction set to score_atoms."""
    if record.get('contract_sha256')!=CONTRACT_SHA256:raise ValueError('CONTRACT_MISMATCH')
    if record.get('author_type')!='AI_MEASUREMENT_PREANNOTATION' or record.get('human_review_complete') is not False:
        raise ValueError('ANNOTATION_AUTHORITY_MISREPRESENTED')
    if record.get('missing_reviews') or record.get('complete_grounding_extraction') is not True:
        raise ValueError('EXTRACTION_INCOMPLETE')
    atoms=record.get('prediction_atoms')
    if not isinstance(atoms,list):raise ValueError('OBSERVED_ATOM_LIST_REQUIRED')
    decisions=record.get('unit_decisions')
    units={u['unit_id']:u for u in record['units']}
    if not isinstance(decisions,list) or len(decisions)!=len(units) or {d.get('unit_id') for d in decisions}!=set(units):
        raise ValueError('UNACCOUNTED_WITNESS_OR_FP_CLAIM')
    allowed={'ATOM','DUPLICATE_WITNESS','OUTSIDE_RQ1_SCOPE','NOT_ASSERTED','NON_SEMANTIC_FIELD'}
    if any(d.get('disposition') not in allowed or not d.get('rationale') for d in decisions):
        raise ValueError('EXPLICIT_DISPOSITION_REQUIRED')
    unit_ids=set(units)
    used=set()
    prediction_ids=set()
    for atom in atoms:
        witnesses=atom.get('witness_unit_ids')
        if (not witnesses or not set(witnesses)<=unit_ids or not atom.get('task_binding_receipt')
                or not atom.get('task_id') or not atom.get('prediction_id') or atom['prediction_id'] in prediction_ids):
            raise ValueError('UNBOUND_PREDICTION_ATOM')
        prediction_ids.add(atom['prediction_id'])
        for witness in witnesses:
            candidate=units[witness].get('candidate')
            if not candidate or candidate['kind']!=atom.get('kind') or not exact_json(candidate['value'],atom.get('value')):
                raise ValueError('ATOM_NOT_SUPPORTED_BY_FROZEN_CANONICAL_WITNESS')
        used.update(witnesses)
    declared={d['unit_id'] for d in decisions if d['disposition'] in {'ATOM','DUPLICATE_WITNESS'}}
    if used!=declared:raise ValueError('ATOM_DISPOSITION_MISMATCH')
    # A full raw-response audit must additionally be independently supplied.
    # Presence of sparse literal preannotations can never satisfy this gate.
    receipt=record.get('full_response_review') or {}
    if receipt.get('raw_sha256')!=record['raw_sha256'] or receipt.get('status')!='ALL_ASSERTIONS_REVIEWED':
        raise ValueError('FULL_RESPONSE_REVIEW_REQUIRED')
    return atoms
