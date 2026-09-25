import io
import zipfile

import pytest

from scripts.archive_maritime_references import save_artifact, validate_document


def test_download_error_page_is_not_a_document():
    with pytest.raises(ValueError, match='HTML error'):
        validate_document(b'<html><body>Service unavailable</body></html>')


def test_incomplete_pdf_is_rejected():
    with pytest.raises(ValueError, match='Incomplete PDF'):
        validate_document(b'%PDF-1.7\ntruncated')


def test_hwpx_is_identified_from_package_contents():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('Contents/content.hpf', '<package/>')
    assert validate_document(stream.getvalue()) == 'hwpx'


def test_changed_original_cannot_overwrite_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr('scripts.archive_maritime_references.ROOT',tmp_path)
    save_artifact(tmp_path,'notice',b'original','txt',{})
    with pytest.raises(ValueError, match='snapshot differs'):
        save_artifact(tmp_path,'notice',b'changed','txt',{})
    assert (tmp_path/'notice.txt').read_bytes()==b'original'
