import io
import zipfile
from xml.etree import ElementTree as ET
from scripts.docx_source_text import paragraph_text,docx_source_text


def test_preserves_controls_and_nonbreaking_hyphen():
    p=ET.fromstring('<p><r><t>35</t><tab/><t>02</t><br/><t>20</t><cr/><t>East</t><noBreakHyphen/><t>West</t></r></p>')
    assert paragraph_text(p)=='35\t02\n20\nEast\u2011West'


def test_extractors_preserve_control_boundaries(tmp_path):
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:z.writestr('word/document.xml','<document><p><r><t>15</t><tab/><t>30</t></r></p></document>')
    p=tmp_path/'x.docx';p.write_bytes(raw.getvalue())
    from scripts.build_document_rag_chunks import docx_text
    from scripts.build_dataset_embedding_coverage import docx_sections
    from scripts.dataset_pipeline import sections
    assert docx_source_text(raw.getvalue())=='15\t30'
    assert docx_text(p)=='15\t30'
    assert docx_sections(p)[0][1]=='15\t30'
    assert list(sections(p))[0][1]=='15\t30'
