import json
import shutil
from pathlib import Path

import pytest

from research.marine_geollm_scie.runners.freeze_v2_benchmark import ROOT, digest, freeze, verify


@pytest.fixture
def bundle(tmp_path):
    source = ROOT/'research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1'
    target = tmp_path/'bundle'
    shutil.copytree(source, target)
    return target


def rewrite_manifest(bundle, transform):
    path = bundle/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    transform(manifest)
    path.write_text(json.dumps(manifest), encoding='utf-8')
    (bundle/'manifest.sha256').write_text(digest(path), encoding='ascii')


def test_existing_bundle_verifies_without_mutation(bundle):
    before = {p.name: digest(p) for p in bundle.iterdir()}
    result = verify(bundle, expected_manifest_sha256=digest(bundle/'manifest.json'))
    assert result['benchmark_freeze_complete'] is True
    assert result['execution_ready_is_separate_gate'] is True
    assert before == {p.name: digest(p) for p in bundle.iterdir()}


def test_exclusive_creation_never_overwrites(bundle):
    before = digest(bundle/'manifest.json')
    with pytest.raises(FileExistsError):
        freeze(bundle)
    assert digest(bundle/'manifest.json') == before


@pytest.mark.parametrize('action', ['modify', 'delete'])
def test_changed_or_missing_artifact_rejected(bundle, action):
    path = bundle/'queries.jsonl'
    if action == 'modify':
        path.write_text('{}', encoding='utf-8')
    else:
        path.unlink()
    with pytest.raises(ValueError, match='artifact changed'):
        verify(bundle)


@pytest.mark.parametrize('name', ['../outside', 'queries.jsonl'])
def test_manifest_cannot_smuggle_or_duplicate_entries(bundle, name):
    rewrite_manifest(bundle, lambda m: m['files'].append({'name': name, 'sha256': 'x'}))
    with pytest.raises(ValueError, match='artifact set mismatch'):
        verify(bundle)


def test_external_pin_detects_manifest_and_sidecar_rewrite(bundle):
    original = digest(bundle/'manifest.json')
    rewrite_manifest(bundle, lambda m: m.update(independent_expert_review_complete=True))
    with pytest.raises(ValueError, match='pinned run identity'):
        verify(bundle, expected_manifest_sha256=original)


def test_hash_consistent_duplicate_cases_still_rejected(bundle):
    path = bundle/'queries.jsonl'
    rows = path.read_text(encoding='utf-8').splitlines()
    path.write_text('\n'.join([rows[0]]*18), encoding='utf-8')
    def update(m):
        for entry in m['files']:
            if entry['name'] == path.name:
                entry['sha256'] = digest(path)
    rewrite_manifest(bundle, update)
    with pytest.raises(ValueError, match='identity mismatch'):
        verify(bundle)
