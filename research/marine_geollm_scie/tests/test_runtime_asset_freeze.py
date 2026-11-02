import hashlib
import json

import pytest

from research.marine_geollm_scie.runners.freeze_comparison_sources import runtime_assets


def write(root, name, body):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_registry_asset_is_pinned_and_mutation_rejected(tmp_path):
    sha = write(tmp_path, 'data/source_inventory/example.json', '{}')
    write(tmp_path, 'data/spatial_layer_registry.yaml', json.dumps({'layers': {'s101': {
        'corpus_contract': {'source_asset': 'data/source_inventory/example.json', 'source_sha256': sha}}}}))
    assert tmp_path/'data/source_inventory/example.json' in runtime_assets(tmp_path)
    write(tmp_path, 'data/source_inventory/example.json', '{"changed":true}')
    with pytest.raises(ValueError, match='digest'):
        runtime_assets(tmp_path)


def test_receipt_pointer_manifest_and_rows_all_frozen(tmp_path):
    receipt_sha = write(tmp_path, 'data/source_verification/v/receipts.jsonl', '{}\n')
    manifest_sha = write(tmp_path, 'data/source_verification/v/manifest.json', json.dumps({'complete': True, 'files': {'receipts.jsonl': receipt_sha}}))
    write(tmp_path, 'data/source_verification/current.json', json.dumps({'manifest': 'v/manifest.json', 'sha256': manifest_sha}))
    assert {p.name for p in runtime_assets(tmp_path)} == {'current.json', 'manifest.json', 'receipts.jsonl'}


def test_external_asset_is_rejected(tmp_path):
    write(tmp_path, 'data/spatial_layer_registry.yaml', json.dumps({'layers': {'x': {
        'coverage_contract': {'path': '../outside.json', 'sha256': 'a'*64}}}}))
    with pytest.raises(ValueError, match='external'):
        runtime_assets(tmp_path)
