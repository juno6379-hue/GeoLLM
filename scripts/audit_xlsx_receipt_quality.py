"""Audit legacy archive text against decoded worksheet cell values, without DB writes."""
import argparse
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.verify_xlsx_source_revision import decode_cells, source_workbook


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def norm(value):
    return ' '.join(str(value).split())


def assess_cell_span(content, member, decoded):
    prefix = f'Archive member: {member}. '
    body = norm(content[len(prefix):] if content.startswith(prefix) else content)
    pieces, spans, offset = [], [], 0
    for cell in decoded['cells']:
        if cell['value'] is None:
            continue
        value = norm(cell['value'])
        if not value:
            continue
        if pieces:
            offset += 1
        spans.append((offset, offset + len(value), cell))
        pieces.append(value)
        offset += len(value)
    text = ' '.join(pieces)
    start = text.find(body) if body else -1
    result = dict(status='CELL_TEXT_UNVERIFIED', normalization='WHITESPACE_ONLY',
                  representation='WORKSHEET_CELL_VALUES_IN_SOURCE_ORDER',
                  decoded_values_sha256=sha(text.encode()), content_body_sha256=sha(body.encode()),
                  workbook_sha256=decoded['workbook_sha256'], formula_evaluated=False,
                  semantic_authority=False, coordinate_authority=False)
    if start < 0:
        return {**result, 'reason': 'NO_DECODED_CELL_VALUE_SPAN'}
    end = start + len(body)
    if text.find(body, start + 1) >= 0:
        return {**result, 'reason': 'AMBIGUOUS_DECODED_CELL_VALUE_SPAN'}
    if (start and not text[start-1].isspace()) or (end < len(text) and not text[end].isspace()):
        return {**result, 'reason': 'PARTIAL_CELL_TOKEN_BOUNDARY'}
    return {**result, 'status': 'VERIFIED_CELL_TEXT', 'reason': 'UNIQUE_DECODED_CELL_VALUE_SPAN',
            'normalized_char_span': [start, end],
            'locators': [{k: cell[k] for k in ('sheet_name', 'worksheet_member', 'address', 'xml_element_sha256')}
                         for a, b, cell in spans if a < end and b > start]}


def audit(root, receipt_manifest, receipt_manifest_sha, snapshot, snapshot_sha, output):
    manifest_raw, snapshot_raw = receipt_manifest.read_bytes(), snapshot.read_bytes()
    if sha(manifest_raw) != receipt_manifest_sha or sha(snapshot_raw) != snapshot_sha:
        raise ValueError('Pinned receipt manifest or snapshot changed')
    manifest = json.loads(manifest_raw)
    raw = (receipt_manifest.parent / 'receipts.jsonl').read_bytes()
    if sha(raw) != manifest['files']['receipts.jsonl']:
        raise ValueError('Receipt bytes changed')
    receipts = [json.loads(line) for line in raw.splitlines()]
    previous = {r['chunk_id']: r for r in receipts}
    if len(previous) != len(receipts):
        raise ValueError('Duplicate receipt ID')
    rows = [json.loads(line) for line in snapshot_raw.splitlines()]
    rowmap = {r['chunk_id']: r for r in rows}
    if len(rowmap) != len(rows):
        raise ValueError('Duplicate snapshot ID')
    evidence, cache, sources = [], {}, {}
    for receipt in receipts:
        member = str(receipt.get('source_locator') or '')
        if not member.lower().endswith('.xlsx') or receipt.get('retrieval_status', 'ACTIVE') != 'ACTIVE':
            continue
        row = rowmap.get(receipt['chunk_id'])
        if not row or sha(row['content'].encode()) != receipt['content_sha256'] or row['source_sha256'] != receipt['source_sha256']:
            raise ValueError('Current receipt/snapshot triple differs')
        source = row['source_file'].replace('\\', '/')
        if source.startswith('/app/'):
            source = source[5:]
        path = (root / source).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Source escaped repository')
        key = (source, row['source_sha256'], member)
        if key not in cache:
            workbook = source_workbook(root, source, member, row['source_sha256'])
            cache[key] = decode_cells(workbook)
            sources[str(path)] = row['source_sha256']
        quality = assess_cell_span(row['content'], member, cache[key])
        evidence.append(dict(chunk_id=row['chunk_id'], source_sha256=row['source_sha256'],
                             content_sha256=receipt['content_sha256'], source_file=source,
                             source_locator=member, previous_status=receipt['status'], **quality))
    if not evidence:
        raise ValueError('No XLSX receipts to audit')
    for path, expected in sources.items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError('Source changed during audit')
    if sha(snapshot.read_bytes()) != snapshot_sha or sha(receipt_manifest.read_bytes()) != receipt_manifest_sha:
        raise ValueError('Pinned input changed during audit')
    evidence_raw = b''.join((json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n').encode() for r in evidence)
    evidence_sha = sha(evidence_raw)
    checks = {r['chunk_id']: r for r in evidence}
    for row in receipts:
        q = checks.get(row['chunk_id'])
        if not q:
            continue
        row['extraction_quality'] = {'status': q['status'], 'reason': q['reason'],
            'evidence_sha256': evidence_sha, 'scope': 'XLSX_DECODED_CELL_VALUES_AT_AUDIT_TIME',
            'source_member': q['source_locator'], 'workbook_sha256': q['workbook_sha256'],
            'decoded_values_sha256': q['decoded_values_sha256']}
        if q['status'] != 'VERIFIED_CELL_TEXT':
            # Literal storage-XML agreement is not a resolved cell-text receipt.
            row['previous_literal_status'] = row['status']
            if row['status'] == 'VERIFIED_TEXT':
                row['status'] = 'UNVERIFIED'
    overlay_raw = b''.join((json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n').encode() for r in receipts)
    lineage = dict(parent_manifest_sha256=receipt_manifest_sha, parent_receipts_sha256=sha(raw),
                   source_snapshot_sha256=snapshot_sha, quality_evidence_sha256=evidence_sha,
                   sources=sources, audit_code_sha256=sha(Path(__file__).read_bytes()),
                   decoder_code_sha256=sha(Path(__file__).with_name('verify_xlsx_source_revision.py').read_bytes()))
    lineage_raw = (json.dumps(lineage, ensure_ascii=False, sort_keys=True)+'\n').encode()
    now = datetime.now(timezone.utc).isoformat()
    result = {**manifest, 'files': {'compact_receipts.jsonl': sha(overlay_raw)},
              'snapshot_kind': 'BASELINE_RECEIPTS_PLUS_XLSX_CELL_QUALITY_AUDIT',
              'snapshot_sha256': sha(lineage_raw), 'snapshot_file': 'quality_lineage.json',
              'full_current_db_export': False, 'audited_at': now,
              'status_counts': dict(collections.Counter(r['status'] for r in receipts)),
              'active_status_counts': dict(collections.Counter(r['status'] for r in receipts if r.get('retrieval_status', 'ACTIVE') == 'ACTIVE')),
              'extraction_quality_sha256': evidence_sha,
              'completion_scope': 'Pinned baseline receipt overlay with XLSX cell-order checks; no DB mutation',
              'published': False, 'coordinate_authority': False, 'semantic_correctness_verified': False}
    summary = dict(audited_at=now, checked=len(evidence), counts=dict(collections.Counter(r['status'] for r in evidence)),
                   previous_status_counts=dict(collections.Counter(r['previous_status'] for r in evidence)),
                   changed_verified_to_unverified=sum(r['previous_status']=='VERIFIED_TEXT' and r['status']!='VERIFIED_CELL_TEXT' for r in evidence),
                   database_modified=False, model_called=False, holdout_used=False, published=False,
                   evidence_sha256=evidence_sha, lineage=lineage)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in [('quality_evidence.jsonl', evidence_raw), ('compact_receipts.jsonl', overlay_raw), ('quality_lineage.json', lineage_raw)]:
        (output / name).write_bytes(content)
    for name, content in [('receipt_manifest.json', result), ('summary.json', summary)]:
        (output / name).write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--receipt-manifest', type=Path, required=True)
    p.add_argument('--receipt-manifest-sha', required=True)
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--snapshot-sha', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.root, a.receipt_manifest, a.receipt_manifest_sha, a.snapshot, a.snapshot_sha, a.output)))
