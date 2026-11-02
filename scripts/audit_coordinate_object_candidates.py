"""Non-authoritative coordinate/object proximity candidates for manual review.

Uses operational snapshots only. Spherical distance is a review aid, not a GIS
execution result, canonical identity, entrance position, or research GOLD.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

TABLES = ('small_harbour_guide', 'marine_gazetteer_current', 'island_gazetteer_current', 'navigation_aid_current')


def point(row):
    geo = row.get('geojson')
    if isinstance(geo, str):
        geo = json.loads(geo)
    if not isinstance(geo, dict) or geo.get('type') != 'Point':
        return None
    coords = geo.get('coordinates') or []
    if len(coords) < 2:
        return None
    lon, lat = coords[:2]
    if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in (lon, lat)):
        return None
    return (lon, lat) if -180 <= lon <= 180 and -90 <= lat <= 90 else None


def distances(lon, lat, points):
    values = np.radians(points)
    longitude, latitude = math.radians(lon), math.radians(lat)
    a = np.sin((values[:, 1] - latitude) / 2) ** 2 + math.cos(latitude) * np.cos(values[:, 1]) * np.sin((values[:, 0] - longitude) / 2) ** 2
    return 6371008.8 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--spatial', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate-distance-m', type=float, default=100)
    args = parser.parse_args()
    if not math.isfinite(args.candidate_distance_m) or not 0 < args.candidate_distance_m <= 1000:
        raise ValueError('Candidate distance must be 0..1000 m, exclusive zero')
    args.output.mkdir(parents=True, exist_ok=False)
    inputs, objects, positions = {}, [], []
    pair_path = args.source / 'explicit_coordinate_pairs.jsonl'
    paths = [pair_path] + [args.spatial / (table + '.json') for table in TABLES]
    for path in paths:
        inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for table in TABLES:
        rows = json.loads((args.spatial / (table + '.json')).read_text(encoding='utf-8'))
        for row in rows:
            geo = row.get('geojson')
            geo = json.loads(geo) if isinstance(geo, str) else geo
            parts = ([{'type': 'Point', 'coordinates': c} for c in geo.get('coordinates', [])]
                     if isinstance(geo, dict) and geo.get('type') == 'MultiPoint' else [geo])
            for part in parts:
                position = point({'geojson': part})
                if position is not None:
                    positions.append(position)
                    objects.append({'source_id': row['source_id'], 'name': row.get('name'), 'relation': 'serving.' + table})
    positions = np.asarray(positions)
    total = eligible = linked = ambiguous = 0
    with pair_path.open(encoding='utf-8') as stream, (args.output / 'candidates.jsonl').open('w', encoding='utf-8') as out:
        for line in stream:
            row = json.loads(line)
            total += 1
            if row.get('status') != 'EXPLICIT_PAIR_RANGE_VALID_LOCATION_UNVERIFIED':
                continue
            lon, lat = row.get('longitude'), row.get('latitude')
            if point({'geojson': {'type': 'Point', 'coordinates': [lon, lat]}}) is None:
                continue
            eligible += 1
            meters = distances(lon, lat, positions)
            ids = np.flatnonzero(meters <= args.candidate_distance_m)
            if not len(ids):
                continue
            linked += 1
            candidates, seen = [], set()
            for i in ids[np.argsort(meters[ids])]:
                item = objects[int(i)]
                key = (item['relation'], item['source_id'])
                if key not in seen:
                    candidates.append({**item, 'spherical_distance_m': float(meters[i])})
                    seen.add(key)
            ambiguous += len(candidates) > 1
            result = {k: row.get(k) for k in ('chunk_id', 'source_id', 'source_sha256', 'content_sha256', 'source_locator', 'start', 'end', 'text')}
            result.update(status='PROXIMITY_CANDIDATE_ONLY', candidates=candidates,
                          coordinate_authority=False, object_identity_verified=False,
                          reason='Near source-inventory points; no name, referent, CRS or real-world identity adjudication.')
            out.write(json.dumps(result, ensure_ascii=False) + '\n')
    summary = dict(input_sha256=inputs, coordinate_pairs_total=total, eligible_syntax_pairs=eligible,
                   source_point_objects=len({(x['relation'], x['source_id']) for x in objects}),
                   source_point_parts=len(objects), pairs_with_candidates=linked, pairs_with_multiple_candidates=int(ambiguous),
                   candidate_distance_m=args.candidate_distance_m, approximate_distance_method='spherical_haversine_R6371008.8m',
                   coordinate_authority=False, verified_links=0, paper_experiment=False, holdout_used=False,
                   limitation='Unlabelled and invalid coordinates excluded. No nearby match does not prove absence. All matches require source referent/CRS/identity review.')
    summary['candidate_sha256'] = hashlib.sha256((args.output / 'candidates.jsonl').read_bytes()).hexdigest()
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}))


if __name__ == '__main__':
    main()
