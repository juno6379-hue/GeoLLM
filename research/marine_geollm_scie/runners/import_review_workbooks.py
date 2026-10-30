"""Read review XLSX cells without executing formulas or granting GOLD status."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_workbook(path: Path) -> dict:
    with ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in si.findall('.//m:t', NS))
                       for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in
                ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet', NS):
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = rels[rid]
            name = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(z.read(name)).findall('m:sheetData/m:row', NS):
                cells = {}
                for cell in row.findall('m:c', NS):
                    value = cell.find('m:v', NS)
                    text = value.text or '' if value is not None else ''
                    if cell.get('t') == 's':
                        text = strings[int(text)]
                    elif cell.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                    formula = cell.find('m:f', NS)
                    cells[cell.attrib['r']] = {'value': text, 'formula': formula.text if formula is not None else None}
                rows.append(cells)
            sheets[sheet.attrib['name']] = rows
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'sheets': sheets, 'import_grants_gold': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = [read_workbook(path) for path in args.input]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps([{'path': r['path'], 'sheets': {k: len(v) for k, v in r['sheets'].items()}}
                      for r in result], ensure_ascii=False))


if __name__ == '__main__':
    main()
