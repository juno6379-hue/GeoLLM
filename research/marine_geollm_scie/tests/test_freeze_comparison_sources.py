import json
import pytest
from research.marine_geollm_scie.runners import freeze_comparison_sources as module


def test_execution_sources_exclude_ui_and_runtime_feedback(tmp_path):
    for name in ('services/a.py','shared/a.py','services/static/a.js',
                 'data/x.yaml','data/feedback/a.jsonl','research/marine_geollm_scie/runners/a.py'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('')
    paths={p.relative_to(tmp_path).as_posix() for p in module.execution_files(tmp_path)}
    assert paths=={'services/a.py','shared/a.py','data/x.yaml','research/marine_geollm_scie/runners/a.py'}


def test_existing_snapshot_never_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        module.freeze(tmp_path/'absent.json',tmp_path)


def test_nonresearch_parent_rejected_before_export(tmp_path):
    parent=tmp_path/'parent.json';parent.write_text(json.dumps({'status':'LOADED_VERIFIED','db_identity':{'database':'production'}}))
    with pytest.raises(ValueError,match='verified research'):
        module.freeze(parent,tmp_path/'new')
