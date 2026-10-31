import hashlib
import json
import pytest
from services.orchestrator.public_catalogue_attribute import (
    CATALOGUE, ROOT, match_public_catalogue_attribute_query, resolve_public_catalogue_attribute,
)


@pytest.mark.parametrize('query',[
    '제한구역의 제한 종류는 어떤 코드로 표현해?',
    'Explain the restriction attribute codes of S-101 RestrictedArea.',
    'S101 제한구역 restriction 허용값을 알려줘',
    'What are the restriction codes for RestrictedArea?',
    'Describe colour permitted values for S-101 Landmark.',
])
def test_complete_public_attribute_contract(query):
    assert match_public_catalogue_attribute_query(query)
    assert resolve_public_catalogue_attribute(query)


@pytest.mark.parametrize('query',[
    '제한구역 주변 5km를 찾아줘',
    '제한구역의 비공개 제한 종류는 어떤 코드로 표현해?',
    '제한구역의 제한 종류는 어떤 코드로 표현해? 그리고 좌표를 알려줘',
    'Explain the restriction attribute codes of S-101 RestrictedArea and find its coordinates.',
    'Explain private restriction attribute codes of S-101 RestrictedArea.',
    '제한구역', 'restriction',
    'Explain restriction codes of S-101 Wreck.',
    'Explain restriction codes of S-101 DoesNotExist.',
])
def test_mixed_private_spatial_or_unbound_query_is_not_public_lookup(query):
    assert resolve_public_catalogue_attribute(query) is None


def test_source_values_binding_and_hash_are_real():
    entry=resolve_public_catalogue_attribute('제한구역의 제한 종류는 어떤 코드로 표현해?')
    raw=CATALOGUE.read_bytes();fc=json.loads(raw)
    feature=next(f for f in fc['features'] if f['code']=='RestrictedArea')
    attribute=next(a for a in fc['attributes'] if a['code']=='restriction')
    assert entry['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert entry['source_version']=='2.0.0'
    assert entry['definition']==attribute['definition']
    assert entry['binding'] in feature['bindings']
    assert {v['value'] for v in entry['allowed_values']}==set(entry['permitted_values'])
    assert {'value':'7','label':'Entry Prohibited'} in entry['allowed_values']
    xml=(ROOT/entry['xml_source_ref']).read_bytes()
    assert hashlib.sha256(xml).hexdigest()==entry['xml_source_sha256']


def test_allowed_colour_is_not_global_attribute_enumeration():
    entry=resolve_public_catalogue_attribute('Explain colour attribute codes of LightAllAround.')
    assert len(entry['listed_values'])==13
    assert [v['value'] for v in entry['allowed_values']]==['1','3','4','5','6','9','10','11']


@pytest.mark.parametrize('query',[
    '제한구역의 제한 종류는 어떤 코드로 표현해?',
    'Explain the restriction attribute codes of S-101 RestrictedArea.',
])
def test_response_uses_validator_and_preserves_public_source_evidence(query):
    from services.orchestrator.public_catalogue_attribute import build_public_catalogue_attribute_response
    result=build_public_catalogue_attribute_response({'task_id':'public-fc-test','query':query})
    final=result['final_dict'];data=final['structured_result'];qec=result['query_execution_context']
    assert final['status']=='COMPLETED' and len(data['allowed_values'])==29
    assert data['search_execution']['status']=='NOT_RUN'
    assert data['web_rag_usage']['llm_used'] is False
    assert qec['provenance']['execution_validation']['authority']=='ExecutionValidator'
    assert any(b['snapshot_version']==data['source_sha256'] for b in qec['data_bindings'])
    assert final['rag_evidence'][0]['data']['locators']
