"""Project validated execution separately from planning and scope source evidence."""
from copy import deepcopy
from pathlib import PurePosixPath
import re

OPERATION_ROUTES = {
    'definition_lookup': 'STANDARD_RAG', 'terminology_relation_lookup': 'STANDARD_RAG',
    'catalogue_attribute_lookup': 'STANDARD_RAG', 'catalogue_document_lookup': 'STANDARD_RAG',
    'public_catalogue_attribute_lookup': 'STANDARD_RAG', 'public_catalogue_document_lookup': 'STANDARD_RAG',
    'document_search': 'STANDARD_RAG', 'local_document_lookup': 'STANDARD_RAG',
    'dataset_source_lookup': 'DATASET_PROVENANCE', 'coastal_evidence_lookup': 'STANDARD_RAG',
    'metadata_discovery': 'DATASET_PROVENANCE', 'evidence_validation': 'QUALITY_REVIEW',
    'dataset_evidence_lookup': 'DATASET_PROVENANCE', 'dataset_document_lookup': 'STANDARD_RAG',
    'traffic_layer_description': 'DATA_DISCOVERY', 'document_coverage': 'DATA_DISCOVERY',
    'traffic_coverage': 'DATA_DISCOVERY', 'capability_vector': 'DATA_DISCOVERY', 'resolver_registry': 'DATA_DISCOVERY',
    'place_lookup': 'PLACE_LOOKUP', 'place_navigation': 'PLACE_LOOKUP',
    'feature_search_by_radius': 'SPATIAL_ANALYSIS', 'feature_search_by_bounds': 'SPATIAL_ANALYSIS',
    'nearest_feature_search': 'SPATIAL_ANALYSIS', 'feature_search_nearest': 'SPATIAL_ANALYSIS',
    'nearest_feature': 'SPATIAL_ANALYSIS',
    'accident_event_lookup': 'ACCIDENT_ANALYSIS', 'accident_spatial_history_lookup': 'ACCIDENT_ANALYSIS',
}


def final_execution_contract(planning, qec, status, *, authorized):
    """authorized MUST be supplied by is_execution_authorized, never by rank/status."""
    qec = qec if isinstance(qec, dict) else {}
    decision = (qec.get('provenance') or {}).get('execution_validation') or {}
    valid_decision = decision.get('authority') == 'ExecutionValidator'
    operation = decision.get('operation') if valid_decision else None
    route = OPERATION_ROUTES.get(operation)
    # A reporting layer may revoke a contradictory display, never grant ready.
    ready = bool(authorized and valid_decision and status not in ('BLOCKED', 'FAILED', 'NEEDS_CLARIFICATION'))
    return {
        'contract': 'validated_execution_reporting.v1', 'status': status,
        'status_scope': 'FINAL_RESULT', 'execution_authorized': ready,
        'execution_authority': 'ExecutionValidator',
        'execution_readiness': qec.get('readiness', 'NOT_VALIDATED'),
        'validated_operation': operation, 'execution_route': route,
        'route_scope': 'VALIDATED_OPERATION' if route else 'UNRESOLVED',
        # Binding is not a claim that the tool was called or succeeded.
        'steps': [{'tool_id': b.get('tool_id'), 'operation': b.get('operation'),
                   'status': 'VALIDATED_BINDING' if ready else 'NOT_AUTHORIZED'}
                  for b in qec.get('tool_bindings') or [] if isinstance(b, dict)],
        'planning_status': (planning or {}).get('planning_status', (planning or {}).get('status')),
        'planning_execution_contract': deepcopy(planning or {}),
    }


IDENTITY_STOPWORDS = {
    'dataset', 'data', 'csv', 'zip', 'embedding', 'embedded', 'chunks', 'source',
    '파싱', '표준화', '공간', '근거', '출처', '원천', '적재', '임베딩', '폴더',
    '데이터', '데이터셋', '파일', '대상', '대상인지', '확인', '확인해줘', '보여줘',
    '알려줘', '설명해줘', '현황', '해양수산부', '해양경찰청', '국립해양조사원',
}


def filename_identities(query):
    # Match a filename token, not a bare extension or arbitrary content term.
    matches = re.findall(r'[\w가-힣().-]+\.(?:csv|zip|xlsx?|pdf|docx?|shp|jsonl?|txt)(?![A-Za-z0-9_.])', str(query or ''), re.I)
    return list(dict.fromkeys(value.casefold() for value in matches))


def identity_terms(terms):
    return sorted({str(t).casefold() for t in terms if len(str(t)) >= 2
                   and str(t).casefold() not in IDENTITY_STOPWORDS
                   and not str(t).startswith(('파싱', '표준화', '임베딩', '적재', '확인', '폴더', '대상'))})


def source_identity(query, terms, source_file, title):
    filenames = filename_identities(query)
    basename = PurePosixPath(str(source_file or '').replace('\\', '/')).name.casefold()
    if filenames:
        matched = [value for value in filenames if basename == value or basename.endswith('_' + value)]
        return {'accepted': bool(matched), 'scope': 'EXPLICIT_SOURCE_FILENAME', 'matched': matched}
    needles = identity_terms(terms)
    haystack = (str(source_file or '') + ' ' + str(title or '')).casefold()
    matched = [term for term in needles if term in haystack]
    return {'accepted': bool(matched) if needles else True,
            'scope': 'SOURCE_IDENTITY_TERMS' if needles else 'UNSCOPED_METADATA_SEARCH', 'matched': matched}


def source_rank(item):
    # More chunks never increase source relevance. Deterministic lexical ties.
    return (-len(item.get('source_identity_matches') or []),
            -len(item.get('matched_terms') or []), str(item.get('source_file') or ''))


def literal_ilike_pattern(value):
    return '%' + str(value).replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
