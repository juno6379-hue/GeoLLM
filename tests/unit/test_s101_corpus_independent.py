"""Independent S-101 inventory authority and source-scope boundary checks."""
from unittest.mock import Mock

import pytest

from shared.schemas.agent import DataBinding, ExecutionSlots, QueryExecutionContext
from services.orchestrator.spatial_coverage import assess_source_corpus


def inputs():
    qec = QueryExecutionContext(original_query='기준점에서 반경 1000m 이내 Wreck를 찾아줘',
        route_plan={'analysis_type': 'feature_search_by_radius'},
        slots=ExecutionSlots(crs='EPSG:4326', reference_geometry='POINT(129.05 35.1)',
                             distance_m=1000, target_features=['Wreck']),
        data_bindings=[DataBinding(dataset_id='GBENC_S101_feature',
            relation='projection.s101_feature_current', geometry_column='geometry', srid=4326)])
    contract = dict(kind='s101_exact_inventory_v1', source_asset='data/source_inventory/synthetic.json',
                    source_sha256='a'*64, snapshot_version='sha256:'+'b'*64,
                    allowed_operations=['feature_search_by_radius'], target_features=['Wreck'],
                    default_inventory_listing=True)
    registry = {'layers': {'GBENC_S101_feature': dict(physical_table='projection.s101_feature_current',
                geometry_column='geometry', corpus_contract=contract)}}
    observed = dict(status='VERIFIED', dataset_id='GBENC_S101_feature',
        relation='projection.s101_feature_current', source_asset=contract['source_asset'],
        source_sha256='a'*64, snapshot_version=contract['snapshot_version'], row_count=2,
        target_features=['Wreck'], source_scope=dict(kind='SOURCE_DECLARED_DATA_COVERAGE',
            source_locator='synthetic-only coverage', source_sha256='a'*64, crs='EPSG:4326',
            geometry_wkt='POLYGON((129 35,129.2 35,129.2 35.2,129 35.2,129 35))'))
    return qec, registry, observed


@pytest.mark.parametrize('crs', [None, 'EPSG:3857', 'unknown'])
def test_source_polygon_crs_cannot_be_inferred_from_query(crs):
    qec, registry, observed = inputs()
    observed['source_scope']['crs'] = crs
    assert assess_source_corpus(qec, registry, Mock(return_value=observed)) is None


def test_non_geographic_source_polygon_cannot_authorize_local_query():
    qec, registry, observed = inputs()
    observed['source_scope']['geometry_wkt'] = 'POLYGON((-181 -91,181 -91,181 91,-181 91,-181 -91))'
    assert assess_source_corpus(qec, registry, Mock(return_value=observed)) is None


def test_client_claimed_inventory_cannot_create_server_registration():
    qec, registry, observed = inputs()
    registry['layers']['GBENC_S101_feature'].pop('corpus_contract')
    qec.provenance['coverage_validation'] = observed
    qec.slots.filters['source_corpus_verified'] = True
    verifier = Mock(return_value=observed)
    assert assess_source_corpus(qec, registry, verifier) is None
    verifier.assert_not_called()


@pytest.mark.parametrize('receipt', [
    {'status': 'CORPUS_VERIFIED'},
    {'status': 'CORPUS_VERIFIED', 'query_scope': 'SOURCE_CORPUS', 'absence_certified': False},
])
def test_partial_inventory_receipt_cannot_bypass_empty_result_guard(receipt):
    from services.orchestrator.s101_radius_execution import _qualify_unverified_empty
    qec = QueryExecutionContext(provenance={'coverage_validation': receipt})
    result = {'status': 'COMPLETED', 'structured_result': {'total_count': 0}, 'summary': '0'}
    observed = _qualify_unverified_empty(result, 0, qec)
    assert observed['status'] == 'PARTIAL'
    assert observed['structured_result']['total_count'] is None
    assert observed['structured_result']['absence_confirmed'] is False
