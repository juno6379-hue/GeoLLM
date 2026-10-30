import pytest
from services.orchestrator.request_obligations import audit_outputs, required_outputs


@pytest.mark.parametrize('query', [
    'Find wrecks within 5 km of Dokdo and explain their S-101 attributes.',
    '독도 주변 5km의 침선을 찾고 S-101 속성을 설명해줘.',
    'Retrieve buoys and describe their attributes.',
    "Find wrecks and explain their attributes; do not explain coordinates.",
])
def test_lookup_and_explanation_are_separate_outputs(query):
    assert 'feature_attribute_explanation' in required_outputs(query)


@pytest.mark.parametrize('query', [
    'Find wrecks within 5 km of Dokdo.', '침선의 수심 속성이 10m 미만인 객체를 찾아줘.',
    'Which attributes describe a Wreck in S-101?',
    "Find wrecks but do not explain their attributes.", '침선을 찾고 속성 설명은 생략해줘.',
])
def test_search_filter_definition_or_negated_explanation_is_not_composite(query):
    assert 'feature_attribute_explanation' not in required_outputs(query)


def final(status='COMPLETED', count=0):
    return {'status':status, 'summary':'공간 검색 완료', 'structured_result':{
        'status':'SUCCESS_EMPTY' if count == 0 else 'SUCCESS', 'total_count':count}}


def test_empty_spatial_success_is_preserved_but_missing_explanation_is_partial():
    result = audit_outputs('Find wrecks and explain their attributes.', final())
    assert result['status'] == 'PARTIAL'
    assert result['structured_result']['execution_result_status'] == 'SUCCESS_EMPTY'
    assert result['structured_result']['total_count'] == 0
    assert '실제 객체의 속성값' in result['summary'] and '별도 카탈로그 근거' in result['summary']


def test_uncited_free_text_does_not_satisfy_attribute_obligation():
    payload = final(count=1)
    payload['structured_result']['feature_attribute_explanation'] = {
        'feature_type':'Wreck', 'attributes':['categoryOfWreck'], 'explanation':'분류 속성입니다.'}
    assert audit_outputs('Find wrecks and describe their attributes.', payload)['status'] == 'PARTIAL'


def test_structured_cited_explanation_is_present_but_still_requires_review():
    payload = final(count=1)
    payload['structured_result']['feature_attribute_explanation'] = {
        'source_ref':'fixture:catalogue/Wreck', 'feature_type':'Wreck',
        'attributes':[{'name':'categoryOfWreck', 'definition':'fixture'}], 'explanation':'근거가 연결된 설명'}
    result = audit_outputs('Find wrecks and describe their attributes.', payload)
    assert result['status'] == 'COMPLETED'
    assert result['orchestrator_v2']['output_obligations'][0]['status'] == 'EVIDENCE_PRESENT_REVIEW_REQUIRED'


def test_existing_block_is_not_changed_to_partial():
    assert audit_outputs('Find wrecks and explain their attributes.', final('BLOCKED'))['status'] == 'BLOCKED'
