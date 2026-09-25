import copy
import json

import pytest

from services.orchestrator.marine_terminology import REGISTRY, match_terminology, validate_bundle
from services.orchestrator.korean_query_analysis import constraints
from services.orchestrator.semantic_slot_binding import bind_semantic_slots
from scripts.build_mof_normalization_review import build


@pytest.mark.parametrize('query,original,raw', [
    ('잠제의 순화어는?', '잠제', '잠제'),
    ('수중방파제를 찾아줘', '잠제', '수중방파제'),
    ('수중 방파제에서 관측해줘', '잠제', '수중 방파제'),
    ('소형선 부두란?', '물양장', '소형선 부두'),
    ('끌배는 무엇인가?', '예선', '끌배'),
    ('소형선 정박장은 어디야?', '선유장', '소형선 정박장'),
])
def test_original_spans_and_source_relations(query, original, raw):
    result = match_terminology(query, constraints(query))
    assert result['status'] == 'AVAILABLE'
    candidate, = result['candidates']
    assert candidate['original_label'] == original
    assert query[slice(*candidate['span'])] == raw
    assert candidate['reference']['source_id'] == 'mof_standard_terms_3'
    assert candidate['canonical_id'] is None
    assert not candidate['execution_authorized']


@pytest.mark.parametrize('query', ['월드컵 예선전 결과', '잠제작업장', '국제예선', '물양장비'])
def test_word_prefix_is_not_a_marine_term(query):
    assert match_terminology(query, constraints(query))['candidates'] == []


def test_homonym_not_promoted_to_maritime_sense():
    candidate, = match_terminology('축구 예선 결과', [])['candidates']
    assert candidate['sense_status'] == 'DOMAIN_SENSE_UNRESOLVED'
    assert not candidate['ontology_equivalence_verified']


def test_multiword_exclusion_and_quoted_terms_are_not_tool_inputs():
    query = '수중 방파제 말고 침선을 찾아줘'
    result = bind_semantic_slots(query, {'constraints':constraints(query),'slots':[]}, [])
    assert result['maritime_terminology']['candidates'][0]['excluded']
    assert result['unresolved_terminology'] == []
    assert result['target_features'] == ['Wreck']
    quoted = bind_semantic_slots('"잠제"라는 표현', {'constraints':[],'slots':[]}, [])
    assert quoted['unresolved_terminology'] == []
    assert quoted['maritime_terminology']['candidates'][0]['quoted']


def test_missing_mapping_cannot_satisfy_tool_feature_input():
    result = bind_semantic_slots('잠제를 찾아줘', {'constraints':[],'slots':[]}, [
        {'candidate_id':'fixture-feature-search','input_slots':['target_feature_group'],'output_slots':[]}])
    assert result['target_features'] == []
    assert result['kg_seed_ids'] == []
    assert result['capability_bindings'][0]['unresolved_inputs'] == ['target_feature_group']
    assert result['unresolved_terminology'][0]['candidate_tool_contracts'] == ['fixture-feature-search']


def test_source_relation_reaches_review_pack_without_becoming_gold():
    from scripts.export_korean_review_pack import reference_candidates
    bundle = json.loads(REGISTRY.read_text(encoding='utf-8'))
    candidates, binding = reference_candidates({'query':'수중방파제의 뜻은?'},bundle['units'])
    assert candidates[0]['unit_id'] == bundle['units'][0]['unit_id']
    assert candidates[0]['status'] == 'RETRIEVAL_CANDIDATE_NOT_GOLD'
    assert binding['target_features'] == []


def test_explicit_label_question_has_a_source_answer_without_definition_claim():
    from services.orchestrator.definition_router import is_definition_query
    from services.orchestrator.definition_response import build_definition_response
    assert is_definition_query('잠제의 순화어는?')
    final = build_definition_response({'query':'잠제의 순화어는?', 'task_id':'fixture'})['final_dict']
    assert final['structured_result']['analysis_type'] == 'terminology_relation_lookup'
    assert final['structured_result']['definition'] is None
    assert final['structured_result']['feature_code'] is None
    assert not final['structured_result']['web_rag_usage']['llm_used']
    assert final['rag_evidence'][0]['evidence_type'] == 'source_lexical_relation'
    assert final['rag_evidence'][0]['data']['quote']


@pytest.mark.parametrize('query', ['잠제의 정의는?', '잠제 순화어와 위치를 찾아줘',
                                  '축구 예선의 순화어는?', '수중방파제 주변 침선을 찾아줘'])
def test_label_lookup_cannot_capture_definition_or_compound_execution(query):
    from services.orchestrator.marine_terminology import resolve_label_request
    assert resolve_label_request(query) is None


def test_next_table_row_is_not_an_alias():
    bundle = json.loads(REGISTRY.read_text(encoding='utf-8'))
    seeds = copy.deepcopy(bundle['seeds'])
    seeds['pairs'] = [{'original':'잠제','preferred':'압축기'}]
    with pytest.raises(ValueError, match='Preferred label'):
        build(seeds, bundle['units'])


@pytest.mark.parametrize('tamper', ['text', 'quote', 'authority'])
def test_tampered_source_or_promotion_rejected(tamper):
    bundle = json.loads(REGISTRY.read_text(encoding='utf-8'))
    if tamper == 'text':
        bundle['units'][0]['text'] += 'changed'
    elif tamper == 'quote':
        bundle['relations'][0]['quote'] = 'invented'
    else:
        bundle['relations'][0]['execution_authorized'] = True
    with pytest.raises(ValueError):
        validate_bundle(bundle)


def test_missing_supplement_keeps_existing_bindings(monkeypatch, tmp_path):
    from services.orchestrator import marine_terminology as module
    monkeypatch.setattr(module, 'REGISTRY', tmp_path/'absent.json')
    module._registry.cache_clear()
    try:
        result = bind_semantic_slots('침선을 찾아줘', {'constraints':[],'slots':[]}, [])
        assert result['target_features'] == ['Wreck']
        assert result['maritime_terminology']['status'] == 'TERMINOLOGY_UNAVAILABLE'
    finally:
        module._registry.cache_clear()
