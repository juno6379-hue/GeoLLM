"""Freeze observed service cases without regenerating candidates or inventing gold."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--source-revision', required=True)
    p.add_argument('--ollama', default='http://host.docker.internal:11434')
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve earlier runs; choose a new directory')
    rows = [json.loads(line) for line in args.baseline.read_text(encoding='utf-8').splitlines()]
    args.output.mkdir(parents=True)
    copied = args.output / 'service_observations.jsonl'
    shutil.copyfile(args.baseline, copied)
    files = list((ROOT/'data').glob('*registry*.yaml')) + [ROOT/'data/marine_term_dictionary.yaml']
    files += list((ROOT/'services/orchestrator').glob('*.py'))
    files += [ROOT/'pyproject.toml', ROOT/'scripts/compare_web_pipeline_ollama.py']
    files += [f for f in (ROOT/'data/kg_ontology_contract.yaml', ROOT/'outputs/graph/kg_nodes_v2.jsonl',
                         ROOT/'outputs/graph/kg_edges_v2.jsonl') if f.exists()]
    hardware = {'platform': platform.platform(), 'python': platform.python_version(), 'cpu_count': os.cpu_count(),
                'disk_free_bytes': shutil.disk_usage(ROOT).free, 'scope': 'container_visible_only'}
    mem = Path('/proc/meminfo')
    if mem.exists():
        hardware['memory'] = [line for line in mem.read_text().splitlines() if line.startswith(('MemTotal:', 'MemAvailable:'))]
    try:
        proc = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=10)
        hardware['gpu'] = proc.stdout.strip() if proc.returncode == 0 else 'NOT_OBSERVABLE'
    except (OSError, subprocess.TimeoutExpired):
        hardware['gpu'] = 'NOT_OBSERVABLE'
    info = {}
    for endpoint in ('version', 'tags'):
        with urlopen(args.ollama+'/api/'+endpoint, timeout=10) as response:
            info[endpoint] = json.load(response)
    contracts = args.baseline.parent.parent / 'contracts-v7.jsonl'
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'source_revision': args.source_revision,
                'working_files_sha256': {str(f.relative_to(ROOT)): digest(f) for f in files},
                'baseline_sha256': digest(copied), 'case_count': len(rows), 'ollama': info, 'hardware': hardware,
                'gold_status': 'DEVELOPMENT_CASES_NOT_INDEPENDENT_GOLD', 'used_for_execution': False,
                'candidate_policy': 'Preserve entire original trace, candidate order and context; no lexical replay',
                'request_time_policy': 'Original requests did not freeze reference_now; do not invent historical reference time',
                'contracts_sha256': digest(contracts) if contracts.exists() else None}
    for package in ('kiwipiepy', 'kiwipiepy_model'):
        try:
            manifest[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            manifest[package] = 'NOT_INSTALLED'
    (args.output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'cases': len(rows), 'baseline_sha256': manifest['baseline_sha256'], 'hardware': hardware}, ensure_ascii=False))


if __name__ == '__main__':
    main()
