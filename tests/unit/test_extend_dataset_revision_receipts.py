import copy
import json
import pytest
from xml.etree import ElementTree as ET
from scripts import extend_dataset_revision_receipts as e
from scripts import repair_source_document_revisions as w


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(w, 'ROOT', tmp_path)
    xml=b'<root><S100_FC_FeatureType><code>F</code><name>Feature</name><definition>Definition</definition></S100_FC_FeatureType></root>'
    (tmp_path/'a.xml').write_bytes(xml)
    source_sha=w.sha(xml)
    old=dict(chunk_id='old',content='Old derived text',source_file='a.xml',source_sha256=source_sha,source_id='s',document_type='feature_catalogue',title='T',section='feature:F',page_no=None,metadata={},embedding='[1]')
    text='S-101 Feature Catalogue feature definition. Feature code: F. Feature name: Feature. Definition: Definition. Aliases: none. Permitted primitives: not specified. Attribute/information bindings: .'
    c={k:old[k] for k in ['source_file','source_sha256','source_id','document_type','title','section','page_no']}
    c.update(chunk_id='new',old_chunk_id='old',old_content_sha256=w.sha(old['content'].encode()),text=text,metadata=dict(extraction_method='fc_direct_xml_fields_v3',content_sha256=w.sha(text.encode()),source_element_sha256=w.sha(ET.tostring(ET.fromstring(xml)[0])),source_fields=[]))
    check=w.verify_source(c,old,{})
    p=dict(stage='PREPARED',batch_id='test',before=dict(rows=[old],rows_sha256=w.digest([old])),candidates=[c],source_validation=[check],source_validation_sha256=w.digest([check]),model=w.MODEL,model_digest=w.DIGEST,dimension=w.DIM)
    p['prepared_sha256']=w.digest(p)
    p.update(stage='EMBEDDED',embeddings=[dict(chunk_id='new',plan_sha256=p['prepared_sha256'],input_sha256=w.sha(text.encode()),model=w.MODEL,model_digest=w.DIGEST,dimension=w.DIM,truncate=False,embedding=[0.1]*w.DIM)])
    emb=tmp_path/'embedded.json';emb.write_text(json.dumps(p))
    retired=copy.deepcopy(old);retired['metadata'].update(retrieval_status='SUPERSEDED',revision_batch_id='test',superseded_by_chunk_ids=['new'])
    after=[retired,w.build_new_rows(p)[0]]
    a=dict(stage='APPLIED',database='gbhd_s101',batch_id='test',artifact_sha256=w.sha(emb.read_bytes()),before_sha256=p['before']['rows_sha256'],after_sha256=w.digest(after),after_rows=after,old_ids=['old'],new_ids=['new'])
    app=tmp_path/'applied.json';app.write_text(json.dumps(a))
    base=tmp_path/'base';base.mkdir()
    records=[dict(chunk_id='old',content_sha256=w.sha(old['content'].encode()),source_sha256=source_sha,status='UNVERIFIED',retrieval_status='ACTIVE'),dict(chunk_id='untouched',content_sha256=w.sha(b'untouched'),status='MISMATCH',extra={'keep':[1,2]})]
    raw=b''.join((json.dumps(r)+'\n').encode() for r in records)
    (base/'compact_receipts.jsonl').write_bytes(raw)
    (base/'receipt_manifest.json').write_text(json.dumps({'files':{'compact_receipts.jsonl':w.sha(raw)}}))
    return base,emb,app,tmp_path/'output'


def test_fc_is_derived_not_literal_and_untargeted_preserved(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch);r=e.extend(*args)
    rows=[json.loads(l) for l in (args[3]/'compact_receipts.jsonl').read_bytes().splitlines()]
    assert rows[0]['retrieval_status']=='SUPERSEDED'
    assert rows[1]==dict(chunk_id='untouched',content_sha256=w.sha(b'untouched'),status='MISMATCH',extra={'keep':[1,2]})
    assert rows[2]['status']=='UNVERIFIED' and rows[2]['derived_field_verification']['status']=='VERIFIED_DERIVED_FIELDS'
    assert r['active_rows']==2 and r['stored_rows']==3 and not r['full_current_db_export']
    assert w.sha((args[3]/'baseline_delta_snapshot.json').read_bytes())==r['snapshot_sha256']
    from scripts.publish_dataset_verification import publish
    pointer=publish(args[3],tmp_path/'isolated_test_publish','test-v1')
    published=json.loads((tmp_path/'isolated_test_publish'/pointer['manifest']).read_bytes())
    assert published['snapshot_kind']=='BASELINE_RECEIPTS_PLUS_APPLIED_DELTA'


@pytest.mark.parametrize('change', ['vector','old_content','source','duplicate','artifact','database'])
def test_apply_mismatch_rejected(tmp_path,monkeypatch,change):
    args=fixture(tmp_path,monkeypatch);a=json.loads(args[2].read_bytes())
    if change=='vector':a['after_rows'][1]['embedding']=json.dumps([0.2]*w.DIM)
    if change=='old_content':a['after_rows'][0]['content']='tampered'
    if change=='source':(tmp_path/'a.xml').write_text('changed')
    if change=='duplicate':a['after_rows'].append(a['after_rows'][0])
    if change=='artifact':a['artifact_sha256']='wrong'
    if change=='database':a['database']='research'
    a['after_sha256']=w.digest(a['after_rows']);args[2].write_text(json.dumps(a))
    with pytest.raises(ValueError):e.extend(*args)
    assert not args[3].exists()


def test_pdf_requires_exact_source_span_before_literal_status(tmp_path,monkeypatch):
    import sys,types
    args=fixture(tmp_path,monkeypatch)
    p=json.loads(args[1].read_bytes());old=p['before']['rows'][0];c=p['candidates'][0]
    (tmp_path/'source.pdf').write_bytes(b'pdf fixture')
    monkeypatch.setitem(sys.modules,'pypdf',types.SimpleNamespace(PdfReader=lambda path:types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda:'North 35 02')])) )
    old.update(content='North 35\n02',source_file='source.pdf',source_sha256=w.sha(b'pdf fixture'))
    c.update(source_file=old['source_file'],source_sha256=old['source_sha256'],old_content_sha256=w.sha(old['content'].encode()),text='North 35 02',metadata=dict(extraction_method='pdf_source_span_revision_v1',content_sha256=w.sha(b'North 35 02'),source_locators=['page:1'],source_extracted_pages_sha256=w.sha(b'North 35 02'),source_char_start=0,source_char_end=11))
    p['before']['rows_sha256']=w.digest([old]);p['source_validation']=[w.verify_source(c,old,{})];p['source_validation_sha256']=w.digest(p['source_validation'])
    embedding=p.pop('embeddings')[0];p.pop('prepared_sha256');p['stage']='PREPARED';p['prepared_sha256']=w.digest(p)
    embedding.update(plan_sha256=p['prepared_sha256'],input_sha256=w.sha(c['text'].encode()))
    p.update(stage='EMBEDDED',embeddings=[embedding]);args[1].write_text(json.dumps(p))
    a=json.loads(args[2].read_bytes());retired=copy.deepcopy(old);retired['metadata'].update(retrieval_status='SUPERSEDED',revision_batch_id='test',superseded_by_chunk_ids=['new'])
    a.update(after_rows=[retired,w.build_new_rows(p)[0]],before_sha256=p['before']['rows_sha256'],artifact_sha256=w.sha(args[1].read_bytes()));a['after_sha256']=w.digest(a['after_rows']);args[2].write_text(json.dumps(a))
    rows=[json.loads(l) for l in (args[0]/'compact_receipts.jsonl').read_bytes().splitlines()];rows[0].update(content_sha256=w.sha(old['content'].encode()),source_sha256=old['source_sha256'])
    raw=b''.join((json.dumps(r)+'\n').encode() for r in rows);(args[0]/'compact_receipts.jsonl').write_bytes(raw);(args[0]/'receipt_manifest.json').write_text(json.dumps({'files':{'compact_receipts.jsonl':w.sha(raw)}}))
    e.extend(*args)
    result=[json.loads(l) for l in (args[3]/'compact_receipts.jsonl').read_bytes().splitlines()][-1]
    assert result['status']=='VERIFIED_TEXT' and not result['coordinate_authority']
    (tmp_path/'source.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError,match='source hash'):
        e.extend(args[0],args[1],args[2],tmp_path/'rejected')
