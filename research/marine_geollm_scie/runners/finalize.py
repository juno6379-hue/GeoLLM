"""Finalize completed research pilots without exposing environment secrets."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT/'research/marine_geollm_scie'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def finalize(run_dir, *, allow_incomplete=False):
    run = Path(run_dir).resolve()
    inputs = [run/'validator/validator_rows.jsonl', run/'spatial/spatial_rows.jsonl',
              *sorted((run/'semantic_isolated').glob('*rows.jsonl'))]
    missing = [str(p.relative_to(run)) for p in inputs if not p.exists()]
    if not list((run/'semantic_isolated').glob('*rows.jsonl')):
        missing.append('semantic_isolated/*rows.jsonl')
    for marker in ('validator/validator_summary.json','semantic_isolated/summary.json','spatial/spatial_summary.json'):
        if not (run/marker).is_file():
            missing.append(marker)
    if missing and not allow_incomplete:
        raise RuntimeError('Pilot inputs not complete: '+', '.join(missing))
    rows = [r for p in inputs if p.exists() for r in read_jsonl(p)]
    cases = read_jsonl(RESEARCH/'benchmark/query_cases_v1.jsonl')
    from ..fault_injection.pilot import cases as fault_cases
    cases.extend({'case_id':name, 'category':'FAULT_FIXTURE', 'expected_invalid':invalid,
                  'fault_code':code,'review_status':'DRAFT','diagnostic_only':True}
                 for name, code, invalid, *_ in fault_cases())
    spatial_cases = run/'spatial/spatial_cases.jsonl'
    if spatial_cases.exists():
        cases.extend(read_jsonl(spatial_cases))
    identifiers = [c['case_id'] for c in cases]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Case IDs must be unique across benchmark and diagnostics')
    research_files = [p for p in RESEARCH.rglob('*') if p.is_file()
        and not any(x in p.relative_to(RESEARCH).parts for x in ('runs','latest','__pycache__','.pytest_cache'))
        and p.suffix in ('.py','.json','.jsonl','.yaml','.yml','.md','.txt')]
    production_files = [ROOT/p for p in (
        'shared/schemas/agent.py','services/orchestrator/execution_validator.py',
        'services/orchestrator/schema_binding_adapter.py','services/orchestrator/route_planner.py',
        'configs/evaluation/failure_taxonomy.yaml') if (ROOT/p).is_file()]
    source_hashes = {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(research_files+production_files)}
    source_audit_path = RESEARCH/'protocol/source_audit.json'
    audited_sources = json.loads(source_audit_path.read_text(encoding='utf-8-sig')).get('files',{}) if source_audit_path.exists() else {}
    referenced_sources = set(audited_sources)
    component_metadata = {}
    for p in sorted(run.glob('*/*.json')):
        if 'manifest' in p.name or 'summary' in p.name:
            data = json.loads(p.read_text(encoding='utf-8-sig'))
            component_metadata[p.relative_to(run).as_posix()] = {
                'sha256':digest(p),
                **{key:data[key] for key in ('source_hashes','benchmark_sha256','timestamp','python_version',
                   'package_versions','model_metadata','model_metadata_error','limitations','limitation') if key in data}}
            referenced_sources.update(data.get('source_hashes',{}))
    for relative in referenced_sources:
        path = (ROOT/relative.replace('\\','/')).resolve()
        if path.is_relative_to(ROOT) and path.is_file():
            source_hashes[path.relative_to(ROOT).as_posix()] = digest(path)
    source_audit = {'path':'research/marine_geollm_scie/protocol/source_audit.json',
        'sha256':digest(source_audit_path) if source_audit_path.exists() else None,
        'audited_source_hashes':audited_sources,
        'changed_since_audit':[p for p,data in audited_sources.items()
            if source_hashes.get(p.replace('\\','/')) != data.get('sha256')]}
    snapshots = [p for p in RESEARCH.rglob('*manifest*.json')
                 if 'runs' not in p.parts and 'latest' not in p.parts]
    spatial_snapshot = run/'spatial/snapshot_manifest.json'
    if spatial_snapshot.exists():
        snapshots.append(spatial_snapshot)
    snapshot_records = []
    for path in snapshots:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        snapshot_records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path),
            **{k:data[k] for k in ('source_relation','source_database','source_transaction','captured_at',
                'source_sha256','subset_rows','scope','gold_status','bbox_epsg4326','postgres_version') if k in data}})
    models = sorted({r['model'] for r in rows if isinstance(r.get('model'),str)})
    model_meta = []
    model_error = None
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags',timeout=5) as response:
            model_meta = [{k:m.get(k) for k in ('name','model','digest','size','modified_at','details')}
                          for m in json.load(response).get('models',[]) if m.get('name') in models or m.get('model') in models]
    except Exception as exc:
        model_error = type(exc).__name__
    versions = {}
    for package in ('numpy','contourpy','matplotlib','pydantic','shapely','pytest','PyYAML','psycopg2-binary'):
        try: versions[package] = version(package)
        except PackageNotFoundError: versions[package] = None
    timings = [r.get(k) for r in rows for k in ('timestamp','started_at','ended_at') if r.get(k)]
    manifest = {'schema_version':'marine-geollm-scie-pilot-1','run_id':run.name,
        'finalized_at':datetime.now(timezone.utc).isoformat(),'publication_status':'NOT_READY',
        'pilot_bundle_status':'INCOMPLETE' if missing else 'COMPLETED',
        'scope':'Diagnostic semantic classification, synthetic validator faults and spatial execution pilot; not expert-gold benchmark results.',
        'missing_inputs':missing,'git_head':git('rev-parse','HEAD'),'git_dirty':bool(git('status','--porcelain')),
        'source_sha256':source_hashes,'input_sha256':{p.relative_to(run).as_posix():digest(p) for p in inputs if p.exists()},
        'component_provenance':component_metadata,
        'source_audit':source_audit,
        'dataset_snapshots':snapshot_records,
        'dataset_snapshot_status':'RECORDED' if snapshots else 'NOT_AVAILABLE',
        'models_requested':models,'model_metadata':model_meta,'model_metadata_error':model_error,
        'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'packages':versions},
        'row_timestamps':{'first':min(timings) if timings else None,'last':max(timings) if timings else None},
        'input_file_mtimes_utc':{p.relative_to(run).as_posix():datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat() for p in inputs if p.exists()},
        'cases':len(cases),'rows':len(rows),'diagnostic_labels':'DRAFT; no human gold inferred'}
    run.mkdir(parents=True,exist_ok=True)
    (run/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    from ..reporting.build_tables import report
    summary = report(run,cases,rows)
    if not missing:
        latest = RESEARCH/'latest'
        latest.mkdir(exist_ok=True)
        for folder in ('tables','figures','metrics','reports'):
            shutil.copytree(run/folder,latest/folder,dirs_exist_ok=True)
        shutil.copy2(run/'manifest.json',latest/'manifest.json')
        (latest/'README.md').write_text('# Completed diagnostic pilot bundle\n\nPILOT — NOT FINAL PAPER RESULT. Publication status: NOT_READY.\n\nRaw responses remain under ignored runs/. Source and input digests are preserved in manifest.json.\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',default=str(RESEARCH/'runs/20261029_pilot'))
    args=parser.parse_args()
    result=finalize(args.run_dir)
    print(json.dumps({k:result[k] for k in ('publication_status','cases','rows')},ensure_ascii=False))
