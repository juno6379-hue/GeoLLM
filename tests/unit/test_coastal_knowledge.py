from scripts.build_coastal_knowledge import parts, build_graph
from services.orchestrator.coastal_knowledge import query_terms, retrieve
from services.orchestrator.coastal_knowledge import validate_quotes


def test_relative_expression_not_resolved_to_coordinates():
    assert query_terms('부산항 입구로 이동') == ['부산항']
    assert query_terms('다대포항 항해 정보를 알려줘') == ['다대포항']
    assert query_terms('울릉도 주변 항만 정보') == ['울릉도']
    assert query_terms('없는항구XYZ123 항만 안내') == ['없는항구XYZ123']
    assert query_terms('수로 항로 북극항로 정보를 찾아줘') == ['수로','항로','북극항로']


def test_chunking_retains_full_text():
    value = '해양안내' * 700
    chunks = list(parts(value))
    assert chunks[0][0] == 0
    assert all(text == value[offset:offset + 1100] for offset, text in chunks)
    assert chunks[-1][0] + len(chunks[-1][1]) == len(value)


def test_blocked_gate_does_not_query_database(monkeypatch):
    from types import SimpleNamespace
    from services.orchestrator import coastal_knowledge as module
    monkeypatch.setattr(module, 'validate_lookup_request', lambda *a: SimpleNamespace(provenance={},blockers=['missing source']))
    monkeypatch.setattr(module, 'is_execution_authorized', lambda qec: False)
    monkeypatch.setattr(module, 'engine', lambda: (_ for _ in ()).throw(AssertionError('must not query')))
    assert retrieve('부산항')['status'] == 'BLOCKED'


def test_model_cannot_invent_or_cite_unretrieved_facts():
    doc = dict(chunk_id='a',content='오륙도는 부산항 입구 동쪽에 위치한다고 문서에 서술되어 있습니다.',title='항로지',page_no=6,section='page6',source_id='source')
    accepted,rejected = validate_quotes([{'chunk_id':'a','quote':doc['content']},
        {'chunk_id':'a','quote':'부산항 입구의 정확한 좌표는 임의로 생성한 값입니다.'},
        {'chunk_id':'other','quote':doc['content']}],[doc])
    assert len(accepted)==1 and len(rejected)==2


def test_spatial_timeout_retains_successful_document_evidence(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    from sqlalchemy.exc import OperationalError
    from services.orchestrator import coastal_knowledge as module
    qec=SimpleNamespace(provenance={'execution_validation':{'authority':'ExecutionValidator'}},blockers=[])
    monkeypatch.setattr(module,'validate_lookup_request',lambda *a:qec)
    monkeypatch.setattr(module,'is_execution_authorized',lambda q:True)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    doc=dict(chunk_id='c',source_id='s',source_sha256='a'*64,title='계획',page_no=1,section='page:1',content='해양공간관리계획 원문',metadata={})
    def result(value):
        return SimpleNamespace(mappings=lambda:SimpleNamespace(all=lambda:value,one=lambda:value))
    first,second=MagicMock(),MagicMock()
    first.__enter__.return_value.execute.side_effect=[None,result([doc]),result([]),result({'total':1,'embedded':0})]
    second.__enter__.return_value.execute.side_effect=OperationalError('select',{},Exception('timeout'))
    db=MagicMock();db.begin.side_effect=[first,second]
    monkeypatch.setattr(module,'engine',lambda:db)
    observed=retrieve('해양공간관리계획',scope='dataset')
    assert observed['status']=='PARTIAL'
    assert len(observed['documents']) == 1
    assert {k:observed['documents'][0][k] for k in doc} == doc
    assert observed['documents'][0]['source_text_verification']['coordinate_authority'] is False
    assert observed['document_lookup_status']=='COMPLETED'
    assert observed['spatial_lookup_status']=='UNAVAILABLE'
    assert observed['coordinate_authority'] is False


def test_document_source_failure_is_not_a_successful_empty_search(monkeypatch):
    from sqlalchemy.exc import OperationalError
    from services.orchestrator import coastal_knowledge as module
    def fail(*args,**kwargs):raise OperationalError('select',{},Exception('unavailable'))
    monkeypatch.setattr(module,'retrieve',fail)
    result=module.dataset_evidence('양식장',semantic=True)
    assert result['status']=='UNAVAILABLE'
    assert result['document_lookup_status']=='UNAVAILABLE'
    assert result['error_code']=='DOCUMENT_SOURCE_UNAVAILABLE'
