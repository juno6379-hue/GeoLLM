"""Observe live web preset responses via SSE; this is NOT browser/UI validation."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen


def extract_presets(html):
    match = re.search(r'function setupPresetPrompts\(\)\s*\{\s*const prompts\s*=\s*(\[.*?\]);', html, re.S)
    if not match:
        raise ValueError('Live page preset definition was not found')
    prompts = json.loads(match.group(1))
    if not prompts or not all(isinstance(p, str) for p in prompts):
        raise ValueError('Invalid live preset list')
    return prompts


def observe(base_url, number, query, spatial_context=None, *, socket_timeout=30, observation_timeout=120):
    context = spatial_context or {}
    row = {'sample': number, 'query': query, 'browser_tested': False, 'spatial_context': context, 'events': []}
    start = time.monotonic()
    try:
        body = json.dumps({'query': query, 'user_id': 'admin', 'organization_id': 'test',
                           'spatial_context': context}, ensure_ascii=False).encode()
        req = Request(base_url+'/api/v1/tasks/stream', data=body, headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=socket_timeout) as response:
            for raw in response:
                if time.monotonic()-start > observation_timeout:
                    raise TimeoutError('Observation deadline exceeded; backend task may still be running')
                line = raw.decode('utf-8').strip()
                if not line.startswith('data: '):
                    continue
                event = json.loads(line[6:])
                row['events'].append(event)
                if event.get('task_id'):
                    row['task_id'] = event['task_id']
                if event.get('event') == 'completed':
                    row['completion'] = event
                    row['observation'] = 'COMPLETED_EVENT_RECEIVED'
                    break
            else:
                row['observation'] = 'STREAM_ENDED_WITHOUT_COMPLETION'
    except Exception as exc:
        row.update(observation='OBSERVATION_ERROR', observation_error=f'{type(exc).__name__}: {exc}')
    row['elapsed_seconds'] = round(time.monotonic()-start, 3)
    return row


def observed_status(row):
    completion = row.get('completion') or {}
    return (completion.get('final_result') or {}).get('status') or completion.get('status') or row['observation']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2, choices=[1,2])
    parser.add_argument('--ids', nargs='+', type=int)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new output directory')
    with urlopen(args.base_url+'/', timeout=30) as response:
        page = response.read().decode('utf-8')
    prompts = extract_presets(page)
    cases = [(i,p) for i,p in enumerate(prompts,1) if not args.ids or i in args.ids]
    args.output.mkdir(parents=True)
    (args.output/'live_page.html').write_text(page, encoding='utf-8')
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'url': args.base_url+'/',
                'page_sha256': hashlib.sha256(page.encode()).hexdigest(), 'presets': prompts,
                'selected_ids': [i for i,_ in cases], 'browser_tested': False,
                'limitation': 'Direct SSE observation; current browser viewport, UI rendering and clicks are NOT observed. No fabricated map context.'}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(observe,args.base_url,number,query) for number,query in cases]
        for future in as_completed(futures):
            row=future.result()
            rows.append(row)
            with (args.output/'responses.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            final = (row.get('completion') or {}).get('final_result') or {}
            print(json.dumps({'sample':row['sample'],'observation':row['observation'],
                              'status':observed_status(row),'error_code':final.get('error_code'),
                              'seconds':row['elapsed_seconds']},ensure_ascii=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps({'count':len(rows),'browser_tested':False,
        'status_is_not_accuracy': True,
        'statuses':dict(Counter(observed_status(r) for r in rows)),
        'failed_tasks':[r['sample'] for r in rows if observed_status(r)=='FAILED'],
        'observation_errors':[r['sample'] for r in rows if r['observation']!='COMPLETED_EVENT_RECEIVED']},indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
