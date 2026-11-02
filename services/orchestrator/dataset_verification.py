"""Snapshot text-audit receipts; never coordinate or semantic authority."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'data/source_verification'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_receipts(root=None):
    base = Path(root or ROOT).resolve()
    try:
        pointer = json.loads((base / 'current.json').read_bytes())
        manifest_path = (base / pointer['manifest']).resolve()
        if not manifest_path.is_relative_to(base):
            raise ValueError('Manifest outside receipt root')
        raw = manifest_path.read_bytes()
        if _sha(raw) != pointer['sha256']:
            raise ValueError('Manifest hash mismatch')
        manifest = json.loads(raw)
        if manifest.get('complete') is not True:
            raise ValueError('Incomplete audit')
        receipt_path = (manifest_path.parent / 'receipts.jsonl').resolve()
        if not receipt_path.is_relative_to(base):
            raise ValueError('Receipt outside root')
        raw = receipt_path.read_bytes()
        if _sha(raw) != manifest['files']['receipts.jsonl']:
            raise ValueError('Receipt hash mismatch')
        rows = {}
        for line in raw.splitlines():
            row = json.loads(line)
            key = str(row['chunk_id'])
            if key in rows:
                raise ValueError('Duplicate chunk identity')
            rows[key] = row
        return rows, {'manifest_sha256': pointer['sha256'], 'audited_at': manifest.get('audited_at'),
                      'snapshot_sha256': manifest.get('snapshot_sha256'),
                      'spatial_links_sha256': manifest.get('spatial_links_sha256')}
    except (OSError, ValueError, KeyError, TypeError):
        return {}, {}


def verify_document(document, receipts=None):
    rows, audit = receipts if receipts is not None else load_receipts()
    result = {'status': 'UNVERIFIED', 'reason': 'NO_MATCHING_AUDIT_RECEIPT',
              'coordinate_authority': False, 'semantic_correctness_verified': False}
    # Current retrieval metadata controls retirement; historical receipt state
    # must not silently retire a currently ACTIVE row after an explicit rollback.
    metadata = document.get('metadata') or {}
    if isinstance(metadata, dict) and metadata.get('retrieval_status') == 'SUPERSEDED':
        return {**result, 'status': 'CURRENT_CHUNK_SUPERSEDED', 'reason': 'CURRENT_RETRIEVAL_METADATA_SUPERSEDED'}
    content_hash = _sha(str(document.get('content') or '').encode('utf-8'))
    result['retrieved_content_sha256'] = content_hash
    row = rows.get(str(document.get('chunk_id')))
    if not row:
        return result
    if (row.get('content_sha256') != content_hash or row.get('source_sha256') != document.get('source_sha256')
            or (document.get('content_sha256') and document['content_sha256'] != content_hash)):
        return {**result, 'reason': 'CURRENT_CHUNK_IDENTITY_CHANGED'}
    result.update(audit)
    result['source_locator'] = row.get('source_locator')
    result['audit_reason'] = row.get('reason')
    result['audit_retrieval_status'] = row.get('retrieval_status')
    derived = row.get('derived_field_verification')
    if isinstance(derived, dict) and derived.get('status') in (
            'VERIFIED_DERIVED_FIELDS', 'INCOMPLETE_DERIVED_FIELDS'):
        evidence_hash = derived.get('evidence_sha256')
        if (isinstance(evidence_hash, str) and len(evidence_hash) == 64
                and all(c in '0123456789abcdef' for c in evidence_hash)):
            result['derived_field_verification'] = {
                'status': derived['status'], 'reason': derived.get('reason'),
                'evidence_sha256': evidence_hash, 'scope': derived.get('scope', 'SOURCE_FIELDS_AT_AUDIT_TIME'),
                'semantic_authority': False, 'coordinate_authority': False,
                'current_database_rechecked': False,
            }
            for key in ('historical_full_source_hash_verified', 'historical_partial_hash_matches',
                        'derived_geometry_count_basis', 'coordinate_range_validity_not_established'):
                if key in derived:
                    result['derived_field_verification'][key] = derived[key]
    result['object_links'] = []
    spatial_hash = audit.get('spatial_links_sha256')
    if isinstance(spatial_hash, str) and len(spatial_hash) == 64 and all(c in '0123456789abcdef' for c in spatial_hash):
        for link in row.get('object_links') or []:
            if (not isinstance(link, dict) or link.get('status') != 'AUDIT_SNAPSHOT_LINK'
                    or link.get('source_id') != document.get('source_id') or not link.get('source_id')
                    or link.get('raw_geometry_transform_verified') is not True
                    or link.get('relation') != 'serving.small_harbour_guide'
                    or link.get('geometry_role') != 'REPRESENTATIVE_POINT'):
                continue
            result['object_links'].append({
                'source_id': link['source_id'], 'name': link.get('name'), 'relation': link['relation'],
                'status': 'AUDIT_SNAPSHOT_LINK', 'geometry_role': 'REPRESENTATIVE_POINT',
                'entrance_location_verified': False, 'coordinate_authority': False,
                'current_database_rechecked': False,
            })
    issues = row.get('coordinate_literal_issues')
    result['coordinate_literal_issues'] = [dict(issue) for issue in issues
        if isinstance(issue, dict) and issue.get('status') == 'INVALID_OR_AMBIGUOUS_LITERAL'] if isinstance(issues, list) else []
    source_hash = row.get('source_sha256')
    full_hash = isinstance(source_hash, str) and len(source_hash) == 64 and all(c in '0123456789abcdef' for c in source_hash)
    if row.get('status') == 'VERIFIED_TEXT' and full_hash:
        result.update(status='AUDIT_SNAPSHOT_MATCH', reason='SOURCE_TEXT_MATCH_AT_AUDIT_TIME')
    elif row.get('status') == 'MISMATCH':
        result.update(status='AUDIT_SNAPSHOT_MISMATCH', reason='SOURCE_TEXT_MISMATCH_AT_AUDIT_TIME')
    return result


def filter_answer_documents(documents, receipts=None):
    """Filter exact snapshot mismatches, preserving diagnostic identities only."""
    receipts = load_receipts() if receipts is None else receipts
    accepted, excluded = [], []
    for document in documents:
        item = dict(document)
        identity = {**item, 'chunk_id': item.get('chunk_id') or item.get('doc_id')}
        verification = verify_document(identity, receipts)
        item['source_text_verification'] = verification
        if verification['status'] in ('AUDIT_SNAPSHOT_MISMATCH', 'CURRENT_CHUNK_SUPERSEDED'):
            excluded.append({'chunk_id': identity['chunk_id'], 'source_id': item.get('source_id'),
                             'source_text_verification': verification})
        else:
            accepted.append(item)
    return accepted, excluded
