"""Bounded Kiwi adapter and conservative, explicit Korean constraint evidence."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import threading
import time
from functools import lru_cache
from pathlib import Path

import yaml

from services.orchestrator.slot_evidence import extract_quantities, query_hash

ROOT = Path(__file__).resolve().parents[2]
_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def registry_words() -> tuple[tuple[str, ...], str]:
    from services.orchestrator.marine_lexicon import load_terms
    entries,sources=load_terms()
    raw=json.dumps(sources,ensure_ascii=False,sort_keys=True).encode('utf-8')
    words = set(entries)
    for entry in entries.values():
        words.update(x for x in entry.get('aliases', []) if isinstance(x, str))
    return tuple(sorted(w for w in words if re.fullmatch(r'[가-힣]{2,40}', w))), hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def _engine():
    # Cache failure as well: a missing dependency must not be retried per request.
    try:
        from kiwipiepy import Kiwi
        words, digest = registry_words()
        kiwi = Kiwi(num_workers=1)
        for word in words:
            kiwi.add_user_word(word, 'NNP')
        kiwi.tokenize('초기화')
        return kiwi, {'status': 'AVAILABLE', 'version': importlib.metadata.version('kiwipiepy'),
                      'model_version': importlib.metadata.version('kiwipiepy_model'),
                      'dictionary_sha256': digest, 'dictionary_terms': len(words)}
    except Exception as exc:
        return None, {'status': 'KOREAN_ANALYZER_UNAVAILABLE', 'error_type': type(exc).__name__}


def constraints(query: str) -> list[dict]:
    """Preserve supported scopes. Quoted and complex negations remain review-only."""
    patterns = {
        'missing_location': r'(?:위치|좌표|기준점)(?:가|는|를|이)?\s*(?:없이|없는데|없어)',
        'exclusion': r'(?P<target>[가-힣A-Za-z0-9_-]+?)(?:은|는|을|를)?\s*(?:말고|제외하고|빼고)',
        'absence_predicate': r'(?P<target>[가-힣A-Za-z0-9_-]+?)(?:이|가)\s*없는\s*(?:구역|해역|지역)',
    }
    quoted = [(m.start(), m.end()) for m in re.finditer(r'"[^"]*"|\'[^\']*\'|“[^”]*”|‘[^’]*’', query)]
    result = []
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, query):
            result.append({'kind': kind, 'raw_text': match[0], 'span': list(match.span()),
                           'target': match.groupdict().get('target'),
                           'scope_status': 'QUOTED_REVIEW_REQUIRED' if any(a <= match.start() < b for a, b in quoted) else 'EXPLICIT_LOCAL_SCOPE'})
    return sorted(result, key=lambda row: row['span'][0])


def analyze_query(query: str) -> dict:
    start = time.monotonic()
    result = {'schema_version': 'korean_query.v1', 'query_sha256': query_hash(query),
              'index_unit': 'unicode_code_point', 'original_preserved': True,
              'slots': extract_quantities(query), 'constraints': constraints(query), 'tokens': [],
              'role': 'linguistic_evidence_not_execution_authority'}
    from services.orchestrator.marine_terminology import match_terminology
    result['maritime_terminology'] = match_terminology(query, result['constraints'])
    if os.getenv('GEOLLM_KIWI_ENABLED', 'true').lower() not in {'true', '1', 'yes', 'on'}:
        result['analyzer'] = {'status': 'DISABLED'}
    elif len(query) > 4096:
        result['analyzer'] = {'status': 'INPUT_LIMIT_EXCEEDED', 'limit_code_points': 4096}
    else:
        with _LOCK:
            engine, metadata = _engine()
            result['analyzer'] = dict(metadata)
            if engine:
                try:
                    result['tokens'] = [{'form': t.form, 'pos': t.tag, 'span': [t.start, t.start+t.len],
                                         'raw_text': query[t.start:t.start+t.len]} for t in engine.tokenize(query)]
                except Exception as exc:
                    result['analyzer'] = {'status': 'KOREAN_ANALYZER_UNAVAILABLE', 'error_type': type(exc).__name__}
    result['latency_ms'] = round((time.monotonic()-start)*1000, 3)
    return result


def contract_problem(query: str, analysis: dict, spatial_context: dict | None = None) -> dict | None:
    """Never silently execute an exclusion with a planner that cannot apply it."""
    from services.orchestrator.request_semantics import requires_execution
    from services.orchestrator.request_obligations import missing_selected_feature
    if missing_selected_feature(query, spatial_context):
        return {'status': 'NEEDS_CLARIFICATION', 'code': 'SELECTED_FEATURE_REQUIRED', 'missing_slots': ['selected_feature_id'],
                'message': '설명할 지도 객체를 선택해주세요. 실제 객체 ID와 원천 정보를 확인해야 해당 객체의 근거를 조회할 수 있습니다.'}
    if not requires_execution(query):
        return None
    context = spatial_context or {}
    if hasattr(context, 'model_dump'):
        context = context.model_dump()
    selected_intersection = re.search(r'\bintersect(?:ing|s)?\b|교차', query, re.I) and re.search(r'selected\s+(?:area|polygon)|선택.*(?:영역|구역|폴리곤)', query, re.I)
    if selected_intersection:
        selected = context.get('selected_feature') or {}
        geometry = context.get('geometry') or context.get('selected_area') or selected.get('geometry')
        if not geometry:
            return {'status': 'NEEDS_CLARIFICATION', 'code': 'AOI_REQUIRED', 'missing_slots': ['selected_area_geometry'],
                    'message': '교차 검색할 영역의 다각형을 지도에서 선택해주세요. 기준 영역이 없어 공간 검색을 실행하지 않았습니다.'}
        return {'status': 'BLOCKED', 'code': 'INTERSECTION_EXECUTION_NOT_SUPPORTED', 'missing_slots': [],
                'message': '선택 영역은 받았지만 교차 조건을 검증하는 실행 경로가 아직 연결되지 않았습니다. 반경 검색이나 문서 검색으로 대체하지 않았습니다.'}
    from services.orchestrator.request_semantics import missing_map_scope
    if missing_map_scope(query, context):
        return {'status': 'NEEDS_CLARIFICATION', 'code': 'MAP_SCOPE_REQUIRED', 'missing_slots': ['map_search_scope'],
                'message': '지도에 표시할 객체의 검색 위치나 영역을 지정해 주세요. 지도 영역·선택한 위치·지명 없이 전체 자료를 임의로 조회하지 않았습니다.'}
    active = [c for c in analysis.get('constraints', []) if c['scope_status'] == 'EXPLICIT_LOCAL_SCOPE']
    context = spatial_context or {}
    has_context = any(context.get(k) for k in ('geometry', 'map_bounds', 'viewport', 'selected_feature', 'selected_features', 'clicked_point', 'place_id'))
    if any(c['kind'] == 'missing_location' for c in active) and re.search(r'부근|주변|근처|이내|반경', query):
        if not has_context:
            return {'status': 'NEEDS_CLARIFICATION', 'code': 'LOCATION_REQUIRED', 'missing_slots': ['reference_location'],
                    'message': '부근 검색의 기준 위치가 없습니다. 지명·좌표 또는 지도에서 선택한 기준 위치를 알려주세요.'}
        # Context presence alone does not validate the spatial accident tool contract.
        return {'status': 'BLOCKED', 'code': 'SPATIAL_CONTEXT_BINDING_REQUIRED', 'missing_slots': [],
                'message': '지도 문맥은 받았지만 이 조건을 사건 조회의 공간 필터로 검증·연결하지 못했습니다. 위치 없는 일반 텍스트 조회로 대체하지 않았습니다.'}
    if any(c['kind'] in {'exclusion', 'absence_predicate'} for c in active):
        return {'status': 'BLOCKED', 'code': 'NEGATION_EXECUTION_NOT_SUPPORTED', 'missing_slots': [],
                'message': '제외·부재 조건을 확인했지만 현재 실행 계획은 해당 조건을 끝까지 검증하지 못합니다. 조건을 무시한 조회를 실행하지 않았습니다.'}
    invalid = [s for s in analysis.get('slots', []) if s['validation_status'] == 'REJECTED']
    if invalid:
        return {'status': 'NEEDS_CLARIFICATION', 'code': 'INVALID_QUANTITY', 'missing_slots': ['quantity'],
                'message': '거리·기간의 값과 단위를 확인해주세요. 해석할 수 없는 수량을 임의로 보정하지 않았습니다.'}
    return None


def guard_result(state: dict, analysis: dict, problem: dict) -> dict:
    status = problem['status']
    plan = {'intent': 'UNRESOLVED', 'analysis_type': 'query_constraint_validation', 'status': status,
            'slots': {'quantity_evidence': analysis['slots'], 'constraints': analysis['constraints'],
                      'unresolved_slots': problem['missing_slots']},
            'execution_ready': False, 'tools': [], 'clarification_required': status == 'NEEDS_CLARIFICATION'}
    from shared.schemas.agent import QueryExecutionContext, PlanStatus
    readiness = PlanStatus.NEEDS_USER_INPUT if status == 'NEEDS_CLARIFICATION' else PlanStatus.BLOCKED_CONFIG
    context = QueryExecutionContext(request_id=state['task_id'], revision=state.get('execution_revision') or 1, original_query=state.get('query'),
                                    route_plan=plan, readiness=readiness,
                                    blockers=[problem['code']], provenance={'execution_status': 'NOT_RUN'}).model_dump(mode='json')
    context['execution_status'] = 'NOT_RUN'
    final = {'task_id': state['task_id'], 'status': status, 'error_code': problem['code'],
             'answer_text': problem['message'], 'summary': problem['message'],
             'structured_result': {'count': None, 'korean_query_analysis': analysis},
             'orchestrator_v2': {'route_plan': plan, 'query_execution_context': context, 'korean_query_analysis': analysis}}
    if status == 'NEEDS_CLARIFICATION':
        final['clarification_questions'] = [problem['message']]
    return {'final_dict': final, 'task_plan': plan, 'query_execution_context': context, 'status': status,
            'korean_query_analysis': analysis, 'query_contract_blocked': True}
