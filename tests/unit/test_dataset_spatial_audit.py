import pytest
from shapely.geometry import Point,LineString
from scripts.audit_dataset_static_geometry import compare_geometry,resolve_archive_member

def test_projection_roundoff_is_distinct_from_wrong_coordinate():
    assert compare_geometry(Point(127,35),Point(127+1e-12,35))[0]
    assert not compare_geometry(Point(127,35),Point(35,127))[0]
    assert not compare_geometry(Point(127,35),Point(127.00001,35))[0]

def test_geometry_structure_not_flattened_away():
    assert not compare_geometry(LineString([(127,35),(128,36)]),LineString([(128,36),(127,35)]))[0]

def test_archive_decoding_requires_reversible_full_path():
    native='간출암(점)/a.shp'
    mangled=native.encode('cp949').decode('cp437')
    assert resolve_archive_member(mangled,[native])==native
    assert resolve_archive_member(native,[native])==native
    with pytest.raises((ValueError,UnicodeError)):
        resolve_archive_member('missing/a.shp',[native])
from scripts.audit_dataset_csv_rows import jsonb_array_hash

def test_jsonb_array_hash_preserves_values_and_order():
    assert jsonb_array_hash(['한글', 'a', '']) != jsonb_array_hash(['한글', '', 'a'])
    assert jsonb_array_hash(['1']) != jsonb_array_hash(['01'])
    assert jsonb_array_hash(['a\nb']) != jsonb_array_hash(['a\\nb'])
from scripts.dataset_spatial_audit_io import refuse_existing

def test_existing_evidence_is_never_implicitly_overwritten(tmp_path):
    target=tmp_path/'new'/'receipt.json'
    assert refuse_existing(target)==target
    target.write_text('preserved',encoding='utf8')
    with pytest.raises(FileExistsError):refuse_existing(target)
    assert target.read_text(encoding='utf8')=='preserved'
