import json
import pytest
from scripts.audit_xlsx_receipt_quality import assess_cell_span, audit, sha
from scripts.verify_xlsx_source_revision import decode_cells
from tests.unit.test_xlsx_source_revision import workbook
from services.orchestrator.dataset_verification import filter_answer_documents, verify_document


def test_storage_string_indexes_are_not_resolved_cells():
    decoded = decode_cells(workbook())
    assert assess_cell_span('Archive member: a.xlsx. 0 4', 'a.xlsx', decoded)['status'] == 'CELL_TEXT_UNVERIFIED'
    result = assess_cell_span('Archive member: a.xlsx. 부산항 4', 'a.xlsx', decoded)
    assert result['status'] == 'VERIFIED_CELL_TEXT'
    assert [r['address'] for r in result['locators']] == ['A1', 'B1']


def test_real_numeric_cells_are_not_blocked_by_numeric_heuristic():
    decoded = decode_cells(workbook('<c r="A1"><v>683</v></c><c r="B1"><v>694</v></c>'))
    assert assess_cell_span('683 694', 'a.xlsx', decoded)['status'] == 'VERIFIED_CELL_TEXT'
    assert assess_cell_span('83 694', 'a.xlsx', decoded)['reason'] == 'PARTIAL_CELL_TOKEN_BOUNDARY'


def fixture_quality(status='CELL_TEXT_UNVERIFIED'):
    doc = {'doc_id':'a', 'content':'body', 'source_sha256':'a'*64}
    record = {'chunk_id':'a', 'content_sha256':sha(b'body'), 'source_sha256':'a'*64, 'status':'VERIFIED_TEXT',
              'extraction_quality':{'status':status,'reason':'NO_DECODED_CELL_VALUE_SPAN',
                'scope':'XLSX_DECODED_CELL_VALUES_AT_AUDIT_TIME','source_member':'source.xlsx','evidence_sha256':'b'*64}}
    return doc, ({'a':record}, {'extraction_quality_sha256':'b'*64})


def test_quality_guard_applies_even_to_legacy_verified_receipt():
    doc, receipts = fixture_quality()
    accepted, excluded = filter_answer_documents([doc], receipts)
    assert not accepted and excluded[0]['source_text_verification']['status'] == 'SOURCE_EXTRACTION_UNVERIFIED'
    doc['source_sha256'] = None
    assert not filter_answer_documents([doc], receipts)[0]


def test_verified_cell_span_is_usable_but_not_semantic_authority():
    doc, receipts = fixture_quality('VERIFIED_CELL_TEXT')
    accepted, excluded = filter_answer_documents([doc], receipts)
    assert accepted and not excluded
    assert accepted[0]['source_text_verification']['status'] == 'AUDIT_SNAPSHOT_MATCH'
    assert not accepted[0]['source_text_verification']['semantic_correctness_verified']
    assert not filter_answer_documents([doc], (receipts[0], {}))[0]


def test_new_overlay_preserves_old_receipt_and_rejects_changed_inputs(tmp_path):
    raw = workbook()
    (tmp_path/'a.xlsx').write_bytes(raw)
    old = dict(chunk_id='a', content='0 4', source_file='a.xlsx', source_sha256=sha(raw))
    snapshot = tmp_path/'snapshot.jsonl'
    snapshot.write_text(json.dumps(old), encoding='utf-8')
    record = dict(chunk_id='a', content_sha256=sha(b'0 4'), source_sha256=sha(raw),
                  source_locator='a.xlsx', status='VERIFIED_TEXT')
    receipt_raw = (json.dumps(record)+'\n').encode()
    (tmp_path/'receipts.jsonl').write_bytes(receipt_raw)
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'complete':True,'rows':1,'files':{'receipts.jsonl':sha(receipt_raw)}}))
    manifest_raw = manifest.read_bytes()
    result = audit(tmp_path,manifest,sha(manifest_raw),snapshot,sha(snapshot.read_bytes()),tmp_path/'new')
    assert result['changed_verified_to_unverified'] == 1
    assert manifest.read_bytes() == manifest_raw
    assert (tmp_path/'receipts.jsonl').read_bytes() == receipt_raw
    updated = json.loads((tmp_path/'new/compact_receipts.jsonl').read_bytes())
    assert updated['status']=='UNVERIFIED'
    assert updated['extraction_quality']['status']=='CELL_TEXT_UNVERIFIED'
    with pytest.raises(ValueError,match='Pinned'):
        audit(tmp_path,manifest,'0'*64,snapshot,sha(snapshot.read_bytes()),tmp_path/'bad')


def test_answer_excludes_unverified_extraction_without_claiming_source_absence(monkeypatch):
    from services.orchestrator import dataset_answer as answer
    from tests.unit.test_dataset_answer import evidence
    query = '다대포항 안내정보를 알려줘'
    source = evidence(query)
    doc = source['documents'][0]
    _, receipts = fixture_quality()
    record = receipts[0]['a']
    record.update(chunk_id=doc['chunk_id'], content_sha256=sha(doc['content'].encode()), source_sha256=doc['source_sha256'])
    monkeypatch.setattr(answer, 'retrieve', lambda *a, **k: source)
    monkeypatch.setattr(answer, 'load_receipts', lambda: ({doc['chunk_id']:record}, receipts[1]))
    final = answer.build_dataset_answer({'query':query,'task_id':'t'})['final_dict']
    assert final['error_code'] == 'DATASET_SOURCE_EXTRACTION_UNVERIFIED'
    assert final['structured_result']['source_passages'] == []
    assert final['structured_result']['source_text_audit']['excluded_extraction_unverified_chunks'] == 1
    assert '자료가 없다는 뜻은 아닙니다' in final['summary']


@pytest.mark.parametrize('tamper', ['missing', 'changed'])
def test_published_quality_sidecar_is_required_for_positive_receipt(tmp_path, tamper):
    from scripts.publish_dataset_verification import publish
    from services.orchestrator.dataset_verification import load_receipts
    doc, receipts = fixture_quality('VERIFIED_CELL_TEXT')
    quality = b'quality evidence\n'
    lineage = b'lineage\n'
    record = receipts[0]['a']
    record['extraction_quality']['evidence_sha256'] = sha(quality)
    raw = (json.dumps(record)+'\n').encode()
    source = tmp_path/'source'
    source.mkdir()
    (source/'compact_receipts.jsonl').write_bytes(raw)
    (source/'quality_evidence.jsonl').write_bytes(quality)
    (source/'quality_lineage.json').write_bytes(lineage)
    manifest = dict(complete=True, rows=1, audited_at='2026-11-02',
                    snapshot_file='quality_lineage.json', snapshot_sha256=sha(lineage),
                    extraction_quality_sha256=sha(quality), files={'compact_receipts.jsonl':sha(raw)})
    (source/'receipt_manifest.json').write_text(json.dumps(manifest))
    destination = tmp_path/'published'
    publish(source, destination, 'new')
    assert (destination/'new/quality_lineage.json').read_bytes() == lineage
    assert filter_answer_documents([doc], load_receipts(destination))[0]
    sidecar = destination/'new/quality_evidence.jsonl'
    if tamper == 'missing':
        sidecar.unlink()
    else:
        sidecar.write_bytes(b'changed')
    loaded = load_receipts(destination)
    assert loaded[0]  # Retain receipts so quality-specific failure stays closed.
    accepted, excluded = filter_answer_documents([doc], loaded)
    assert not accepted and excluded[0]['source_text_verification']['reason'] == 'EXTRACTION_QUALITY_EVIDENCE_UNBOUND'
    (source/'quality_evidence.jsonl').write_bytes(b'changed')
    with pytest.raises(ValueError, match='sidecar hash'):
        publish(source, destination, 'bad')
    assert not (destination/'bad').exists()


def test_publisher_rejects_unsafe_snapshot_sidecar(tmp_path):
    from scripts.publish_dataset_verification import publish
    from tests.unit.test_dataset_verification import snapshot
    snapshot(tmp_path)
    source = tmp_path/'audit'
    manifest = json.loads((source/'receipt_manifest.json').read_bytes())
    manifest['snapshot_file'] = '../outside.json'
    (source/'receipt_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Unsafe audit sidecar'):
        publish(source,tmp_path/'published','bad')
