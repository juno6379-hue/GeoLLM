from scripts.verify_dataset_pdf_followup import exact_span


def test_whitespace_run_preserved_as_separator():
    assert exact_span('Busan 35.5 N', 'heading\nBusan\n35.5   N\nend')


def test_numeric_merge_rejected():
    assert exact_span('1234', '12 34') is None
    assert exact_span('12 34', '1234') is None
    assert exact_span('1.2', '1 .2') is None


def test_word_merge_and_typography_rejected():
    assert exact_span('부산항', '부산 항') is None
    assert exact_span("ship's", 'ship’s') is None


def test_ambiguous_duplicate_rejected():
    assert exact_span('부산항', '부산항 및 부산항') is None


def test_invalid_character_and_empty_rejected():
    assert exact_span('\ufffd', '\ufffd') is None
    assert exact_span('\x00a', '\x00a') is None
    assert exact_span('', 'hello') is None


def test_exact_source_offsets():
    actual='before\nBusan\n35.5   N\nafter'
    r=exact_span('Busan 35.5 N',actual)
    assert actual[r['start']:r['end']]=='Busan\n35.5   N'
    assert r['numeric_lexemes']==['35.5']


def test_candidate_is_not_verification_and_flags_numeric_change():
    from scripts.prepare_dataset_pdf_reextraction import locate_candidate
    r=locate_candidate('coordinate1234','coordinate 12 34')
    assert r['text']=='coordinate 12 34'
    assert r['old_text_verified'] is False
    assert r['requires_visual_numeric_review'] is True
    assert r['requires_new_embedding'] is True


def test_candidate_no_fuzzy_word_or_replacement_substitution():
    from scripts.prepare_dataset_pdf_reextraction import locate_candidate
    assert locate_candidate('Busan','Ulsan') is None
    assert locate_candidate('a\ufffdb','ab') is None


def test_revision_requires_numeric_preservation_and_new_identity():
    from scripts.package_dataset_pdf_revisions import revision
    from scripts.prepare_dataset_pdf_reextraction import locate_candidate
    from scripts.verify_dataset_pdf_followup import digest
    row=dict(chunk_id='old',content='Busan35.5',source_sha256='s',metadata={},source_file='x.pdf',
             document_type='coastal_pilot',title='x',section='page:1',page_no=1,source_id='source')
    check=dict(candidate=locate_candidate(row['content'],'Busan 35.5'),content_sha256=digest(row['content'].encode()),
               source_sha256='s',source_locator=['page:1'],extracted_pages_sha256='p',extractor_version='6.18.0')
    new=revision(row,check)
    assert new['chunk_id']!='old'
    assert new['requires_new_embedding'] is True
    assert new['text']=='Busan 35.5'
    assert row['content']=='Busan35.5'
    check['candidate']['numeric_lexemes_equal']=False
    assert revision(row,check) is None
