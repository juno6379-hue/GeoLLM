"""Post-generation scoring of live Q4 outputs against a fixed, source-bound oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import math

from research.marine_geollm_scie.evaluation.metrics import object_sets

ROOT=Path(__file__).resolve().parents[3]
TERMINAL={'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','REVIEW_REQUIRED'}


def validate_capture(raw_path, raw, benchmark_path):
    manifest=json.loads((raw_path.parent/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('rows_sha256')!=hashlib.sha256(raw_path.read_bytes()).hexdigest():
        raise ValueError('Captured rows hash mismatch')
    if manifest.get('benchmark_sha256')!=hashlib.sha256(benchmark_path.read_bytes()).hexdigest():
        raise ValueError('Benchmark hash mismatch')
    queries={r['case_id']:r['query'] for r in (json.loads(s) for s in benchmark_path.read_text(encoding='utf-8').splitlines() if s.strip())}
    if any(r.get('case_id') not in queries or r.get('query')!=queries[r['case_id']] for r in raw):
        raise ValueError('Original case/query mapping mismatch')
    before=manifest.get('production_source_hashes_before')
    after=manifest.get('production_source_hashes_after')
    if before is not None or after is not None:
        if not before or not after or before!=after:
            raise ValueError('Production sources changed or capture hashes incomplete')
        return 'CAPTURE_BEFORE_AFTER_MATCH'
    return 'UNVERIFIED_NOT_CAPTURED'


def score(row, reference, oracle_hash):
    final=(row.get('final') or {}).get('final_result') or {}
    structured=final.get('structured_result') or {}
    search=structured.get('search_execution') or {}
    capture_valid=row.get('status')=='CAPTURED' and (row.get('final') or {}).get('status') in TERMINAL
    execution=(True if search.get('status')=='COMPLETED' and search.get('authority')=='ExecutionValidator' else False if search.get('status')=='NOT_RUN' else None) if capture_valid else None
    features=structured.get('features')
    expected_hash=reference['snapshot_sha256']
    known={r['source_id']:r for r in reference['objects']}
    observed=[]; mappings=[]; errors=[]; differences=[]
    if not capture_valid:errors.append('CAPTURE_NOT_TERMINAL')
    if execution is True:
        if not isinstance(features,list):errors.append('RETURNED_FEATURE_RECORDS_MISSING')
        for f in features or []:
            source_id=str(f.get('공간정보일련번호',''))
            if f.get('provenance',{}).get('source_sha256')!=expected_hash:
                errors.append('SOURCE_SNAPSHOT_MISMATCH')
            if not source_id:errors.append('SOURCE_ID_MISSING')
            observed.append('mof_marine_names_20221231:'+source_id)
            mappings.append({'returned_feature_id':f.get('feature_id'),'source_object_id':source_id})
            if source_id in known and isinstance(f.get('distance_m'),(int,float)) and not isinstance(f['distance_m'],bool) and math.isfinite(f['distance_m']):
                differences.append(abs(f['distance_m']-known[source_id]['distance_postgis_m']))
        if len(observed)!=len(set(observed)):errors.append('DUPLICATE_SOURCE_ID')
        if structured.get('total_count')!=len(observed):errors.append('INCOMPLETE_RETURNED_OBJECT_SET')
        if structured.get('distance_m')!=5000:errors.append('RADIUS_MISMATCH')
        point=structured.get('reference_geometry') or ''
        coords=re.fullmatch(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)',point)
        anchor=reference['anchor']
        if not coords or abs(float(coords[1])-anchor['longitude'])>1e-10 or abs(float(coords[2])-anchor['latitude'])>1e-10:
            errors.append('REFERENCE_GEOMETRY_MISMATCH')
    bound=execution is True and not errors and bool(features)
    # An unbound empty result is not evidence that the intended source was queried.
    metrics=object_sets(reference['object_ids'],observed) if bound else object_sets(None,None)
    return {'case_id':row['case_id'],'query':row['query'],'method':row['method'],'repeat':row['repeat'],
        'scope':'LIVE_Q4_USER_APPROVED_REFERENCE_NOT_HOLDOUT','status':row['status'],
        'graph_status':row.get('final',{}).get('status'),'execution_attempted':execution,
        'execution_success':execution,'returned_object_ids':observed if bound else None,
        'dataset_snapshot_sha256':expected_hash if bound else None,'oracle_sha256':oracle_hash,
        'source_binding_verified':bound,'binding_errors':errors,'source_id_mapping':mappings,
        'spatial_correct':metrics['exact_match'],'spatial_f1':metrics['f1'],
        'spatial_metric_scope':'SOURCE_BOUND_OBJECT_SET_ONLY',
        'distance_evaluated_object_count':len(differences) if bound else 0,
        'distance_correct':all(d<=.01 for d in differences) if bound and len(differences)==len(observed) else None,
        'silent_spatial_failure':not metrics['exact_match'] if bound else None,
        'full_success':None,'semantic_correct':None,'plan_valid':None,'evidence_correct':None,
        'distance_max_abs_error_m':max(differences) if differences else None,
        'distance_tolerance_m':.01,'distance_tolerance_basis':'API outputs rounded to 0.01m; fixed rounding allowance, independent of measured errors',
        'total_latency_ms':row['total_latency_ms'],'input_tokens':None,'output_tokens':None,
        'gold_used_for_generation':False,'equivalence_group':'Q4_DOKDO_5000M',
        'independent_expert_review':False,'split':'development','holdout_eligible':False,
        'predicted_qec':(final.get('orchestrator_v2') or {}).get('query_execution_context')}


def run(raw_path,reference_path,output):
    ref=json.loads(reference_path.read_text(encoding='utf-8'))
    if ref['status']!='COMPUTED_VERIFIED_REFERENCE' or ref['object_ids'] is None:
        raise ValueError('Verified complete oracle required')
    if hashlib.sha256(Path(ref['source_snapshot']['path']).read_bytes()).hexdigest()!=ref['snapshot_sha256']:
        raise ValueError('Source CSV changed')
    oracle_hash=hashlib.sha256(reference_path.read_bytes()).hexdigest()
    raw=[json.loads(s) for s in raw_path.read_text(encoding='utf-8').splitlines()]
    source_stability=validate_capture(raw_path,raw,ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl')
    if {r['case_id'] for r in raw}!=set(ref['case_ids']) or len(raw)!=3:
        raise ValueError('All three original equivalent cases required')
    rows=[score(r,ref,oracle_hash) for r in raw]
    for row in rows:row['production_source_stability']=source_stability
    output.mkdir(parents=True,exist_ok=False)
    (output/'scored_rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    summary={'rows':3,'independent_equivalence_groups':1,'approved_by_user':True,'independent_expert_review':False,
        'raw_path':str(raw_path.resolve()),'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        'oracle_path':str(reference_path.resolve()),'oracle_sha256':oracle_hash,
        'execution_success_count':sum(r['execution_success'] is True for r in rows),
        'spatial_exact_count':sum(r['spatial_correct'] is True for r in rows),
        'missing_spatial_evaluation_count':sum(r['spatial_correct'] is None for r in rows),
        'distance_evaluated_case_count':sum(r['distance_correct'] is not None for r in rows),
        'distance_correct_case_count':sum(r['distance_correct'] is True for r in rows),
        'distance_evaluated_object_count':sum(r['distance_evaluated_object_count'] for r in rows),
        'production_source_stability':source_stability,
        'capture_manifest_sha256':hashlib.sha256((raw_path.parent/'manifest.json').read_bytes()).hexdigest(),
        'limitation':'Three equivalent development queries, one geographic group, live API observation only; not comparative model or holdout accuracy.'}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.raw,a.reference,a.output)
