"""Original-cell provenance and complete target membership regression."""
import copy
import json
from pathlib import Path

import pytest
import yaml
from shapely import wkt

from services.orchestrator.s101_corpus import verify_s101_corpus
from services.orchestrator.s101_source_coverage import reconstruct_coverage
from shared.schemas.agent import DataBinding

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT/'data/source_inventory/s101_busan_20261102'
MANIFEST = json.loads((ASSET/'wreck_inventory.json').read_text(encoding='utf-8'))
CONTRACT = yaml.safe_load((ROOT/'data/spatial_layer_registry.yaml').read_text(encoding='utf-8'))['layers']['GBENC_S101_feature']['corpus_contract']
BINDING = DataBinding(dataset_id='GBENC_S101_feature', relation='projection.s101_feature_current',
                      geometry_column='geometry', srid=4326)


class Cursor:
    def __init__(self):
        self.rows = [dict(row, geometry_valid=True) for row in copy.deepcopy(MANIFEST['rows'])]
        proof = MANIFEST['source_proof']
        self.source = [(proof['source_sha256'],proof['dataset_name'],MANIFEST['source_scope']['geometry_wkt'])]
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql,params))
        self.target = 'geometry_valid' in sql
        self.description = [(key,) for key in self.rows[0]]

    def fetchall(self):
        return self.rows if self.target else self.source


def test_registered_original_scope_is_not_object_extent_or_inferred_crs():
    polygon, proof = reconstruct_coverage((ASSET/'101KR005G3B33.000').read_bytes(),20)
    assert proof['horizontal_crs'] == 'EPSG:4326'
    assert proof['horizontal_crs_source'].startswith('CSID/CRSH')
    assert polygon.equals(wkt.loads(MANIFEST['source_scope']['geometry_wkt']))
    assert not polygon.equals(polygon.envelope)
    assert proof['coordinate_count'] == 234


def test_original_source_crs_cannot_be_guessed_from_coordinate_bounds():
    raw = (ASSET/'101KR005G3B33.000').read_bytes().replace(b'WGS84\x1f4326',b'WGS84\x1f3857',1)
    with pytest.raises(ValueError,match='source CRS'):
        reconstruct_coverage(raw,20)


def test_non_datacoverage_source_feature_is_rejected():
    with pytest.raises(ValueError,match='not DataCoverage'):
        reconstruct_coverage((ASSET/'101KR005G3B33.000').read_bytes(),1)


def test_full_registered_target_identity_and_original_coverage_must_match():
    cursor = Cursor()
    result = verify_s101_corpus(cursor,BINDING,CONTRACT)
    assert result['status'] == 'VERIFIED'
    assert result['row_count'] == 4339
    assert result['inventory_scope'] == 'ALL_ROWS_OF_REGISTERED_TARGET_TYPES'
    assert result['absence_certified'] is False
    assert cursor.calls[-1][1] == (['Wreck'],)
    assert 'feature_type_name=ANY(%s)' in cursor.calls[-1][0]


@pytest.mark.parametrize('change',['missing','extra','attribute','geometry','source_hash','scope_geometry','invalid_geometry'])
def test_changed_live_target_or_original_source_fails_closed(change):
    cursor=Cursor()
    if change=='missing':cursor.rows.pop()
    elif change=='extra':cursor.rows.append(dict(cursor.rows[-1],feature_instance_id='999999999'))
    elif change=='attribute':cursor.rows[0]['attributes']={'unexpected':'new'}
    elif change=='geometry':cursor.rows[0]['geometry_identity']='modified'
    elif change=='invalid_geometry':cursor.rows[0]['geometry_valid']=False
    elif change=='source_hash':cursor.source=[('0'*64,cursor.source[0][1],cursor.source[0][2])]
    else:cursor.source=[(cursor.source[0][0],cursor.source[0][1],'POLYGON((0 0,1 0,1 1,0 1,0 0))')]
    assert verify_s101_corpus(cursor,BINDING,CONTRACT)['status']=='UNVERIFIED'


def test_new_target_cannot_inherit_wreck_inventory_authority():
    contract=dict(CONTRACT,target_features=['Wreck','Obstruction'])
    cursor=Cursor()
    assert verify_s101_corpus(cursor,BINDING,contract)['status']=='UNVERIFIED'
    assert not cursor.calls
