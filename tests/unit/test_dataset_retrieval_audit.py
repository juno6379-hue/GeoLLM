import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from services.orchestrator import dataset_verification as audit


def bad_receipt():
    return ({'bad': dict(content_sha256=hashlib.sha256(b'wrong').hexdigest(), source_sha256='a'*64,
                        status='MISMATCH')}, {})


def test_filter_does_not_blacklist_corrected_chunk_or_mutate_raw():
    raw = dict(doc_id='bad', content='wrong', source_sha256='a'*64)
    accepted, excluded = audit.filter_answer_documents([raw], bad_receipt())
    assert accepted == [] and excluded[0]['chunk_id'] == 'bad'
    assert 'content' not in excluded[0] and 'source_text_verification' not in raw
    assert audit.filter_answer_documents([{**raw, 'content':'corrected'}], bad_receipt())[0]


def test_current_superseded_is_excluded_but_historical_retirement_is_not_current_authority():
    raw=dict(chunk_id='new',content='body',source_sha256='a'*64,metadata={'retrieval_status':'SUPERSEDED'})
    accepted,excluded=audit.filter_answer_documents([raw], ({},{}))
    assert not accepted
    assert excluded[0]['chunk_id']=='new'
    assert excluded[0]['source_text_verification']['status']=='CURRENT_CHUNK_SUPERSEDED'
    assert 'content' not in excluded[0]
    historical={'new':dict(content_sha256=hashlib.sha256(b'body').hexdigest(),source_sha256='a'*64,
                           retrieval_status='SUPERSEDED',status='UNVERIFIED')}
    restored={**raw,'metadata':{'retrieval_status':'ACTIVE'}}
    accepted,excluded=audit.filter_answer_documents([restored], (historical,{}))
    assert not excluded and accepted[0]['source_text_verification']['status']=='UNVERIFIED'
    assert accepted[0]['source_text_verification']['audit_retrieval_status']=='SUPERSEDED'


def test_direct_dataset_passage_path_cannot_use_current_superseded(monkeypatch):
    from services.orchestrator import dataset_answer as answer
    from tests.unit.test_dataset_answer import evidence
    query='다대포항 안내정보를 알려줘'
    source=evidence(query)
    source['documents'][0]['metadata']['retrieval_status']='SUPERSEDED'
    assert answer._source_passages(query,source)==[]
    monkeypatch.setattr(answer,'retrieve',lambda *a,**k:source)
    final=answer.build_dataset_answer({'query':query,'task_id':'t'})['final_dict']
    assert final['error_code']=='DATASET_SUPERSEDED_EVIDENCE_EXCLUDED'
    assert final['structured_result']['source_text_audit']['excluded_superseded_chunks']==1
    assert final['structured_result']['source_text_audit']['excluded_mismatch_chunks']==0
    assert not final['structured_result']['citations']


@pytest.mark.parametrize('fallback', [False, True])
def test_vector_retrieval_never_returns_exact_audit_mismatch(monkeypatch, fallback):
    from services.standard_rag_agent import vdb
    monkeypatch.delenv('S101_DB_URL', raising=False)
    monkeypatch.setattr(vdb.db_module, 'init_engines', lambda: None)
    monkeypatch.setattr(vdb, 'llm_api_enabled', lambda: True)
    monkeypatch.setattr(vdb, '_query_embedding', lambda q:[0.1])
    monkeypatch.setattr(vdb, 'load_receipts', bad_receipt)
    def result(rows):return SimpleNamespace(mappings=lambda:SimpleNamespace(all=lambda:rows))
    row = dict(doc_id='bad', content='wrong', source_sha256='a'*64, similarity=0.9)
    database=MagicMock()
    database.execute.side_effect=[None,result([row]),result([row])] if fallback else [None,result([row])]
    context=MagicMock();context.__enter__.return_value=database
    monkeypatch.setattr(vdb.db_module,'PostgisSessionLocal',lambda:context)
    assert vdb.search_vdb('query', rag_filters={'candidate_document_ids':['bad']} if fallback else {}) == []
    queries=[str(c.args[0]) for c in database.execute.call_args_list][1:]
    assert len(queries) == (2 if fallback else 1)
    assert all("COALESCE(metadata->>'retrieval_status','ACTIVE') <> 'SUPERSEDED'" in q for q in queries)


@pytest.mark.parametrize('fallback', [False, True])
def test_vector_overfetch_preserves_valid_candidate_after_mismatch(monkeypatch, fallback):
    from services.standard_rag_agent import vdb
    monkeypatch.delenv('S101_DB_URL', raising=False)
    monkeypatch.setattr(vdb.db_module,'init_engines',lambda:None)
    monkeypatch.setattr(vdb,'llm_api_enabled',lambda:True)
    monkeypatch.setattr(vdb,'_query_embedding',lambda q:[0.1])
    monkeypatch.setattr(vdb,'load_receipts',bad_receipt)
    bad=dict(doc_id='bad',content='wrong',source_sha256='a'*64,similarity=0.9)
    good=dict(doc_id='good',content='valid',source_sha256='b'*64,similarity=0.8)
    def result(rows):return SimpleNamespace(mappings=lambda:SimpleNamespace(all=lambda:rows))
    db=MagicMock();db.execute.side_effect=[None,result([bad]),result([bad,good])] if fallback else [None,result([bad,good])]
    context=MagicMock();context.__enter__.return_value=db
    monkeypatch.setattr(vdb.db_module,'PostgisSessionLocal',lambda:context)
    rows=vdb.search_vdb('query',top_k=1,rag_filters={'candidate_document_ids':['bad','good']})
    assert [r['doc_id'] for r in rows]==['good']
    assert all(call.args[1]['top_k']==2 for call in db.execute.call_args_list[1:])


def test_coastal_retrieval_filters_before_citation_and_preserves_diagnostics(monkeypatch,tmp_path):
    from services.orchestrator import coastal_knowledge as coastal
    from tests.unit.test_dataset_answer import qec
    query='다대포항 안내정보를 알려줘'
    monkeypatch.setattr(coastal,'validate_lookup_request',lambda *a:qec(query))
    monkeypatch.setattr(coastal,'ROOT',tmp_path)
    monkeypatch.setattr(audit,'load_receipts',bad_receipt)
    doc=dict(chunk_id='bad',content='wrong',source_sha256='a'*64,source_id='s',page_no=1,section='p1')
    def result(rows):return SimpleNamespace(mappings=lambda:SimpleNamespace(all=lambda:rows,one=lambda:rows))
    db=MagicMock();db.execute.side_effect=[None,result([doc]),result({'total':1,'embedded':1})]
    context=MagicMock();context.__enter__.return_value=db
    engine=MagicMock();engine.begin.return_value=context
    monkeypatch.setattr(coastal,'engine',lambda:engine)
    output=coastal.retrieve(query,scope='dataset',include_spatial=False)
    assert output['documents']==[] and output['knowledge_links']==[]
    assert output['excluded_audit_documents'][0]['chunk_id']=='bad'
    assert 'content' not in output['excluded_audit_documents'][0]
    assert all("<> 'SUPERSEDED'" in str(call.args[0]) for call in db.execute.call_args_list[1:])


def test_provenance_query_retains_counts_but_not_bad_or_archived_excerpt(monkeypatch):
    import psycopg2
    import requests
    monkeypatch.setenv('DISABLE_LLM_API','true')
    monkeypatch.setattr(requests.sessions.Session,'request',MagicMock(side_effect=AssertionError('No network')))
    from services.orchestrator import graph
    monkeypatch.setattr(graph,'_dataset_evidence_terms',lambda q:['topic'])
    monkeypatch.setattr(graph,'_dataset_evidence_db_url',lambda:'test')
    monkeypatch.setattr(audit,'load_receipts',bad_receipt)
    rows=[dict(chunk_id='bad',content='wrong',source_sha256='a'*64,source_id='s',metadata={},
               source_file='same',title='topic',document_type='dataset_csv'),
          dict(chunk_id='archived',content='old',source_sha256='b'*64,source_id='s',
               metadata={'retrieval_status':'SUPERSEDED'},source_file='same',title='topic',document_type='dataset_csv')]
    cursor=MagicMock();cursor.__enter__.return_value=cursor;cursor.fetchall.return_value=rows
    connection=MagicMock();connection.__enter__.return_value=connection;connection.cursor.return_value=cursor
    monkeypatch.setattr(psycopg2,'connect',lambda *a,**k:connection)
    result=graph._query_dataset_evidence_sources('topic')[0]
    assert result['row_count']==2 and result['active_chunk_count']==1
    assert result['superseded_chunk_count']==1 and result['audit_mismatch_chunk_count']==1
    assert result['excerpt']=='' and result['chunk_ids']==['bad','archived']
