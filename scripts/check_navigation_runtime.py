"""Read actual task results from the running API; no fabricated service inputs."""
import argparse
import json
import time
from urllib.request import Request, urlopen


def check(base_url):
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(base_url.rstrip('/') + '/api/v1' + path, data=data,
                             headers={'Content-Type': 'application/json'}), timeout=30) as response:
            return json.load(response)

    cases = [
        ('busan_map', '이 해역의 통항위험이 높은 이유를 설명해줘', {'map_bounds': [128.98, 35.02, 129.18, 35.18]}, 'PARTIAL', '부산항'),
        ('incheon_map', '이 해역의 통항위험이 높은 이유를 설명해줘', {'map_bounds': [126.5, 37.35, 126.7, 37.55]}, 'PARTIAL', '인천항'),
        ('explicit_over_map', '인천항 통항위험이 높은 이유를 설명해줘', {'map_bounds': [128.98, 35.02, 129.18, 35.18]}, 'PARTIAL', '인천항'),
        ('no_context', '이 해역의 통항위험이 높은 이유를 설명해줘', {}, 'NEEDS_CLARIFICATION', None),
        ('remote_context', '이 해역의 통항위험이 높은 이유를 설명해줘', {'map_center': [0, 0]}, 'NEEDS_CLARIFICATION', None),
        ('unknown_port', '존재하지않는항 통항위험 분석해줘', {}, 'NEEDS_CLARIFICATION', None),
        ('definition', '조석예보란', {}, 'COMPLETED', None),
    ]
    checks = []
    for name, query, spatial, expected, port in cases:
        task = request('/tasks', {'query': query, 'spatial_context': spatial})
        deadline = time.monotonic() + 150
        while True:
            result = request('/tasks/' + task['task_id'])
            if result.get('status') in {'PARTIAL', 'COMPLETED', 'FAILED', 'BLOCKED', 'NEEDS_CLARIFICATION'} or time.monotonic() > deadline:
                break
            time.sleep(0.5)
        final = result.get('final_result') or {}
        structured = final.get('structured_result') or {}
        location = structured.get('nearest_port_resolution') or {}
        route = (final.get('orchestrator_v2') or {}).get('route_plan') or {}
        intent = (result.get('parsed_intent') or {}).get('intent_type')
        passed = result.get('status') == final.get('status') == expected
        passed &= intent == route.get('intent') == ('DEFINITION' if name == 'definition' else 'ANALYSIS')
        if port:
            passed &= location.get('port') == port and bool(location.get('source_id'))
            passed &= bool(structured.get('traffic_analysis'))
            passed &= (structured.get('quality_metrics') or {}).get('evaluation_status') == 'NOT_EVALUATED'
        row = {'case': name, 'passed': bool(passed), 'status': result.get('status'), 'intent': intent,
               'port': location.get('port'), 'source_id': location.get('source_id'),
               'traffic_available': bool(structured.get('traffic_analysis')), 'error_code': final.get('error_code')}
        checks.append(row)
        print(json.dumps(row, ensure_ascii=True), flush=True)
    return all(row['passed'] for row in checks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://localhost:8000')
    raise SystemExit(0 if check(parser.parse_args().base_url) else 1)
