"""Independent source-proof boundaries for the pinned S-101 inventory."""
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from services.orchestrator.s101_corpus import inventory_digest, verify_s101_corpus
from shared.schemas.agent import DataBinding

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = 'data/source_inventory/s101_busan_20261102/wreck_inventory.json'


def fixture(root):
    data = json.loads((ROOT / MANIFEST_PATH).read_text(encoding='utf-8'))
    data['rows'] = data['rows'][:1]
    data['snapshot_version'] = 'sha256:' + inventory_digest(data['rows'])
    source_path = root / data['source_proof']['source_asset']
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes((ROOT / data['source_proof']['source_asset']).read_bytes())
    binding = DataBinding(dataset_id=data['dataset_id'], relation=data['relation'],
                          geometry_column='geometry', srid=4326)
    contract = dict(kind=data['schema_version'], source_asset=MANIFEST_PATH,
                    snapshot_version=data['snapshot_version'], target_features=['Wreck'])
    cursor = Mock()
    cursor.description = [(key,) for key in data['rows'][0]] + [('geometry_valid',)]
    cursor.fetchall.side_effect = [[(data['source_proof']['source_sha256'],
                                    data['source_proof']['dataset_name'],
                                    data['source_scope']['geometry_wkt'])],
                                  [dict(copy.deepcopy(data['rows'][0]), geometry_valid=True)]]
    return data, binding, contract, cursor, source_path


def store(root, data, contract):
    path = root / MANIFEST_PATH
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    contract['source_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_unchanged_temporary_source_proof_is_verifiable(tmp_path):
    data, binding, contract, cursor, _ = fixture(tmp_path)
    store(tmp_path, data, contract)
    result = verify_s101_corpus(cursor, binding, contract, root=tmp_path)
    assert result['status'] == 'VERIFIED'
    assert result['geographic_completeness'] is False


@pytest.mark.parametrize('change', ['outside_asset', 'missing_asset', 'changed_bytes',
                                  'repinned_wrong_crs', 'scope_changed'])
def test_manifest_hash_alone_cannot_replace_original_source_proof(tmp_path, change):
    data, binding, contract, cursor, source_path = fixture(tmp_path)
    if change == 'outside_asset':
        data['source_proof']['source_asset'] = '../outside.000'
    elif change == 'missing_asset':
        data['source_proof']['source_asset'] += '.absent'
    elif change == 'changed_bytes':
        source_path.write_bytes(source_path.read_bytes() + b'changed')
    elif change == 'repinned_wrong_crs':
        raw = source_path.read_bytes().replace(b'WGS84\x1f4326', b'WGS84\x1f3857', 1)
        source_path.write_bytes(raw)
        data['source_proof']['source_sha256'] = hashlib.sha256(raw).hexdigest()
    else:
        data['source_scope']['geometry_wkt'] = 'POLYGON((129 35,130 35,130 36,129 36,129 35))'
    store(tmp_path, data, contract)
    assert verify_s101_corpus(cursor, binding, contract, root=tmp_path)['status'] == 'UNVERIFIED'
    cursor.execute.assert_not_called()
