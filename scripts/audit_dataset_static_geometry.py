"""Independent raw SHP -> pyproj -> WKB audit of every staged static record."""
from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import argparse,csv,gzip,hashlib,io,itertools,json,logging,time,zipfile
import numpy as np
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import pyproj,shapefile,shapely
from shapely.geometry import shape
from scripts.dataset_spatial_pipeline import strict_srid
ROOT=Path(__file__).resolve().parents[1]

def resolve_archive_member(member, names):
 lookup={n.lower():n for n in names}
 if member.lower() in lookup:return lookup[member.lower()]
 recovered=member.encode('cp437').decode('cp949')
 if recovered.lower() not in lookup:raise ValueError('Unresolved archive member; no basename guessing')
 return lookup[recovered.lower()]

def compare_geometry(expected, observed, tolerance=1e-8):
 a=shapely.get_coordinates(expected);b=shapely.get_coordinates(observed)
 delta=float(np.max(np.abs(a-b))) if a.shape==b.shape and a.size else (0.0 if a.shape==b.shape else float('inf'))
 return bool(delta<=tolerance and shapely.equals_exact(expected,observed,tolerance=tolerance)),delta

def run(output):
 out=Path(output);refuse_existing(out/'static_source_reconciliation_v2.json');refuse_existing(out/'static_geometry_mismatches_v2.jsonl');csv.field_size_limit(100000000)
 stream=gzip.open(out/'static_geometry_wkb.csv.gz','rt',encoding='utf8',newline='')
 groups=itertools.groupby(csv.DictReader(stream),key=lambda r:(r['source_sha256'],r['source_file'],r['source_member']))
 result={'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat(),'pyproj':pyproj.__version__,'proj':pyproj.proj_version_str,'shapely':shapely.__version__,'geometry_policy':'strict source CRS, always_xy, transform 4326, force2D; no MakeValid/repair/dedup','sources':[]}
 logging.getLogger('shapefile').setLevel(logging.ERROR)
 def save():
  result['updated_at']=datetime.now(timezone.utc).isoformat();(out/'static_source_reconciliation_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 save()
 with (out/'static_geometry_mismatches_v2.jsonl').open('w',encoding='utf8') as errors:
  for (h,file,member),dbrows in groups:
   dbrows=list(dbrows)
   started=time.monotonic();p=ROOT/file;digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();report={'source_sha256':h,'source_file':file,'member':member,'db_rows':len(dbrows),'source_hash_match':digest==h,'compared':0,'exact_wkb_matches':0,'tolerance_matches':0,'mismatches':0,'null_matches':0,'max_coordinate_delta_degrees':0.0,'excluded_static':sum(r['geometry_valid']=='f' for r in dbrows)}
   if digest!=h:raise ValueError('Source hash mismatch')
   with zipfile.ZipFile(p) as z:
    lookup={n.lower():n for n in z.namelist()};resolved=resolve_archive_member(member,z.namelist())
    if resolved!=member:
     report['member_encoding_resolution']={'stored':member,'archive':resolved,'method':'reversible_cp437_bytes_to_cp949'}
    stem=resolved[:-4];read=lambda ext:z.read(lookup[(stem+ext).lower()])
    srid=strict_srid(read('.prj').decode('utf-8-sig'));report['source_srid']=srid
    reader=shapefile.Reader(shp=io.BytesIO(read('.shp')),shx=io.BytesIO(read('.shx')))
    report['source_rows']=len(reader);transformer=pyproj.Transformer.from_crs(srid,4326,always_xy=True)
    for i,s in enumerate(reader.iterShapes()):
     db=dbrows[i];assert int(db['row_index'])==i
     sid='dataset_record:'+hashlib.sha256(f'{h}:{member}:{i}'.encode()).hexdigest();assert sid==db['source_id']
     if s.shapeType:
      g=shape(s.__geo_interface__);g=shapely.transform(g,transformer.transform,interleaved=False);g=shapely.force_2d(g);wkb=shapely.to_wkb(g,byte_order=1,output_dimension=2)
      actual=wkb.hex()
     else:actual=''
     report['compared']+=1
     if actual==db['wkb']:
      report['exact_wkb_matches']+=1
      if not actual:report['null_matches']+=1
     else:
      observed=shapely.from_wkb(bytes.fromhex(db['wkb']));matches,delta=compare_geometry(g,observed)
      report['max_coordinate_delta_degrees']=max(report['max_coordinate_delta_degrees'],delta)
      if matches:
       report['tolerance_matches']+=1
      else:
       report['mismatches']+=1;errors.write(json.dumps({'source_id':sid,'source_sha256':h,'member':member,'row_index':i,'max_coordinate_delta_degrees':delta,'geometry_valid':db['geometry_valid']},ensure_ascii=False)+'\n')
    assert report['source_rows']==report['db_rows']
   report['elapsed_seconds']=round(time.monotonic()-started,3);result['sources'].append(report);save();print(json.dumps(report,ensure_ascii=True),flush=True)
 result['status']='COMPLETED';result['counts']={k:sum(r[k] for r in result['sources']) for k in ('source_rows','db_rows','compared','exact_wkb_matches','tolerance_matches','mismatches','null_matches','excluded_static')};save();stream.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'outputs/dataset_location_audit_20261102/spatial'));run(p.parse_args().output)
