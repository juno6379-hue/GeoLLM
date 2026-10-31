"""Serial frozen K5 research run; failures and original per-run rows are immutable."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT/'research/marine_geollm_scie'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    tmp = path.with_suffix('.pending.json')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def source_paths(root=ROOT):
    paths = list((root/'services').rglob('*.py'))+list((root/'shared').rglob('*.py'))
    paths += list((root/'research/marine_geollm_scie/runners').glob('*.py'))
    paths += list((root/'research/marine_geollm_scie/baselines').glob('*.py'))
    paths += list((root/'research/marine_geollm_scie/benchmark/frozen_v5').glob('*'))
    paths += list((root/'data').glob('*.json'))+list((root/'data').glob('*.yaml'))
    paths += [root/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl']
    return sorted(p for p in set(paths) if p.is_file())


def require_unchanged(hashes):
    for path, expected in hashes.items():
        if not Path(path).is_file() or sha(path) != expected:
            raise ValueError('Frozen artifact changed: '+str(path))


def require_models(expected):
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=30) as response:
        tags = json.load(response)
    actual = {r['name']: r['digest'] for r in tags['models']}
    if any(actual.get(name) != digest for name, digest in expected.items()):
        raise ValueError('Pinned model identity changed')


def validate_stage(folder, kind):
    folder = Path(folder)
    if kind == 'baseline':
        m = read(folder/'manifest.json')
        if (m.get('status') != 'COMPLETED' or m.get('rows') != 450
                or m.get('repeats') != 5 or m.get('source_integrity_after') is not True
                or m.get('snapshot_manifest_unchanged') is not True):
            raise ValueError('Baseline K5 completion/integrity gate failed')
        path = folder/'execution_rows.jsonl'
        rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
        keys = {(r['case_id'], r['method'], r['repeat']) for r in rows}
        case_ids = {json.loads(s)['case_id'] for s in (RESEARCH/'benchmark/query_cases_v1.jsonl').read_text(encoding='utf-8').splitlines()}
        expected = {(c, method+'_EXECUTION_ADAPTER', repeat) for c in case_ids
                    for method in ('B0', 'B1', 'B2', 'B3', 'B4') for repeat in range(5)}
        if len(rows) != 450 or len(keys) != 450 or keys != expected or sha(path) != m.get('rows_sha256'):
            raise ValueError('Baseline raw observations incomplete or changed')
    else:
        m = read(folder/'model_graph_manifest.json')
        if (m.get('worker_status') != 'EXECUTION_OBSERVED' or m.get('observed_rows') != 18
                or m.get('source_unchanged_after') is not True
                or (m.get('warmup_verification') or {}).get('status') != 'WARMUP_OBSERVED_WITHOUT_PROXY_ERRORS'):
            raise ValueError('Graph completion/warmup/integrity gate failed')
        path = folder/'production_rows.jsonl'
        rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
        case_ids = {json.loads(s)['case_id'] for s in (RESEARCH/'benchmark/query_cases_v1.jsonl').read_text(encoding='utf-8').splitlines()}
        if len(rows) != 18 or {r['case_id'] for r in rows} != case_ids:
            raise ValueError('Graph raw observations incomplete')
    return {'rows': len(rows), 'raw_path': str(path), 'raw_sha256': sha(path)}


def _run(output, baseline_profile, model_profile, snapshot, contracts, *, execute=False):
    output, baseline_profile, model_profile, snapshot, contracts = [Path(p).resolve() for p in
        (output, baseline_profile, model_profile, snapshot, contracts)]
    if output.exists():
        raise FileExistsError('Fresh repeat experiment directory required')
    baseline, model = read(baseline_profile), read(model_profile)
    expected_snapshot = sha(snapshot)
    if any(p.get('contains_gold_answers') is not False for p in (baseline, model)):
        raise ValueError('Generation profiles must exclude GOLD')
    if any(p.get('snapshot_manifest', {}).get('sha256') != expected_snapshot for p in (baseline, model)):
        raise ValueError('Both profiles must bind the same immutable snapshot')
    if baseline.get('model_digest') != model.get('model_digests', {}).get('qwen2.5:1.5b'):
        raise ValueError('Generation model digest differs across conditions')
    output.mkdir(parents=True)
    (output/'baseline_profile.json').write_bytes(baseline_profile.read_bytes())
    (output/'model_profile.json').write_bytes(model_profile.read_bytes())
    baseline_profile, model_profile = output/'baseline_profile.json', output/'model_profile.json'
    hashes = {str(p): sha(p) for p in source_paths()+[baseline_profile, model_profile, snapshot, contracts]}
    state = {'status': 'PREPARED', 'pid': os.getpid(), 'repeats': 5, 'planned_baseline_rows': 450,
        'planned_graph_rows': 90, 'source_hashes': hashes, 'events': [],
        'created_at': datetime.now(timezone.utc).isoformat(), 'snapshot': str(snapshot),
        'contracts': str(contracts), 'semantic_accuracy': None, 'independent_human_gold': False,
        'repeat_policy': 'Baseline seeds 42..46; P unmodified production generation options, fresh process each repeat. Repeat indices stored externally; raw repeat=0 retained.',
        'schedule_policy': 'Serialized graph repeat0, baselines K5, graph repeats1..4; temporal/cache order confounding retained, no parallel Ollama jobs.'}

    def save():
        state['observed_at'] = datetime.now(timezone.utc).isoformat()
        write(output/'status.json', state)

    def stage(name, module, args, timeout, folder=None, kind=None):
        require_unchanged(hashes)
        require_models(model['model_digests'])
        state.update(status='RUNNING', stage=name)
        save()
        with (output/(name+'.log')).open('xb') as log:
            child = subprocess.Popen([sys.executable, '-u', '-m', module, *map(str, args)], cwd=ROOT,
                                     stdout=log, stderr=subprocess.STDOUT)
            state['child_pid'] = child.pid
            save()
            started = time.monotonic()
            while child.poll() is None:
                if (output/'STOP_AFTER_STAGE').exists():
                    state['stop_requested'] = True
                if time.monotonic()-started > timeout:
                    child.terminate()
                    child.wait(timeout=30)
                    raise TimeoutError(name+' deadline; partial artifacts retained, inspect descendants before resuming')
                save()
                time.sleep(5)
        state['child_pid'] = None
        state['events'].append({'stage': name, 'exit_code': child.returncode,
                                'finished_at': datetime.now(timezone.utc).isoformat()})
        save()
        require_unchanged(hashes)
        require_models(model['model_digests'])
        if child.returncode:
            raise RuntimeError(name+' failed; original artifacts retained')
        if folder is not None:
            state['events'][-1]['verification'] = validate_stage(folder, kind)
        save()
        if state.get('stop_requested') or (output/'STOP_AFTER_STAGE').exists():
            raise InterruptedError('Stopped at completed stage boundary as requested')

    save()
    if not execute:
        return state
    try:
        folder = output/'graph_repeat_0'
        stage('graph_repeat_0', 'research.marine_geollm_scie.runners.launch_model_graph',
              ['--output', folder, '--snapshot', snapshot, '--profile', model_profile], 14400, folder, 'graph')
        stage('baselines_k5', 'research.marine_geollm_scie.runners.compare_execution',
              ['--output-dir', output/'baselines', '--profile', baseline_profile, '--execute', '--repeats', '5'],
              43200, output/'baselines', 'baseline')
        for index in range(1, 5):
            folder = output/f'graph_repeat_{index}'
            stage(f'graph_repeat_{index}', 'research.marine_geollm_scie.runners.launch_model_graph',
                  ['--output', folder, '--snapshot', snapshot, '--profile', model_profile], 14400, folder, 'graph')
        stage('repeat_report', 'research.marine_geollm_scie.runners.repeat_analysis',
              ['--run', output, '--contracts', contracts, '--output', output/'report'], 600)
        state.update(status='COMPLETED_OBSERVATIONS', stage='DONE', scientific_completion=False)
    except BaseException as exc:
        state.update(status='PAUSED_AT_STAGE_BOUNDARY' if isinstance(exc, InterruptedError) else 'STOPPED_REQUIRES_REVIEW',
                     error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()
    return state


def require_no_active_research():
    names = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    if set(names) & {'marine-scie-model-worker', 'marine-scie-model-proxy', 'geollm-dataset-embedding-completion'}:
        raise RuntimeError('Existing model/embedding worker; serialized research required')
    if os.name == 'nt':
        # Match executable modules of Python processes only; do not mistake the
        # parent PowerShell command text for another Python research worker.
        command = "$all = Get-CimInstance Win32_Process; $excluded = @("+str(os.getpid())+"); $cursor = "+str(os.getpid())+"; while ($cursor -gt 0) { $item = $all | Where-Object ProcessId -eq $cursor; if (!$item) { break }; $cursor = $item.ParentProcessId; if ($excluded -contains $cursor) { break }; $excluded += $cursor }; $all | Where-Object { $_.Name -match '^python(w)?(\\.exe)?$' -and $excluded -notcontains $_.ProcessId -and $_.CommandLine -match ' -m research\\.marine_geollm_scie\\.runners\\.(compare_execution|launch_model_graph|repeat_experiment|full_pipeline)( |$)' } | Select-Object -ExpandProperty ProcessId"
        found = subprocess.check_output(['powershell', '-NoProfile', '-Command', command], text=True).strip()
        if found:
            raise RuntimeError('Existing Python research worker; serialized execution required')


def run(output, baseline_profile, model_profile, snapshot, contracts, *, execute=False):
    if not execute:
        return _run(output, baseline_profile, model_profile, snapshot, contracts, execute=False)
    lock = ROOT/'outputs/scie_repeat_active.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'output': str(Path(output).resolve())}))
    try:
        require_no_active_research()
        return _run(output, baseline_profile, model_profile, snapshot, contracts, execute=True)
    finally:
        # Only our exclusive lock is removed. Abnormal process termination leaves
        # a stale lock intentionally; inspect actual workers before manual recovery.
        lock.unlink()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('output', 'baseline-profile', 'model-profile', 'snapshot', 'contracts'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    run(a.output, a.baseline_profile, a.model_profile, a.snapshot, a.contracts, execute=a.execute)
