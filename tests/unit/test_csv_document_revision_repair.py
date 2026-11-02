import copy
import hashlib
import json
from unittest.mock import Mock

import pytest

from scripts import repair_csv_document_revision as repair


def plan():
    old = [dict(chunk_id=i, source_sha256=repair.SOURCE_SHA,document_type='law',
                source_file=repair.SOURCE, metadata={}, embedding='[0.1,0.2]',
                content='old', document_id='document') for i in repair.OLD_IDS]
    candidates = [dict(chunk_id=f'new{i}',text=f'corrected {i}',metadata={
        'source_sha256':repair.SOURCE_SHA,'extraction_revision':'csv_positional_v2',
        'document_id':'document','document_type':'law','source_file':repair.SOURCE}) for i in range(6)]
    embeddings = [dict(chunk_id=r['chunk_id'], input_sha256=hashlib.sha256(r['text'].encode()).hexdigest(),
        embedding=[0.1]*1024, model=repair.MODEL,model_digest=repair.DIGEST,
        dimension=1024,truncate=False) for r in candidates]
    return dict(stage='EMBEDDED',batch_id='fixture',before={'rows':old,'rows_sha256':repair.digest(old)},
                candidates=candidates, embeddings=embeddings)


def test_new_revision_never_reuses_original_vector_or_model_claim():
    value=plan(); original=copy.deepcopy(value)
    rows=repair.build_new_rows(value)
    assert value==original
    assert len(rows)==6
    assert set(r['chunk_id'] for r in rows).isdisjoint(repair.OLD_IDS)
    for row in rows:
        assert row['metadata']['historical_embedding_model'] is None
        assert row['metadata']['embedding']['model_digest']==repair.DIGEST
        assert row['metadata']['retrieval_status']=='ACTIVE'
        assert len(json.loads(row['embedding']))==1024


@pytest.mark.parametrize('field,value',[('input_sha256','bad'),('model_digest','bad'),
    ('model','another'),('truncate',True),('embedding',[0.0]*1024),
    ('embedding',[float('nan')]*1024),('embedding',[1.0]*10)])
def test_bad_embedding_receipt_fails_closed(field,value):
    item=plan(); item['embeddings'][0][field]=value
    with pytest.raises(ValueError): repair.build_new_rows(item)


def test_original_export_tamper_rejected():
    item=plan(); item['before']['rows'][0]['content']='changed'
    with pytest.raises(ValueError): repair.build_new_rows(item)


def test_revision_collision_rejected():
    item=plan(); item['candidates'][0]['chunk_id']=repair.OLD_IDS[0]
    item['embeddings'][0]['chunk_id']=repair.OLD_IDS[0]
    with pytest.raises(ValueError): repair.build_new_rows(item)


def test_apply_artifact_hash_mismatch_does_not_connect(tmp_path,monkeypatch):
    path=tmp_path/'artifact.json'; path.write_text('{}')
    connect=Mock(side_effect=AssertionError('must not connect'))
    monkeypatch.setattr(repair,'connect',connect)
    with pytest.raises(ValueError): repair.apply(path,'wrong',tmp_path/'out')
    connect.assert_not_called()


def test_current_query_model_mismatch_never_calls_model(monkeypatch):
    monkeypatch.setenv('EMBEDDING_MODEL','other')
    api=Mock(side_effect=AssertionError('must not call'))
    monkeypatch.setattr(repair,'api',api)
    with pytest.raises(ValueError): repair.check_current_model()
    api.assert_not_called()


def test_export_is_immutable(tmp_path):
    path=tmp_path/'preserved.json'; repair.write_new(path, {'original':True})
    with pytest.raises(FileExistsError): repair.write_new(path, {'original':False})
    assert repair.read(path)=={'original':True}


def test_apply_concurrent_change_refuses_before_any_archive_or_write(tmp_path,monkeypatch):
    from unittest.mock import MagicMock
    value=plan(); path=tmp_path/'plan.json'; repair.write_new(path,value)
    expected=hashlib.sha256(path.read_bytes()).hexdigest()
    conn=MagicMock(); conn.__enter__.return_value=conn
    monkeypatch.setattr(repair,'connect',Mock(return_value=conn))
    monkeypatch.setattr(repair,'check_current_model',Mock())
    changed=copy.deepcopy(value['before']['rows']); changed[0]['embedding']='[9]'
    monkeypatch.setattr(repair,'fetch_rows',Mock(return_value=changed))
    archive=Mock(side_effect=AssertionError('no archive or writes before CAS'))
    monkeypatch.setattr(repair,'archived',archive)
    with pytest.raises(ValueError,match='changed since'): repair.apply(path,expected,tmp_path/'receipt')
    archive.assert_not_called()
    assert conn.__exit__.call_args.args[0] is ValueError


def test_existing_receipt_prevents_mutation(tmp_path,monkeypatch):
    output=tmp_path/'receipt.json'; output.write_text('{}')
    connect=Mock(side_effect=AssertionError('must not connect'))
    monkeypatch.setattr(repair,'connect',connect)
    with pytest.raises(FileExistsError): repair.apply('missing','hash',output)
    with pytest.raises(FileExistsError): repair.rollback('missing','hash',output)
    connect.assert_not_called()
