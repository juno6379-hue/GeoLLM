"""Apply to tests/unit only after the proposed graph/helper patch is integrated."""
from copy import deepcopy
from contextlib import nullcontext
from services.orchestrator import graph
from services.orchestrator.execution_validator import validate_lookup_request


def test_filename_identity_accepts_korean_particles_without_generalizing_source():
    from services.orchestrator.reporting_and_source_scope import filename_identities, source_identity
    query='항로표지정보_20250623.csv의 적재 근거를 보여줘'
    assert filename_identities(query)==['항로표지정보_20250623.csv']
    assert source_identity(query, [], 'Dataset/해양수산부_항로표지정보_20250623.csv','')['accepted']
    assert not source_identity(query, [], 'Dataset/사고.csv','항로표지정보_20250623.csv')['accepted']


def test_final_obligation_downgrade_is_projected_into_execution_contract():
    import asyncio
    from shared.schemas.agent import AgentStatus
    state={'task_id':'post-audit','query':'S-101이 뭐야','status':AgentStatus.COMPLETED}
    qec=validate_lookup_request(state,'definition_lookup')
    state['query']='S-101 정의와 지도 표시를 해줘'
    state['candidate_trace']={'execution_contract':{'status':'ready','execution_route':'SPATIAL_ANALYSIS'}}
    state['final_dict']={'status':'COMPLETED','orchestrator_v2':{'query_execution_context':qec.model_dump(mode='json')}}
    result=asyncio.run(graph.verify_output_obligations_node(state))
    final=result['final_dict']
    assert final['status']=='PARTIAL'
    assert final['orchestrator_v2']['execution_contract']['status']=='PARTIAL'
    assert final['orchestrator_v2']['execution_contract']['execution_route']=='STANDARD_RAG'


def test_final_definition_route_uses_validated_operation_not_shadow():
    state={'task_id':'projection-fixture','query':'S-101이 뭐야','user_id':'fixture'}
    qec=validate_lookup_request(state,'definition_lookup')
    trace={'execution_contract':{'status':'ready','execution_route':'SPATIAL_ANALYSIS','steps':[{'status':'ready'}]}}
    before=deepcopy(trace)
    final={'status':'COMPLETED','orchestrator_v2':{'query_execution_context':qec.model_dump(mode='json')}}
    graph._attach_candidate_trace({'candidate_trace':trace},final)
    projected=final['orchestrator_v2']['execution_contract']
    assert projected['execution_route']=='STANDARD_RAG'
    assert projected['execution_authorized'] is True
    assert projected['steps'][0]['tool_id']=='definition.registry_lookup'
    assert trace==before
    invalid=qec.model_dump(mode='json')
    invalid['original_query']='changed after validator'
    final={'status':'COMPLETED','orchestrator_v2':{'query_execution_context':invalid}}
    graph._attach_candidate_trace({'candidate_trace':trace},final)
    assert final['orchestrator_v2']['execution_contract']['execution_authorized'] is False


def test_source_identity_filters_many_general_hits_and_counts_unique_terms(monkeypatch):
    import psycopg2
    from services.orchestrator import dataset_verification
    calls=[]
    rows=[{'chunk_id':str(i),'document_type':'dataset_profile','title':'사고',
           'source_file':'Dataset/해양수산부_사고.csv','source_id':'accident',
           'content':'해양수산부 항로표지 metadata','metadata':{},'embedding_missing':False}
          for i in range(30)]
    rows.append({'chunk_id':'target','document_type':'dataset_profile','title':'항로표지',
           'source_file':'Dataset/해양수산부_항로표지정보_20250623.csv','source_id':'target',
           'content':'항로표지정보 원문 profile','metadata':{},'embedding_missing':False})
    class Cursor:
        def execute(self,sql,args): calls.append((sql,args))
        def fetchall(self): return rows
    class Connection:
        def cursor(self,**kwargs): return nullcontext(Cursor())
    monkeypatch.setattr(psycopg2,'connect',lambda *a,**k:nullcontext(Connection()))
    monkeypatch.setattr(graph,'_dataset_evidence_db_url',lambda:'fixture-only')
    monkeypatch.setattr(dataset_verification,'load_receipts',lambda:{})
    monkeypatch.setattr(dataset_verification,'verify_document',lambda *a:{'status':'UNVERIFIED'})
    results=graph._query_dataset_evidence_sources('항로표지정보_20250623.csv 파싱/표준화/공간 적재 근거를 보여줘')
    assert len(results)==1 and results[0]['dataset_id']=='target'
    assert results[0]['row_count']==1
    assert results[0]['source_scope']=='EXPLICIT_SOURCE_FILENAME'
    assert results[0]['row_count_scope']=='MATCHED_CHUNKS_WITHIN_RETRIEVAL_LIMIT_240'
    assert 'ORDER BY' in calls[0][0]
    assert calls[0][1][1] is False
    assert r'\_' in calls[0][1][2][0]
