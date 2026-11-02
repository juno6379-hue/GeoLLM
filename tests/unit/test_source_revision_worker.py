import copy
import pytest
from scripts import repair_source_document_revisions as w


def plan():
    old=dict(chunk_id='old',content='old text',source_id='src',source_file='a.xml',source_sha256='s',document_type='feature_catalogue',title='T',section='feature:F',page_no=None,metadata={},embedding='[1]',keywords=['unchanged'])
    c=dict(chunk_id='new',old_chunk_id='old',old_content_sha256=w.sha(b'old text'),text='new text',metadata={'source_sha256':'s'})
    p=dict(stage='PREPARED',batch_id='b',before={'rows':[old],'rows_sha256':w.digest([old])},candidates=[c],source_validation=[],source_validation_sha256=w.digest([]),model=w.MODEL,model_digest=w.DIGEST,dimension=w.DIM)
    p['prepared_sha256']=w.digest(p)
    return p


def receipt(p):
    return dict(chunk_id='new',plan_sha256=p['prepared_sha256'],input_sha256=w.sha(b'new text'),model=w.MODEL,model_digest=w.DIGEST,dimension=w.DIM,truncate=False,embedding=[0.1]*w.DIM)


def test_plan_tamper_fails():
    p=plan();w.validate_plan(p);p['candidates'][0]['text']='changed'
    with pytest.raises(ValueError):w.validate_plan(p)


def test_model_or_input_receipt_tamper_fails():
    p=plan();r=receipt(p);w.check_receipt(r,p['candidates'][0],p)
    r['truncate']=True
    with pytest.raises(ValueError):w.check_receipt(r,p['candidates'][0],p)


def test_new_rows_preserve_all_original_columns_and_require_new_vector():
    p=plan();p.update(stage='EMBEDDED',embeddings=[receipt(p)])
    r=w.build_new_rows(p)[0]
    assert r['keywords']==['unchanged'] and r['title']=='T' and r['source_id']=='src'
    assert r['chunk_id']=='new' and r['content']=='new text' and r['embedding']!='[1]'
    assert r['metadata']['supersedes_chunk_ids']==['old']


def test_duplicate_old_mapping_rejected():
    p=plan();c=copy.deepcopy(p['candidates'][0]);c['chunk_id']='other'
    with pytest.raises(ValueError):w.validate_candidates(p['candidates']+[c])


def test_resume_uses_checked_receipt_without_model_call(tmp_path,monkeypatch):
    p=plan();src=tmp_path/'plan.json';w.write_new(src,p);dest=tmp_path/'embedded.json'
    folder=tmp_path/'embedded.json.checkpoints';folder.mkdir();w.write_new(folder/'new.json',receipt(p))
    monkeypatch.setattr(w,'check_current_model',lambda:None)
    monkeypatch.setattr(w,'api',lambda *a,**k:pytest.fail('must reuse checked receipt'))
    w.embed(src,dest)
    assert w.read(dest)['stage']=='EMBEDDED' and not (folder/'worker.lock').exists()


def test_embedding_failure_releases_lock_without_publishing(tmp_path,monkeypatch):
    p=plan();src=tmp_path/'plan.json';w.write_new(src,p);dest=tmp_path/'embedded.json'
    monkeypatch.setattr(w,'check_current_model',lambda:None)
    def fail(*a,**k):raise RuntimeError('model unavailable')
    monkeypatch.setattr(w,'api',fail)
    with pytest.raises(RuntimeError):w.embed(src,dest)
    assert not dest.exists() and not (tmp_path/'embedded.json.checkpoints/worker.lock').exists()


def test_pdf_verifies_actual_span_and_rejects_number_change(tmp_path,monkeypatch):
    import sys,types
    source=tmp_path/'source.pdf';source.write_bytes(b'pdf-fixture')
    monkeypatch.setattr(w,'ROOT',tmp_path)
    monkeypatch.setitem(sys.modules,'pypdf',types.SimpleNamespace(PdfReader=lambda p:types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda:'North 35 02')])) )
    old=dict(chunk_id='old',content='North 35\n02',metadata={},embedding='[1]',source_file='source.pdf',source_sha256=w.sha(b'pdf-fixture'),source_id='s',document_type='dataset_source_text',title='T',section='page:1',page_no=1)
    candidate={k:old[k] for k in ['source_file','source_sha256','source_id','document_type','title','section','page_no']}
    candidate.update(chunk_id='new',old_chunk_id='old',old_content_sha256=w.sha(old['content'].encode()),text='North 35 02',metadata=dict(extraction_method='pdf_source_span_revision_v1',content_sha256=w.sha(b'North 35 02'),source_locators=['page:1'],source_extracted_pages_sha256=w.sha(b'North 35 02'),source_char_start=0,source_char_end=11))
    assert w.verify_source(candidate,old,{})['chunk_id']=='new'
    old['content']='North 3502';candidate['old_content_sha256']=w.sha(old['content'].encode())
    with pytest.raises(ValueError,match='numeric'):w.verify_source(candidate,old,{})
