import pytest
from scripts.complete_dataset_embeddings import validate_vectors


def test_invalid_remote_vectors_rejected_before_db_write():
    for vectors in ([[float('nan')]*1024], [[0.0]*1024], [[True]*1024], [[1.0]*1000], []):
        with pytest.raises(ValueError): validate_vectors(vectors,1)


def test_finite_complete_vectors_accepted():
    validate_vectors([[0.25]*1024,[0.5]*1024],2)
    with pytest.raises(ValueError):validate_vectors([[0.25]*1024],2)


def test_same_input_retry_is_bounded_and_recorded(monkeypatch,tmp_path):
    import json
    from scripts import complete_dataset_embeddings as worker
    calls=[]
    def fail(path,payload):
        calls.append(payload)
        raise worker.ModelHTTPError(400,b'{"error":"temporary failure"}')
    monkeypatch.setattr(worker,'api',fail)
    monkeypatch.setattr(worker,'check_model',lambda:None)
    monkeypatch.setattr(worker.time,'sleep',lambda _:None)
    with pytest.raises(worker.ModelHTTPError):worker.embed_batch([('id','original full text','source')],12,tmp_path)
    assert len(calls)==2 and calls[0]==calls[1]
    assert calls[0]['truncate'] is False
    records=[json.loads(s) for s in (tmp_path/'errors.jsonl').read_text().splitlines()]
    assert [r['retry_same_input'] for r in records]==[True,False]
    assert 'original full text' not in (tmp_path/'errors.jsonl').read_text()


def test_transient_error_then_success_and_failure_state(monkeypatch,tmp_path):
    import json
    from scripts import complete_dataset_embeddings as worker
    results=iter([worker.ModelHTTPError(400,b'error'),{'embeddings':[[0.25]*1024]}])
    def api(*args):
        value=next(results)
        if isinstance(value,Exception):raise value
        return value
    monkeypatch.setattr(worker,'api',api)
    monkeypatch.setattr(worker,'check_model',lambda:None)
    monkeypatch.setattr(worker.time,'sleep',lambda _:None)
    result=worker.embed_batch([('id','text','source')],12,tmp_path)
    worker.validate_vectors(result['embeddings'],1)
    for name in ('progress.json','manifest.json'):worker.write(tmp_path/name,{'status':'RUNNING','pending':42})
    worker.mark_failed(tmp_path,ValueError())
    worker.mark_failed(tmp_path,RuntimeError())
    for name in ('progress.json','manifest.json'):
        state=json.loads((tmp_path/name).read_text())
        assert state['status']=='FAILED' and state['pending']==42 and state['error_type']=='ValueError'
