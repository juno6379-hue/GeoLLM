import copy
import pytest

from scripts import repair_source_document_revisions as worker


def test_receipt_rejects_wrong_model_zero_nan_and_wrong_plan():
    candidate={'chunk_id':'new','text':'source text'}
    plan={'prepared_sha256':'a'*64}
    valid=dict(chunk_id='new',plan_sha256='a'*64,input_sha256=worker.sha(b'source text'),
               model=worker.MODEL,model_digest=worker.DIGEST,dimension=worker.DIM,
               truncate=False,embedding=[0.1]*worker.DIM)
    worker.check_receipt(valid,candidate,plan)
    for field,value in [('model_digest','changed'),('plan_sha256','b'*64),
                        ('embedding',[0.0]*worker.DIM),
                        ('embedding',[float('nan')]+[0.1]*(worker.DIM-1))]:
        bad=copy.deepcopy(valid);bad[field]=value
        with pytest.raises(ValueError):worker.check_receipt(bad,candidate,plan)


def test_candidate_mapping_cannot_reuse_original_or_duplicate_new_id():
    a=dict(chunk_id='new',original_chunk_id='old',original_content_sha256='a'*64,text='source')
    worker.validate_candidates([a])
    with pytest.raises(ValueError):worker.validate_candidates([{**a,'chunk_id':'old'}])
    with pytest.raises(ValueError):worker.validate_candidates([a,{**a,'original_chunk_id':'other'}])


def test_existing_worker_lock_prevents_any_model_call(tmp_path,monkeypatch):
    # The lock is conservative: a hard-kill lock requires supervised recovery.
    plan={'prepared_sha256':'a'*64,'stage':'PREPARED'}
    monkeypatch.setattr(worker,'read',lambda p:plan)
    monkeypatch.setattr(worker,'validate_plan',lambda p:None)
    monkeypatch.setattr(worker,'check_current_model',lambda:pytest.fail('must not call model'))
    target=tmp_path/'embedded.json';folder=tmp_path/'embedded.json.checkpoints';folder.mkdir()
    lock=folder/'worker.lock';lock.write_text('existing')
    with pytest.raises(FileExistsError):worker.embed(tmp_path/'prepared.json',target)
    assert lock.read_text()=='existing'
    assert not target.exists()


def test_changed_raw_source_stops_before_write_transaction(tmp_path,monkeypatch):
    artifact=tmp_path/'embedded.json';artifact.write_bytes(b'preserved artifact')
    (tmp_path/'source.pdf').write_bytes(b'changed source')
    plan={'candidates':[{'original_chunk_id':'old','source_file':'source.pdf',
                         'source_sha256':worker.sha(b'original source')}]}
    monkeypatch.setattr(worker,'ROOT',tmp_path)
    monkeypatch.setattr(worker,'read',lambda p:plan)
    monkeypatch.setattr(worker,'build_new_rows',lambda p:[])
    monkeypatch.setattr(worker,'check_current_model',lambda:None)
    monkeypatch.setattr(worker,'connect',lambda *a,**k:pytest.fail('must not open write transaction'))
    with pytest.raises(ValueError,match='Source changed after preparation'):
        worker.apply(artifact,worker.sha(artifact.read_bytes()),tmp_path/'applied.json')
