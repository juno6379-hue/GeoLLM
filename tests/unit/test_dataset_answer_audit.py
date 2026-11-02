from scripts.audit_dataset_answer_usage import inspect, write


def test_missing_response_is_not_success():
    assert inspect({})['passed'] is False


def test_negative_response_cannot_hide_an_unrelated_passage():
    row = {'observation': 'COMPLETED_EVENT_RECEIVED', 'completion': {'final_result': {
        'error_code': 'DATASET_DOCUMENT_EVIDENCE_NOT_FOUND',
        'structured_result': {'coordinate_authority': False, 'search_execution': {'status': 'NOT_RUN'},
                              'source_passages': [{'quote': 'unrelated'}]},
        'orchestrator_v2': {'query_execution_context': {'route_plan': {'analysis_type': 'dataset_document_lookup'}}}}}}
    assert inspect(row, negative=True)['passed'] is False


def test_status_write_retries_transient_windows_reader_lock(tmp_path, monkeypatch):
    from pathlib import Path
    original = Path.replace
    count = []

    def replace(self, target):
        count.append(1)
        if len(count) == 1:
            raise PermissionError('reader lock')
        return original(self, target)

    monkeypatch.setattr(Path, 'replace', replace)
    monkeypatch.setattr('scripts.audit_dataset_answer_usage.time.sleep', lambda _: None)
    path = tmp_path / 'status.json'
    write(path, {'status': 'RUNNING'})
    assert len(count) == 2
    assert 'RUNNING' in path.read_text()
