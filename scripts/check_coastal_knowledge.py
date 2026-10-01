"""Read-only runtime checks; preserve responses, including partial embedding coverage."""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def get(path):
    with urllib.request.urlopen('http://localhost:8000/api/v1/' + path,timeout=240) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', action='store_true')
    parser.add_argument('--semantic', action='store_true')
    parser.add_argument('--stream', action='store_true')
    args = parser.parse_args()
    output = Path('outputs/coastal_knowledge/runtime_checks')
    output.mkdir(parents=True,exist_ok=True)
    records = []
    if args.stream:
        request = urllib.request.Request('http://localhost:8000/api/v1/tasks/stream',
            data=json.dumps({'query':'부산항 입구로 이동'}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=240) as response:
            completed = None
            for line in response:
                if line.startswith(b'data: '):
                    event = json.loads(line[6:])
                    if event.get('event') == 'completed':
                        completed = event
            assert completed is not None
            final = completed['final_result']
            assert final['status']=='NEEDS_CLARIFICATION'
            assert final['coastal_evidence']['documents']
            assert final['coastal_evidence']['execution_validation']['operation']=='coastal_evidence_lookup'
            records.append({'stream_result':completed})
            print(json.dumps({'stream_status':final['status'],'documents':len(final['coastal_evidence']['documents'])}),flush=True)
    queries = ['부산항 입구로 이동','다대포항 항해 정보를 알려줘','울릉도 주변 항만 정보','없는항구XYZ123 입구']
    for query in queries:
        started = time.monotonic()
        result = get('coastal-evidence?' + urllib.parse.urlencode({'query':query,'semantic':str(args.semantic).lower()}))
        record = {'query':query,'elapsed':round(time.monotonic()-started,2),'result':result}
        records.append(record)
        assert result['status']=='COMPLETED'
        assert result['execution_validation']['authority']=='ExecutionValidator'
        assert result['coordinate_authority'] is False
        if query.startswith('없는'):
            assert not result['documents']
        else:
            assert result['documents'],query
            assert all(d['source_sha256'] for d in result['documents'])
        print(json.dumps({'query':query,'docs':len(result['documents']),'links':len(result['knowledge_links']),'elapsed':record['elapsed']},ensure_ascii=False),flush=True)
    if args.model:
        result = get('coastal-explanation?' + urllib.parse.urlencode({'query':'부산항 입구 관련 정보를 알려줘'}))
        records.append({'model_result':result})
        print(json.dumps(result,ensure_ascii=False),flush=True)
    name = f'{time.time_ns()}-{"vector" if args.semantic else "lexical"}.json'
    (output / name).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
