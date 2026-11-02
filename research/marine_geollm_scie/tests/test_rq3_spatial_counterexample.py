import pytest

from research.marine_geollm_scie.runners.rq3_spatial_counterexample import assess,build_sql,section,MUTATION


def test_sql_uses_one_readonly_repeatable_read_transaction_and_fixed_mutation():
    sql=build_sql()
    assert sql.count('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;')==1
    assert sql.count('ROLLBACK;')==1
    assert 'COMMIT' not in sql and 'CREATE ' not in sql and 'UPDATE ' not in sql
    assert 'ST_DWithin(p.geometry::geography,h.g::geography,2000,true)' in sql
    assert 'ST_DWithin(ST_Centroid(p.geometry)::geography,ST_Centroid(h.g)::geography,2000,true)' in sql
    assert 'feature_instance_id=1137770' in sql
    assert 'ST_Boundary' not in sql
    assert "MUTATION" not in sql
    assert 'TARGET_AND_REFERENCE' in MUTATION


def test_output_parser_preserves_exact_csv_newline_bytes():
    raw=b'__RQ3_SOURCE_0_BEGIN__\na,b\n1,2\n__RQ3_SOURCE_0_END__\n'
    assert section(raw,'SOURCE_0')==b'a,b\n1,2\n'


def test_output_parser_rejects_partial_or_duplicate_receipt():
    with pytest.raises(ValueError):section(b'__RQ3_RESULT_BEGIN__\n{}','RESULT')
    with pytest.raises(ValueError):section(b'__RQ3_RESULT_BEGIN__\n__RQ3_RESULT_BEGIN__\n__RQ3_RESULT_END__\n','RESULT')


def _inputs(wrong_same=False):
    rows=[{'id':'a','feature':'AnchorageArea','normal_included':True,'wrong_included':wrong_same},
          {'id':'r','feature':'RestrictedArea','normal_included':True,'wrong_included':True},
          {'id':'r2','feature':'RestrictedArea','normal_included':False,'wrong_included':not wrong_same}]
    gold={'spatial_gold':{'AnchorageArea':{'object_ids':['a']},'RestrictedArea':{'object_ids':['r']}}}
    q4={'spatial_reference':{'objects':[{'source_id':'44'}]}}
    return {'candidate_rows':rows,'q4_rows':[{'id':'44'}]},gold,q4


def test_sql_success_and_spatial_correctness_are_separate():
    result=assess(*_inputs())
    assert result['normal']=={'E':True,'S':True}
    assert result['wrong']=={'E':True,'S':False}
    assert result['counterexample_found'] is True
    assert result['difference']['AnchorageArea']['missing']==['a']
    assert result['difference']['RestrictedArea']['extra']==['r2']


def test_no_counterexample_is_not_fabricated():
    result=assess(*_inputs(wrong_same=True))
    assert result['wrong']['S'] is True
    assert result['counterexample_found'] is False


def test_missing_gold_rows_are_not_zero_result_success():
    inputs=list(_inputs());inputs[0]['candidate_rows']=[]
    result=assess(*inputs)
    assert result['normal']['S'] is False
    assert result['counterexample_found'] is False


def test_raw_db_identity_is_not_compared_to_original_csv_identity():
    inputs=list(_inputs())
    inputs[0]['q4_rows']=[{'id':'db_hash'}]
    unknown=assess(*inputs)
    assert unknown['q4']['S'] is None
    linked=assess(*inputs,q4_source_ids=['44'])
    assert linked['q4']['S'] is True
    assert linked['q4']['db_source_ids']==['db_hash']


def test_q4_identity_link_requires_original_bytes_properties_and_provenance(monkeypatch):
    import csv,io
    import research.marine_geollm_scie.runners.rq3_spatial_counterexample as module
    original={'공간정보일련번호':'44','지명명':'북향초','공간정보':'POINT (1 2)'}
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(original));writer.writeheader();writer.writerow(original)
    raw=stream.getvalue().encode('cp949')
    expected=module.sha(raw);monkeypatch.setattr(module,'GAZETTEER_SHA',expected)
    row={'id':module.sha('marine_gazetteer_mof|44|북향초'.encode())[:24],
         'name':'북향초','properties':original,'provenance':{'source_sha256':expected}}
    assert module.source_object_ids([row],raw)==['44']
    with pytest.raises(ValueError):module.source_object_ids([{**row,'id':'44'}],raw)
    with pytest.raises(ValueError):module.source_object_ids([{**row,'provenance':{}}],raw)
    with pytest.raises(ValueError):module.source_object_ids([row],raw+b' ')
