import copy
import json

import pytest

from research.marine_geollm_scie.runners.build_contracts_v4 import build, validate, REFERENCE, REGISTRY, sha


def test_all_original_cases_and_transcribed_values_are_preserved():
    before = sha(REFERENCE.read_bytes())
    refs = {r['case_id']: r for r in map(json.loads, REFERENCE.read_text(encoding='utf-8').splitlines())}
    rows = build()
    assert len(rows) == 18 and sha(REFERENCE.read_bytes()) == before
    for r in rows:
        ref = refs[r['case_id']]
        assert r['query'] == ref['query']
        for key in ('qec_fields', 'spatial', 'expected_behavior'):
            assert r['transcribed_approved_values'][key] == ref[key]
        assert r['source_human_approval'] is True and r['human_approval'] is False
        assert r['evaluation_enabled'] is False
        assert r['source_provenance']['query']['exact_text'] == ref['query']
        assert r['source_provenance']['query']['source_sha256'] == before


def test_only_approved_q4_has_spatial_objects_no_invented_aoi():
    rows = build()
    spatial = [r for r in rows if r['transcribed_approved_values']['spatial']]
    assert {r['case_id'] for r in spatial} == {'PILOT_Q4_01','PILOT_Q4_02','PILOT_Q4_03'}
    assert all(len(r['transcribed_approved_values']['spatial']['object_ids']) == 11 for r in spatial)
    assert all(r['execution_guards']['new_default_geometry'] is None for r in rows)
    aoi = next(r for r in rows if r['case_id'] == 'PILOT_Q3_03')
    assert aoi['transcribed_approved_values']['expected_behavior'] == 'NEEDS_USER_INPUT'
    assert any(t['obligation_id'] == 'request_aoi_when_missing' for t in aoi['task_obligations'])


def test_registry_combinations_are_candidates_not_execution_proofs():
    for row in build():
        for combo in row['acceptable_capability_combinations']:
            assert combo['sufficient_for_execution'] is False
            for cap in combo['all_of']:
                assert cap['provenance']['source_sha256'] == sha(REGISTRY.read_bytes())
                assert cap['provenance']['exact_text']
                assert cap['runtime_availability'] == 'NOT_VERIFIED'


@pytest.mark.parametrize('field,value',[('human_approval',True),('annotation_status','GOLD'),('evaluation_enabled',True),('holdout_eligible',True)])
def test_new_interpretation_cannot_be_promoted(field,value):
    rows = build();rows[0][field] = value
    with pytest.raises(ValueError): validate(rows)


def test_source_tampering_is_detected():
    rows = build();rows[0]['source_provenance']['query']['exact_text'] += 'changed'
    with pytest.raises(ValueError,match='span/hash'): validate(rows)


def test_declared_json_schema():
    jsonschema = pytest.importorskip('jsonschema')
    schema = json.loads((REFERENCE.parent.parent/'contracts_v4/schema.json').read_text(encoding='utf-8'))
    for row in build(): jsonschema.validate(row,schema)
