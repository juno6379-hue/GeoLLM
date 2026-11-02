import hashlib
import json

import pytest

from scripts.merge_dataset_followup_receipts import merge


def write_json(path, value):
    path.write_text(json.dumps(value),encoding='utf-8')


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_derived(independent, derived):
    path=independent.parent/'summary.json'
    summary=json.loads(path.read_text())
    summary['input_sha256'][str(derived)]=hashlib.sha256(derived.read_bytes()).hexdigest()
    write_json(path,summary)


def no_literal_approval(independent):
    h=write_rows(independent,[])
    path=independent.parent/'summary.json'
    summary=json.loads(path.read_text());summary['results_sha256']=h
    write_json(path,summary)


@pytest.fixture
def inputs(tmp_path):
    baseline=tmp_path/'base';baseline.mkdir()
    row=dict(chunk_id='a',status='UNVERIFIED',content_sha256='a'*64,source_sha256='b'*64,
             retrieval_status='ACTIVE',coordinate_authority=False)
    h=write_rows(baseline/'receipts.jsonl',[row])
    write_json(baseline/'manifest.json',{'complete':True,'files':{'receipts.jsonl':h}})
    producer=tmp_path/'producer.jsonl'
    ph=write_rows(producer,[{**row,'status':'VERIFIED_TEXT','reason':'EXACT','source_locator':'page:1'}])
    review_dir=tmp_path/'independent';review_dir.mkdir()
    independent=review_dir/'results.jsonl'
    rh=write_rows(independent,[{'chunk_id':'a','status':'PASS_INDEPENDENT_TEXT'}])
    write_json(review_dir/'summary.json',{'results_sha256':rh,'input_sha256':{str(producer):ph}})
    return baseline,independent,producer,tmp_path/'new',row


def test_merge_bound_literal_and_derived_remain_distinct(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    report=merge(baseline,independent,[producer],out)
    result=json.loads((out/'compact_receipts.jsonl').read_text())
    assert report['new_literal_confirmations']==1
    assert result['status']=='VERIFIED_TEXT'
    assert result['semantic_authority'] is False
    assert result['coordinate_authority'] is False
    assert json.loads((baseline/'receipts.jsonl').read_text())['status']=='UNVERIFIED'


def test_reject_producer_changed_after_independent_review(inputs):
    baseline,independent,producer,out,row=inputs
    write_rows(producer,[{**row,'status':'VERIFIED_TEXT','reason':'EXACT','source_locator':'wrong-page'}])
    with pytest.raises(ValueError,match='review|Review|producer|Producer'):
        merge(baseline,independent,[producer],out)
    assert not out.exists()


def test_reject_review_changed_without_summary_rebinding(inputs):
    baseline,independent,producer,out,_=inputs
    independent.write_text(independent.read_text()+'\n')
    with pytest.raises(ValueError,match='review|Review'):
        merge(baseline,independent,[producer],out)
    assert not out.exists()


def test_reject_duplicate_derived_target(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    derived=tmp_path/'derived.jsonl'
    record={**row,'status':'VERIFIED_DERIVED_FIELDS','reason':'fields',
            'verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME'}
    write_rows(derived,[record,record])
    bind_derived(independent,derived)
    no_literal_approval(independent)
    with pytest.raises(ValueError,match='Duplicate derived'):
        merge(baseline,independent,[producer],out,derived)
    assert not out.exists()


def test_derived_status_does_not_promote_literal(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    review_dir=independent.parent
    h=write_rows(independent,[])
    summary=json.loads((review_dir/'summary.json').read_text());summary['results_sha256']=h
    write_json(review_dir/'summary.json',summary)
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**row,'status':'INCOMPLETE_DERIVED_FIELDS','reason':'missing field',
                         'verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME'}])
    bind_derived(independent,derived)
    report=merge(baseline,independent,[producer],out,derived)
    result=json.loads((out/'compact_receipts.jsonl').read_text())
    assert result['status']=='UNVERIFIED'
    assert result['derived_field_verification']['status']=='INCOMPLETE_DERIVED_FIELDS'
    assert report['new_literal_confirmations']==0


def test_unreviewed_derived_file_cannot_quarantine_source(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'unreviewed.jsonl'
    write_rows(derived,[{**row,'status':'INCOMPLETE_DERIVED_FIELDS',
        'reason':'SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT','verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME'}])
    with pytest.raises(ValueError,match='Derived producer'):
        merge(baseline,independent,[producer],out,derived)
    assert not out.exists()


def test_derived_change_after_review_is_rejected(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'derived.jsonl'
    record={**row,'status':'VERIFIED_DERIVED_FIELDS','reason':'fields',
            'verification_scope':'CURRENT_OPERATIONAL_DATABASE_FIELDS'}
    write_rows(derived,[record]);bind_derived(independent,derived)
    write_rows(derived,[{**record,'reason':'different source assessment'}])
    with pytest.raises(ValueError,match='Derived producer'):
        merge(baseline,independent,[producer],out,derived)


def test_current_db_scope_and_coordinate_limit_are_preserved(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**row,'status':'VERIFIED_DERIVED_FIELDS','reason':'CURRENT_DB_BODY_MATCH',
        'verification_scope':'CURRENT_OPERATIONAL_DATABASE_FIELDS',
        'coordinate_range_validity_not_established':True,'derived_geometry_count_basis':'numeric_presence_only'}])
    bind_derived(independent,derived)
    merge(baseline,independent,[producer],out,derived)
    result=json.loads((out/'compact_receipts.jsonl').read_text())
    field=result['derived_field_verification']
    assert result['status']=='UNVERIFIED'
    assert field['scope']=='CURRENT_OPERATIONAL_DATABASE_FIELDS'
    assert field['historical_full_source_hash_verified'] is False
    assert field['coordinate_range_validity_not_established'] is True
    assert field['derived_geometry_count_basis']=='numeric_presence_only'


def test_spreadsheet_storage_is_quarantined_without_vector_or_text_change(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**row,'status':'INCOMPLETE_DERIVED_FIELDS',
        'reason':'SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT','verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME'}])
    bind_derived(independent,derived)
    report=merge(baseline,independent,[producer],out,derived)
    result=json.loads((out/'compact_receipts.jsonl').read_text())
    assert result['status']=='MISMATCH'
    assert result['content_sha256']==row['content_sha256']
    assert report['database_rows_modified'] is False


def test_derived_identity_mismatch_rejected_even_when_file_reviewed(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**row,'source_sha256':'f'*64,'status':'VERIFIED_DERIVED_FIELDS',
                         'reason':'fields','verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME'}])
    bind_derived(independent,derived)
    with pytest.raises(ValueError,match='identity mismatch'):
        merge(baseline,independent,[producer],out,derived)


def test_unknown_derived_status_is_not_counted_as_verified(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**row,'status':'UNKNOWN','reason':'unobserved'}])
    bind_derived(independent,derived)
    report=merge(baseline,independent,[producer],out,derived)
    result=json.loads((out/'compact_receipts.jsonl').read_text())
    assert result['status']=='UNVERIFIED'
    assert 'derived_field_verification' not in result
    assert report['derived_field_checks']==0


def test_partial_historical_hash_is_not_upgraded_by_current_full_hash(inputs,tmp_path):
    baseline,independent,producer,out,row=inputs
    no_literal_approval(independent)
    partial={**row,'source_sha256':'partial:'+'b'*64}
    h=write_rows(baseline/'receipts.jsonl',[partial])
    write_json(baseline/'manifest.json',{'complete':True,'files':{'receipts.jsonl':h}})
    derived=tmp_path/'derived.jsonl'
    write_rows(derived,[{**partial,'status':'VERIFIED_DERIVED_FIELDS','reason':'profile',
        'verification_scope':'SOURCE_FIELDS_AT_AUDIT_TIME','observed_source_sha256':'c'*64,
        'historical_partial_hash_matches':True}])
    bind_derived(independent,derived)
    merge(baseline,independent,[producer],out,derived)
    field=json.loads((out/'compact_receipts.jsonl').read_text())['derived_field_verification']
    assert field['historical_full_source_hash_verified'] is False
    assert field['observed_source_sha256']=='c'*64
    assert field['historical_partial_hash_matches'] is True
