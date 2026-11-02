import json
from tools.scie_results_ui.dataset_audit import PREFIX, load_progress


def test_progress_projects_only_safe_fields_and_no_raw_reads(tmp_path):
    path = tmp_path / PREFIX / 'source/status.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(status='RUNNING', counts={'scanned': 3, 'unknown': None, 'bad': -1, 'false': False},
        raw_document='secret', limitations=['partial'], evidence=[{'path': 'research/holdout/private.json'},
        {'path': (PREFIX / 'source/result.json').as_posix(), 'sha256': None}])) )
    result = load_progress(tmp_path)
    assert result['status'] == 'RUNNING'
    row = result['stages'][0]
    assert row['counts'] == {'scanned': 3, 'unknown': None}
    assert 'raw_document' not in row
    assert len(row['evidence']) == 1
    assert result['stages'][1]['status'] == 'NOT_STARTED'
    assert result['dataset_semantic_audit_complete'] is False


def test_partial_status_write_does_not_become_success(tmp_path):
    path = tmp_path / PREFIX / 'answer/status.json'
    path.parent.mkdir(parents=True)
    path.write_text('{')
    result = load_progress(tmp_path)
    assert result['stages'][2]['status'] == 'UNAVAILABLE_LOCAL_ARTIFACT'


def test_followup_progress_is_separate_and_never_replaces_baseline(tmp_path):
    from tools.scie_results_ui.dataset_audit import FOLLOWUP_PREFIX
    path = tmp_path / FOLLOWUP_PREFIX / 'pdf/status.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'status':'RUNNING','counts':{'target_chunks':2654},'evidence':[{'path':str(FOLLOWUP_PREFIX / 'pdf/result.json')},{'path':'research/holdout/answers.json'}]}))
    result = load_progress(tmp_path)
    assert result['stages'][0]['stage'] == 'source'
    row = next(x for x in result['stages'] if x['stage']=='followup_pdf')
    assert row['counts']['target_chunks'] == 2654
    assert len(row['evidence']) == 1
    assert result['holdout_used'] is False
    assert result['dataset_semantic_audit_complete'] is False
