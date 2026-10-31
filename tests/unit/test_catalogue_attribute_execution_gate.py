import pytest
from types import SimpleNamespace
from services.orchestrator.execution_validator import validate_lookup_request,is_execution_authorized
from services.orchestrator import public_catalogue_attribute as module
from shared.schemas.agent import PlanStatus, QueryExecutionContext

QUERY='제한구역의 제한 종류는 어떤 코드로 표현해?'
OP='public_catalogue_attribute_lookup'

def test_actual_catalogue_requires_validator_receipt_and_digest():
    qec=validate_lookup_request({'task_id':'catalogue-gate-test','query':QUERY},OP)
    assert is_execution_authorized(qec)
    entry=module.resolve_public_catalogue_attribute(QUERY)
    assert qec.data_bindings[0].snapshot_version==entry['source_sha256']
    assert qec.tool_bindings[0].tool_id=='catalogue.attribute_lookup'
    qec.original_query='A different request'
    assert not is_execution_authorized(qec)

@pytest.mark.parametrize('query',['', '비공개 제한구역 좌표와 제한코드를 알려줘', 'Explain restriction codes of DoesNotExist.'])
def test_missing_private_or_unbound_lookup_never_authorized(query):
    qec=validate_lookup_request({'task_id':'catalogue-negative','query':query},OP)
    assert not is_execution_authorized(qec)
    assert qec.blockers

@pytest.mark.parametrize('patch',[
    {'source_sha256':'0'*64}, {'source_ref':'outside/unknown.json'}, {'definition':''}, {'locators':[]},
])
def test_stale_or_incomplete_evidence_fails_closed(monkeypatch,patch):
    entry=module.resolve_public_catalogue_attribute(QUERY)
    monkeypatch.setattr(module,'resolve_public_catalogue_attribute',lambda query:{**entry,**patch})
    qec=validate_lookup_request({'query':QUERY},OP)
    assert qec.readiness==PlanStatus.BLOCKED_DATA
    assert not is_execution_authorized(qec)


def test_missing_tool_binding_is_not_authorized():
    qec=validate_lookup_request({'query':QUERY},OP,binding_adapter=SimpleNamespace(tool_registry={'tools':{}}))
    assert qec.readiness==PlanStatus.BLOCKED_CONFIG
    assert not is_execution_authorized(qec)


def test_response_builder_uses_real_authorized_source():
    response=module.build_public_catalogue_attribute_response({'task_id':'catalogue-response','query':QUERY})
    assert response['final_dict']['status']=='COMPLETED'
    qec=response['query_execution_context']
    assert is_execution_authorized(QueryExecutionContext.model_validate(qec))
    assert qec['provenance']['execution_validation']['authority']=='ExecutionValidator'
    assert qec['data_bindings'][0]['snapshot_version']==response['final_dict']['structured_result']['source_sha256']
