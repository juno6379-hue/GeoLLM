"""Source-bound lexical suggestions, distinct from ontology identity and tool inputs."""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[2] / 'data/mof_terminology_relations.json'
PARTICLES = ('에서는', '에서도', '으로는', '으로', '에서', '에게', '이란', '란',
             '은', '는', '이', '가', '을', '를', '의', '에', '도', '만', '과', '와')


def validate_bundle(bundle):
    from scripts.build_mof_normalization_review import build
    if bundle.get('schema_version') != 'marine_terminology.v1' or bundle.get('mode') != 'ADVISORY_ONLY':
        raise ValueError('Unsupported terminology contract')
    if bundle.get('human_gold') is not False or bundle.get('query_rewrite_enabled') is not False:
        raise ValueError('Terminology must remain advisory')
    if bundle['seeds'].get('relation') != 'recommended_korean_label':
        raise ValueError('Unsupported lexical relation')
    if build(bundle['seeds'], bundle['units']) != bundle['relations']:
        raise ValueError('Terminology relations differ from source rows')
    return bundle['relations']


@lru_cache(maxsize=1)
def _registry():
    try:
        raw = REGISTRY.read_bytes()
        return validate_bundle(json.loads(raw)), {'status':'AVAILABLE',
            'registry_sha256':hashlib.sha256(raw).hexdigest()}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # A missing/corrupt supplement must not break existing query execution.
        return [], {'status':'TERMINOLOGY_UNAVAILABLE', 'error_type':type(exc).__name__}


def match_terminology(query, constraints):
    relations, metadata = _registry()
    matches = []
    quoted = [(m.start(),m.end()) for m in re.finditer(r'"[^"]*"|\'[^\']*\'|“[^”]*”|‘[^’]*’',query)]
    tail = r'(?=$|[^가-힣A-Za-z0-9_]|(?:'+'|'.join(PARTICLES)+r')(?=$|[^가-힣A-Za-z0-9_]))'
    for row in relations:
        for label in (row['original'], row['preferred']):
            pattern = re.escape(label)
            if row['optional_spacing'] and label == row['preferred']:
                pattern = r'\s*'.join(re.escape(p) for p in label.split())
            for match in re.finditer(r'(?<![가-힣A-Za-z0-9_])'+pattern+tail,query):
                excluded = any(c['kind']=='exclusion' and c['scope_status']=='EXPLICIT_LOCAL_SCOPE'
                               and match.start()<c['span'][1] and c['span'][0]<match.end()
                               for c in constraints)
                matches.append({'raw_text':match[0], 'span':list(match.span()),
                    'original_label':row['original'], 'preferred_label':row['preferred'],
                    'relation':row['relation'], 'reference':row['reference'], 'quote':row['quote'],
                    'source_span':row['source_span'], 'review_status':row['review_status'],
                    'sense_status':'DOMAIN_SENSE_UNRESOLVED', 'excluded':excluded,
                    'quoted':any(a<=match.start()<b for a,b in quoted),
                    'canonical_id':None, 'ontology_equivalence_verified':False,
                    'execution_authorized':False})
    return {**metadata, 'contract':'marine_terminology.v1', 'mode':'ADVISORY_ONLY',
            'original_preserved':True,'candidates':sorted(matches,key=lambda m:m['span'])}


def resolve_label_request(query):
    """Answer only an explicit label lookup, not a definition or compound request."""
    request = re.fullmatch(r'\s*(.+?)(?:의)?\s*순화어(?:는|를|가|은)?'
                           r'\s*(?:뭐야|무엇인가요|무엇|알려줘)?[?!.\s]*', query)
    if not request:
        return None
    subject = request.group(1).strip()
    candidates = match_terminology(subject, [])['candidates']
    matches = [c for c in candidates if c['span']==[0,len(subject)]]
    if len(matches) != 1:
        return None
    relation = matches[0]
    original, preferred = relation['original_label'], relation['preferred_label']
    return {'term_id':relation['reference']['unit_id']+':'+original,
            'canonical_term':original, 'aliases':[], 'context':'maritime_terminology',
            'definition_ko':None, 'recommended_label':preferred,
            'source_title':'해양수산부 해양수산 분야 전문용어 순화 자료 (PDF 1쪽)',
            'source_ref':'data/mof_terminology_relations.json#'+relation['reference']['unit_id'],
            'source_kind':'mof_terminology_relation', 'verification_status':'SOURCE_BOUND_AI_REVIEW_REQUIRED',
            'source_relation':relation}
