import json
from pathlib import Path
import pytest

from research.marine_geollm_scie.runners import derive_execution_snapshot as d


def parent_fixture(tmp_path):
    root = tmp_path/'root'; root.mkdir()
    parent_dir = tmp_path/'parent'; parent_dir.mkdir()
    records = []
    for relation in d.RELATION_KEYS:
        name = relation.replace('.', '__')+'.csv'
        p = parent_dir/name; p.write_bytes(b'id\n1\n')
        records.append({'relation': relation, 'csv_path': name, 'sha256': d.digest(p), 'rows': 1})
    code = 'services/orchestrator/query_normalizer.py'
    data = 'data/fixed.json'
    for name, value in [(code, 'old code'), (data, 'fixed data')]:
        p = root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(value)
    parent = {'status': 'LOADED_VERIFIED', 'db_identity': {'container': d.TARGET_CONTAINER, 'database': d.DATABASE},
        'relations': records, 'files': [{'path': name, 'sha256': d.digest(root/name)} for name in (code, data)]}
    (root/code).write_text('new code')
    return root, parent_dir, parent, code, data


def test_only_requested_execution_code_can_change(tmp_path):
    root, folder, parent, code, data = parent_fixture(tmp_path)
    changes = d.validate_parent(parent, folder, [code], root)
    assert len(changes) == 1 and changes[0]['path'] == code
    assert changes[0]['parent_sha256'] != changes[0]['derived_sha256']
    with pytest.raises(ValueError, match='Non-authorized'):
        d.validate_parent(parent, folder, ['services/orchestrator/graph_rag_retriever.py'], root)


def test_cannot_rebaseline_data_even_with_explicit_request(tmp_path):
    root, folder, parent, code, data = parent_fixture(tmp_path)
    with pytest.raises(ValueError, match='allowlist'):
        d.validate_parent(parent, folder, [code, data], root)
    (root/data).write_text('changed data')
    with pytest.raises(ValueError, match='Non-authorized'):
        d.validate_parent(parent, folder, [code], root)


def test_original_csv_change_rejected(tmp_path):
    root, folder, parent, code, _ = parent_fixture(tmp_path)
    (folder/parent['relations'][0]['csv_path']).write_text('changed')
    with pytest.raises(ValueError, match='Parent data'):
        d.validate_parent(parent, folder, [code], root)


def test_escape_and_missing_relation_rejected(tmp_path):
    root, folder, parent, code, _ = parent_fixture(tmp_path)
    parent['relations'][0]['csv_path'] = '../escape.csv'
    with pytest.raises(ValueError, match='escapes'):
        d.validate_parent(parent, folder, [code], root)
    parent['relations'].pop()
    with pytest.raises(ValueError, match='six'):
        d.validate_parent(parent, folder, [code], root)


def test_actual_export_uses_readonly_and_exact_digest(tmp_path, monkeypatch):
    root, folder, parent, code, _ = parent_fixture(tmp_path)
    record = parent['relations'][0]
    calls = []
    def fake_run(command, **kwargs):
        calls.append(command)
        kwargs['stdout'].write(b'id\n1\n')
    monkeypatch.setattr(d.subprocess, 'run', fake_run)
    result = d.export_relation(record, tmp_path/'verified.csv')
    assert result['content_match'] is True
    assert 'REPEATABLE READ READ ONLY' in calls[0][-1]
    assert 'TO STDOUT' in calls[0][-1]
    assert 'INSERT' not in calls[0][-1]
    record['sha256'] = 'wrong'
    with pytest.raises(ValueError, match='differs'):
        d.export_relation(record, tmp_path/'failed.csv')
    assert (tmp_path/'failed.csv').exists()


def test_derived_manifest_parent_immutable_and_lineage_preserved(tmp_path, monkeypatch):
    root, folder, parent, code, _ = parent_fixture(tmp_path)
    path = folder/'snapshot_manifest.json'
    path.write_text(json.dumps(parent))
    original = path.read_bytes()
    validate = d.validate_parent
    monkeypatch.setattr(d, 'validate_parent', lambda p, f, c: validate(p, f, c, root))
    monkeypatch.setattr(d.subprocess, 'check_output', lambda command: json.dumps([{'Config': {'Labels': {'marine.scie.research': 'true'}}}]).encode())
    def export(record, destination):
        destination.write_bytes((folder/record['csv_path']).read_bytes())
        return {'relation': record['relation'], 'content_match': True, 'roundtrip_sha256': d.digest(destination)}
    monkeypatch.setattr(d, 'export_relation', export)
    from research.marine_geollm_scie.runners import binding_snapshot
    monkeypatch.setattr(binding_snapshot, 'ROOT', root)
    result = d.derive(path, tmp_path/'new', [code])
    assert path.read_bytes() == original
    assert result['status'] == 'LOADED_VERIFIED'
    assert result['relations'] == parent['relations']
    assert result['derivation']['all_six_db_content_hashes_match_parent']
    assert result['derivation']['data_rebaselined'] is False
    with pytest.raises(FileExistsError):
        d.derive(path, tmp_path/'new', [code])
