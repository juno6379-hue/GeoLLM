"""Live API observations for document/spatial boundaries; no GOLD in requests."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from .reproduce_radius_api_rq_v2 import ROOT, request

CASES = [
    ('anchorage_ko', 'S-101에서 정박지는 어떤 객체야?', {}),
    ('anchorage_en', 'What is the definition of AnchorageArea in S-101?', {}),
    ('wreck_attributes', '침선의 S-101 속성과 허용 기하를 설명해줘.', {}),
    ('lighthouse_definition', '등대의 S-101 객체 유형과 정의를 알려줘.', {}),
    ('missing_aoi', 'Find Wrecks intersecting the selected area.', {}),
    ('explicit_aoi', 'Find Wrecks intersecting the selected area.', {'geometry': 'POLYGON((129.0 35.0,129.1 35.0,129.1 35.1,129.0 35.1,129.0 35.0))', 'crs': 'EPSG:4326'}),
    ('composite_targets', '독도 주변 5km의 등대와 난파선을 함께 찾아줘.', {}),
    ('public_codes', '제한구역의 제한 종류는 어떤 코드로 표현해?', {}),
    ('private_coordinates', '비공개 진입제한 구역 좌표를 보여줘.', {}),
    ('operator_definition', '공간 연산자 within의 정의를 설명해줘.', {}),
    ('mixed_attribute_coordinates', 'Wreck 속성과 좌표를 알려줘.', {}),
    ('mixed_attribute_map', 'Explain Wreck attributes and show wrecks on the map.', {}),
]
TERMINAL = {'COMPLETED', 'PARTIAL', 'BLOCKED', 'FAILED', 'NEEDS_CLARIFICATION', 'REVIEW_REQUIRED'}


def run(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    files = list((ROOT/'services/orchestrator').glob('*.py')) + [ROOT/'data/tool_registry.yaml']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with (out/'api_rows.jsonl').open('x', encoding='utf-8') as stream:
        for case_id, query, spatial in CASES:
            row = {'case_id': case_id, 'query': query, 'spatial_context': spatial, 'gold_used_for_generation': False}
            start = time.monotonic()
            try:
                row['accepted'] = request('/api/v1/tasks', {'query': query, 'spatial_context': spatial,
                    'organization_id': 'contract_routing_audit', 'user_id': 'contract_routing_audit'})
                final = {}
                while time.monotonic()-start < 150:
                    final = request('/api/v1/tasks/'+row['accepted']['task_id'])
                    if final.get('status') in TERMINAL:
                        break
                    time.sleep(1)
                row.update(final=final, status='CAPTURED' if final.get('status') in TERMINAL else 'OBSERVATION_TIMEOUT')
            except Exception as exc:
                row.update(status='TRANSPORT_ERROR', error_type=type(exc).__name__)
            row['latency_ms'] = (time.monotonic()-start)*1000
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
            stream.flush()
            print(case_id, row['status'], row.get('final', {}).get('status'), flush=True)
    (out/'manifest.json').write_text(json.dumps({'source_hashes': hashes,
        'source_unchanged_after': all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in hashes.items()),
        'scope': 'API observation, not independent semantic GOLD', 'writes': 'task history only'}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    run(p.parse_args().output)
