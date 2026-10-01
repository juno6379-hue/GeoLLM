"""Describe observed processing facts without treating plans or model scores as execution."""


def build_processing_steps(result):
    def mapping(value):
        return value if isinstance(value, dict) else {}
    structured = mapping(result.get('structured_result'))
    orch = mapping(result.get('orchestrator_v2'))
    qec = mapping(orch.get('query_execution_context') or result.get('query_execution_context'))
    plan = mapping(orch.get('route_plan') or qec.get('route_plan'))
    slots = mapping(qec.get('slots') or plan.get('slots'))
    trace = mapping(orch.get('candidate_trace'))
    interpretation = mapping(structured.get('query_interpretation'))
    receipt = mapping(mapping(qec.get('provenance')).get('execution_validation') or plan.get('execution_validation'))
    status = result.get('status') or 'UNKNOWN'
    query = structured.get('original_query') or qec.get('original_query') or trace.get('query')
    normalized = qec.get('normalized_query') or trace.get('normalized_query') or mapping(structured.get('normalization')).get('normalized_query')
    location = interpretation.get('location_text') or slots.get('location_text') or structured.get('location_text')
    geometry = slots.get('reference_geometry') or structured.get('reference_geometry') or structured.get('geometry')
    distance = slots.get('distance_m') if slots.get('distance_m') is not None else structured.get('distance_m')
    evidence = mapping(result.get('evidence_bundle'))
    counts = {key: len(value) for key, value in evidence.items() if isinstance(value, list) and value}
    search = mapping(structured.get('search_execution'))
    calls = result.get('tool_calls') or []
    operation = plan.get('analysis_type') or structured.get('analysis_type')
    approved = receipt.get('authority') == 'ExecutionValidator' and receipt.get('readiness') == 'EXECUTION_READY'
    stopped = search.get('status') == 'NOT_RUN' or status in {'BLOCKED', 'NEEDS_CLARIFICATION'}
    execution_text = '검색/분석을 실행하지 않았습니다.' if search.get('status') == 'NOT_RUN' else (
        '실행 완료 기록이 있습니다.' if search.get('status') == 'COMPLETED' else
        f'도구 호출 기록 {len(calls)}개. 호출 기록은 성공 보증이 아닙니다.' if calls else
        '도구 실행 완료 기록이 없습니다. 계획이나 비교 점수를 실행 성공으로 보지 않습니다.')
    return [
        {'step': '질의 해석', 'status': 'RECORDED' if query or normalized or operation else 'UNRECORDED',
         'detail': ' / '.join(str(x) for x in [f'입력: {query}' if query else None,
                   f'정규화: {normalized}' if normalized else None, f'처리 유형: {operation}' if operation else None] if x) or '해석 기록이 없습니다.'},
        {'step': '위치·조건 확인', 'status': 'RECORDED' if location or geometry or distance is not None else 'UNRECORDED',
         'detail': f"기준 지명: {location or '기록 없음'} / 기준 좌표: {'확인 기록 있음' if geometry else '확인 기록 없음'} / 반경: {str(distance) + 'm' if distance is not None else '미지정 또는 해당 없음'}"},
        {'step': '실행 승인', 'status': 'APPROVED' if approved else 'NOT_APPROVED',
         'detail': f"ExecutionValidator: {receipt.get('readiness') or qec.get('readiness') or '승인 기록 없음'}" +
                   (' / ' + '; '.join(str(x) for x in qec.get('blockers') or []) if qec.get('blockers') else '')},
        {'step': '도구 실행', 'status': 'NOT_RUN' if search.get('status') == 'NOT_RUN' else 'RECORDED' if calls or search.get('status') == 'COMPLETED' else 'UNRECORDED', 'detail': execution_text},
        {'step': '결과 근거', 'status': 'RECORDED' if counts else 'UNRECORDED',
         'detail': ' / '.join(f'{key}: {value}건' for key, value in counts.items()) or '반환된 근거 묶음이 없습니다. 근거 없음과 검색 결과 0건은 다릅니다.'},
        {'step': '결과·다음 입력', 'status': status,
         'detail': result.get('answer_text') or result.get('summary') or ('추가 조건 또는 원천 확인이 필요합니다.' if stopped else '결과 설명 기록이 없습니다.')},
    ]
