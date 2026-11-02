"""Read-only XLSX replacement preparation; never writes DB or calls a model.

Old XML-storage chunks cannot be mapped one-to-one to decoded cells. Candidates
therefore retain workbook-level many-to-many lineage and are NOT apply receipts.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import posixpath
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

REASON = 'SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT'
VERSION = 'xlsx_cell_revision_candidate_v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local(tag):
    return tag.rsplit('}', 1)[-1]


def rich_text(node):
    """Exclude phonetic annotations; retain explicit rich-text run order."""
    return ''.join(c.text or '' for c in node if local(c.tag) == 't') if not any(local(c.tag) == 'r' for c in node) else ''.join(''.join(t.text or '' for t in c if local(t.tag) == 't') for c in node if local(c.tag) == 'r')


def decode_cells(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('Duplicate XLSX ZIP member')
        names = set(archive.namelist())
        shared = []
        if 'xl/sharedStrings.xml' in names:
            shared = [rich_text(s) for s in ET.fromstring(archive.read('xl/sharedStrings.xml')) if local(s.tag) == 'si']
        relations = {}
        for rel in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels')):
            if rel.get('TargetMode') == 'External':
                continue
            target = rel.get('Target', '')
            path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            if rel.get('Id') in relations:
                raise ValueError('Duplicate relationship ID')
            relations[rel.get('Id')] = path
        rows, sheets, seen_sheets = [], [], set()
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).iter():
            if local(sheet.tag) != 'sheet':
                continue
            rid = next((v for k, v in sheet.attrib.items() if local(k) == 'id'), None)
            if rid not in relations:
                raise ValueError('Unresolved sheet relationship')
            path = relations[rid]
            if not path.startswith('xl/') or '..' in path.split('/'):
                raise ValueError('Unsafe worksheet relationship')
            if path in seen_sheets:
                raise ValueError('Duplicate worksheet relationship')
            seen_sheets.add(path)
            xml = archive.read(path)
            tree = ET.fromstring(xml)
            sheet_info = dict(name=sheet.get('name'), state=sheet.get('state', 'visible'), member=path, member_sha256=sha(xml),
                              merged_ranges=[n.get('ref') for n in tree.iter() if local(n.tag) == 'mergeCell'],
                              hidden_rows=[dict(n.attrib) for n in tree.iter() if local(n.tag) == 'row' and n.get('hidden') == '1'],
                              hidden_columns=[dict(n.attrib) for n in tree.iter() if local(n.tag) == 'col' and n.get('hidden') == '1'])
            sheets.append(sheet_info)
            seen_cells = set()
            for cell in tree.iter():
                if local(cell.tag) != 'c':
                    continue
                address = cell.get('r')
                if not address or address in seen_cells:
                    raise ValueError('Missing or duplicate cell address')
                seen_cells.add(address)
                raw_value = next((c.text or '' for c in cell if local(c.tag) == 'v'), None)
                inline = next((c for c in cell if local(c.tag) == 'is'), None)
                formula = next((c for c in cell if local(c.tag) == 'f'), None)
                kind = cell.get('t', 'n')
                value = raw_value
                if kind == 's':
                    index = int(raw_value)
                    if not 0 <= index < len(shared):
                        raise ValueError('Shared string index out of bounds')
                    value = shared[index]
                elif kind == 'inlineStr':
                    if inline is None:
                        raise ValueError('Missing inline string')
                    value = rich_text(inline)
                rows.append(dict(sheet_name=sheet_info['name'], sheet_state=sheet_info['state'], worksheet_member=path,
                                 address=address, cell_type=kind, style_id=cell.get('s', '0'), raw_value=raw_value,
                                 value=value, formula=None if formula is None else formula.text or '',
                                 formula_attributes=None if formula is None else dict(formula.attrib),
                                 xml_element_sha256=sha(ET.tostring(cell))))
        if not sheets:
            raise ValueError('No worksheets')
        return dict(workbook_sha256=sha(raw), sheets=sheets, cells=rows,
                    shared_strings_sha256=sha(archive.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in names else None,
                    styles_sha256=sha(archive.read('xl/styles.xml')) if 'xl/styles.xml' in names else None,
                    formula_evaluated=False, excel_display_format_interpreted=False)


def render_cell(cell):
    label = json.dumps(cell['sheet_name'], ensure_ascii=False) + '!' + cell['address']
    label += f" [type={cell['cell_type']}; style={cell['style_id']}] "
    value = json.dumps(cell['value'], ensure_ascii=False)
    if cell['formula'] is not None:
        return label + 'formula=' + json.dumps(cell['formula'], ensure_ascii=False) + '; cached=' + value + '; formula_attributes=' + json.dumps(cell['formula_attributes'], ensure_ascii=False, sort_keys=True)
    return label + value


def source_workbook(root, source, member, expected_sha):
    path = (root / source).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Source escaped root')
    raw = path.read_bytes()
    if sha(raw) != expected_sha:
        raise ValueError('Source SHA changed')
    if path.suffix.lower() == '.xlsx':
        return raw
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist().count(member) != 1 or not member.lower().endswith('.xlsx'):
            raise ValueError('Workbook member missing or ambiguous')
        return archive.read(member)


def prepare(root, audit_file, snapshot_file, output):
    audit_raw, snapshot_raw = audit_file.read_bytes(), snapshot_file.read_bytes()
    audit = [json.loads(line) for line in audit_raw.decode('utf-8').splitlines() if line]
    old_rows = [json.loads(line) for line in snapshot_raw.decode('utf-8').splitlines() if line]
    old = {r['chunk_id']: r for r in old_rows}
    if len(old) != len(old_rows):
        raise ValueError('Duplicate snapshot chunk IDs')
    groups = defaultdict(list)
    selected = [r for r in audit if r.get('reason') == REASON]
    if not selected or len({r['chunk_id'] for r in selected}) != len(selected):
        raise ValueError('Missing or duplicate XLSX audit rows')
    for row in selected:
        original = old[row['chunk_id']]
        if sha(original['content'].encode()) != row['content_sha256']:
            raise ValueError('Old content identity differs')
        if any(original[k] != row[k] for k in ('source_file', 'source_sha256', 'document_type')):
            raise ValueError('Old source identity differs')
        groups[(row['source_file'], row['source_sha256'], row['source_locator'])].append(row)
    output.mkdir(parents=True, exist_ok=False)
    generated, manifests = [], []
    for index, ((source, source_sha, member), group) in enumerate(sorted(groups.items())):
        decoded = decode_cells(source_workbook(root, source, member, source_sha))
        old_ids = sorted(r['chunk_id'] for r in group)
        original_rows = [old[key] for key in old_ids]
        document_ids = {r['metadata'].get('document_id') for r in original_rows}
        # Archive documents may combine XLSX and PDF members. Never propose
        # replacing every row sharing a document_id. Keep all other IDs pinned.
        related_ids = {r['chunk_id'] for r in old_rows if r['source_file'] == source and r['metadata'].get('document_id') in document_ids}
        preserve_ids = sorted(related_ids - set(old_ids))
        # Identical bytes at distinct registered source paths remain separate
        # source identities unless an explicit deduplication policy says otherwise.
        group_key = sha((source + '|' + source_sha + '|' + member).encode())[:24]
        detail_path = output / f'workbook_{index:02d}.json'
        detail_path.write_text(json.dumps(decoded, ensure_ascii=False, indent=2), encoding='utf-8')
        chunks, current, size = [], [], 0
        for cell_index, cell in enumerate(decoded['cells']):
            if cell['value'] is None and cell['formula'] is None:
                continue  # Blank cell preserved in workbook receipt, not prose.
            line = render_cell(cell)
            if current and size + len(line) + 1 > 4000:
                chunks.append(current); current, size = [], 0
            current.append((cell_index, line)); size += len(line) + 1
        if current:
            chunks.append(current)
        for number, chunk in enumerate(chunks):
            text = '\n'.join(line for _, line in chunk)
            key = sha((VERSION + '|' + group_key + '|' + str(number) + '|' + text).encode())[:24]
            generated.append(dict(chunk_id=key, text=text, content_sha256=sha(text.encode()), source_file=source,
                                  source_sha256=source_sha, workbook_member=member, workbook_sha256=decoded['workbook_sha256'],
                                  source_cell_indexes=[n for n, _ in chunk], workbook_receipt=detail_path.name,
                                  replaces_workbook_chunk_ids=old_ids, revision_cardinality='MANY_TO_MANY_WORKBOOK',
                                  semantic_authority=False, coordinate_authority=False, requires_new_embedding=True))
        manifests.append(dict(source_file=source, source_sha256=source_sha, workbook_member=member,
                              old_chunk_ids=old_ids, old_content_sha256={r['chunk_id']: r['content_sha256'] for r in group},
                              preserve_other_document_chunk_sha256={key: sha(old[key]['content'].encode()) for key in preserve_ids},
                              scope_review_required=bool(preserve_ids),
                              cell_count=len(decoded['cells']), replacement_chunks=len(chunks), workbook_receipt=detail_path.name,
                              workbook_receipt_sha256=sha(detail_path.read_bytes())))
    if len({r['chunk_id'] for r in generated}) != len(generated):
        raise ValueError('Candidate ID collision')
    result = dict(stage='SOURCE_CANDIDATES_ONLY', version=VERSION, generator_sha256=sha(Path(__file__).read_bytes()),
                  audit_sha256=sha(audit_raw), snapshot_sha256=sha(snapshot_raw),
                  source_groups=manifests, old_chunk_count=len(selected), rows=generated, database_applied=False,
                  embedding_completed=False, source_receipt_published=False, one_to_one_apply_compatible=False, apply_ready=False,
                  limitations=['Workbook-level lineage; old XML character spans are not cell spans.',
                               'Formulas not evaluated; cached values may be stale; styles do not establish displayed date/unit.',
                               'Snapshot lacks original vectors; export live full rows before transactional replacement.'])
    (output / 'candidates.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return dict(old_chunk_count=len(selected), workbook_count=len(manifests), candidate_count=len(generated),
                stage=result['stage'], manifest_sha256=sha((output / 'candidates.json').read_bytes()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.audit, args.snapshot, args.output)))


if __name__ == '__main__':
    main()
