import json
from pathlib import Path

import pytest

from research.marine_geollm_scie.runners import prepare_eight_profiles as profiles
from research.marine_geollm_scie.runners.freeze_comparison_sources import execution_files


def fixture(tmp_path, monkeypatch):
    original = profiles.ROOT
    for relative in (profiles.EXECUTION_CONTRACT, profiles.REVIEW_PROTOCOL):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((original / relative).read_bytes())
    monkeypatch.setattr(profiles, 'ROOT', tmp_path)
    return {'files': [{'path': p.relative_to(tmp_path).as_posix(), 'sha256': profiles.digest(p)}
                      for p in execution_files(tmp_path)]}


def test_v5_declares_v3_and_both_exact_bytes_are_frozen(tmp_path, monkeypatch):
    snapshot = fixture(tmp_path, monkeypatch)
    path, contract, review = profiles.execution_contract(snapshot)
    assert path.name == 'eight_execution_contract_v5.json'
    assert contract['review_protocol'] == profiles.REVIEW_PROTOCOL
    assert review['version'] == profiles.REVIEW_VERSION
    assert review['sha256'] == profiles.digest(tmp_path / profiles.REVIEW_PROTOCOL)


@pytest.mark.parametrize('missing', [profiles.EXECUTION_CONTRACT, profiles.REVIEW_PROTOCOL])
def test_missing_either_frozen_contract_rejected(tmp_path, monkeypatch, missing):
    snapshot = fixture(tmp_path, monkeypatch)
    snapshot['files'] = [x for x in snapshot['files'] if x['path'] != missing]
    with pytest.raises(ValueError, match='new source freeze'):
        profiles.execution_contract(snapshot)


def test_old_review_pointer_cannot_be_declared_for_new_code(tmp_path, monkeypatch):
    snapshot = fixture(tmp_path, monkeypatch)
    path = tmp_path / profiles.EXECUTION_CONTRACT
    contract = json.loads(path.read_text())
    contract['review_protocol'] = 'research/marine_geollm_scie/protocol/structured_review_v2.json'
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match='different review protocol'):
        profiles.execution_contract(snapshot)


@pytest.mark.parametrize('field,value', [('version', 'old'), ('schema_sha256', 'old'),
                                      ('schema', {}), ('budget', {})])
def test_runtime_schema_budget_and_version_must_match_even_if_rehashed(tmp_path, monkeypatch, field, value):
    snapshot = fixture(tmp_path, monkeypatch)
    path = tmp_path / profiles.REVIEW_PROTOCOL
    data = json.loads(path.read_text()); data[field] = value
    path.write_text(json.dumps(data))
    for item in snapshot['files']:
        if item['path'] == profiles.REVIEW_PROTOCOL:
            item['sha256'] = profiles.digest(path)
    with pytest.raises(ValueError, match='running implementation'):
        profiles.execution_contract(snapshot)


def test_original_v4_contract_unchanged():
    root = Path(__file__).resolve().parents[3]
    assert profiles.digest(root / 'research/marine_geollm_scie/protocol/eight_execution_contract_v4.json') == '51eae565022dfc1475db1f798c3f994786a56c65e878b402951d4ef7807460a2'
