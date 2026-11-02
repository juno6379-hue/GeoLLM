"""Development UI API replay. Preserve every SSE event, including partial failures."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--cases', default='outputs/api_probe_20261102_v1/summary.jsonl')
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    cases = [json.loads(line) for line in Path(args.cases).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ('services/orchestrator', 'services/spatial_analysis_agent')
              for p in Path(folder).rglob('*') if p.suffix in ('.py', '.js', '.html')}
    (output / 'sources.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    for case in cases:
        events, error = [], None
        start = time.time()
        status = {'index': case['idx'], 'query': case['query'], 'status': 'RUNNING'}
        (output / 'status.json').write_text(json.dumps(status, ensure_ascii=False), encoding='utf-8')
        request = urllib.request.Request('http://localhost:8000/api/v1/tasks/stream',
            data=json.dumps({'query': case['query']}).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                for raw in response:
                    line = raw.decode('utf-8').strip()
                    if line.startswith('data:'):
                        events.append(json.loads(line[5:]))
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        final = next((e['final_result'] for e in reversed(events) if isinstance(e.get('final_result'), dict)), {})
        features = final.get('features') or []
        if isinstance(features, dict):
            features = features.get('features') or []
        row = {'index': case['idx'], 'query': case['query'], 'elapsed': time.time()-start,
               'transport_error': error, 'status': final.get('status'), 'error_code': final.get('error_code'),
               'final_received': bool(final), 'feature_count': len(features),
               'answer': final.get('answer_text'), 'events': events}
        (output / f"{case['idx']:02d}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        print(case['idx'], row['status'], row['error_code'], flush=True)
    changed = [name for name, digest in hashes.items() if not Path(name).exists() or hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest]
    (output / 'status.json').write_text(json.dumps({'status': 'COLLECTION_FINISHED', 'cases': len(cases), 'changed_sources': changed,
        'interpretation': 'development replay, not paper benchmark or human accuracy'}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
