import io
import zipfile
from scripts.verify_docx_source_chunks import locate

def doc(body):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        z.writestr('word/document.xml','<w:document xmlns:w="urn:word"><w:body>'+body+'</w:body></w:document>')
    return b.getvalue()

def test_table_paragraph_locator():
    raw=doc('<w:p><w:r><w:t>Header</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Dokdo 37.2</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
    r=locate(raw,'Dokdo 37.2')
    assert r['status']=='VERIFIED_TEXT'
    assert r['locators'][0]['xpath']=='(//w:p)[2]'

def test_ambiguous_and_numeric_mismatch():
    raw=doc('<w:p><w:r><w:t>Port 12 Port 12</w:t></w:r></w:p>')
    assert locate(raw,'Port 12')['reason']=='AMBIGUOUS_SPAN'
    assert locate(raw,'Port 13')['status']=='UNVERIFIED'

def test_partial_word_rejected():
    assert locate(doc('<w:p><w:r><w:t>Newport</w:t></w:r></w:p>'),'port')['status']=='UNVERIFIED'
