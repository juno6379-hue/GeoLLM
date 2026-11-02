from scripts.audit_dataset_locations import compare, mentions, norm


def test_pdf_comparison_does_not_accept_wrong_page():
    row={'document_type':'coastal_pilot','content':'Busan harbour','page_no':2,'metadata':{}}
    assert compare(row,{'page:1':'Busan harbour','page:2':'Other harbour'})[0]=='TEXT_MISMATCH'


def test_normalized_comparison_preserves_numbers():
    row={'document_type':'coastal_pilot','content':'35.123 N','page_no':1,'metadata':{}}
    assert compare(row,{'page:1':'35.124 N'})[0]=='TEXT_MISMATCH'
    assert compare(row,{'page:1':'35.123\nN'})[0]=='MATCH_NORMALIZED'


def test_profiles_are_not_promoted_to_source_body():
    row={'document_type':'dataset_profile','content':'hello','page_no':1,'metadata':{}}
    assert compare(row,{'page:1':'hello'})[0]=='PROFILE_NOT_SOURCE_BODY'


def test_mentions_are_non_authoritative_exact_offsets():
    text='부산항 좌표 35° 12′ 129.1234,35.1234'
    found=mentions(text)
    assert len(found)>=3
    assert all(text[m['start']:m['end']]==m['text'] and m['authority'] is False for m in found)


def test_csv_row_locator_does_not_accept_other_rows():
    row={'document_type':'law','content':'columns: name\nBusan','metadata':{'source_row_start':2,'source_row_end':2}}
    assert compare(row,{'csv_rows':[['name'],['Busan'],['Incheon']]})[0]=='TEXT_MISMATCH'


def test_missing_locator_remains_unverified():
    row={'document_type':'document','content':'text','metadata':{}}
    assert compare(row,{'page:1':'text'})[0]=='LOCATOR_UNSUPPORTED'


def test_explicit_coordinate_axes_and_bounds():
    from scripts.audit_dataset_coordinate_literals import parse
    _,pairs=parse('북위 35° 12′ 30″ 동경 129° 5′ 0″')
    assert len(pairs)==1 and pairs[0]['longitude']==129+5/60
    assert pairs[0]['latitude']==35+12/60+30/3600
    assert pairs[0]['coordinate_authority'] is False
    _,invalid=parse('북위 91° 0′ 동경 129° 61′')
    assert invalid[0]['status']=='INVALID_OR_AMBIGUOUS_LITERAL'
    assert invalid[0]['latitude'] is None


def test_unlabelled_decimal_and_code_not_coordinates():
    from scripts.audit_dataset_coordinate_literals import parse
    assert parse('129.123, 35.123 code 35N 129E')==([],[])


def test_south_west_sign_is_preserved():
    from scripts.audit_dataset_coordinate_literals import parse
    _,pairs=parse('35° 12′ S 129° 5′ W')
    assert pairs[0]['latitude']<0 and pairs[0]['longitude']<0


def test_coordinate_axes_are_not_reused_in_overlapping_pairs():
    from scripts.audit_dataset_coordinate_literals import parse
    _,pairs=parse('북위 35 동경 129 북위 36 동경 130')
    assert len(pairs)==2
    assert pairs[0]['end']<=pairs[1]['start']


def test_relaxed_whitespace_is_never_verified():
    from scripts.classify_dataset_text_mismatches import classify
    assert classify('3512','35 12')=='UNVERIFIED_EXTRACTION_WHITESPACE_VARIATION'
    assert classify('35.124','35.123')=='TEXT_MISMATCH'
    assert classify('formula','for\ufffdmula')=='UNVERIFIED_EXTRACTION_REPLACEMENT_VARIATION'
