import io
import json
import zipfile

import pytest

from scripts.verify_xlsx_source_revision import decode_cells, prepare, render_cell, sha, source_workbook


def workbook(cells=None, target='worksheets/sheet1.xml', other_relation=''):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('xl/workbook.xml', '<workbook xmlns:r="urn:rel"><sheets><sheet name="한글" r:id="r1" state="hidden"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', f'<Relationships><Relationship Id="r1" Target="{target}"/>{other_relation}</Relationships>')
        z.writestr('xl/sharedStrings.xml', '<sst><si><r><t>부산</t></r><rPh><t>NOT DISPLAY TEXT</t></rPh><r><t>항</t></r></si></sst>')
        z.writestr('xl/worksheets/sheet1.xml', '<worksheet><sheetData><row>' + (cells or '<c r="A1" t="s"><v>0</v></c><c r="B1" s="2"><f t="shared" si="3">SUM(A2:A3)</f><v>4</v></c><c r="C1"/>') + '</row></sheetData></worksheet>')
    return stream.getvalue()


def test_resolves_shared_string_and_preserves_formula_identity():
    result = decode_cells(workbook())
    assert result['cells'][0]['value'] == '부산항'
    assert result['cells'][0]['raw_value'] == '0'
    assert result['cells'][0]['sheet_state'] == 'hidden'
    formula = result['cells'][1]
    assert formula['formula'] == 'SUM(A2:A3)'
    assert formula['formula_attributes'] == {'t': 'shared', 'si': '3'}
    assert formula['value'] == '4'
    assert formula['style_id'] == '2'
    assert 'cached="4"' in render_cell(formula)
    assert result['formula_evaluated'] is False
    assert result['excel_display_format_interpreted'] is False
    assert result['cells'][2]['value'] is None


@pytest.mark.parametrize('cells', ['<c r="A1" t="s"><v>2</v></c>', '<c r="A1"/><c r="A1"/>', '<c><v>1</v></c>'])
def test_rejects_ambiguous_cell_identity(cells):
    with pytest.raises(ValueError):
        decode_cells(workbook(cells))


def test_rejects_escaped_relationship():
    with pytest.raises(ValueError, match='Unsafe'):
        decode_cells(workbook(target='../../outside.xml'))


def test_nonworksheet_relationship_not_mistaken_for_sheet():
    assert len(decode_cells(workbook(other_relation='<Relationship Id="other" Target="../customXml/item1.xml"/>'))['cells']) == 3


def inputs(tmp_path, extra=False):
    raw = workbook()
    (tmp_path / 'source.xlsx').write_bytes(raw)
    old = dict(chunk_id='old1', content='0 4', source_file='source.xlsx', source_sha256=sha(raw), document_type='validation', metadata={'document_id': 'document1'})
    audit = dict(chunk_id='old1', content_sha256=sha(b'0 4'), source_file='source.xlsx', source_sha256=sha(raw), document_type='validation', reason='SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT', source_locator='source.xlsx')
    (tmp_path / 'audit.jsonl').write_text(json.dumps(audit), encoding='utf-8')
    rows = [old]
    if extra:
        rows.append({**old, 'chunk_id': 'old2'})
    (tmp_path / 'snapshot.jsonl').write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
    return tmp_path / 'audit.jsonl', tmp_path / 'snapshot.jsonl'


def test_many_to_many_candidate_keeps_old_identity_and_does_not_approve(tmp_path):
    audit, snapshot = inputs(tmp_path)
    result = prepare(tmp_path, audit, snapshot, tmp_path / 'out')
    assert result['old_chunk_count'] == 1
    package = json.loads((tmp_path / 'out/candidates.json').read_text(encoding='utf-8'))
    assert package['one_to_one_apply_compatible'] is False
    assert package['database_applied'] is False
    assert package['embedding_completed'] is False
    assert package['rows'][0]['replaces_workbook_chunk_ids'] == ['old1']
    assert package['rows'][0]['source_cell_indexes'] == [0, 1]
    assert '부산항' in package['rows'][0]['text']
    with pytest.raises(FileExistsError):
        prepare(tmp_path, audit, snapshot, tmp_path / 'out')


def test_preserves_other_document_members_and_blocks_apply(tmp_path):
    audit, snapshot = inputs(tmp_path, extra=True)
    prepare(tmp_path, audit, snapshot, tmp_path / 'out')
    package = json.loads((tmp_path / 'out/candidates.json').read_text(encoding='utf-8'))
    assert package['source_groups'][0]['preserve_other_document_chunk_sha256'] == {'old2': sha(b'0 4')}
    assert package['source_groups'][0]['scope_review_required'] is True
    assert package['rows'][0]['replaces_workbook_chunk_ids'] == ['old1']
    assert package['apply_ready'] is False


def test_blocks_stale_audit_and_source(tmp_path):
    audit, snapshot = inputs(tmp_path)
    value = json.loads(snapshot.read_text())
    value['content'] = 'changed'
    snapshot.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='Old content identity'):
        prepare(tmp_path, audit, snapshot, tmp_path / 'out')
    with pytest.raises(ValueError, match='Source SHA'):
        source_workbook(tmp_path, 'source.xlsx', 'source.xlsx', 'bad')


def test_identical_workbook_bytes_with_distinct_registered_paths_have_distinct_ids(tmp_path):
    audit, snapshot = inputs(tmp_path)
    (tmp_path / 'duplicate.xlsx').write_bytes((tmp_path / 'source.xlsx').read_bytes())
    audit_row = json.loads(audit.read_text())
    old = json.loads(snapshot.read_text())
    audit.write_text(json.dumps(audit_row) + '\n' + json.dumps({**audit_row, 'chunk_id': 'old2', 'source_file': 'duplicate.xlsx', 'source_locator': 'duplicate.xlsx'}))
    snapshot.write_text(json.dumps(old) + '\n' + json.dumps({**old, 'chunk_id': 'old2', 'source_file': 'duplicate.xlsx'}))
    prepare(tmp_path, audit, snapshot, tmp_path / 'out')
    package = json.loads((tmp_path / 'out/candidates.json').read_text(encoding='utf-8'))
    assert len(package['rows']) == 2
    assert len({r['chunk_id'] for r in package['rows']}) == 2
