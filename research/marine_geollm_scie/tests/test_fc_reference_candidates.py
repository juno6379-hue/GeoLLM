import json
import pytest
from research.marine_geollm_scie.runners.extract_fc_reference_candidates import build, catalogue, PARSED


@pytest.fixture(scope='module')
def candidates(): return {r['case_id']:r for r in build()}


def test_nine_cases_are_source_verified_without_gold_promotion(candidates):
    assert len(candidates)==9
    for row in candidates.values():
        assert row['human_approval'] is False and row['gold_promoted'] is False
        assert row['source_backed_claims']
        assert all(c['source_status']=='VERIFIED_XML_EXTRACTION' and c['version']=='2.0.0' for c in row['source_backed_claims'])


def test_feature_colour_binding_is_not_global_codelist(candidates):
    objs={r['code']:r for r in candidates['PILOT_Q2_01']['source_backed_claims']}
    def colours(code):
        return next(b['permitted_values'] for b in objs[code]['bindings'] if any(r['ref']=='colour' for r in b['references']))
    assert colours('Landmark')==[str(i) for i in range(1,14)]
    assert colours('LightAllAround')==['1','3','4','5','6','9','10','11']
    assert len(objs['colour']['listed_values'])==13
    assert 'sectorCharacteristics' in objs and 'lightSector' in objs
    assert colours('lightSector')==['1','3','4','5','6','9','10','11']


def test_wreck_bindings_match_existing_parsed_source(candidates):
    original=next(r for r in json.loads(PARSED.read_text(encoding='utf-8'))['features'] if r['code']=='Wreck')
    actual=next(r for r in candidates['PILOT_Q2_03']['source_backed_claims'] if r['code']=='Wreck')
    assert actual['definition']==original['definition']
    assert actual['permitted_primitives']==original['permitted_primitives']
    xml=[(ref['ref'],b['permitted_values'],b['lower'],b['upper'],b['unbounded']) for b in actual['bindings'] for ref in b['references'] if ref['type']=='attribute']
    parsed=[(b['ref'],b['permitted_values'],b['lower'],b['upper'],b['unbounded']) for b in original['bindings'] if b['type']=='attribute']
    assert xml==parsed


def test_xml_hash_mismatch_is_rejected(tmp_path):
    original=json.loads(PARSED.read_text(encoding='utf-8'));original['metadata']['sha256']='0'*64
    path=tmp_path/'changed.json';path.write_text(json.dumps(original),encoding='utf-8')
    with pytest.raises(ValueError,match='hash'):catalogue(path)
