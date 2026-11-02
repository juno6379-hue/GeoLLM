from scripts.audit_dataset_remaining_locators import token_span

def test_whitespace_without_number_join():
    assert token_span('north 35 02', 'north\n35\t02') == [0,11]
    assert token_span('north 3502', 'north 35 02') is None

def test_unique_complete_tokens():
    assert token_span('port', 'port port') is None
    assert token_span('35', '135') is None
    assert token_span('port', 'ports') is None

def test_sign_preservation():
    assert token_span('speed -5', 'speed −5') is None

from scripts.complete_dataset_locator_followup import unique_fragment

def test_fragment_records_truncated_token_without_fabricating_completion():
    assert unique_fragment('abc def', 'abc defghi') == [0,7]
    assert unique_fragment('3502', '35 02') is None
    assert unique_fragment('abc', 'abc abc') is None
