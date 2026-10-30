import json
import pytest
from research.marine_geollm_scie.runners.freeze_contracts_v5 import build,validate,REFERENCE,V4,sha,STATUS


@pytest.fixture(scope='module')
def rows():return build()


def test_finalized_is_not_independent_human_gold(rows):
    assert len(rows)==18
    for r in rows:
        assert r['finalization_status']==STATUS
        assert not r['human_approval'] and not r['independent_human_review']
        assert not r['holdout_eligible'] and not r['single_intent_match_is_sufficient']


def test_approved_slots_and_spatial_not_expanded(rows):
    old={r['case_id']:r for r in map(json.loads,REFERENCE.read_text(encoding='utf-8').splitlines())}
    assert sum(r['spatial_object_scoring_enabled'] for r in rows)==3
    for r in rows:
        assert r['required_qec_fields']==old[r['case_id']]['qec_fields']
        assert r['spatial_reference']==old[r['case_id']]['spatial']
    missing=next(r for r in rows if r['case_id']=='PILOT_Q3_03')
    assert any(c.get('expected')=='NEEDS_USER_INPUT' for c in missing['machine_checks'])


def test_attributes_bind_to_owner_not_global_colour(rows):
    r=next(r for r in rows if r['case_id']=='PILOT_Q2_01')
    b=r['document_scope']['attribute_scope']['bindings']
    assert next(x for x in b if x['owner']=='Landmark' and x['attribute']=='colour')['permitted_values']==[str(i) for i in range(1,14)]
    assert next(x for x in b if x['owner']=='LightAllAround' and x['attribute']=='colour')['permitted_values']==['1','3','4','5','6','9','10','11']
    assert any(x['owner']=='lightSector' and x['attribute']=='colour' for x in b)


def test_composite_wreck_explanation_is_required_even_without_spatial_gold(rows):
    r=next(r for r in rows if r['case_id']=='PILOT_Q5_03')
    assert r['spatial_reference'] is None
    assert r['document_scope']['attribute_scope']['bindings']
    assert 'per_task_status' in r['required_output_fields']
    assert any(x['id']=='attribute_binding_contract' for x in r['machine_checks'])


def test_verbatim_source_request_and_citation_scope(rows):
    r=next(r for r in rows if r['case_id']=='PILOT_Q6_01')
    assert any(c['id']=='requested_verbatim_definition' and c['expected'] for c in r['machine_checks'])
    assert r['document_scope']['evidence_requirements']['edition']=='2.0.0'
    assert r['document_scope']['evidence_requirements']['locators']


def test_build_does_not_change_prior_versions():
    paths=[REFERENCE,V4/'task_contracts_DRAFT.jsonl',V4/'evidence_reference_candidates.jsonl']
    before=[sha(p.read_bytes()) for p in paths];build()
    assert before==[sha(p.read_bytes()) for p in paths]
