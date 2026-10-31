"""Create/verify a content-addressed, write-once benchmark bundle."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[3]
REQUIRED_FILES = frozenset({
    'answer_contracts.jsonl', 'canonical_busan_boundary.json',
    'parent_gold_manifest.json', 'queries.jsonl', 'comparison_protocol.json',
    'oracle_checks.json', 'oracle_query.sql', 'source_checks.json',
})


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder, *, expected_manifest_sha256=None):
    folder=Path(folder).resolve()
    manifest_hash = digest(folder/'manifest.json')
    if expected_manifest_sha256 is not None and manifest_hash != expected_manifest_sha256:
        raise ValueError('Frozen manifest differs from pinned run identity')
    if manifest_hash!=(folder/'manifest.sha256').read_text().strip():
        raise ValueError('Frozen manifest changed')
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    names = [entry['name'] for entry in manifest['files']]
    if len(names) != len(set(names)) or set(names) != REQUIRED_FILES:
        raise ValueError('Frozen benchmark artifact set mismatch')
    for entry in manifest['files']:
        path=(folder/entry['name']).resolve()
        if not path.is_relative_to(folder) or not path.is_file() or digest(path)!=entry['sha256']:
            raise ValueError('Frozen benchmark artifact changed: '+entry['name'])
    contracts=[json.loads(x) for x in (folder/'answer_contracts.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    queries=[json.loads(x) for x in (folder/'queries.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    expected={f'PILOT_Q{group}_{case:02}' for group in range(1,7) for case in range(1,4)}
    if (manifest.get('case_count') != 18 or len(contracts) != 18 or len(queries) != 18
            or {x['case_id'] for x in contracts} != expected
            or {x['case_id'] for x in queries} != expected):
        raise ValueError('Benchmark identity mismatch')
    if manifest.get('execution_ready_is_separate_gate') is not True:
        raise ValueError('Freeze must not imply execution readiness')
    return manifest


def freeze(output):
    output=Path(output)
    if output.exists():
        raise FileExistsError('Frozen bundle already exists: '+str(output))
    parent=ROOT/'research/marine_geollm_scie/benchmark/gold_v2_20261031_r2'
    old=json.loads((parent/'manifest.json').read_text(encoding='utf-8'))
    if digest(parent/'answer_contracts.jsonl')!=old['contract_sha256']:
        raise ValueError('GOLD parent changed')
    sources={
        'answer_contracts.jsonl':parent/'answer_contracts.jsonl',
        'canonical_busan_boundary.json':parent/'canonical_busan_boundary.json',
        'parent_gold_manifest.json':parent/'manifest.json',
        'queries.jsonl':ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl',
        'comparison_protocol.json':ROOT/'research/marine_geollm_scie/protocol/gold_v2_comparison_contract.json',
        'oracle_checks.json':ROOT/'outputs/gold_v2_oracle_audit_20261031_v3/summary.json',
        'oracle_query.sql':ROOT/'outputs/gold_v2_oracle_audit_20261031_v3/independent_queries.sql',
        'source_checks.json':ROOT/'outputs/gold_v2_oracle_audit_20261031_v3/source_checks.json',
    }
    if digest(sources['oracle_checks.json'])!=old['oracle_audit_summary_sha256'] or digest(sources['oracle_query.sql'])!=old['oracle_query_sha256']:
        raise ValueError('Oracle lineage changed')
    contracts=[json.loads(x) for x in sources['answer_contracts.jsonl'].read_text(encoding='utf-8').splitlines()]
    queries=[json.loads(x) for x in sources['queries.jsonl'].read_text(encoding='utf-8').splitlines()]
    if len(queries)!=18 or len(contracts)!=18 or len({x['case_id'] for x in queries})!=18 or {x['case_id'] for x in queries}!={x['case_id'] for x in contracts}:
        raise ValueError('Benchmark identity mismatch')
    output.mkdir(parents=True,exist_ok=False)
    files=[]
    for name,path in sources.items():
        shutil.copyfile(path,output/name)
        files.append({'name':name,'sha256':digest(output/name),'source':str(path.relative_to(ROOT))})
    manifest={'version':'GOLD_v2_immutable_v1','created_at':datetime.now(timezone.utc).isoformat(),
        'files':files,'case_count':18,'methods':['B0','B1','B2','B3','B4','P0','H','P1'],
        'immutability':'exclusive creation + SHA256 manifest; any change requires a new bundle ID',
        'independent_expert_review_complete':False,'benchmark_freeze_complete':True,
        'execution_ready_is_separate_gate':True,'old_results_reusable':False,
        'supplementary_busan_cases_included':False}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'manifest.sha256').write_text(digest(output/'manifest.json')+'\n',encoding='ascii')
    return verify(output)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--verify-only',action='store_true')
    a=p.parse_args();print(json.dumps(verify(a.output) if a.verify_only else freeze(a.output),ensure_ascii=True))
