from scripts.build_coastal_knowledge import parts, build_graph
from services.orchestrator.coastal_knowledge import query_terms, retrieve
from services.orchestrator.coastal_knowledge import validate_quotes


def test_relative_expression_not_resolved_to_coordinates():
    assert query_terms('부산항 입구로 이동') == ['부산항']
    assert query_terms('다대포항 항해 정보를 알려줘') == ['다대포항']
    assert query_terms('울릉도 주변 항만 정보') == ['울릉도']
    assert query_terms('없는항구XYZ123 항만 안내') == ['없는항구XYZ123']


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
