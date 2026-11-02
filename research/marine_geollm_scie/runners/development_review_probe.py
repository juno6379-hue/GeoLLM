"""Small development review probe; no GOLD, GIS, holdout or benchmark execution."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

from .structured_review import call_review, REVIEW_VERSION, REVIEW_BUDGET
from ..baselines.tool_contract import TOOL_INSTRUCTIONS, TOOL_SCHEMAS

ROOT = Path(__file__).resolve().parents[3]
MODEL = 'qwen2.5:1.5b'
DIGEST = '65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b'
SEED = 42
SOURCES = (
    'research/marine_geollm_scie/runners/development_review_probe.py',
    'research/marine_geollm_scie/runners/structured_review.py',
    'research/marine_geollm_scie/runners/review_consistency.py',
    'research/marine_geollm_scie/baselines/plan_comparison.py',
    'research/marine_geollm_scie/baselines/tool_contract.py',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def model_digest():
    with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10) as response:
        tags = json.load(response)
    return next((m['digest'] for m in tags['models'] if m['name'] == MODEL), None)


def cases():
    query = '제공한 기준점에서 반경 1500m 이내의 Wreck를 찾아줘. 좌표 CRS는 EPSG:4326이다.'
    args = dict(source='s101', feature_types=['Wreck'],
                reference_geometry='POINT(129.08 35.08)', crs='EPSG:4326',
                radius_m=1500, relation='dwithin', analysis_type='feature_search_by_radius')
    initial = dict(action='search', intent='spatial_search', target_features=['Wreck'],
                   attributes=[], spatial_relation='dwithin', location_text=None,
                   radius_m=1500, crs='EPSG:4326',
                   tool_calls=[dict(tool_id='spatial.query', arguments=args)],
                   evidence_refs=[], missing_inputs=[], answer='')
    context = dict(map=dict(geometry=args['reference_geometry'], crs='EPSG:4326'),
                   source_scope={'s101': dict(scope_verified=True,
                       scope_type='SYNTHETIC_DEVELOPMENT_INPUT_ONLY',
                       bbox_epsg4326=[129.0, 35.0, 129.2, 35.2],
                       real_world_completeness=False)},
                   allowed_feature_codes=['Wreck', 'Obstruction'],
                   tool_instructions=TOOL_INSTRUCTIONS, tool_schemas=TOOL_SCHEMAS)
    specifications = [('NORMAL', None, None), ('CRS', 'crs', 'EPSG:3857'),
                      ('RADIUS', 'radius_m', 4500), ('MISSING_GEOMETRY', 'reference_geometry', None)]
    result = []
    for name, key, value in specifications:
        plan, public = copy.deepcopy(initial), copy.deepcopy(context)
        if key:
            if value is None:
                plan['tool_calls'][0]['arguments'].pop(key)
                public['map'].pop('geometry')
            else:
                plan['tool_calls'][0]['arguments'][key] = value
        result.append(dict(case_id='DEV_REVIEW_' + name, query=query, context=public,
                           initial_plan=plan, expected_invalid=key is not None,
                           label_basis='SYNTHETIC_DEVELOPMENT_CONSTRAINT_NOT_HUMAN_GOLD'))
    return result


def run(output):
    if model_digest() != DIGEST:
        raise ValueError('Pinned model digest differs')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    hashes = {name: digest(ROOT / name) for name in SOURCES}
    manifest = dict(kind='DEVELOPMENT_PROBE_NOT_PAPER_RESULT', model=MODEL,
                    model_digest=DIGEST, seed=SEED, review_version=REVIEW_VERSION,
                    budget=REVIEW_BUDGET, source_hashes=hashes, warmup_calls=0,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    gis_execution=False, holdout_used=False, expected_observations=4)
    save(output / 'manifest.json', manifest)
    rows = []
    for item in cases():
        save(output / (item['case_id'] + '.input.json'), item)
        call, review, errors = call_review(item['query'], item['context'],
                                           item['initial_plan'], model=MODEL, seed=SEED)
        raw_invalid = call['review_consistency']['raw_initial_invalid']
        row = dict(**item, call=call, review=review, errors=errors,
                   raw_initial_invalid=raw_invalid, usable=review is not None,
                   raw_verdict_matches_control=(raw_invalid == item['expected_invalid'])
                       if type(raw_invalid) is bool else None)
        save(output / (item['case_id'] + '.result.json'), row)
        rows.append(row)
        print(json.dumps(dict(case_id=item['case_id'], status=call['status'],
            raw_initial_invalid=raw_invalid, usable=row['usable'], errors=errors)), flush=True)
    stable = hashes == {name: digest(ROOT / name) for name in SOURCES}
    model_stable = model_digest() == DIGEST
    summary = dict(kind=manifest['kind'], observations=len(rows), denominator=4,
        model_digest_stable=model_stable, sources_stable=stable,
        raw_verdict_matches=sum(r['raw_verdict_matches_control'] is True for r in rows),
        raw_verdict_missing=sum(r['raw_verdict_matches_control'] is None for r in rows),
        usable=sum(r['usable'] for r in rows),
        undeclared_changes=sum(r['call']['review_consistency']['undeclared_plan_change'] is True for r in rows),
        limits=['Synthetic development inputs; no GIS execution or source truth verification',
                'K1, no warmup, no independent human GOLD, no benchmark comparison',
                'Contract rejection is not a positive LLM error detection'])
    save(output / 'summary.json', summary)
    if not (stable and model_stable):
        raise ValueError('Probe lineage changed; preserve outputs and do not compare')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        parser.error('Explicit --execute required for four real model calls')
    print(json.dumps(run(args.output), ensure_ascii=False))
