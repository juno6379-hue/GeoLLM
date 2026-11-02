import pytest
from services.spatial_analysis_agent import place_resolver as r


def children():
    items = []
    for i, name in enumerate(('북항', '연안항', '남항', '내항')):
        c = r._candidate(f'small_harbour:{i}', f'인천항({name})', [],
                         f'POINT(126.{60+i} 37.4)', [{'source_ref': 'serving.small_harbour_guide'}])
        c.update(parent_name='인천항', requires_confirmation=True,
                 geometry_role='harbour_reference_point_not_entrance')
        items.append(c)
    return items


def test_parent_returns_four_children_and_does_not_autoselect():
    with pytest.raises(r.PlaceResolutionProblem) as error:
        r.resolve_location('인천항', catalog={'candidates': children()})
    assert {x['label'] for x in error.value.candidates} == {'인천항(북항)', '인천항(연안항)', '인천항(남항)', '인천항(내항)'}
    assert error.value.code == 'LOCATION_UNCONFIRMED'


def test_child_query_does_not_expand_siblings():
    assert [x['label'] for x in r._family_matches('인천항(북항)', children())] == ['인천항(북항)']
    assert r._family_matches('다른항', children()) == []


def test_entrance_cannot_be_bound_to_child_representative():
    item = children()[0]
    with pytest.raises(r.PlaceResolutionProblem) as error:
        r.resolve_location('인천항 입구', item, catalog={'candidates': children()})
    assert error.value.candidates[0]['selection_scope'] == 'PARENT_PLACE_ONLY'


def test_selected_child_preserves_object_identity():
    item = children()[1]
    _, name, _, resolution = r.resolve_location('인천항', item, catalog={'candidates': children()})
    assert name == '인천항(연안항)'
    assert resolution['place_id'] == item['place_id']
    assert resolution['status'] == 'CONFIRMED_SELECTION'


def test_catalog_load_preserves_source_id_properties_and_photo_reference(monkeypatch):
    monkeypatch.setenv('S101_DB_URL', 'fixture')
    monkeypatch.delenv('POSTGIS_URL', raising=False)
    row = {'id': 'small_harbour:fixture:1', 'name': '인천항(북항)', 'wkt': 'POINT(126.6 37.4)',
           'srid': 4326, 'provenance': {'source_sha256': 'a'*64},
           'properties': {'PHOTO1_PAT': 'photo.jpg', 'PPATH': 'source/path/'}}
    monkeypatch.setattr(r, '_read_source', lambda env, sql: [row] if 'small_harbour_guide' in sql else [])
    c = next(x for x in r.load_catalog(refresh=True)['candidates'] if x['place_id'] == row['id'])
    assert c['parent_name'] == '인천항'
    assert c['source_properties'] == row['properties']
    assert c['photo_references'][0]['asset_verified'] is False
    assert c['geometry_role'] == 'harbour_reference_point_not_entrance'
    assert c['requires_confirmation'] is True
