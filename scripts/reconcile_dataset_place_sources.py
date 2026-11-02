"""Reconcile operational point/place tables against raw Dataset files, without mutation."""
from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import csv,hashlib,io,json,zipfile
from pathlib import Path
import shapefile
from scripts.ingest_requested_dataset_layers import source_id,parse_navigation_aid_location
from scripts.dataset_spatial_pipeline import strict_srid
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/dataset_location_audit_20261102/spatial'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(output=None):
    global OUT
    OUT=Path(output or OUT)
    refuse_existing(OUT/'source_reconciliation.json')
    refuse_existing(OUT/'expected_geometry.json')
    expected=[];results={}
    for table in ('small_harbour_guide','marine_gazetteer_current','navigation_aid_current','island_gazetteer_current'):
        live=json.loads((OUT/(table+'.json')).read_text(encoding='utf-8')); byid={r['source_id']:r for r in live}; source=[]
        if table=='small_harbour_guide':
            p=ROOT/'Dataset/소형선항만 안내정보/TB_SAILER.shp'; hashes={p.with_suffix(x).name:sha(p.with_suffix(x)) for x in ('.shp','.shx','.dbf','.prj','.cpg')}; h=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
            reader=shapefile.Reader(str(p),encoding='utf-8',encodingErrors='replace'); srid=strict_srid(p.with_suffix('.prj').read_text())
            for i,r in enumerate(reader.iterShapeRecords()):source.append((f'small_harbour:{h}:{i}',r.record.as_dict(),r.shape.__geo_interface__,srid,h,i))
        elif table=='island_gazetteer_current':
            p=ROOT/'Dataset/도서지명.zip';h=sha(p)
            with zipfile.ZipFile(p) as z:
                lookup={n.lower():n for n in z.namelist()}
                for member in z.namelist():
                    if not member.lower().endswith('.shp'):continue
                    stem=member[:-4];read=lambda ext:z.read(lookup[(stem+ext).lower()]);srid=strict_srid(read('.prj').decode('utf-8-sig'))
                    cpg=read('.cpg').decode().strip().lower() if (stem+'.cpg').lower() in lookup else 'cp949';encoding={'utf_8':'utf-8','949':'cp949'}.get(cpg,cpg)
                    reader=shapefile.Reader(shp=io.BytesIO(read('.shp')),shx=io.BytesIO(read('.shx')),dbf=io.BytesIO(read('.dbf')),encoding=encoding,encodingErrors='replace')
                    for i,r in enumerate(reader.iterShapeRecords()):
                        props=r.record.as_dict();natural=props.get('OBJECTID') or props.get('OBJ_SN') or i+1
                        sid=hashlib.sha256(f'island_gazetteer|Dataset/도서지명.zip|{member}|{natural}|{i+1}'.encode()).hexdigest()[:24]
                        source.append((sid,props,r.shape.__geo_interface__,srid,h,i))
        else:
            name='해양수산부_공동활용체계_해양지명_20221231.csv' if table=='marine_gazetteer_current' else '해양수산부 부산지방해양수산청_항로표지정보_20250623.csv';p=ROOT/'Dataset'/name;h=sha(p)
            with p.open(encoding='cp949',newline='') as f:
                for i,r in enumerate(csv.DictReader(f)):
                    if table=='marine_gazetteer_current':sid=source_id('marine_gazetteer_mof',r.get('공간정보일련번호'),r.get('지명명'));g=r['공간정보'];srid=5179
                    else:sid=source_id('navigation_aid_busan',r.get('순번'),r.get('이름'),r.get('위치'));g={'type':'Point','coordinates':parse_navigation_aid_location(r['위치'])};srid=4326
                    source.append((sid,r,g,srid,h,i))
        bad=[]
        for sid,props,g,srid,h,idx in source:
            db=byid.get(sid)
            if not db:bad.append({'source_id':sid,'reason':'MISSING_IN_DB'});continue
            if props!=db['properties'] or h!=db['provenance']['source_sha256']:bad.append({'source_id':sid,'reason':'PROPERTY_OR_HASH_MISMATCH'})
            expected.append({'table':table,'source_id':sid,'source_row_index':idx,'geometry':g,'srid':srid,'source_sha256':h})
        results[table]={'source_rows':len(source),'db_rows':len(live),'issues':bad,'db_without_source':sorted(set(byid)-{r[0] for r in source}),'source_path':p.relative_to(ROOT).as_posix(),'sha256':h}
    (OUT/'source_reconciliation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'expected_geometry.json').write_text(json.dumps(expected,ensure_ascii=False),encoding='utf-8');print(json.dumps({k:{'source_rows':v['source_rows'],'issues':len(v['issues']),'db_without_source':len(v['db_without_source'])} for k,v in results.items()}))
if __name__=='__main__':main(output_argument())
