"""Output obligations are independent of the selected route name."""
from __future__ import annotations

import re


def required_outputs(query: str) -> list[str]:
    text = str(query or '').casefold()
    outputs = []
    from services.orchestrator.request_semantics import requests_map_output
    if requests_map_output(query):
        outputs.append('map_spatial_result')
    if re.search(r"렌더링|묘화|portrayal", text) and re.search(r"규칙|rule", text):
        outputs.append("portrayal_rule_evidence")
    if re.search(r'portrayal|묘화|심볼|symbol|아이콘', text) and re.search(r'매칭|연결|대응|일치', text):
        outputs.append('portrayal_symbol_binding')
    if re.search(r'지도|클릭|선택', text) and re.search(r'이 객체|이것|폴리곤|feature 정보|객체.*근거', text) and re.search(r'설명|정보|근거|무엇', text):
        outputs.append('selected_feature_evidence')
    if re.search(r'zip|원천|dataset|파일', text) and re.search(r'좌표|crs|변환|보완|정제', text) and re.search(r'방식|어떻게|했어|이력|과정', text):
        outputs.append('data_processing_provenance')
    if re.search(r'통항량|교통량', text) and re.search(r'분석|집계|요약|비교', text):
        outputs.append('traffic_aggregation')
    if re.search(r'사고.*(?:이력|원인|분석)|(?:이력|원인).*사고', text):
        outputs.append('accident_evidence')
    # A lookup plus an explicit explanation is two output obligations. Merely
    # mentioning an attribute/filter must not turn a simple search into this task.
    lookup = re.search(r'찾|검색|조회|\b(?:find|search|list|retrieve)\b', text)
    attribute_explanation = re.search(
        r'속성[^.!?\n]{0,50}(?:설명|알려)|(?:설명|알려)[^.!?\n]{0,30}속성|'
        r'\b(?:explain|describe)\b[^.!?\n]{0,80}\battributes?\b', text)
    negated_explanation = re.search(
        r'(?:do not|don\x27t|without)\s+(?:explain(?:ing)?|describ(?:e|ing))\b[^.!?\n]{0,80}\battributes?\b|'
        r'속성[^.!?\n]{0,30}(?:설명하지|설명은?\s*(?:제외|생략))', text)
    from services.orchestrator.request_semantics import requires_execution
    if requires_execution(query) and len(requested_feature_groups(query)) > 1:
        outputs.append('all_requested_feature_groups')
    if lookup and attribute_explanation and not negated_explanation:
        outputs.append('feature_attribute_explanation')
    elif requests_grounded_explanation(query) and not negated_explanation:
        outputs.append('grounded_term_explanation')
    return outputs


def requests_grounded_explanation(query: str) -> bool:
    text = str(query or '').casefold()
    # Retrieving documents about a concept is a different output contract from
    # explaining the concept itself. A mixed retrieval+explanation keeps both.
    retrieval = re.search(r'(?:문서|자료|출처|참고문헌)[^.!?\n]{0,35}(?:찾|검색|목록)|\b(?:find|search|retrieve|list)\b[^.!?\n]{0,80}\b(?:documents?|sources?|references?)\b', text)
    explanation_action = re.search(r'설명|뜻.*알려|의미.*알려|정의.*알려|\b(?:explain|describe|what is|what does)\b', text)
    if retrieval and not explanation_action:
        return False
    from services.orchestrator.request_semantics import requires_execution
    definition = re.search(r'정의|뜻|의미|\b(?:definition|meaning)\b|\bwhat does\b.*\bmean\b', text)
    if not requires_execution(query):
        definition = definition or re.search(r'어떤\s*객체|\bwhat is\b', text)
    attributes = re.search(r'속성[^.!?\n]{0,50}(?:설명|알려|허용)|(?:설명|알려)[^.!?\n]{0,30}속성|\b(?:explain|describe|which|what)\b[^.!?\n]{0,80}\battributes?\b', text)
    return bool(definition or attributes)


def _has_grounded_term_explanation(query: str, final: dict) -> bool:
    from services.orchestrator.execution_validator import is_execution_authorized
    from shared.schemas.agent import QueryExecutionContext
    structured = final.get('structured_result') or {}
    try:
        qec = QueryExecutionContext.model_validate((final.get('orchestrator_v2') or {}).get('query_execution_context') or {})
        if not is_execution_authorized(qec):
            return False
    except (TypeError, ValueError):
        return False
    operations = {binding.operation for binding in qec.tool_bindings}
    if 'public_catalogue_document_lookup' in operations:
        from services.orchestrator.catalogue_document import resolve_catalogue_document
        expected = resolve_catalogue_document(query)
        actual = structured.get('document_answer')
        # The response must bind the requested subject to a real explanation,
        # not merely have retrieved a related document title or excerpt.
        return bool(expected and actual == expected and expected.get('features'))
    if 'public_catalogue_attribute_lookup' in operations:
        from services.orchestrator.public_catalogue_attribute import resolve_public_catalogue_attribute
        expected = resolve_public_catalogue_attribute(query)
        return bool(expected and all(structured.get(k) == expected[k] for k in
                                     ('feature_code', 'attribute_code', 'definition', 'allowed_values', 'source_sha256')))
    if 'definition_lookup' in operations:
        from services.orchestrator.definition_router import resolve_definition
        expected = resolve_definition(query)
        return bool(expected and structured.get('definition') == expected.get('definition_ko')
                    and structured.get('canonical_term') == expected.get('canonical_term')
                    and structured.get('source_ref') == expected.get('source_ref'))
    return False


def _has_executed_map_output(final: dict) -> bool:
    from services.orchestrator.execution_validator import is_execution_authorized
    from shared.schemas.agent import QueryExecutionContext
    structured = final.get('structured_result') or {}
    qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
    try:
        typed = QueryExecutionContext.model_validate(qec)
        if not is_execution_authorized(typed):
            return False
        if not any(binding.tool_id.startswith('postgis.') for binding in typed.tool_bindings):
            return False
    except (TypeError, ValueError):
        return False
    geojson = structured.get('geojson') or final.get('features')
    if not isinstance(geojson, dict) or geojson.get('type') != 'FeatureCollection' or not isinstance(geojson.get('features'), list):
        return False
    # The scope alone is not a result. Empty result collections also need an
    # actual successful spatial outcome, rather than a synthetic zero.
    executed = ((structured.get('search_execution') or {}).get('status') in {'COMPLETED', 'SUCCESS', 'SUCCESS_EMPTY'}
                or structured.get('status') in {'SUCCESS', 'SUCCESS_EMPTY'})
    return bool(executed and final.get('map_layers'))


def requested_feature_groups(query: str) -> dict[str, set[str]]:
    # Independent object families must each have an executed target; selecting
    # one hazard type cannot satisfy a request for both aids and hazards.
    groups = {
        'lighthouse': (r'등대|\blighthouses?\b', {'Landmark', 'Building', 'LightAllAround', 'LightSectored', 'navigation_aid_busan'}),
        'wreck': (r'난파선|침선|\bwrecks?\b', {'Wreck'}),
        'anchorage': (r'정박지|묘박지|\banchorage(?:area)?s?\b', {'AnchorageArea', 'anchorage_area'}),
        'restricted': (r'제한\s*구역|\brestricted\s*areas?\b', {'RestrictedArea', 'RestrictedAreaNavigational', 'RestrictedAreaRegulatory', 'entry_restricted'}),
    }
    return {name: values for name, (pattern, values) in groups.items() if re.search(pattern, query, re.I)}


def missing_selected_feature(query: str, spatial_context: dict | None) -> bool:
    if 'selected_feature_evidence' not in required_outputs(query):
        return False
    selected = (spatial_context or {}).get('selected_feature') or {}
    return not isinstance(selected, dict) or not (selected.get('id') or (selected.get('properties') or {}).get('feature_id'))


def audit_outputs(query: str, final: dict) -> dict:
    """Downgrade an incomplete success; preserve failed/clarification states."""
    obligations = required_outputs(query)
    if not obligations:
        return final
    structured = final.get('structured_result') or {}
    def evidence(name):
        value = structured.get(name)
        return value if isinstance(value, dict) else {}
    # Each field is a contract-specific evidence object, not model free text.
    groups = requested_feature_groups(query)
    executed_targets = {str(row.get('target')) for row in structured.get('per_target_execution', [])
                        if isinstance(row, dict) and row.get('status') in {'SUCCESS', 'SUCCESS_EMPTY'}
                        and row.get('execution_receipt') and row.get('source_ref')}
    missing_groups = [name for name, candidates in groups.items() if not candidates.intersection(executed_targets)]
    checks = {
        'grounded_term_explanation': _has_grounded_term_explanation(query, final) if 'grounded_term_explanation' in obligations else False,
        'map_spatial_result': _has_executed_map_output(final) if 'map_spatial_result' in obligations else False,
        'all_requested_feature_groups': not missing_groups,
        'portrayal_rule_evidence': bool(evidence('portrayal_binding').get('rule_ref') or evidence('portrayal_rule_evidence').get('rule_ref')),
        'portrayal_symbol_binding': bool(evidence('portrayal_binding').get('rule_ref') and
                                        evidence('portrayal_binding').get('symbol_ref') and
                                        evidence('portrayal_binding').get('feature_id')),
        'selected_feature_evidence': bool(evidence('selected_feature_evidence').get('source_ref') and
                                          evidence('selected_feature_evidence').get('feature_id')),
        'data_processing_provenance': bool(evidence('processing_lineage').get('source_hash') and
                                           evidence('processing_lineage').get('steps')),
        'traffic_aggregation': bool(structured.get('monthly_breakdown') or structured.get('traffic_analysis')),
        'accident_evidence': bool(structured.get('analysis_type') in {'accident_event_lookup','accident_spatial_history_lookup'} or
                                   (final.get('evidence_bundle') or {}).get('accident_evidence')),
        'feature_attribute_explanation': bool(
            evidence('feature_attribute_explanation').get('source_ref') and
            evidence('feature_attribute_explanation').get('feature_type') and
            evidence('feature_attribute_explanation').get('attributes') and
            evidence('feature_attribute_explanation').get('explanation')),
    }
    report = [{'output': name, 'status': 'EVIDENCE_PRESENT_REVIEW_REQUIRED' if checks[name] else 'UNMET'} for name in obligations]
    final.setdefault('orchestrator_v2', {})['output_obligations'] = report
    missing = [r['output'] for r in report if r['status'] == 'UNMET']
    if missing and final.get('status') == 'COMPLETED':
        final['status'] = 'PARTIAL'
        final['error_code'] = 'OUTPUT_OBLIGATIONS_UNMET'
        final.setdefault('structured_result', {})['unmet_outputs'] = missing
        # Overall answer completeness is separate from a successful (possibly
        # empty) spatial execution. Preserve its original outcome for callers.
        if structured.get('status') in {'SUCCESS', 'SUCCESS_EMPTY'}:
            structured.setdefault('execution_result_status', structured['status'])
        final['structured_result']['status'] = 'PARTIAL'
        labels = {'grounded_term_explanation': '요청한 용어·속성과 출처가 연결된 설명 (관련 문서 검색만으로는 미충족)', 'map_spatial_result': '실제 공간 검색 결과와 지도 레이어', 'all_requested_feature_groups': '모든 요청 대상의 개별 공간 실행 결과 (' + ', '.join(missing_groups) + ')', 'portrayal_rule_evidence': '렌더링 규칙 원문 근거', 'portrayal_symbol_binding': '지도 객체와 심볼의 연결 근거',
                  'selected_feature_evidence': '선택한 지도 객체의 원천 정보',
                  'data_processing_provenance': '원천 자료의 좌표 변환·정제 이력',
                  'traffic_aggregation': '통항량 집계 결과', 'accident_evidence': '사고 분석 근거',
                  'feature_attribute_explanation': '조회한 객체의 속성 설명과 출처'}
        note = '요청한 결과에 필요한 근거가 아직 부족합니다: ' + ', '.join(labels[name] for name in missing)
        if ('feature_attribute_explanation' in missing and
                structured.get('execution_result_status') == 'SUCCESS_EMPTY' and
                structured.get('total_count') == 0):
            note += ('\n검색 결과가 없어 실제 객체의 속성값은 설명할 수 없습니다. '
                     'S-101에서 허용하는 속성의 설명은 별도 카탈로그 근거가 필요한 작업입니다.')
        final['answer_text'] = note + '\n' + str(final.get('answer_text') or '')
        final['summary'] = note
        plan = final['orchestrator_v2'].get('route_plan')
        if isinstance(plan, dict):
            plan['status'] = 'PARTIAL'
    return final
