"""Controlled live API probes; not browser E2E or human-gold accuracy tests.

Use a completed check_marine_mapping_runtime run as the real geometry source.
The selected geometry is an explicit evaluation input, not a browser selection.
"""
import argparse
import json
from pathlib import Path

from scripts.check_geollm_web_samples import observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--anchor-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default='http://localhost:8000')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new output path; preserve previous observations')
    anchors = [json.loads(line) for line in args.anchor_run.read_text(encoding='utf-8').splitlines()]
    anchor = next(row for row in anchors if row.get('sample') == 201 and row.get('contract_check_passed'))
    context = anchor['spatial_context']
    if not context.get('geometry') or not anchor.get('evaluation_anchor'):
        raise ValueError('A recorded, source-backed evaluation geometry is required')
    cases = [
        (401, '창원 정비불량 사고를 찾아줘', {}),
        (402, '위험객체', context),
        (403, '반경 1km 이내 위험객체를 찾아줘', context),
        (404, '부산항 최신 적재 월 AIS 통항량을 구역별로 요약해줘', {}),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    observations = []
    with args.output.open('x', encoding='utf-8') as stream:
        for number, query, spatial in cases:
            row = observe(args.base_url.rstrip('/'), number, query, spatial)
            row.update(human_gold=False, evaluation_note='Controlled API input, not an observed browser selection',
                       anchor_run=str(args.anchor_run), evaluation_anchor=anchor['evaluation_anchor'] if spatial else None)
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
            result = (row.get('completion') or {}).get('final_result') or {}
            structured = result.get('structured_result') or {}
            print(json.dumps({'sample': number, 'observation': row['observation'], 'status': result.get('status'),
                              'error_code': result.get('error_code'), 'distance_m': structured.get('distance_m'),
                              'count': structured.get('count'), 'answer': result.get('answer_text')}, ensure_ascii=True), flush=True)
            observations.append(row)
    # A complete observation is not a correct semantic answer.
    return int(any(row['observation'] != 'COMPLETED_EVENT_RECEIVED' for row in observations))


if __name__ == '__main__':
    raise SystemExit(main())
