"""Read-only, hash-verified spatial development diagnostics, never benchmark metrics."""
from pathlib import Path
import hashlib
import json

BASE = Path('outputs/rq3_wrong_executable_20261102_v2')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_rq3_development(root):
    root = Path(root).resolve()
    base = (root / BASE).resolve()
    result = dict(status='NOT_MEASURED', scope='SEPARATE_DEVELOPMENT_DIAGNOSTIC',
                  included_in_selected_run=False, spatial_cases=[], sources=[], errors=[],
                  limitation='수작업으로 구성한 개발 진단이며 8방법 논문 결과·RQ3 방법별 분모에 합산하지 않습니다.')
    if not base.is_relative_to(root):
        result['errors'].append('INVALID_DIAGNOSTIC_PATH'); return result
    manifest_path=base/'manifest.json'
    if not manifest_path.is_file():return result
    try:
        raw=manifest_path.read_bytes(); manifest=json.loads(raw)
        result['sources'].append(dict(path=manifest_path.relative_to(root).as_posix(),sha256=hashlib.sha256(raw).hexdigest()))
        files=manifest['files']
        if not isinstance(files,dict) or 'summary.json' not in files:raise ValueError('SUMMARY_HASH_REQUIRED')
        for name, digest in files.items():
            if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts or any('holdout' in x.lower() for x in Path(name).parts):raise ValueError('INVALID_ARTIFACT_PATH')
            path=(base/name).resolve()
            if not path.is_relative_to(base):raise ValueError('INVALID_ARTIFACT_PATH')
            if file_sha256(path)!=digest:raise ValueError('ARTIFACT_HASH_MISMATCH')
            result['sources'].append(dict(path=path.relative_to(root).as_posix(),sha256=digest))
        summary=json.loads((base/'summary.json').read_text(encoding='utf-8-sig'))
        if not isinstance(summary,dict):raise ValueError('INVALID_SUMMARY')
        if summary.get('evidence_verified') is not True:raise ValueError('EVIDENCE_NOT_VERIFIED')
        if summary.get('production_authority_granted') is not False or summary.get('scope') != 'DEVELOPMENT_SQL_MUTATION_NOT_METHOD_BENCHMARK':raise ValueError('DEVELOPMENT_SCOPE_REQUIRED')
        trace=summary.get('sql_trace') or {}
        if any(trace.get(k) is not True for k in ('execution_attempted','execution_started','tool_called','sql_executed')):raise ValueError('SQL_EXECUTION_UNVERIFIED')
        rows=summary.get('spatial_cases')
        if not isinstance(rows,list) or not rows:raise ValueError('SPATIAL_OBSERVATIONS_MISSING')
        seen=set()
        for row in rows:
            if not isinstance(row,dict):raise ValueError('INVALID_CASE')
            key=(row.get('case_id'),row.get('variant'))
            if key in seen or not all(isinstance(k,str) and k for k in key):raise ValueError('DUPLICATE_OR_INVALID_CASE')
            seen.add(key)
            if any(type(row.get(k)) is not bool for k in ('execution_success','spatial_correct')):raise ValueError('E_OR_S_UNMEASURED')
            if any(type(row.get(k)) is not int or row[k]<0 for k in ('returned_count','gold_count')):raise ValueError('COUNTS_UNMEASURED')
            if any(not isinstance(row.get(k),list) for k in ('missing_ids','extra_ids')):raise ValueError('OBJECT_DIFFERENCES_MISSING')
            ids=row.get('object_ids')
            if not isinstance(ids,list) or any(not isinstance(x,(str,int)) or isinstance(x,bool) for x in ids):raise ValueError('OBJECT_IDS_MISSING')
            if len(set(ids))!=len(ids) or len(ids)!=row['returned_count']:raise ValueError('OBJECT_COUNT_MISMATCH')
            missing,extra=row['missing_ids'],row['extra_ids']
            if len(set(missing))!=len(missing) or len(set(extra))!=len(extra) or set(missing)&set(ids) or not set(extra).issubset(ids):raise ValueError('OBJECT_DIFFERENCES_INCONSISTENT')
            if row['gold_count']!=row['returned_count']-len(extra)+len(missing):raise ValueError('GOLD_COUNT_MISMATCH')
            if row['spatial_correct'] != (not missing and not extra):raise ValueError('SPATIAL_VERDICT_INCONSISTENT')
        result.update(status='VERIFIED_DEVELOPMENT_DIAGNOSTIC',spatial_cases=rows,
                      evidence_verified=True,summary_sha256=files['summary.json'])
    except (OSError,KeyError,TypeError,ValueError) as exc:
        result.update(status='INVALID_OR_UNMEASURED',errors=[str(exc)],spatial_cases=[])
    return result
