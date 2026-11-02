import hashlib
import json
import pytest
from services.orchestrator.dataset_verification import load_receipts, verify_document
from scripts.publish_dataset_verification import publish


def snapshot(tmp_path, status='VERIFIED_TEXT'):
    source = tmp_path / 'audit'
    source.mkdir()
    row = dict(chunk_id='c1', content_sha256=hashlib.sha256(b'body').hexdigest(),
               source_sha256='a'*64, source_locator='page 1', status=status)
    raw = (json.dumps(row)+'\n').encode()
    (source / 'compact_receipts.jsonl').write_bytes(raw)
    (source / 'receipt_manifest.json').write_text(json.dumps(dict(complete=True, rows=1,
        files={'compact_receipts.jsonl':hashlib.sha256(raw).hexdigest()}, audited_at='2026-11-02', snapshot_sha256='f'*64)))
    target = tmp_path / 'published'
    publish(source, target, 'v1')
    return target


def test_exact_current_chunk_identity_required(tmp_path):
    receipt = load_receipts(snapshot(tmp_path))
    doc = dict(chunk_id='c1', content='body', source_sha256='a'*64)
    verified = verify_document(doc, receipt)
    assert verified['status'] == 'AUDIT_SNAPSHOT_MATCH'
    assert verified['coordinate_authority'] is False
    assert verified['semantic_correctness_verified'] is False
    for changed in ({'content':'changed'}, {'source_sha256':'b'*64}, {'chunk_id':'other'}, {'content_sha256':'b'*64}):
        assert verify_document({**doc, **changed}, receipt)['status'] == 'UNVERIFIED'


def test_hash_tampering_and_missing_manifest_do_not_verify(tmp_path):
    target = snapshot(tmp_path)
    (target / 'v1/receipts.jsonl').write_text('{}')
    assert load_receipts(target) == ({}, {})
    assert load_receipts(tmp_path / 'missing') == ({}, {})


def test_matching_mismatch_receipt_is_explicit(tmp_path):
    receipt = load_receipts(snapshot(tmp_path, 'MISMATCH'))
    assert verify_document(dict(chunk_id='c1', content='body', source_sha256='a'*64), receipt)['status'] == 'AUDIT_SNAPSHOT_MISMATCH'


def test_partial_source_hash_is_preserved_but_never_verified(tmp_path):
    target = snapshot(tmp_path, 'UNVERIFIED')
    source = tmp_path / 'audit'
    raw = (source / 'compact_receipts.jsonl').read_bytes().replace(('a'*64).encode(), ('partial:'+'a'*64).encode())
    (source / 'compact_receipts.jsonl').write_bytes(raw)
    manifest = json.loads((source / 'receipt_manifest.json').read_bytes())
    manifest['files']['compact_receipts.jsonl'] = hashlib.sha256(raw).hexdigest()
    (source / 'receipt_manifest.json').write_text(json.dumps(manifest))
    publish(source, target, 'v2')
    result = verify_document(dict(chunk_id='c1', content='body', source_sha256='partial:'+'a'*64), load_receipts(target))
    assert result['status'] == 'UNVERIFIED'


@pytest.mark.parametrize('field,value', [('rows',0), ('snapshot_sha256',None), ('audited_at','')])
def test_publication_requires_complete_snapshot_provenance(tmp_path, field, value):
    snapshot(tmp_path)
    source = tmp_path / 'audit'
    manifest = json.loads((source / 'receipt_manifest.json').read_bytes())
    manifest[field] = value
    (source / 'receipt_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='snapshot provenance'):
        publish(source, tmp_path / 'published', 'rejected')
    assert not (tmp_path / 'published/rejected').exists()


def test_dataset_answer_excludes_audit_mismatch_and_discloses_counts(monkeypatch):
    from services.orchestrator import dataset_answer as answer
    from tests.unit.test_dataset_answer import evidence
    query = '다대포항 안내정보를 알려줘'
    source = evidence(query)
    doc = source['documents'][0]
    record = dict(chunk_id=doc['chunk_id'], content_sha256=hashlib.sha256(doc['content'].encode()).hexdigest(),
                  source_sha256=doc['source_sha256'], status='MISMATCH')
    monkeypatch.setattr(answer, 'retrieve', lambda *a, **k: source)
    monkeypatch.setattr(answer, 'load_receipts', lambda: ({doc['chunk_id']:record}, {}))
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    assert not final['structured_result']['source_passages']
    assert final['structured_result']['source_text_audit']['excluded_mismatch_chunks'] == 1
    assert final['error_code'] == 'DATASET_SOURCE_TEXT_MISMATCH_ONLY'
    assert '감사 당시 원문과 불일치' in final['summary']
    record['status'] = 'VERIFIED_TEXT'
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    assert final['structured_result']['source_text_audit']['verified_passages'] == 1
    assert '확인 1건, 미검증 0건' in final['summary']
    assert final['structured_result']['coordinate_authority'] is False


def test_coordinate_literal_warning_is_receipt_bound_and_never_authority(monkeypatch):
    from services.orchestrator import dataset_answer as answer
    from tests.unit.test_dataset_answer import evidence
    query = '다대포항 안내정보를 알려줘'
    source = evidence(query)
    doc = source['documents'][0]
    record = dict(chunk_id=doc['chunk_id'], content_sha256=hashlib.sha256(doc['content'].encode()).hexdigest(),
                  source_sha256=doc['source_sha256'], status='VERIFIED_TEXT',
                  coordinate_literal_issues=[{'status':'INVALID_OR_AMBIGUOUS_LITERAL','reason':'seconds_out_of_range'}])
    monkeypatch.setattr(answer, 'retrieve', lambda *a, **k: source)
    monkeypatch.setattr(answer, 'load_receipts', lambda: ({doc['chunk_id']:record}, {}))
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    verification = final['structured_result']['citations'][0]['source_text_verification']
    assert verification['coordinate_literal_issues'] == record['coordinate_literal_issues']
    assert verification['coordinate_authority'] is False
    assert '원문 좌표 표기에 검토가 필요한 항목이 있어 위치 기준으로 사용하지 않았습니다.' in final['summary']
    assert final['structured_result']['source_passages'][0]['quote'] in doc['content']
    record['coordinate_literal_issues'] = []
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    assert '원문 좌표 표기에 검토가 필요한' not in final['summary']
    assert final['structured_result']['citations'][0]['source_text_verification']['coordinate_authority'] is False
    record['coordinate_literal_issues'] = [{'status':'INVALID_OR_AMBIGUOUS_LITERAL'}]
    record['content_sha256'] = 'b'*64
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    assert '원문 좌표 표기에 검토가 필요한' not in final['summary']
    assert final['structured_result']['citations'][0]['source_text_verification']['reason'] == 'CURRENT_CHUNK_IDENTITY_CHANGED'


def test_object_links_are_snapshot_only_and_require_current_identity(monkeypatch):
    from services.orchestrator import dataset_answer as answer
    from tests.unit.test_dataset_answer import evidence
    query = '다대포항 안내정보를 알려줘'
    source = evidence(query)
    doc = source['documents'][0]
    record = dict(chunk_id=doc['chunk_id'], content_sha256=hashlib.sha256(doc['content'].encode()).hexdigest(),
        source_sha256=doc['source_sha256'], status='VERIFIED_TEXT', object_links=[dict(
            source_id=doc['source_id'], name='다대포항', relation='serving.small_harbour_guide',
            status='AUDIT_SNAPSHOT_LINK', geometry_role='REPRESENTATIVE_POINT',
            raw_geometry_transform_verified=True, geometry={'coordinates':[1,2]})])
    audit = {'spatial_links_sha256':'c'*64}
    monkeypatch.setattr(answer, 'retrieve', lambda *a, **k: source)
    monkeypatch.setattr(answer, 'load_receipts', lambda: ({doc['chunk_id']:record}, audit))
    final = answer.build_dataset_answer({'query':query, 'task_id':'t'})['final_dict']
    linked = final['structured_result']['citations'][0]['source_text_verification']['object_links']
    assert len(linked) == 1 and linked[0]['name'] == '다대포항'
    assert linked[0]['current_database_rechecked'] is False
    assert linked[0]['entrance_location_verified'] is False
    assert linked[0]['coordinate_authority'] is False and 'geometry' not in linked[0]
    assert '항만 객체 연결 1건' in final['summary']
    assert final['structured_result']['search_execution']['status'] == 'NOT_RUN'
    for changed in ({'source_id':'other'}, {'content':'changed'}, {'source_sha256':'d'*64}):
        assert not verify_document({**doc, **changed}, ({doc['chunk_id']:record}, audit)).get('object_links')
    assert not verify_document(doc, ({doc['chunk_id']:record}, {})).get('object_links')


def test_publication_rejects_unbound_object_links(tmp_path):
    snapshot(tmp_path)
    source = tmp_path / 'audit'
    row = json.loads((source / 'compact_receipts.jsonl').read_text())
    row['object_links'] = [{'source_id':'object'}]
    raw = (json.dumps(row)+'\n').encode()
    (source / 'compact_receipts.jsonl').write_bytes(raw)
    manifest = json.loads((source / 'receipt_manifest.json').read_bytes())
    manifest['files']['compact_receipts.jsonl'] = hashlib.sha256(raw).hexdigest()
    (source / 'receipt_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='spatial audit hash'):
        publish(source, tmp_path / 'published', 'unbound')


@pytest.mark.parametrize('status', ['VERIFIED_DERIVED_FIELDS', 'INCOMPLETE_DERIVED_FIELDS'])
def test_derived_field_check_is_not_literal_or_coordinate_authority(status):
    row = dict(chunk_id='d',content_sha256=hashlib.sha256(b'body').hexdigest(),source_sha256='a'*64,status='UNVERIFIED',derived_field_verification={'status':status,'reason':'source fields','evidence_sha256':'b'*64})
    doc = dict(chunk_id='d',content='body',source_sha256='a'*64)
    result = verify_document(doc, ({'d':row}, {}))
    assert result['status'] == 'UNVERIFIED'
    assert result['derived_field_verification']['status'] == status
    assert result['derived_field_verification']['current_database_rechecked'] is False
    assert result['coordinate_authority'] is False
    assert 'derived_field_verification' not in verify_document({**doc,'content':'changed'}, ({'d':row},{}))
    row['derived_field_verification']['evidence_sha256']='invalid'
    assert 'derived_field_verification' not in verify_document(doc, ({'d':row},{}))
