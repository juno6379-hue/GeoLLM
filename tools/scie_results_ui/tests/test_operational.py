import hashlib
import json
from tools.scie_results_ui.adapter import ResultsAdapter
from tools.scie_results_ui.operational import SUMMARY, load_summary
import pytest


def test_operational_summary_rejects_modified_evidence(tmp_path):
    folder = tmp_path / 'research/marine_geollm_scie' / SUMMARY
    folder.parent.mkdir(parents=True)
    folder.write_text(json.dumps({'paper_experiment': False, 'holdout_evaluation_executed': False, 'total_cases': 8}))
    manifest = folder.parent / 'manifest.json'
    manifest.write_text(json.dumps({'summary_sha256': hashlib.sha256(folder.read_bytes()).hexdigest()}))
    assert load_summary(ResultsAdapter(tmp_path))['total_cases'] == 8
    folder.write_text('{}')
    assert load_summary(ResultsAdapter(tmp_path))['status'] == 'UNAVAILABLE_LOCAL_ARTIFACT'


def test_missing_operational_summary_is_not_zero(tmp_path):
    assert load_summary(ResultsAdapter(tmp_path)) == {'status': 'UNAVAILABLE_LOCAL_ARTIFACT'}


def test_changed_operational_source_preserves_historical_result(tmp_path):
    folder = tmp_path / 'research/marine_geollm_scie' / SUMMARY
    folder.parent.mkdir(parents=True)
    folder.write_text(json.dumps({'paper_experiment': False, 'holdout_evaluation_executed': False, 'total_cases': 8}))
    (tmp_path / 'source.py').write_text('new')
    (folder.parent / 'manifest.json').write_text(json.dumps({
        'summary_sha256': hashlib.sha256(folder.read_bytes()).hexdigest(),
        'operational_source_sha256': {'source.py': hashlib.sha256(b'old').hexdigest()}}))
    result = load_summary(ResultsAdapter(tmp_path))
    assert result['total_cases'] == 8
    assert result['historical_verification_valid'] is True
    assert result['current_source_freshness'] == 'CHANGED'


def test_latest_pointer_selects_hash_bound_version_and_keeps_old_summary(tmp_path):
    research=tmp_path / 'research/marine_geollm_scie'
    old=research / SUMMARY
    old.parent.mkdir(parents=True)
    old.write_text('old immutable')
    folder=research / 'operational/new_v2'
    folder.mkdir()
    summary=folder / 'summary.json'
    summary.write_text(json.dumps(dict(paper_experiment=False,holdout_evaluation_executed=False,total_cases=8)))
    manifest=folder / 'manifest.json'
    manifest.write_text(json.dumps(dict(summary_sha256=hashlib.sha256(summary.read_bytes()).hexdigest())))
    (research / 'operational/latest.json').write_text(json.dumps(dict(manifest='operational/new_v2/manifest.json',sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())))
    result=load_summary(ResultsAdapter(tmp_path))
    assert result['total_cases']==8 and result['summary_path']=='operational/new_v2/summary.json'
    assert old.read_text()=='old immutable'
    manifest.write_text('{}')
    assert load_summary(ResultsAdapter(tmp_path))=={'status':'UNAVAILABLE_LOCAL_ARTIFACT'}


@pytest.mark.parametrize('pointer', ['{', '{}', '{"manifest":"../../private/manifest.json","sha256":"x"}'])
def test_invalid_latest_pointer_never_silently_falls_back(tmp_path,pointer):
    path=tmp_path / 'research/marine_geollm_scie/operational/latest.json'
    path.parent.mkdir(parents=True)
    path.write_text(pointer)
    assert load_summary(ResultsAdapter(tmp_path))=={'status':'UNAVAILABLE_LOCAL_ARTIFACT'}


def test_generator_preserves_existing_version_and_pointer(monkeypatch,tmp_path):
    from tools.scie_results_ui import operational
    monkeypatch.setattr(operational,'read_verified',lambda *a:([],{},{}))
    operational.generate(tmp_path,'outputs/test','test_v2')
    pointer=tmp_path / 'research/marine_geollm_scie/operational/latest.json'
    original=pointer.read_bytes()
    with pytest.raises(FileExistsError):
        operational.generate(tmp_path,'outputs/test','test_v2')
    assert pointer.read_bytes()==original
