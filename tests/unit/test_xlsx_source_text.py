import io
import zipfile
import pytest
from scripts.xlsx_source_text import xlsx_source_text


def workbook(index='0'):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:
        z.writestr('xl/workbook.xml','<workbook xmlns:r="urn:r"><sheets><sheet name="Checks" r:id="r1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml','<sst><si><r><t>Busan </t></r><r><t>Port</t></r></si></sst>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet><sheetData><row><c r="A1" t="s"><v>{index}</v></c><c r="B1" s="2"><v>45000</v></c><c r="C1"><f>1+2</f><v>3</v></c><c r="D1" t="inlineStr"><is><t>Wreck</t></is></c></row></sheetData><mergeCells><mergeCell ref="A1:A2"/></mergeCells></worksheet>')
    return buffer.getvalue()


def test_resolves_shared_string_instead_of_raw_index():
    text=xlsx_source_text(workbook())
    assert 'Checks!A1 [type=s; style=0] Busan Port' in text
    assert 'Checks!A1 [type=s; style=0] 0' not in text
    assert 'Checks!D1 [type=inlineStr; style=0] Wreck' in text


def test_preserves_formula_cache_style_and_merge_without_calculation():
    text=xlsx_source_text(workbook())
    assert 'formula=1+2; cached=3' in text
    assert 'Checks!B1 [type=n; style=2] 45000' in text
    assert 'merged_range=A1:A2' in text


def test_rejects_unknown_shared_string_index():
    with pytest.raises(ValueError):xlsx_source_text(workbook('99'))


def test_all_three_extractors_use_cell_decoder():
    from scripts import build_document_rag_chunks as a, build_dataset_embedding_coverage as b, build_s101_catalogue_db_rag as c
    expected=xlsx_source_text(workbook())
    assert a.xlsx_text(workbook())==b.xlsx_text(workbook())==c.xlsx_text(workbook())==expected
