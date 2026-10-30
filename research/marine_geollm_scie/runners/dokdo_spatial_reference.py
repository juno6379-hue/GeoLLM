"""User-fixed Q4 oracle: CSV IDs, WGS84 Vincenty independently checked by PostGIS.

Read-only DB query uses inline records; no table is created or mutated.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dms(text, latitude):
    normalized = text.translate(str.maketrans({'˚':'°','´':"'",'′':"'",'˝':'"','″':'"','‘':"'",'’':"'"}))
    match = re.fullmatch(r'''\s*(\d+(?:\.\d+)?)[-°](\d+(?:\.\d+)?)[-'](\d+(?:\.\d+)?)["']?([NSEW])\s*''', normalized)
    if not match:
        dm = re.fullmatch(r'''\s*(\d+(?:\.\d+)?)[-°](\d+(?:\.\d+)?)[-']([NSEW])\s*''', normalized)
        if not dm:raise ValueError('Unrecognized coordinate: ' + text)
        deg,minute = map(float,dm.groups()[:2]); second=0;direction=dm[3]
    else:
        deg, minute, second = map(float, match.groups()[:3]); direction = match[4]
    # Exactly 60 seconds carries to the next minute without changing the angle.
    if direction not in ('NS' if latitude else 'EW') or minute >= 60 or second > 60:
        raise ValueError('Invalid DMS component: ' + text)
    value = deg + minute / 60 + second / 3600
    if value > (90 if latitude else 180):
        raise ValueError('Coordinate out of bounds')
    return -value if direction in 'SW' else value


def coordinate_pair(first, second, latitude):
    values=[]; issues=[]
    for label,text in [('field1',first),('field2',second)]:
        try:values.append((label,dms(text,latitude)))
        except ValueError as exc:issues.append({'field':label,'raw':text,'reason':str(exc)})
    if not values:raise ValueError('Neither geographic coordinate field is parseable')
    if len(values)==2 and abs(values[0][1]-values[1][1])>1e-7:
        raise ValueError('Two geographic representations disagree')
    return values[0][1], {'selected_field':values[0][0],'raw_fields':[first,second],'parse_warnings':issues}


def vincenty(lat1, lon1, lat2, lon2):
    """Inverse geodesic on WGS84 ellipsoid; fail closed on nonconvergence."""
    a = 6378137.0; f = 1 / 298.257223563; b = (1-f)*a
    u1 = math.atan((1-f)*math.tan(math.radians(lat1)))
    u2 = math.atan((1-f)*math.tan(math.radians(lat2)))
    su1,cu1,su2,cu2 = math.sin(u1),math.cos(u1),math.sin(u2),math.cos(u2)
    l = math.radians(lon2-lon1); lam = l
    for _ in range(200):
        sl,cl = math.sin(lam),math.cos(lam)
        sinsigma = math.hypot(cu2*sl, cu1*su2-su1*cu2*cl)
        if sinsigma == 0:
            return 0.0
        cossigma = su1*su2+cu1*cu2*cl
        sigma = math.atan2(sinsigma,cossigma)
        sinalpha = cu1*cu2*sl/sinsigma
        cos2alpha = 1-sinalpha*sinalpha
        cos2sigmam = cossigma-2*su1*su2/cos2alpha if cos2alpha > 1e-15 else 0
        c = f/16*cos2alpha*(4+f*(4-3*cos2alpha))
        updated = l+(1-c)*f*sinalpha*(sigma+c*sinsigma*(cos2sigmam+c*cossigma*(-1+2*cos2sigmam*cos2sigmam)))
        if abs(updated-lam)<1e-12:
            break
        lam = updated
    else:
        raise ValueError('Vincenty failed to converge')
    u2term = cos2alpha*(a*a-b*b)/(b*b)
    aa = 1+u2term/16384*(4096+u2term*(-768+u2term*(320-175*u2term)))
    bb = u2term/1024*(256+u2term*(-128+u2term*(74-47*u2term)))
    delta = bb*sinsigma*(cos2sigmam+bb/4*(cossigma*(-1+2*cos2sigmam*cos2sigmam)-bb/6*cos2sigmam*(-3+4*sinsigma*sinsigma)*(-3+4*cos2sigmam*cos2sigmam)))
    return b*aa*(sigma-delta)


def run(root, output):
    source = root/'Dataset/해양수산부_공동활용체계_해양지명_20221231.csv'
    anchor_path = root/'data/public_place_anchors.json'
    anchor = next(p for p in json.loads(anchor_path.read_text(encoding='utf-8'))['places'] if p['place_id']=='mof:dokdo:east-island')
    with source.open(encoding='cp949', newline='') as f:
        raw = list(csv.DictReader(f))
    records = []; errors = []; seen = set()
    for line,r in enumerate(raw,2):
        try:
            source_id = r['공간정보일련번호'].strip()
            if not source_id or source_id in seen:raise ValueError('Missing/duplicate source ID')
            seen.add(source_id)
            lat,lat_trace = coordinate_pair(r['도분초위도1'],r['도분초위도2'],True)
            lon,lon_trace = coordinate_pair(r['도분초경도1'],r['도분초경도2'],False)
            distance = vincenty(anchor['latitude'],anchor['longitude'],lat,lon)
            records.append({'source_id':source_id,'object_id':'mof_marine_names_20221231:'+source_id,
                'name':r['지명명'],'latitude':lat,'longitude':lon,'csv_line':line,
                'distance_vincenty_m':distance,'within_5000m':distance<=5000,
                'coordinate_parse_trace':{'latitude':lat_trace,'longitude':lon_trace}})
        except ValueError as exc:
            errors.append({'csv_line':line,'source_id':r.get('공간정보일련번호'),'reason':str(exc)})
    output.mkdir(parents=True,exist_ok=False)
    # Full parse errors are retained; no incomplete source is promoted to a complete oracle.
    payload = json.dumps([{'id':r['source_id'],'lat':r['latitude'],'lon':r['longitude']} for r in records],ensure_ascii=True)
    if '$scie$' in payload:raise ValueError('Unsafe SQL delimiter')
    sql = f"""BEGIN READ ONLY;
SET LOCAL statement_timeout = '30000';
WITH pts AS (SELECT * FROM json_to_recordset($scie${payload}$scie$::json) AS x(id text,lat float8,lon float8)),
dist AS (SELECT id, ST_Distance(ST_SetSRID(ST_MakePoint(lon,lat),4326)::geography,
ST_SetSRID(ST_MakePoint({anchor['longitude']},{anchor['latitude']}),4326)::geography,true) AS distance_m FROM pts)
SELECT json_build_object('postgis_version',PostGIS_Full_Version(),'rows',(SELECT json_agg(dist ORDER BY id) FROM dist));
ROLLBACK;
"""
    (output/'reference_query.sql').write_text(sql,encoding='utf-8')
    response = subprocess.run(['docker','exec','-i','marine-scie-pilot-db','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-U','postgres','-d','scie_pilot'],input=sql,text=True,capture_output=True,timeout=45,check=True)
    measured = json.loads(response.stdout.strip())
    distances = {r['id']:r['distance_m'] for r in measured['rows']}
    if len(distances)!=len(records):raise ValueError('PostGIS result count mismatch')
    for r in records:
        r['distance_postgis_m'] = distances[r['source_id']]
        r['independent_distance_difference_m'] = abs(r['distance_postgis_m']-r['distance_vincenty_m'])
        r['membership_agrees'] = (r['distance_postgis_m']<=5000)==r['within_5000m']
    checks_ok = not errors and all(r['membership_agrees'] and r['independent_distance_difference_m']<=0.01 for r in records)
    selected = sorted((r for r in records if r['within_5000m']),key=lambda r:int(r['source_id']))
    snapshot = {'path':str(source),'sha256':digest(source),'row_count':len(raw)}
    result = {'status':'COMPUTED_VERIFIED_REFERENCE' if checks_ok else 'REFERENCE_INCOMPLETE',
        'case_ids':['PILOT_Q4_01','PILOT_Q4_02','PILOT_Q4_03'],
        'source_snapshot':snapshot,'snapshot_sha256':digest(source),
        'anchor_source_sha256':digest(anchor_path),'anchor':anchor,
        'reference_crs':'EPSG:4326','crs_policy':'Experiment interprets the two explicit geographic DMS fields as WGS84; unlabelled projected WKT is not used.',
        'radius_m':5000,'distance_policy':'WGS84 ellipsoidal geodesic, inclusive <=5000m',
        'coordinate_parse_policy':'DMS and decimal minutes; quote normalization; 60 seconds carries exactly. Prefer field1, fallback to parseable field2, require agreement when both parse. Never infer missing hemisphere.',
        'coordinate_warning_rows':sum(bool(r['coordinate_parse_trace']['latitude']['parse_warnings'] or r['coordinate_parse_trace']['longitude']['parse_warnings']) for r in records),
        'user_scope_approval':'동도 기준점·2022 CSV로 고정','independent_expert_review':False,
        'calculation_verification':'Vincenty inverse and PostGIS geography ST_Distance independently agree within 0.01m and on membership',
        'object_ids':[r['object_id'] for r in selected] if checks_ok else None,
        'source_object_ids':[r['source_id'] for r in selected] if checks_ok else None,
        'objects':selected,'parsed_rows':len(records),'parse_errors':errors,
        'max_distance_difference_m':max((r['independent_distance_difference_m'] for r in records),default=None),
        'boundary_nearest_margin_m':min((abs(r['distance_postgis_m']-5000) for r in records),default=None),
        'reference_query_sha256':digest(output/'reference_query.sql'),
        'reference_query':str(output/'reference_query.sql'),
        'postgis_version':measured['postgis_version'],'code_sha256':digest(Path(__file__)),
        'scope':'2022 CSV records with user-fixed east-island anchor. Not all real-world marine places, not S-101 feature IDs.',
        'gold_originals_modified':False}
    (output/'spatial_reference.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'all_distances.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','parsed_rows','parse_errors','source_object_ids','max_distance_difference_m','boundary_nearest_margin_m')},ensure_ascii=False))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run(args.root,args.output)
