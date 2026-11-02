from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from services.orchestrator import dataset_answer as answer
from services.orchestrator import coastal_knowledge as coastal
from services.orchestrator.execution_validator import validate_lookup_request, is_execution_authorized


@pytest.mark.parametrize('query', [
    '부산항 입구 정보를 알려줘', '다대포항 소형선항만 안내정보를 알려줘',
    '해양공간관리계획을 설명해줘', '양식장 관련 정보를 알려줘', '수로 관련 정보를 알려줘',
    '없는자료XYZ987654에 관한 자료를 찾아줘',
])
def test_information_shape_is_not_location_execution(query):
    assert answer.informational_request(query)


@pytest.mark.parametrize('query', [
    '부산항 입구로 이동', '부산항 입구 정보를 알려주고 지도로 이동해줘',
    '다대포항 3km 이내 양식장 정보를 알려줘', '수로 위치를 알려줘',
    '양식장 정보를 지도에 표시해줘', '선택한 객체의 정보를 알려줘',
    '부산항 현재 파고 정보를 알려줘', '비공개 항만 정보를 알려줘',
    'S-101 등대의 정의를 알려줘', '최근 사고 자료를 분석해줘',
    '이 수로의 정보를 알려줘', '부산항과 인천항 통항량을 비교해줘',
])
def test_information_route_cannot_erase_other_obligations(query):
    assert not answer.informational_request(query)


def qec(query):
    columns = {'chunk_id','source_id','source_sha256','source_file','metadata','content','embedding',
               'document_type','title','page_no','section'}
    adapter = SimpleNamespace(_inspect_relation=lambda rel: {'exists':True,'has_select':True,
        'columns':[{'name':x} for x in columns]})
    return validate_lookup_request({'query':query,'task_id':'t'},'dataset_document_lookup',binding_adapter=adapter)


def evidence(query, content='다대포항은 소형선항만 안내에 기록된 항만입니다. 원문은 당시 자료의 설명입니다.'):
    return {'status':'COMPLETED','document_lookup_status':'COMPLETED','query_execution_context':qec(query).model_dump(mode='json'),
            'documents':[{'chunk_id':'c','source_id':'s','source_sha256':'a'*64,'title':'다대포항 안내',
             'source_file':'Dataset/guide.pdf','document_type':'small_harbour_guide','page_no':12,
             'section':'page12','metadata':{'edition':'2022'},'content':content}]}


def test_actual_answer_contains_verified_passage_and_source_without_map_claim(monkeypatch):
    query='다대포항 소형선항만 안내정보를 알려줘'
    source=evidence(query)
    captured=[]
    def retrieve(*args,**kwargs): captured.append(kwargs);return source
    monkeypatch.setattr(answer,'retrieve',retrieve)
    result=answer.build_dataset_answer({'query':query,'task_id':'t'})
    final=result['final_dict']; passage=final['structured_result']['source_passages'][0]
    assert passage['quote'] in source['documents'][0]['content']
    assert passage['quote'] in final['summary'] == final['answer_text']
    assert final['rag_evidence'][0]['source_sha256']=='a'*64
    assert final['rag_evidence'][0]['edition']=='2022'
    assert final['rag_evidence'][0]['page_no']==12
    assert final['status']=='PARTIAL' and final['clarification_questions']==[]
    assert final['structured_result']['search_execution']['status']=='NOT_RUN'
    assert final['structured_result']['coordinate_authority'] is False
    assert captured[0]['include_spatial'] is False
    assert is_execution_authorized(qec(query))


def test_invalid_source_or_target_cannot_be_laundered_into_answer(monkeypatch):
    query='없는자료XYZ987654에 관한 자료를 찾아줘'
    source=evidence(query)
    monkeypatch.setattr(answer,'retrieve',lambda *a,**k:source)
    final=answer.build_dataset_answer({'query':query})['final_dict']
    assert final['status']=='BLOCKED'
    assert not final['rag_evidence']
    assert '다대포항' not in final['summary']
    assert '0건' not in final['summary']  # source matched rows rejected, not corpus absence


def test_authority_receipt_cannot_be_reused_for_changed_query(monkeypatch):
    query='다대포항 안내정보를 알려줘';source=evidence(query)
    source['query_execution_context']['original_query']='변경된 질의'
    monkeypatch.setattr(answer,'retrieve',lambda *a,**k:source)
    final=answer.build_dataset_answer({'query':query})['final_dict']
    assert final['status']=='BLOCKED' and not final['rag_evidence']


def test_source_outage_not_zero_matches(monkeypatch):
    def fail(*a,**k):raise RuntimeError('source offline')
    monkeypatch.setattr(answer,'retrieve',fail)
    final=answer.build_dataset_answer({'query':'다대포항 안내정보를 알려줘'})['final_dict']
    assert final['error_code']=='DATASET_DOCUMENT_SOURCE_UNAVAILABLE'
    assert '0건이라는 뜻은 아니며' in final['summary']


def test_normalized_negative_does_not_search_generic_function_words():
    assert coastal.query_terms('없는자료XYZ987654에 관한 자료를 찾아줘')==['없는자료XYZ987654']
    assert coastal.query_terms('양식장에 대한 정보를 알려줘')==['양식장']
    assert coastal.query_terms('수로 관련 정보를 알려줘')==['수로']


def test_document_only_lookup_requires_all_topics_and_does_not_query_spatial(monkeypatch,tmp_path):
    query='다대포항 양식장 관련 정보를 알려줘'
    monkeypatch.setattr(coastal,'validate_lookup_request',lambda *a:qec(query))
    monkeypatch.setattr(coastal,'ROOT',tmp_path)
    def rows(value):return SimpleNamespace(mappings=lambda:SimpleNamespace(all=lambda:value,one=lambda:value))
    connection=MagicMock();connection.execute.side_effect=[None,rows([]),rows({'total':1,'embedded':1})]
    context=MagicMock();context.__enter__.return_value=connection
    db=MagicMock();db.begin.return_value=context;monkeypatch.setattr(coastal,'engine',lambda:db)
    result=coastal.retrieve(query,scope='dataset',include_spatial=False,request_state={'query':query})
    statements=[str(x.args[0]) for x in connection.execute.call_args_list]
    assert len(statements)==3
    assert '(content ILIKE :t0 OR title ILIKE :t0) AND (content ILIKE :t1 OR title ILIKE :t1)' in statements[1]
    assert not any('serving.' in sql for sql in statements)
    assert result['spatial_lookup_status']=='NOT_REQUESTED'


def test_information_request_does_not_take_instant_map_shortcut(monkeypatch):
    import requests
    monkeypatch.setenv('DISABLE_LLM_API','true')
    monkeypatch.setattr(requests.sessions.Session,'request',MagicMock(side_effect=AssertionError('No network in unit tests')))
    from services.orchestrator.router import _is_instant_place_navigation
    assert not _is_instant_place_navigation('없는자료XYZ987654에 관한 자료를 찾아줘')
    assert not _is_instant_place_navigation('부산항 입구 정보를 알려줘')


@pytest.mark.asyncio
async def test_graph_routes_source_answer_before_place_clarification(monkeypatch):
    import requests
    monkeypatch.setenv('DISABLE_LLM_API','true')
    monkeypatch.setattr(requests.sessions.Session,'request',MagicMock(side_effect=AssertionError('No network in unit tests')))
    from services.orchestrator import graph
    from services.orchestrator import korean_query_analysis, semantic_slot_binding, public_catalogue_attribute, catalogue_document
    query='다대포항 소형선항만 안내정보를 알려줘'
    monkeypatch.setattr(korean_query_analysis,'analyze_query',lambda q:{'slots':[],'constraints':[]})
    monkeypatch.setattr(graph.normalizer,'normalize_with_debug',lambda q:{'normalized_query':q,'matched_rules':[],'canonical_terms':[],'candidate_contexts':[]})
    monkeypatch.setattr(graph.query_candidate_broker,'build_trace',lambda *a,**k:{'capability_candidates':[]})
    monkeypatch.setattr(semantic_slot_binding,'bind_semantic_slots',lambda *a:{})
    monkeypatch.setattr(public_catalogue_attribute,'build_public_catalogue_attribute_response',lambda s:None)
    monkeypatch.setattr(catalogue_document,'build_catalogue_document_response',lambda s:None)
    monkeypatch.setattr(answer,'retrieve',lambda *a,**k:evidence(query))
    state={'query':query,'task_id':'t','status':'RECEIVED'}
    result=await graph.parse_intent_node(state)
    assert result['dataset_information_handled'] is True
    assert graph.check_intent_parsed(result)=='query_contract_stop'
    assert result['final_dict']['structured_result']['source_passages']
    assert result['final_dict']['summary']==result['final_dict']['answer_text']


@pytest.mark.parametrize('status,phrase', [('VERIFIED_DERIVED_FIELDS','감사 시점 원천 필드와 대조'),('INCOMPLETE_DERIVED_FIELDS','일부 원천 필드')])
def test_derived_source_disclosure_reaches_answer_without_literal_promotion(monkeypatch,status,phrase):
    import hashlib
    query='다대포항 소형선항만 안내정보를 알려줘'
    source=evidence(query)
    row={'chunk_id':'c','content_sha256':hashlib.sha256(source['documents'][0]['content'].encode()).hexdigest(),'source_sha256':'a'*64,'status':'UNVERIFIED','derived_field_verification':{'status':status,'evidence_sha256':'b'*64}}
    monkeypatch.setattr(answer,'retrieve',lambda *a,**k:source)
    monkeypatch.setattr(answer,'load_receipts',lambda:({'c':row},{}))
    final=answer.build_dataset_answer({'query':query,'task_id':'t'})['final_dict']
    assert phrase in final['answer_text']
    assert '확인 0건, 미검증 1건' in final['answer_text']
    assert final['structured_result']['coordinate_authority'] is False
