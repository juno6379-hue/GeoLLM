"""Merge separately reviewed operational receipts, never change chunk text/vector."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path):
    return [json.loads(line) for line in Path(path).read_bytes().splitlines()]


def merge(baseline, independent, producers, output, derived=None):
    baseline, independent, output = Path(baseline), Path(independent), Path(output)
    manifest = json.loads((baseline / 'manifest.json').read_bytes())
    raw = (baseline / 'receipts.jsonl').read_bytes()
    if sha(raw) != manifest['files']['receipts.jsonl']:
        raise ValueError('Baseline receipt changed')
    original = [json.loads(line) for line in raw.splitlines()]
    indexed = {r['chunk_id']:r for r in original}
    if len(indexed) != len(original):
        raise ValueError('Duplicate baseline')
    # The review author checked specific producer bytes. IDs alone cannot bind
    # a later producer's changed locator/reason to that prior independent check.
    review_summary_path = independent.parent / 'summary.json'
    review_summary = json.loads(review_summary_path.read_bytes())
    independent_hash = sha(independent.read_bytes())
    if review_summary.get('results_sha256') != independent_hash:
        raise ValueError('Independent review bytes changed')
    reviewed_inputs = {Path(p).resolve():h for p,h in review_summary.get('input_sha256',{}).items()}
    producer_paths = list(map(Path,producers))
    if any(reviewed_inputs.get(p.resolve()) != sha(p.read_bytes()) for p in producer_paths):
        raise ValueError('Producer differs from independent review input')
    reviews = rows(independent)
    if len({r['chunk_id'] for r in reviews}) != len(reviews):
        raise ValueError('Duplicate independent review')
    approved = {r['chunk_id'] for r in reviews if r['status']=='PASS_INDEPENDENT_TEXT'}
    candidates = {}
    inputs = {str(independent):independent_hash,
              str(review_summary_path):sha(review_summary_path.read_bytes())}
    for p in producer_paths:
        inputs[str(p)] = sha(p.read_bytes())
        for r in rows(p):
            if r['status'] == 'VERIFIED_TEXT':
                if r['chunk_id'] in candidates:
                    raise ValueError('Overlapping producer targets')
                candidates[r['chunk_id']] = r
    if not approved <= candidates.keys():
        raise ValueError('Independent approved target missing producer')
    for cid in sorted(approved):
        old, new = indexed[cid], candidates[cid]
        if (old['status'] != 'UNVERIFIED' or old.get('retrieval_status') == 'SUPERSEDED'
                or any(old.get(k)!=new.get(k) for k in ('content_sha256','source_sha256'))):
            raise ValueError('Target lifecycle/identity mismatch')
        old.update(status='VERIFIED_TEXT', reason='INDEPENDENT_SOURCE_SPAN_CONFIRMED;'+new['reason'],
                   source_locator=new.get('source_locator'), followup_review_sha256=inputs[str(independent)],
                   semantic_authority=False, coordinate_authority=False)
    derived_count = 0
    if derived:
        path=Path(derived); inputs[str(path)]=sha(path.read_bytes())
        if reviewed_inputs.get(path.resolve()) != inputs[str(path)]:
            raise ValueError('Derived producer differs from independent review input')
        derived_seen=set()
        for new in rows(path):
            if new.get('status') not in ('VERIFIED_DERIVED_FIELDS','INCOMPLETE_DERIVED_FIELDS'):
                continue
            if new['chunk_id'] in derived_seen:
                raise ValueError('Duplicate derived target')
            derived_seen.add(new['chunk_id'])
            old=indexed[new['chunk_id']]
            if any(old.get(k)!=new.get(k) for k in ('content_sha256','source_sha256')):
                raise ValueError('Derived target identity mismatch')
            if old.get('retrieval_status')=='SUPERSEDED':
                raise ValueError('Retired derived target')
            if old.get('status') != 'UNVERIFIED' or new['chunk_id'] in approved:
                raise ValueError('Derived target must remain distinct from literal verification')
            scope=new.get('verification_scope')
            if scope not in ('SOURCE_FIELDS_AT_AUDIT_TIME','CURRENT_OPERATIONAL_DATABASE_FIELDS'):
                raise ValueError('Derived verification scope missing or unsupported')
            if (new['reason']=='SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT'
                    and new['status']!='INCOMPLETE_DERIVED_FIELDS'):
                raise ValueError('Spreadsheet storage tokens cannot be verified source fields')
            old['derived_field_verification']={'status':new['status'],'reason':new['reason'],
                'scope':scope,'evidence_sha256':inputs[str(path)],
                'historical_full_source_hash_verified':(
                    scope=='SOURCE_FIELDS_AT_AUDIT_TIME'
                    and re.fullmatch(r'[0-9a-f]{64}',str(new.get('source_sha256',''))) is not None
                    and new.get('observed_source_sha256')==new.get('source_sha256'))}
            # Preserve the qualifiers under which independent review accepted
            # this derived observation. Current DB reproduction is not proof
            # of a historical full source file or geographic validity.
            for key in ('observed_source_sha256','historical_partial_hash_matches',
                        'derived_geometry_count_basis','coordinate_range_validity_not_established',
                        'partial_token_boundary','db_export','db_field_checks',
                        'source_locator','expected_locator','element_sha256',
                        'source_representation_sha256'):
                if key in new:
                    old['derived_field_verification'][key]=new[key]
            if new['reason'] == 'SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT':
                old.update(status='MISMATCH', reason='SPREADSHEET_STORAGE_XML_NOT_CELL_TEXT')
            derived_count+=1
    payload=b''.join((json.dumps(r,ensure_ascii=False)+'\n').encode() for r in original)
    active=[r for r in original if r.get('retrieval_status')!='SUPERSEDED']
    report={**manifest,'files':{'compact_receipts.jsonl':sha(payload)},
        'audited_at':datetime.now(timezone.utc).isoformat(), 'rows':len(original),
        'status_counts':dict(Counter(r['status'] for r in original)),
        'active_status_counts':dict(Counter(r['status'] for r in active)),
        'followup_inputs':inputs,'new_literal_confirmations':len(approved),
        'derived_field_checks':derived_count,'database_rows_modified':False,
        'followup_scope':'Literal source spans and separately annotated derived fields; no location authority'}
    output.mkdir(parents=True,exist_ok=False)
    (output/'compact_receipts.jsonl').write_bytes(payload)
    (output/'receipt_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True); p.add_argument('--independent',type=Path,required=True)
    p.add_argument('--producer',action='append',required=True); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--derived',type=Path)
    a=p.parse_args(); r=merge(a.baseline,a.independent,a.producer,a.output,a.derived)
    print(json.dumps({'active_status_counts':r['active_status_counts'],'new_literal_confirmations':r['new_literal_confirmations']}))
