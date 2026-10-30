"""Output obligations are independent of the selected route name."""
from __future__ import annotations

import re


def required_outputs(query: str) -> list[str]:
    text = str(query or '').casefold()
    outputs = []
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
    if lookup and attribute_explanation and not negated_explanation:
        outputs.append('feature_attribute_explanation')
    return outputs


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
    checks = {
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
        labels = {'portrayal_rule_evidence': '렌더링 규칙 원문 근거', 'portrayal_symbol_binding': '지도 객체와 심볼의 연결 근거',
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
