"""Use only pinned raw-DBF receipts for truncated source prefixes. Never repair text."""
import hashlib
import json
from pathlib import Path

RECEIPT_SHA256 = '4fee8041641994b5ae1a6acce904242837c3bb892b105322f579084243591a67'
RECEIPT_PATH = Path(__file__).resolve().parents[2] / 'data/source_verification/harbour_prefix_20261103_v1.json'


def verified_prefix(row, field, value):
    try:
        raw = RECEIPT_PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest() != RECEIPT_SHA256:
            return None
        receipt = json.loads(raw)
        if receipt.get('schema') != 'harbour-prefix-receipt/v1':
            return None
        entries = [e for e in receipt['entries'] if e['source_id'] == row['source_id'] and e['field'] == field]
        if len(entries) != 1:
            return None
        entry = entries[0]
        provenance = row.get('provenance') or {}
        if (entry['status'] != 'VERIFIED_UTF8_TAIL_TRUNCATION_ONLY'
                or provenance.get('source_sha256') != entry['source_sha256']
                or provenance.get('source_file') != entry['source_file']
                or (provenance.get('component_hashes') or {}).get('TB_SAILER.dbf') != entry['dbf_sha256']
                or entry['dbf_sha256'] != receipt['audit_dbf_sha256']
                or int(row['source_id'].rsplit(':', 1)[1]) != entry['row_index']
                or (row.get('properties') or {}).get(field) != value
                or hashlib.sha256(value.encode('utf-8')).hexdigest() != entry['current_text_sha256']):
            return None
        prefix = entry['prefix']
        if '\ufffd' in prefix or value != prefix + '\ufffd':
            return None
        prefix_bytes = prefix.encode('utf-8')
        original_bytes = prefix_bytes + bytes.fromhex(entry['incomplete_tail_hex'])
        if (len(prefix_bytes) != entry['prefix_byte_length'] or len(original_bytes) != entry['field_width']
                or entry['field_width'] != 254
                or hashlib.sha256(original_bytes).hexdigest() != entry['raw_field_sha256']):
            return None
        try:
            original_bytes.decode('utf-8', errors='strict')
            return None
        except UnicodeDecodeError as exc:
            if exc.reason != 'unexpected end of data' or exc.start != len(prefix_bytes) or exc.end != 254:
                return None
        return {'prefix':prefix, 'receipt':{'manifest_sha256':RECEIPT_SHA256,
                'source_id':row['source_id'], 'field':field, 'raw_field_sha256':entry['raw_field_sha256'],
                'status':entry['status']}}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
