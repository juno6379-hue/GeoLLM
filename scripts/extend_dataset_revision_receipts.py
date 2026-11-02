"""Build baseline-plus-applied-delta receipts; never publish or write the DB."""
import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from scripts.repair_source_document_revisions import (
    sha, digest, old_id, build_new_rows, verify_source,
)


def extend(baseline, embedded, applied, output):
    baseline, embedded, applied, output = map(Path, (baseline, embedded, applied, output))
    if output.exists():
        raise FileExistsError('Output exists')
    manifest_path = baseline / 'receipt_manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    raw = (baseline / 'compact_receipts.jsonl').read_bytes()
    if sha(raw) != manifest['files']['compact_receipts.jsonl']:
        raise ValueError('Baseline hash mismatch')
    records = [json.loads(line) for line in raw.splitlines()]
    indexed = {r['chunk_id']: r for r in records}
    if len(indexed) != len(records):
        raise ValueError('Duplicate baseline IDs')
    plan = json.loads(embedded.read_bytes())
    receipt = json.loads(applied.read_bytes())
    expected_new = build_new_rows(plan)  # validates immutable plan, input/vector/model receipts
    if (receipt.get('stage') != 'APPLIED' or receipt.get('database') != 'gbhd_s101'
            or receipt.get('batch_id') != plan['batch_id']
            or receipt.get('artifact_sha256') != sha(embedded.read_bytes())
            or receipt.get('before_sha256') != plan['before']['rows_sha256']
            or digest(receipt['after_rows']) != receipt.get('after_sha256')):
        raise ValueError('Apply provenance mismatch')
    before = {r['chunk_id']: r for r in plan['before']['rows']}
    after = {r['chunk_id']: r for r in receipt['after_rows']}
    candidates = plan['candidates']
    old_ids = [old_id(c) for c in candidates]
    new_ids = [c['chunk_id'] for c in candidates]
    if (len(before) != len(candidates) or set(before) != set(old_ids)
            or set(receipt['old_ids']) != set(old_ids) or len(receipt['old_ids']) != len(old_ids)
            or set(receipt['new_ids']) != set(new_ids) or len(receipt['new_ids']) != len(new_ids)
            or len(after) != len(receipt['after_rows']) or set(after) != set(old_ids + new_ids)
            or set(new_ids) & set(indexed)):
        raise ValueError('Apply identity/cardinality mismatch')
    cache = {}
    checks = [verify_source(c, before[old_id(c)], cache) for c in candidates]
    if checks != plan['source_validation']:
        raise ValueError('Source validation differs')
    for c, new in zip(candidates, expected_new):
        oid, nid = old_id(c), c['chunk_id']
        old = before[oid]
        base = indexed[oid]
        if (base.get('retrieval_status', 'ACTIVE') != 'ACTIVE'
                or base['content_sha256'] != sha(old['content'].encode())
                or base['source_sha256'] != old['source_sha256']):
            raise ValueError('Baseline target mismatch')
        retired = copy.deepcopy(old)
        retired['metadata'].update(retrieval_status='SUPERSEDED', revision_batch_id=plan['batch_id'], superseded_by_chunk_ids=[nid])
        if retired != after[oid]:
            raise ValueError('Old row not preserved exactly')
        actual = after[nid]
        if any(actual.get(k) != v for k, v in new.items() if k not in ('created_at', 'embedding')):
            raise ValueError('New row differs from plan')
        if json.loads(actual['embedding']) != json.loads(new['embedding']):
            raise ValueError('Applied vector differs')
        base.update(retrieval_status='SUPERSEDED', superseded_by_chunk_ids=[nid], revision_batch_id=plan['batch_id'])
        meta = c['metadata']
        method = meta['extraction_method']
        fresh = dict(chunk_id=nid, content_sha256=sha(c['text'].encode()),
                     source_sha256=c['source_sha256'], source_locator=c['section'],
                     status='UNVERIFIED', reason='SOURCE_XML_DERIVED_RENDERING_NOT_LITERAL',
                     semantic_authority=False, coordinate_authority=False,
                     coordinate_literal_issues=[], object_links=[], retrieval_status='ACTIVE',
                     supersedes_chunk_ids=[oid], revision_batch_id=plan['batch_id'],
                     apply_receipt_sha256=sha(applied.read_bytes()),
                     embedding_model_digest=plan['model_digest'], embedding_dimension=plan['dimension'])
        if method == 'fc_direct_xml_fields_v3':
            fresh['derived_field_verification'] = dict(status='VERIFIED_DERIVED_FIELDS',
                reason='SOURCE_XML_FIELDS_REEXTRACTED_AND_APPLIED', scope='SOURCE_FIELDS_AT_AUDIT_TIME',
                evidence_sha256=sha(embedded.read_bytes()), historical_full_source_hash_verified=True,
                observed_source_sha256=c['source_sha256'], source_element_sha256=meta['source_element_sha256'])
        elif method == 'pdf_source_span_revision_v1':
            fresh.update(status='VERIFIED_TEXT', reason='FULL_SOURCE_HASH_AND_EXACT_PAGE_SPAN_REVERIFIED',
                source_locator=dict(pages=meta['source_locators'], start=meta['source_char_start'],
                    end=meta['source_char_end'], pages_sha256=meta['source_extracted_pages_sha256']))
        else:
            raise ValueError('Unsupported revision method')
        records.append(fresh)
    active = [r for r in records if r.get('retrieval_status') != 'SUPERSEDED']
    payload = b''.join((json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n').encode() for r in records)
    # This is a reproducible receipt-lineage snapshot, not a full current DB dump.
    # Hash actual serialized bytes so the publisher's provenance requirement is
    # satisfied without relabelling a composite as a database export.
    lineage = dict(schema_version='baseline_applied_delta_v1',
        baseline_receipt_sha256=sha(raw), baseline_manifest_sha256=sha(manifest_path.read_bytes()),
        baseline_snapshot_sha256=manifest.get('snapshot_sha256'),
        embedded_artifact_sha256=sha(embedded.read_bytes()), apply_receipt_sha256=sha(applied.read_bytes()),
        applied_after_rows_sha256=receipt['after_sha256'], source_validation_sha256=digest(checks),
        output_receipts_sha256=sha(payload), stored_rows=len(records), active_rows=len(active),
        full_current_db_export=False)
    lineage_raw=(json.dumps(lineage, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
    report = dict(complete=True, completion_scope='Validated baseline receipts plus applied revision delta; not a fresh full DB export',
        snapshot_kind='BASELINE_RECEIPTS_PLUS_APPLIED_DELTA', full_current_db_export=False,
        snapshot_sha256=sha(lineage_raw), snapshot_file='baseline_delta_snapshot.json',
        spatial_links_sha256=manifest.get('spatial_links_sha256'),
        spatial_links_scope='Inherited unchanged baseline links; new revision rows have no object links',
        files={'compact_receipts.jsonl':sha(payload)}, rows=len(records), stored_rows=len(records),
        active_rows=len(active), superseded_rows=len(records)-len(active),
        status_counts=dict(Counter(r['status'] for r in records)),
        active_status_counts=dict(Counter(r['status'] for r in active)),
        derived_field_checks=sum(r.get('derived_field_verification',{}).get('status')=='VERIFIED_DERIVED_FIELDS' for r in active),
        applied_revisions=len(candidates), baseline_receipt_sha256=sha(raw),
        baseline_manifest_sha256=sha(manifest_path.read_bytes()), embedded_artifact_sha256=sha(embedded.read_bytes()),
        apply_receipt_sha256=sha(applied.read_bytes()), source_validation_sha256=digest(checks),
        baseline_path=str(baseline), embedded_artifact_path=str(embedded), apply_receipt_path=str(applied),
        database_rows_modified=False, published=False, audited_at=datetime.now(timezone.utc).isoformat(),
        limitations=['Untargeted rows retain baseline evidence; not independently re-exported.',
                     'Derived fields and literal text are distinct; neither grants geographic authority.'])
    output.mkdir(parents=True)
    (output/'compact_receipts.jsonl').write_bytes(payload)
    (output/'baseline_delta_snapshot.json').write_bytes(lineage_raw)
    (output/'receipt_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','embedded','applied','output'): p.add_argument('--'+name, required=True)
    print(json.dumps(extend(**vars(p.parse_args())), ensure_ascii=False))
