import hashlib
import json

import pytest

from research.marine_geollm_scie.baselines import evidence_packets as ep


@pytest.fixture
def sources(tmp_path, monkeypatch):
    monkeypatch.setattr(ep, 'ROOT', tmp_path)
    def write(path, text):
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    write(ep.REGISTRIES[0], 'terms:\n  침선:\n    aliases: [wreck]\n    maps_to_features: [Wreck]\n')
    write(ep.REGISTRIES[1], 's101_features: {}\n')
    write(ep.FC, json.dumps({'features': [{'code': 'Wreck', 'name': 'Wreck', 'definition': 'original definition', 'bindings': []}], 'attributes': []}))
    nodes = [{'id': 'f', 'name': 'Wreck', 'properties': {'canonical_name': 'Wreck'}}, {'id': 'a', 'name': 'categoryOfWreck', 'properties': {}}]
    edges = [{'id': 'e', 'subject_id': 'f', 'predicate': 'hasAttribute', 'object_id': 'a'}, {'id': 'dangling', 'subject_id': 'f', 'predicate': 'imagined', 'object_id': 'missing'}]
    write(ep.NODES, '\n'.join(map(json.dumps, nodes)))
    write(ep.EDGES, '\n'.join(map(json.dumps, edges)))
    return tmp_path


def test_b0_no_source_even_when_files_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ep, 'ROOT', tmp_path)
    p = ep.build_packet('침선', 'B0')
    assert p['sources'] == [] and p['evidence'] == ''
    assert p['status'] == 'NO_EVIDENCE_BY_DESIGN'


def test_fc_original_source_and_determinism(sources):
    p = ep.build_packet('침선을 설명해', 'B1')
    assert p == ep.build_packet('침선을 설명해', 'B1')
    assert p['sources'][0]['sha256'] == hashlib.sha256((sources / ep.FC).read_bytes()).hexdigest()
    assert json.loads(p['evidence'])['record']['definition'] == 'original definition'
    assert not p['execution_authorized']


def test_kg_only_existing_relationships(sources):
    p = ep.build_packet('wreck', 'B2')
    records = [json.loads(x)['record'] for x in p['evidence'].splitlines()]
    assert len(records) == 1
    assert records[0]['edge']['id'] == 'e'
    assert records[0]['edge']['predicate'] == 'hasAttribute'
    assert {x['id'] for x in records[0]['endpoints']} == {'f', 'a'}


def test_unavailable_and_budget_are_not_synthetic(sources):
    assert ep.build_packet('unmatched_xyz', 'B1')['status'] == 'EVIDENCE_UNAVAILABLE'
    p = ep.build_packet('wreck', 'B2', max_chars=2)
    assert p['evidence'] == '' and p['status'] == 'EVIDENCE_BUDGET_EXHAUSTED'
    (sources / ep.EDGES).unlink()
    p = ep.build_packet('wreck', 'B2')
    assert p['status'] == 'EVIDENCE_UNAVAILABLE' and p['errors']


def test_source_changes_invalidate_cache(sources):
    before = ep.build_packet('wreck', 'B1')
    p = sources / ep.FC
    p.write_text(p.read_text(encoding='utf-8').replace('original definition', 'changed original definition'), encoding='utf-8')
    assert ep.build_packet('wreck', 'B1')['hash'] != before['hash']


def test_invalid_api_arguments():
    with pytest.raises(ValueError): ep.build_packet('x', 'B4')
    with pytest.raises(ValueError): ep.build_packet('x', 'B1', -1)
