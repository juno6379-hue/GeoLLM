from services.orchestrator.processing_explanation import build_processing_steps


def test_candidate_ready_and_qwen_scores_do_not_become_execution_approval():
    steps = build_processing_steps({'status': 'NEEDS_CLARIFICATION', 'summary': '위치를 확인해 주세요',
        'structured_result': {'query_interpretation': {'location_text': '울릉도'},
                              'search_execution': {'status': 'NOT_RUN'}},
        'orchestrator_v2': {'execution_contract': {'status': 'ready'},
                           'candidate_trace': {'query': '울릉도 주변 지명', 'rankings': {'ollama': {}}}}})
    assert len(steps) == 6
    assert steps[2]['status'] == 'NOT_APPROVED'
    assert steps[3]['status'] == 'NOT_RUN'
    assert steps[5]['detail'] == '위치를 확인해 주세요'
    assert '울릉도' in steps[1]['detail']


def test_positive_execution_uses_receipt_and_actual_evidence():
    steps = build_processing_steps({'status': 'COMPLETED', 'summary': '5건',
        'structured_result': {'search_execution': {'status': 'COMPLETED'}},
        'evidence_bundle': {'spatial_feature_evidence': [{'id': 'a'}]},
        'orchestrator_v2': {'query_execution_context': {'provenance': {'execution_validation': {
            'authority': 'ExecutionValidator', 'readiness': 'EXECUTION_READY'}}}}})
    assert steps[2]['status'] == 'APPROVED'
    assert steps[3]['status'] == 'RECORDED'
    assert '1건' in steps[4]['detail']


def test_success_status_alone_does_not_invent_tool_execution():
    steps = build_processing_steps({'status': 'COMPLETED', 'summary': '정의'})
    assert steps[3]['status'] == 'UNRECORDED'
    assert steps[4]['status'] == 'UNRECORDED'
