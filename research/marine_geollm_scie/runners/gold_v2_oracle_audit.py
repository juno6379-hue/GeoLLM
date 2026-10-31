"""Independent read-only SQL/GIS preflight. Candidates never become GOLD silently."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely import wkb
from .dokdo_spatial_reference import vincenty
from .extract_fc_reference_candidates import catalogue, record

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT/'outputs/scie_model_snapshot_20261031_execution_v1/snapshot_manifest.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def psql(sql):
    result = subprocess.run(['docker', 'exec', '-i', 'marine-scie-pilot-db', 'psql',
        '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'scie_model_v3'],
        input=sql.encode('utf-8'), capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout


def instance_links(attributes, feature, source):
    """Bind observed instance fields only along actual FC attribute bindings.

    Flattened child fields are marked ambiguous, not silently attached to an
    invented complex parent. Every accepted field retains its actual value.
    """
    queue = [(feature, [])]; allowed = {}; seen = set()
    while queue:
        owner, prefix = queue.pop(0)
        if owner in seen:
            continue
        seen.add(owner)
        for binding in record(owner, *source)['bindings']:
            for ref in binding['references']:
                if ref['type'] == 'attribute':
                    code = ref['ref']; path = prefix + [code]
                    allowed.setdefault(code, []).append(path)
                    queue.append((code, path))
    linked = []; unresolved = []
    for code, value in attributes.items():
        paths = allowed.get(code, [])
        if [code] not in paths:
            unresolved.append({'attribute': code, 'value': value, 'candidate_paths': paths,
                'reason': 'FLATTENED_COMPLEX_PARENT_UNVERIFIED' if paths else 'NO_FEATURE_BINDING'})
            continue
        definition = record(code, *source)
        listed = {r['value']: r for r in definition['listed_values']}
        code_entry = listed.get(str(value)) if listed else None
        linked.append({'attribute': code, 'object_value': value, 'binding_path': [feature, code],
            'definition': definition['definition'], 'fc_locator': definition['locator'],
            'fc_sha256': definition['source_sha256'], 'fc_edition': definition['version'],
            'listed_value': code_entry, 'value_semantics_status':
                'CODE_RESOLVED' if code_entry else 'CODE_UNRESOLVED' if listed else 'RAW_VALUE_WITH_DEFINITION'})
    return {'linked': linked, 'unresolved': unresolved}


def run(out, boundary_id=None):
    out.mkdir(parents=True, exist_ok=False)
    snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    source_checks = []
    for relation in snapshot['relations']:
        name = relation['relation']
        if name not in {'projection.s101_feature_current', 'serving.navigation_aid_current'}:
            continue
        key = 'feature_instance_id' if name.startswith('projection.') else 'source_id'
        raw = psql(f'BEGIN READ ONLY; COPY (SELECT * FROM {name} ORDER BY {key}) TO STDOUT WITH CSV HEADER; ROLLBACK;')
        observed = hashlib.sha256(raw).hexdigest()
        source_checks.append({'relation': name, 'expected_sha256': relation['sha256'],
            'actual_sha256': observed, 'matches': observed == relation['sha256'], 'coverage': relation['coverage']})
    write(out/'source_checks.json', source_checks)
    if len(source_checks) != 2 or not all(r['matches'] for r in source_checks):
        raise ValueError('Research source differs from frozen snapshot')
    anchor_file = ROOT/'data/public_place_anchors.json'
    anchor = next(x for x in json.loads(anchor_file.read_text(encoding='utf-8'))['places']
                  if x['place_id'] == 'mof:dokdo:east-island')
    lon, lat = float(anchor['longitude']), float(anchor['latitude'])
    boundary_filter = (f'feature_instance_id={int(boundary_id)}' if boundary_id is not None
                       else "attributes->>'name'='부산항'")
    sql = f"""BEGIN READ ONLY;
SET LOCAL statement_timeout='60000';
WITH anchor AS (SELECT ST_SetSRID(ST_MakePoint({lon},{lat}),4326) g),
harbour AS MATERIALIZED (SELECT ST_UnaryUnion(ST_Collect(geometry)) g FROM projection.s101_feature_current
 WHERE feature_type_name='HarbourAreaAdministrative' AND {boundary_filter} AND ST_IsValid(geometry)),
features AS (SELECT p.feature_instance_id::text id,p.feature_type_name feature,p.attributes,
 p.dataset_id,p.dataset_version_id,p.dataset_name,p.min_scale,p.max_scale,p.product_specification,p.foid_fidn,
 encode(ST_AsEWKB(p.geometry),'hex') geometry_ewkb,
 ST_AsGeoJSON(p.geometry,15)::jsonb geometry,ST_IsValid(p.geometry) valid,ST_SRID(p.geometry) srid,
 md5(ST_AsEWKB(p.geometry)) geometry_md5,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name='Wreck' THEN ST_Distance(p.geometry::geography,a.g::geography,true) END dokdo_distance_m,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Covers(h.g,p.geometry) END harbour_covers,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Intersects(h.g,p.geometry) END harbour_intersects,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_DWithin(h.g::geography,p.geometry::geography,2000,true) END harbour_2km
 ,CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Distance(h.g::geography,p.geometry::geography,true) END harbour_distance_m
 FROM projection.s101_feature_current p CROSS JOIN anchor a CROSS JOIN harbour h
 WHERE p.feature_type_name IN ('HarbourAreaAdministrative','AnchorageArea','RestrictedArea','Wreck','LightAllAround','LightSectored','Landmark','Building')),
navigation AS (SELECT p.source_id id,p.aid_no,p.name,p.active,p.properties,p.provenance,
 ST_AsGeoJSON(p.geometry,15)::jsonb geometry,ST_IsValid(p.geometry) valid,
 ST_Distance(p.geometry::geography,a.g::geography,true) dokdo_distance_m
 FROM serving.navigation_aid_current p CROSS JOIN anchor a)
SELECT jsonb_build_object('postgis_version',PostGIS_Full_Version(),
 'features',(SELECT jsonb_agg(f ORDER BY id) FROM features f),
 'navigation',(SELECT jsonb_agg(n ORDER BY id) FROM navigation n));
ROLLBACK;
"""
    (out/'independent_queries.sql').write_text(sql, encoding='utf-8')
    data = json.loads(psql(sql))
    write(out/'source_observations.json', data)
    nav = [r for r in data['navigation'] if r['active'] is True and '등대' in r['name'] and r['valid']]
    for row in nav:
        x,y = row['geometry']['coordinates']
        row['independent_vincenty_m'] = vincenty(lat,lon,y,x)
        row['difference_m'] = abs(row['independent_vincenty_m']-row['dokdo_distance_m'])
    nav.sort(key=lambda r:(r['dokdo_distance_m'],r['id']))
    write(out/'lighthouse_candidates.json', nav)
    harbour_rows = [r for r in data['features'] if r['feature']=='HarbourAreaAdministrative'
                    and r['attributes'].get('name')=='부산항' and r['valid']
                    and (boundary_id is None or r['id']==str(boundary_id))]
    if not harbour_rows or (boundary_id is not None and len(harbour_rows)!=1):
        raise ValueError('Boundary must resolve to one valid named harbour polygon')
    harbour = unary_union([wkb.loads(bytes.fromhex(r['geometry_ewkb'])) for r in harbour_rows])
    polygon_checks = []; sets = {}
    for feature in ('AnchorageArea','RestrictedArea'):
        rows = [r for r in data['features'] if r['feature']==feature and r['valid']]
        for r in rows:
            g = wkb.loads(bytes.fromhex(r['geometry_ewkb']))
            polygon_checks.append({'id':r['id'], 'feature':feature,
                'covers_agrees': harbour.covers(g)==r['harbour_covers'],
                'intersects_agrees': harbour.intersects(g)==r['harbour_intersects'],
                'dwithin_distance_agrees':(r['harbour_distance_m']<=2000)==r['harbour_2km']})
        sets[feature] = {kind: [r['id'] for r in rows if r[kind]]
                        for kind in ('harbour_covers','harbour_intersects','harbour_2km')}
    write(out/'harbour_candidate_sets.json', {'harbour_ids':[r['id'] for r in harbour_rows],
        'policy':'Explicit single snapshot polygon; no legal completeness assertion' if boundary_id is not None else 'PROVISIONAL union of all exact-name harbour features; not approved legal boundary',
        'boundary_records':harbour_rows,
        'sets':sets,'independent_shapely_checks':polygon_checks})
    fc = catalogue()
    wrecks = [r for r in data['features'] if r['feature']=='Wreck']
    links = [{'object_id':r['id'], 'object_attributes':r['attributes'],
              **instance_links(r['attributes'],'Wreck',fc)} for r in wrecks]
    write(out/'wreck_instance_fc_links.json', {'fc_sha256':fc[2], 'rows':links,
        'scope':'All snapshot Wrecks for linkage diagnostics; not substituted for Dokdo objects'})
    selected_wrecks = [r['id'] for r in wrecks if r['valid'] and r['dokdo_distance_m'] <= 5000]
    summary = {'status':'ORACLE_SCOPE_REVIEW_REQUIRED', 'model_comparison_started':False,
        'snapshot_manifest_sha256':sha(SNAPSHOT), 'source_checks':source_checks,
        'anchor':anchor,'anchor_file_sha256':sha(anchor_file),'code_sha256':sha(__file__),
        'feature_counts':dict(Counter(r['feature'] for r in data['features'])),
        'lighthouse_candidate_count':len(nav),'nearest_snapshot_candidate':nav[0] if nav else None,
        'maximum_point_distance_disagreement_m':max((r['difference_m'] for r in nav),default=None),
        'duplicate_aid_numbers':{k:v for k,v in Counter(r['aid_no'] for r in nav).items() if v>1},
        'dokdo_5km_snapshot_wreck_ids':selected_wrecks,
        'dokdo_5km_snapshot_lighthouse_ids':[r['id'] for r in nav if r['dokdo_distance_m']<=5000],
        'empty_set_is_real_world_gold':False,
        'harbour_polygon_checks_agree':all(r['covers_agrees'] and r['intersects_agrees'] and r['dwithin_distance_agrees'] for r in polygon_checks),
        'canonical_boundary_id':boundary_id,
        'harbour_candidate_counts':{f:{k:len(v) for k,v in sets[f].items()} for f in sets},
        'instance_fc_link_count':sum(len(r['linked']) for r in links),
        'instance_fc_unresolved_count':sum(len(r['unresolved']) for r in links),
        'q5_03_linkage_evaluation_ready':bool(selected_wrecks),
        'blockers':['SOURCE_SCOPE_NOT_FIXED','FACILITY_DEDUP_POLICY_NOT_FIXED',
                    'BUSAN_BOUNDARY_AND_2KM_REFERENCE_NOT_APPROVED','EIGHT_METHOD_IMPLEMENTATIONS_NOT_MATCHED'],
        'independent_human_gold':False}
    write(out/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ('status','lighthouse_candidate_count',
        'maximum_point_distance_disagreement_m','harbour_candidate_counts','instance_fc_link_count',
        'instance_fc_unresolved_count','q5_03_linkage_evaluation_ready')},ensure_ascii=True))
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--boundary-id',type=int)
    args=parser.parse_args();run(args.output,args.boundary_id)
