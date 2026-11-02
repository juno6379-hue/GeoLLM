"""Independent runtime-receipt boundary checks for new source freezes."""
import hashlib
import json

import pytest

from research.marine_geollm_scie.runners.freeze_comparison_sources import runtime_assets


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(root, manifest, sha):
    put(root, 'data/source_verification/current.json',
        {'manifest': manifest, 'sha256': sha})


def test_manifest_inside_repo_but_outside_receipt_root_is_rejected(tmp_path):
    sha = put(tmp_path, 'data/other/manifest.json', {'complete': True, 'files': {}})
    pointer(tmp_path, '../other/manifest.json', sha)
    with pytest.raises(ValueError):
        runtime_assets(tmp_path)


def test_incomplete_receipt_manifest_cannot_be_frozen_as_valid_runtime_asset(tmp_path):
    rows_sha = put(tmp_path, 'data/source_verification/v/receipts.jsonl', {})
    sha = put(tmp_path, 'data/source_verification/v/manifest.json',
              {'complete': False, 'files': {'receipts.jsonl': rows_sha}})
    pointer(tmp_path, 'v/manifest.json', sha)
    with pytest.raises(ValueError):
        runtime_assets(tmp_path)


def test_manifest_without_the_runtime_fixed_receipts_filename_is_rejected(tmp_path):
    rows_sha = put(tmp_path, 'data/source_verification/v/other.jsonl', {})
    sha = put(tmp_path, 'data/source_verification/v/manifest.json',
              {'complete': True, 'files': {'other.jsonl': rows_sha}})
    pointer(tmp_path, 'v/manifest.json', sha)
    with pytest.raises(ValueError):
        runtime_assets(tmp_path)


def test_manifest_receipt_digest_cannot_be_missing(tmp_path):
    put(tmp_path, 'data/source_verification/v/receipts.jsonl', {})
    sha = put(tmp_path, 'data/source_verification/v/manifest.json',
              {'complete': True, 'files': {'receipts.jsonl': None}})
    pointer(tmp_path, 'v/manifest.json', sha)
    with pytest.raises(ValueError):
        runtime_assets(tmp_path)


def test_s101_target_inventory_also_pins_original_source_cell(tmp_path):
    raw_sha = put(tmp_path, 'data/source_inventory/source_cells/cell.000', {'binary_fixture': True})
    inventory_sha = put(tmp_path, 'data/source_inventory/inventory.json',
        {'schema_version': 's101_target_inventory_v2',
         'source_proof': {'source_asset': 'data/source_inventory/source_cells/cell.000',
                          'source_sha256': raw_sha}})
    put(tmp_path, 'data/spatial_layer_registry.yaml', {'layers': {'s101': {
        'corpus_contract': {'kind': 's101_target_inventory_v2',
                           'source_asset': 'data/source_inventory/inventory.json',
                           'source_sha256': inventory_sha}}}})
    assert tmp_path / 'data/source_inventory/source_cells/cell.000' in runtime_assets(tmp_path)
    put(tmp_path, 'data/source_inventory/source_cells/cell.000', {'changed': True})
    with pytest.raises(ValueError):
        runtime_assets(tmp_path)
