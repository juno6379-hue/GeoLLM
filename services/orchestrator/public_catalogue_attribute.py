"""Bounded public FC attribute explanations, independent of LLM and spatial execution."""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.orchestrator.definition_router import ROOT

CATALOGUE = ROOT / 'data/s101_feature_catalogue_v2_parsed.json'
FEATURE_ALIASES = {'제한구역': 'RestrictedArea', '제한 구역': 'RestrictedArea'}
ATTRIBUTE_ALIASES = {'제한 종류': 'restriction', '제한종류': 'restriction', '제한': 'restriction',
                     '제한구역 종류': 'categoryOfRestrictedArea', '제한구역 유형': 'categoryOfRestrictedArea'}


def match_public_catalogue_attribute_query(query: str) -> dict[str, str] | None:
    """Require a complete explanation-shaped query with feature AND attribute slots.

    Full matching deliberately leaves mixed/private/spatial requests to normal policy.
    Neither a sensitive-looking feature name nor one keyword triggers this path.
    """
    q = str(query or '').strip()
    english = re.fullmatch(
        r'(?:explain|describe|list|what\s+are)\s+(?:the\s+)?(?P<attribute>[A-Za-z][A-Za-z0-9]*)'
        r'\s+(?:attribute\s+)?(?:codes|values|permitted\s+values|allowed\s+values)\s+'
        r'(?:of|for|in)\s+(?:the\s+)?(?:S-?101\s+)?(?P<feature>[A-Za-z][A-Za-z0-9]*)[?.!\s]*', q, re.I)
    korean = re.fullmatch(
        r'(?:S-?101\s*)?(?P<feature>[A-Za-z][A-Za-z0-9]*|제한\s*구역)(?:의|에서)?\s+'
        r'(?P<attribute>[A-Za-z][A-Za-z0-9]*|제한\s*종류|제한구역\s*(?:종류|유형)|제한)'
        r'(?:\s*속성)?(?:의|는|은)?\s*(?:어떤\s*)?(?:코드|허용\s*값|허용값|값)(?:로|를|을|는|가|은)?\s*'
        r'(?:표현해|표현하나요|표현하나|표현되나요|표현돼|알려줘|알려주세요|설명해줘|설명해주세요|무엇인가요|뭐야)[?.!\s]*', q, re.I)
    match = english or korean
    if not match:
        return None
    feature, attribute = match['feature'], match['attribute']
    feature = FEATURE_ALIASES.get(feature, FEATURE_ALIASES.get(re.sub(r'\s+', '', feature), feature))
    attribute = ATTRIBUTE_ALIASES.get(attribute, ATTRIBUTE_ALIASES.get(re.sub(r'\s+', '', attribute), attribute))
    return {'feature_code': feature, 'attribute_code': attribute}


@lru_cache(maxsize=4)
def _read_catalogue(path: str, modified: int, size: int) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def resolve_public_catalogue_attribute(query: str) -> dict[str, Any] | None:
    slots = match_public_catalogue_attribute_query(query)
    if not slots:
        return None
    try:
        stat = CATALOGUE.stat()
        document, digest = _read_catalogue(str(CATALOGUE), stat.st_mtime_ns, stat.st_size)
        metadata = document['metadata']
        if metadata.get('productId') != 'S-101' or not metadata.get('versionNumber') or not metadata.get('sha256'):
            return None
        feature_index, feature = next((i, f) for i, f in enumerate(document['features']) if f['code'].casefold() == slots['feature_code'].casefold())
        attribute_index, attribute = next((i, a) for i, a in enumerate(document['attributes']) if a['code'].casefold() == slots['attribute_code'].casefold())
        binding_index, binding = next((i, b) for i, b in enumerate(feature['bindings'])
                                     if b.get('type') == 'attribute' and b.get('ref') == attribute['code'])
        listed = attribute.get('listed_values') or []
        if not listed or not attribute.get('definition'):
            return None
        permitted = binding.get('permitted_values') or []
        by_value = {str(v['value']): v for v in listed}
        if any(str(v) not in by_value for v in permitted):
            return None
        allowed = [by_value[str(v)] for v in permitted] if permitted else listed
        return {
            'feature_code': feature['code'], 'attribute_code': attribute['code'],
            'definition': attribute['definition'], 'feature_definition': feature['definition'],
            'listed_values': listed, 'allowed_values': allowed, 'permitted_values': permitted,
            'binding': binding, 'source_version': metadata['versionNumber'],
            'source_ref': 'data/s101_feature_catalogue_v2_parsed.json', 'source_sha256': digest,
            'xml_source_ref': metadata['source'], 'xml_source_sha256': metadata['sha256'],
            'verification_status': 'LOCAL_PARSED_FC_SOURCE',
            'locators': [f'/features/{feature_index}', f'/attributes/{attribute_index}',
                         f'/features/{feature_index}/bindings/{binding_index}'],
            'scope': 'PUBLIC_STANDARD_ATTRIBUTE_DEFINITION_ONLY',
        }
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None


def build_public_catalogue_attribute_response(state: dict[str, Any]) -> dict[str, Any] | None:
    entry = resolve_public_catalogue_attribute(str(state.get('query') or ''))
    if not entry:
        return None
    from services.orchestrator.execution_validator import validate_lookup_request, is_execution_authorized, project_execution_decision
    operation = 'public_catalogue_attribute_lookup'
    validated = validate_lookup_request(state, operation)
    if not is_execution_authorized(validated):
        return None
    # The response must use exactly the source snapshot authorized by the validator.
    if not any(b.snapshot_version == entry['source_sha256'] for b in validated.data_bindings):
        return None
    feature, attribute = entry['feature_code'], entry['attribute_code']
    labels = '\n'.join(f"- {v['value']}: {v['label']}" for v in entry['allowed_values'])
    answer = (f"S-101 Feature Catalogue {entry['source_version']}에서 {feature}의 `{attribute}`는 "
              f"다음과 같이 정의됩니다: {entry['definition']}\n\n{feature}에 허용된 코드:\n{labels}")
    if attribute == 'restriction':
        answer += '\n\n`restriction`은 금지·제한 행위를 나타냅니다. 구역의 종류를 나타내는 `categoryOfRestrictedArea`와 구분합니다.'
    answer += (f"\n\n근거: {entry['source_ref']} ({entry['source_version']}), "
               f"{', '.join(entry['locators'])}. 실제 제한구역 위치나 현행 통제 적용 여부를 조회한 결과는 아닙니다.")
    task_id = str(state.get('task_id') or 'local')
    plan = {'task_id': task_id, 'intent': 'STANDARD_ATTRIBUTE_LOOKUP', 'analysis_type': operation,
            'primary_agent': 'Standard RAG Agent', 'secondary_agents': [],
            'slots': {'feature_code': feature, 'attribute_code': attribute},
            'tools': ['catalogue.attribute_lookup'], 'data': [entry['source_ref']],
            'outputs': ['StandardDocumentOutput', 'EvidenceBundle', 'Summary'], 'clarification_required': False}
    project_execution_decision(validated, plan)
    qec = validated.model_dump(mode='json'); qec['route_plan'] = plan
    evidence = {'evidence_id': f"fc:{feature}:{attribute}:{entry['source_sha256'][:16]}",
                'evidence_type': 'public_standard_attribute', 'source_ref': entry['source_ref'],
                'source_sha256': entry['source_sha256'], 'summary': f'{feature}.{attribute}', 'data': entry}
    structured = {'status': 'COMPLETED', 'analysis_type': operation, **entry,
                  'search_execution': {'status': 'NOT_RUN', 'reason': 'Public document explanation; no spatial task'},
                  'web_rag_usage': {'web_used': False, 'rag_used': False, 'llm_used': False,
                                    'embedding_independent': True, 'evidence_used': True,
                                    'execution_path': 'public_fc_attribute_lookup'}}
    final = {'task_id': task_id, 'request_id': task_id, 'trace_id': f'tr-{task_id}', 'status': 'COMPLETED',
             'agent_name': 'Standard RAG Agent', 'agent_version': 'public-fc-attribute-v1',
             'summary': answer, 'answer_text': answer, 'structured_result': structured,
             'orchestrator_v2': {'route_plan': plan, 'query_execution_context': qec,
                                 'fast_path': 'public_fc_attribute_lookup', 'embedding_independent': True},
             'rag_evidence': [evidence], 'kg_provenance': [],
             'evidence_bundle': {'rag_evidence': [evidence], 'kg_provenance': [], 'regulatory_evidence': [],
                                 'spatial_feature_evidence': [], 'spatial_layer_evidence': [], 'accident_relation_evidence': []},
             'contract_version': 'geollm.execution.v1'}
    return {'final_dict': final, 'task_plan': plan, 'query_execution_context': qec}
