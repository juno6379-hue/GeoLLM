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
    }
    report = [{'output': name, 'status': 'EVIDENCE_PRESENT_REVIEW_REQUIRED' if checks[name] else 'UNMET'} for name in obligations]
    final.setdefault('orchestrator_v2', {})['output_obligations'] = report
    missing = [r['output'] for r in report if r['status'] == 'UNMET']
    if missing and final.get('status') == 'COMPLETED':
        final['status'] = 'PARTIAL'
        final['error_code'] = 'OUTPUT_OBLIGATIONS_UNMET'
        final.setdefault('structured_result', {})['unmet_outputs'] = missing
        final['structured_result']['status'] = 'PARTIAL'
        labels = {'portrayal_rule_evidence': '렌더링 규칙 원문 근거', 'portrayal_symbol_binding': '지도 객체와 심볼의 연결 근거',
                  'selected_feature_evidence': '선택한 지도 객체의 원천 정보',
                  'data_processing_provenance': '원천 자료의 좌표 변환·정제 이력',
                  'traffic_aggregation': '통항량 집계 결과', 'accident_evidence': '사고 분석 근거'}
        note = '요청한 결과에 필요한 근거가 아직 부족합니다: ' + ', '.join(labels[name] for name in missing)
        final['answer_text'] = note + '\n' + str(final.get('answer_text') or '')
        final['summary'] = note
        plan = final['orchestrator_v2'].get('route_plan')
        if isinstance(plan, dict):
            plan['status'] = 'PARTIAL'
    return final
