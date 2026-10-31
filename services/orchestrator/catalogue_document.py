"""Source-grounded FC explanations; never an alternative to a spatial operation."""
from __future__ import annotations
import re
import hashlib
import xml.etree.ElementTree as ET
import yaml
from services.orchestrator.public_catalogue_attribute import CATALOGUE, _read_catalogue


def resolve_catalogue_document(query: str) -> dict | None:
    try:
        return _resolve_catalogue_document(query)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
        return None


def _resolve_catalogue_document(query: str) -> dict | None:
    q = str(query or '')
    from services.orchestrator.request_semantics import requires_execution
    if requires_execution(q):
        return None
    if re.search(r'비공개|기밀|무단|\b(?:private|classified|confidential|unauthorized)\b', q, re.I):
        return None
    # A definition clause in a composite execution request does not cancel its
    # spatial obligations. Explicit location/relation slots take precedence.
    if re.search(r'주변|근처|반경|이내|교차|선택.*영역|\b(?:within|intersect\w*|nearest|closest|nearby)\b|\d+\s*(?:km|m)\b', q, re.I):
        return None
    if not re.search(r'정의|어떤\s*객체|속성|허용\s*기하|뜻|의미|구분|\b(?:definition|what is|attributes?|meaning)\b', q, re.I):
        return None
    stat = CATALOGUE.stat()
    doc, digest = _read_catalogue(str(CATALOGUE), stat.st_mtime_ns, stat.st_size)
    xml_path = CATALOGUE.parents[1] / doc['metadata']['source']
    try:
        xml_raw = xml_path.read_bytes()
        if hashlib.sha256(xml_raw).hexdigest() != doc['metadata']['sha256']:
            return None
        xml_root = ET.fromstring(xml_raw)
        types = {}
        for node in xml_root.iter():
            kind = node.tag.rsplit('}', 1)[-1]
            if kind in {'S100_FC_SimpleAttribute', 'S100_FC_ComplexAttribute'}:
                code = next((c.text for c in node if c.tag.rsplit('}', 1)[-1]=='code'), None)
                types[code] = kind
    except (OSError, ET.ParseError):
        return None
    aliases = yaml.safe_load((CATALOGUE.parent / 's101_feature_dictionary.yaml').read_text(encoding='utf-8'))['s101_features']
    codes = set()
    for f in doc['features']:
        if re.search(r'(?<![A-Za-z0-9_])'+re.escape(f['code'])+r'(?![A-Za-z0-9_])', q, re.I):
            codes.add(f['code'])
    for alias, entry in aliases.items():
        if alias in q:
            candidates = entry.get('feature_candidates') or []
            if len(candidates) == 1:
                codes.update(candidates)
            else:
                # An ambiguous alias cannot be silently reduced to one feature.
                return None
    features = [(i, f) for i, f in enumerate(doc['features']) if f['code'] in codes]
    if not features or len(features) != len(codes):
        return None
    attrs = {a['code']: (i, a) for i, a in enumerate(doc['attributes'])}
    bindings, locators, claims = [], [], []
    for i, f in features:
        loc = "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='"+f['code']+"']]"
        locators.append(loc)
        claims.append({'claim': f['definition'], 'source_ref': doc['metadata']['source'], 'source_sha256': doc['metadata']['sha256'], 'definition_locator': loc+"/*[local-name()='definition']", 'locator': loc+"/*[local-name()='definition']"})
        for j, b in enumerate(f['bindings']):
            if b.get('type') != 'attribute':
                continue
            attribute = attrs.get(b['ref'])
            bindings.append({'owner': f['code'], 'attribute': b['ref'], **b,
                             'definition': attribute[1].get('definition') if attribute else None,
                             'attribute_definition': attribute[1].get('definition') if attribute else None,
                             'global_listed_values': attribute[1].get('listed_values', []) if attribute else [],
                             'owner_locator': loc,
                             'attribute_locator': "//*[local-name()='"+types[b['ref']]+"'][*[local-name()='code' and text()='"+b['ref']+"']]" if b['ref'] in types else None,
                             'listed_values': attribute[1].get('listed_values', []) if attribute else [],
                             'locator': loc+"/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='"+b['ref']+"']]"})
            locators.append(loc+"/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='"+b['ref']+"']]")
    meta = doc['metadata']
    return {'features': [{'code': f['code'], 'definition': f['definition'], 'permitted_primitives': f['permitted_primitives']} for _, f in features],
            'attribute_bindings': bindings, 'definition_quote': '\n'.join(f['definition'] for _, f in features),
            'source_ref': 'data/s101_feature_catalogue_v2_parsed.json', 'source_sha256': digest,
            'evidence': {'edition': meta['versionNumber'], 'source_sha256': meta['sha256'],
                         'parsed_source_sha256': digest, 'source_ref': meta['source'], 'source_path': meta['source'],
                         'locators': locators, 'claim_source_links': claims}}


def build_catalogue_document_response(state: dict) -> dict | None:
    doc = resolve_catalogue_document(state.get('query', ''))
    if not doc:
        return None
    from services.orchestrator.execution_validator import validate_lookup_request, is_execution_authorized, project_execution_decision
    qec = validate_lookup_request(state, 'public_catalogue_document_lookup')
    if not is_execution_authorized(qec) or not any(b.snapshot_version == doc['source_sha256'] for b in qec.data_bindings):
        return None
    parts = [f"S-101 Feature Catalogue {doc['evidence']['edition']}"]
    for f in doc['features']:
        parts.append(f"{f['code']}: {f['definition']}\n허용 기하: {', '.join(f['permitted_primitives'])}")
        if re.search(r'속성|attributes?', state.get('query',''), re.I):
            parts.extend(f"- {b['attribute']}: {b['definition'] or '복합 속성'} (다중도 {b['lower']}..{'*' if b['unbounded'] else b['upper']}; 허용 코드 {', '.join(b['permitted_values']) or '별도 제한 없음'})" for b in doc['attribute_bindings'] if b['owner']==f['code'])
    parts.append('근거: '+doc['source_ref']+'; '+', '.join(doc['evidence']['locators']))
    answer='\n\n'.join(parts)
    plan={'analysis_type':'public_catalogue_document_lookup','intent':'STANDARD_RAG','tools':['catalogue.document_lookup'],'outputs':['StandardDocumentOutput','EvidenceBundle','Summary']}
    project_execution_decision(qec,plan)
    final={'status':'COMPLETED','summary':answer,'answer_text':answer,'structured_result':{'status':'COMPLETED','document_answer':doc,'search_execution':{'status':'NOT_RUN','reason':'Catalogue explanation only'}},
           'orchestrator_v2':{'route_plan':plan,'query_execution_context':qec.model_dump(mode='json')},
           'rag_evidence':[{'source_ref':doc['source_ref'],'source_sha256':doc['source_sha256'],'data':doc}], 'contract_version':'geollm.execution.v1'}
    return {'final_dict':final,'task_plan':plan,'query_execution_context':qec.model_dump(mode='json')}


def exact_document_unmatched(state: dict) -> dict:
    message = ('로컬 표준 사전의 정확 일치 조회에서 요청한 객체·속성의 연결 근거를 확정하지 못했습니다. '
               '전체 문서 검색 결과가 없다는 뜻은 아닙니다. 표준 코드나 용어 범위를 확인해 주세요.')
    final = {'task_id': state.get('task_id'), 'status': 'BLOCKED', 'error_code': 'EXACT_DOCUMENT_BINDING_UNAVAILABLE',
             'summary': message, 'answer_text': message,
             'structured_result': {'status': 'BLOCKED_DATA', 'lookup_scope': 'local_exact_registry_lookup',
                                   'documents': [], 'citations': [], 'retrieved_count': 0,
                                   'full_corpus_searched': False,
                                   'search_execution': {'status': 'NOT_RUN', 'reason': 'Document lookup only; no spatial execution'}},
             'evidence_bundle': {'rag_evidence': [], 'spatial_feature_evidence': []},
             'orchestrator_v2': {'fast_path': 'exact_document_unmatched'}}
    return {'final_dict': final, 'status': 'BLOCKED'}
