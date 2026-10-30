import pytest
from research.marine_geollm_scie.baselines.production_adapter import observable, extract_artifacts, require_isolation, row_base


def test_host_cannot_invoke_production_adapter(monkeypatch):
    monkeypatch.delenv("SCIE_ISOLATED_GRAPH", raising=False)
    with pytest.raises(RuntimeError): require_isolation()


def test_observable_receipts_and_evidence_preserved_without_private_fields():
    state = {"query_execution_context": {"contract_version": "geollm.execution.v1", "slots": {"distance_m": 100},
        "provenance": {"execution_validation": {"authority": "ExecutionValidator", "input_hash": "abc"}}},
        "final_dict": {"evidence_bundle": {"source": "fixture"}}, "thinking": "private", "api_key": "secret"}
    sanitized = observable(state)
    assert "thinking" not in sanitized and sanitized["api_key"] == "[REDACTED]"
    captured = extract_artifacts(sanitized)
    assert captured["full_qec"]["slots"]["distance_m"] == 100
    assert captured["validator_receipts"][0]["input_hash"] == "abc"
    assert captured["evidence_bundles"] == [{"source": "fixture"}]


def test_graph_return_is_never_automatically_spatial_success():
    row = row_base({"case_id": "test", "query": "query"}, 0)
    assert row["execution_success"] is None and row["spatial_correct"] is None
    assert row["method"] == "P_current_production_no_llm"


def test_launcher_fails_closed_on_network_or_env_mask(tmp_path):
    from research.marine_geollm_scie.runners.launch_production import isolation_metadata
    mask = tmp_path / "empty.env"
    mask.write_text("")
    measured = isolation_metadata(mask, {"Internal": True, "Id": "unit-fixture"})
    assert measured["dotenv_mask_source_size_bytes"] == 0
    with pytest.raises(RuntimeError): isolation_metadata(mask, {"Internal": False})
    mask.write_text("not-empty")
    with pytest.raises(RuntimeError): isolation_metadata(mask, {"Internal": True})


def test_expanded_database_requires_explicit_manifest_and_allowlist(tmp_path):
    from research.marine_geollm_scie.runners.launch_production import snapshot_selection
    with pytest.raises(ValueError): snapshot_selection('production')
    with pytest.raises(ValueError): snapshot_selection('scie_binding_v2')
    manifest = tmp_path / 'snapshot.json'
    manifest.write_text('{"status":"LOADED_VERIFIED","db_identity":{"container":"marine-scie-pilot-db","database":"scie_binding_v2"},"relations":[],"files":[]}')
    path, data = snapshot_selection('scie_binding_v2', manifest)
    assert path == manifest.resolve() and data['db_identity']['database'] == 'scie_binding_v2'


def test_adapter_rejects_database_url_outside_selected_snapshot(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.setattr(Path, 'exists', lambda _: True)
    monkeypatch.setenv('SCIE_ISOLATED_GRAPH', '1')
    monkeypatch.setenv('SCIE_RESEARCH_DATABASE', 'scie_binding_v2')
    manifest = tmp_path / 'snapshot.json'
    manifest.write_text('{"status":"LOADED_VERIFIED","db_identity":{"container":"marine-scie-pilot-db","database":"scie_binding_v2"}}')
    monkeypatch.setenv('SCIE_SNAPSHOT_MANIFEST', str(manifest))
    monkeypatch.setenv('S101_DB_URL', 'postgresql://marine-scie-pilot-db/scie_pilot')
    with pytest.raises(RuntimeError, match='isolated research snapshot'): require_isolation()


def test_snapshot_rejects_unloaded_or_changed_csv(tmp_path):
    import json
    from research.marine_geollm_scie.runners.launch_production import snapshot_selection
    manifest = tmp_path / 'snapshot.json'
    manifest.write_text(json.dumps({'status':'EXPORTED', 'db_identity':{'container':'marine-scie-pilot-db','database':'scie_binding_v2'}}))
    with pytest.raises(ValueError, match='loaded'): snapshot_selection('scie_binding_v2', manifest)
    data = {'status':'LOADED_VERIFIED', 'db_identity':{'container':'marine-scie-pilot-db','database':'scie_binding_v2'},
        'relations':[{'csv_path':'rows.csv','sha256':'invalid'}], 'files':[]}
    (tmp_path / 'rows.csv').write_text('changed')
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='changed'): snapshot_selection('scie_binding_v2', manifest)
