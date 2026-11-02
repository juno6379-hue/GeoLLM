"""Reverify all six research relations and freeze current execution source bytes.

New snapshot only; no database writes, GOLD edits, or parent source rebaselining.
The parent source set must still match. Additional current execution sources
are explicitly captured for the new whole-benchmark run.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from .binding_snapshot import ROOT, digest, verify_files, TARGET_CONTAINER
from .derive_execution_snapshot import RELATION_KEYS, export_relation, safe_child


def execution_files(root=ROOT):
    files = set()
    for folder in ('services', 'shared', 'research/marine_geollm_scie/baselines',
                   'research/marine_geollm_scie/evaluation', 'research/marine_geollm_scie/runners',
                   'research/marine_geollm_scie/reliability'):
        files.update((root / folder).rglob('*.py'))
    for suffix in ('*.yaml', '*.yml'):
        files.update((root/'data').glob(suffix))
    for name in ('structured_review_v1.json', 'structured_review_v2.json', 'structured_review_v3.json',
                 'eight_execution_contract_v3.json', 'eight_execution_contract_v4.json',
                 'eight_execution_contract_v5.json',
                 'execution_success_v3_20261101_KR.md'):
        path = root/'research/marine_geollm_scie/protocol'/name
        if path.is_file():
            files.add(path)
    return sorted(files)


def freeze(parent_path, output):
    parent_path, output = Path(parent_path).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError('Fresh frozen execution snapshot required')
    parent_hash = digest(parent_path)
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    if parent.get('status') != 'LOADED_VERIFIED' or parent.get('db_identity') != {
            'container': TARGET_CONTAINER, 'database': 'scie_model_v3'}:
        raise ValueError('Expected verified research database')
    if len(parent['relations']) != 6 or {r['relation'] for r in parent['relations']} != set(RELATION_KEYS):
        raise ValueError('All six research relations required')
    verify_files(parent, parent_path.parent)
    info=json.loads(subprocess.check_output(['docker','inspect',TARGET_CONTAINER]))[0]
    if info['Config'].get('Labels',{}).get('marine.scie.research') != 'true':
        raise ValueError('Research container label required')
    files={x['path']:x for x in parent['files']}
    for path in execution_files():
        rel=path.relative_to(ROOT).as_posix()
        files[rel]={'path':rel,'sha256':digest(path),'role':'CURRENT_EXECUTION_SOURCE_NOT_GOLD'}
    result=deepcopy(parent)
    result.update(status='VERIFYING', files=list(files.values()), loaded_verification=[],
        execution_freeze={'created_at':datetime.now(timezone.utc).isoformat(),
            'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'git_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),
            'parent_manifest_sha256':parent_hash,'parent_path':str(parent_path),
            'data_rebaselined':False,'production_database_writes':False,
            'old_run_outputs_reusable':False,'requires_full_eight_method_rerun':True})
    output.mkdir(parents=True,exist_ok=False)
    def save():
        (output/'snapshot_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    try:
        for record in parent['relations']:
            dest=safe_child(output,record['csv_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            result['loaded_verification'].append(export_relation(record,dest));save()
        if digest(parent_path)!=parent_hash:
            raise ValueError('Parent changed during verification')
        verify_files(result,output)
        result['status']='LOADED_VERIFIED';save()
    except BaseException as exc:
        result.update(status='FREEZE_FAILED',error_type=type(exc).__name__,error=str(exc));save();raise
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();r=freeze(a.parent,a.output);print(json.dumps({'status':r['status'],'relations':len(r['loaded_verification']),'sources':len(r['files'])}))
