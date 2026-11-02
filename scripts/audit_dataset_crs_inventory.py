"""Inventory explicit CRS sidecars in Dataset; never infer missing CRS."""
from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import json,zipfile
from pathlib import Path
from scripts.dataset_spatial_pipeline import strict_srid
ROOT=Path(__file__).resolve().parents[1]
def run(output=None):
 target=refuse_existing(Path(output or ROOT/'outputs/dataset_location_audit_20261102/spatial')/'crs_inventory_v2.json')
 rows=[]
 for p in (ROOT/'Dataset').rglob('*.zip'):
  try:
   with zipfile.ZipFile(p) as z:
    lookup={n.lower():n for n in z.namelist()}
    for name in z.namelist():
     if not name.lower().endswith('.shp'):continue
     row={'file':p.relative_to(ROOT).as_posix(),'member':name}
     prj=lookup.get((name[:-4]+'.prj').lower())
     if not prj:row['status']='MISSING_PRJ'
     else:
      try:row.update(status='STRICT_RECOGNIZED',source_srid=strict_srid(z.read(prj).decode('utf-8-sig')))
      except (ValueError,UnicodeError) as e:row.update(status='UNRECOGNIZED',error=type(e).__name__)
     rows.append(row)
  except zipfile.BadZipFile:rows.append({'file':p.relative_to(ROOT).as_posix(),'status':'NOT_READABLE_ZIP'})
 for p in (ROOT/'Dataset').rglob('*.shp'):
  row={'file':p.relative_to(ROOT).as_posix()};prj=p.with_suffix('.prj')
  if not prj.exists():row['status']='MISSING_PRJ'
  else:
   try:row.update(status='STRICT_RECOGNIZED',source_srid=strict_srid(prj.read_text(encoding='utf-8-sig')))
   except (ValueError,UnicodeError) as e:row.update(status='UNRECOGNIZED',error=type(e).__name__)
  rows.append(row)
 target.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(len(rows),{status:sum(r['status']==status for r in rows) for status in {r['status'] for r in rows}})
if __name__=='__main__':run(output_argument())
