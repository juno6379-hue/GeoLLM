import pytest
from services.orchestrator.catalogue_document import resolve_catalogue_document, build_catalogue_document_response
from services.orchestrator.execution_validator import is_execution_authorized, validate_lookup_request
from services.orchestrator.korean_query_analysis import contract_problem
from services.orchestrator.request_obligations import audit_outputs
from services.orchestrator.request_semantics import requires_execution
from services.orchestrator.query_normalizer import QueryNormalizer

@pytest.mark.parametrize('query', ['What is a wreck in S-101?', 'Which attributes describe a Wreck in S-101?', 'S-101에서 정박지는 어떤 객체야?'])
def test_source_bound_document(query):
    doc=resolve_catalogue_document(query)
    assert doc and doc['source_sha256'] and doc['evidence']['locators']
    qec=validate_lookup_request({'query':query}, 'public_catalogue_document_lookup')
    assert is_execution_authorized(qec)
    result=build_catalogue_document_response({'query':query,'task_id':'test'})
    assert result['final_dict']['structured_result']['document_answer']==doc
    assert result['final_dict']['structured_result']['search_execution']['status']=='NOT_RUN'

@pytest.mark.parametrize('query', ['Find Wreck within 5 km and explain attributes.', '비공개 Wreck 속성을 알려줘', 'What is DoesNotExist in S-101?'])
def test_no_document_substitution_or_unknown_authorization(query):
    assert resolve_catalogue_document(query) is None
    assert not is_execution_authorized(validate_lookup_request({'query':query}, 'public_catalogue_document_lookup'))

def test_no_partial_ascii_synonym_replacement():
    normalizer=QueryNormalizer.__new__(QueryNormalizer)
    normalizer.synonyms={'age':'재령'};normalizer.synonym_meta={};normalizer.compound_terms=set();normalizer.derived_concepts={}
    assert normalizer.normalize('AnchorageArea age')=='AnchorageArea 재령'

def test_intersection_never_becomes_document_or_radius():
    query='Find wrecks intersecting the selected area.'
    assert requires_execution(query)
    analysis={'constraints':[], 'slots':[]}
    assert contract_problem(query,analysis,{})['code']=='AOI_REQUIRED'
    assert contract_problem(query,analysis,{'geometry':'POLYGON ((0 0,1 0,1 1,0 0))'})['code']=='INTERSECTION_EXECUTION_NOT_SUPPORTED'

def test_missing_composite_target_downgrades_completion():
    final={'status':'COMPLETED','structured_result':{'target_features':['Wreck'],'status':'SUCCESS_EMPTY','total_count':0},'answer_text':'0'}
    result=audit_outputs('독도 주변 5km의 등대와 난파선을 찾아줘',final)
    assert result['status']=='PARTIAL'
    assert 'all_requested_feature_groups' in result['structured_result']['unmet_outputs']
    assert result['structured_result']['execution_result_status']=='SUCCESS_EMPTY'

def test_document_explanation_not_spatial_even_with_find_words():
    assert not requires_execution('S-101 등대의 색상 속성과 허용 값을 알려줘.')
    assert requires_execution('Wreck 주변 5km를 찾고 속성을 설명해줘')

@pytest.mark.parametrize('query', ['Wreck 속성과 좌표를 알려줘', 'Wreck 속성을 설명하고 지도에 표시해줘', 'Explain Wreck attributes and show it on the map', 'Wreck 위치와 속성을 알려줘'])
def test_mixed_execution_never_completed_as_document(query):
    assert requires_execution(query)
    assert resolve_catalogue_document(query) is None


def test_declared_targets_are_not_execution_proof():
    final={'status':'COMPLETED','structured_result':{'target_features':['Wreck','Landmark'],'status':'SUCCESS_EMPTY','total_count':0}}
    assert audit_outputs('Find wrecks and lighthouses within 5 km', final)['status']=='PARTIAL'


def test_operator_definition_is_not_execution():
    assert not requires_execution('within 연산자 정의를 알려줘')


def test_missing_source_fails_closed(monkeypatch,tmp_path):
    from services.orchestrator import catalogue_document
    monkeypatch.setattr(catalogue_document,'CATALOGUE',tmp_path/'missing.json')
    assert catalogue_document.resolve_catalogue_document('What is Wreck?') is None

@pytest.mark.parametrize('query', ['공간 연산자 within의 정의를 설명해줘.', 'Explain the within spatial predicate', 'What does intersects mean?'])
def test_operator_explanations_without_operands(query):
    assert not requires_execution(query)

@pytest.mark.parametrize('query', ['좌표계의 정의를 알려줘', 'What is a coordinate system?', '위치 정확도의 정의를 알려줘'])
def test_coordinate_terms_can_be_definition_subjects(query):
    assert not requires_execution(query)

@pytest.mark.parametrize('query', ['등대의 S-101 객체 유형과 정의를 알려줘.', '공간 연산자 within의 정의를 설명해줘.'])
def test_nonexact_document_dispatches_actual_rag(query):
    import ast
    from pathlib import Path
    from types import SimpleNamespace
    import re
    tree=ast.parse(Path('services/orchestrator/graph.py').read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_intent_parsed')
    env={'re':re, 'AgentStatus':SimpleNamespace(NEEDS_CLARIFICATION='NEEDS_CLARIFICATION'),
         '_looks_like_policy_block_query':lambda q:False,
         '_looks_like_definition_question':lambda q:False,
         '_exact_s101_feature_match':lambda q:None,
         '_exact_s100_s101_relation_match':lambda q:None,
         'OrchestratorState':dict}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<dispatch-test>','exec'),env)
    assert env['check_intent_parsed']({'query':query,'status':'INTENT_PARSED'})=='create_plan'


def test_exact_document_failure_preserves_structured_scoped_response():
    from services.orchestrator.catalogue_document import exact_document_unmatched
    result=exact_document_unmatched({'query':'unresolved standard','task_id':'test'})
    assert result['status']=='BLOCKED'
    assert result['final_dict']['error_code']=='EXACT_DOCUMENT_BINDING_UNAVAILABLE'
    structured=result['final_dict']['structured_result']
    assert structured['full_corpus_searched'] is False
    assert structured['search_execution']['status']=='NOT_RUN'
    assert not structured['citations']
