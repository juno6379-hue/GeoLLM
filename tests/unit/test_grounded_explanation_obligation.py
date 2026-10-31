import pytest
from services.orchestrator.request_obligations import audit_outputs, required_outputs
from services.orchestrator.catalogue_document import build_catalogue_document_response


@pytest.mark.parametrize('query', ['What is a wreck in S-101?', 'Which attributes describe a Wreck in S-101?', 'S-101에서 정박지는 어떤 객체야?'])
def test_actual_source_bound_catalogue_explanation_stays_completed(query):
    final=build_catalogue_document_response({'task_id':'explanation-contract','query':query})['final_dict']
    assert audit_outputs(query,final)['status']=='COMPLETED'


def test_related_excerpt_is_not_a_definition_of_requested_subject():
    query='등대의 S-101 객체 유형과 정의를 알려줘.'
    final={'status':'COMPLETED','summary':'Light vessel excerpt',
           'structured_result':{'retrieved_count':1,'documents':[{'title':'Light Vessel','excerpt_reference':'A vessel equipped with a light.'}]}}
    result=audit_outputs(query,final)
    assert result['status']=='PARTIAL'
    assert 'grounded_term_explanation' in result['structured_result']['unmet_outputs']


def test_zero_documents_cannot_complete_operator_definition():
    final={'status':'COMPLETED','summary':'관련 문서를 찾지 못했습니다.',
           'structured_result':{'retrieved_count':0,'documents':[]}}
    result=audit_outputs('공간 연산자 within의 정의를 설명해줘.',final)
    assert result['status']=='PARTIAL'
    assert result['error_code']=='OUTPUT_OBLIGATIONS_UNMET'


@pytest.mark.parametrize('query', ['Wreck 정의 관련 문서를 찾아줘.', 'Find documents about the definition of Wreck.'])
def test_pure_document_retrieval_does_not_require_explanation(query):
    assert 'grounded_term_explanation' not in required_outputs(query)
    final={'status':'COMPLETED','structured_result':{'documents':[{'title':'Wreck'}]}}
    assert audit_outputs(query,final)['status']=='COMPLETED'


def test_modified_subject_definition_is_not_verified_by_a_receipt_alone():
    query='What is a wreck in S-101?'
    final=build_catalogue_document_response({'task_id':'explanation-negative','query':query})['final_dict']
    final['structured_result']['document_answer']['features'][0]['definition']='A made up definition.'
    assert audit_outputs(query,final)['status']=='PARTIAL'

@pytest.mark.parametrize('query', ['조석예보의 정의를 알려줘', 'Wreck 정의를 알려줘'])
def test_existing_verified_dictionary_definition_stays_completed(query):
    from services.orchestrator.definition_response import build_definition_response
    final=build_definition_response({'task_id':'legacy-definition','query':query})['final_dict']
    assert audit_outputs(query,final)['status']=='COMPLETED'


@pytest.mark.parametrize('query', ['제한구역의 제한 종류는 어떤 코드로 표현해?', 'Explain the restriction attribute codes of S-101 RestrictedArea.'])
def test_existing_public_attribute_codes_stay_completed(query):
    from services.orchestrator.public_catalogue_attribute import build_public_catalogue_attribute_response
    final=build_public_catalogue_attribute_response({'task_id':'existing-attribute','query':query})['final_dict']
    assert len(final['structured_result']['allowed_values'])==29
    assert audit_outputs(query,final)['status']=='COMPLETED'

def test_nearest_spatial_question_is_not_a_definition_obligation():
    query='What is the nearest lighthouse to Dokdo?'
    assert 'grounded_term_explanation' not in required_outputs(query)
    final={'status':'COMPLETED','structured_result':{'status':'SUCCESS','features':[{'id':'actual-result'}]}}
    assert audit_outputs(query,final)['status']=='COMPLETED'
