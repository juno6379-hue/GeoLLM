"""Compare every staged static DBF attribute dictionary with raw ZIP DBF records."""
import csv,gzip,hashlib,io,itertools,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
import shapefile
from scripts.audit_dataset_static_geometry import resolve_archive_member
from scripts.dataset_spatial_audit_io import output_argument,refuse_existing
ROOT=Path(__file__).resolve().parents[1]
def run(out):
    out=Path(out);report_path=refuse_existing(out/'static_attribute_reconciliation.json');mismatch_path=refuse_existing(out/'static_attribute_mismatches.jsonl');csv.field_size_limit(10000000)
    result={'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat(),'sources':[]}
    def save():
        result['updated_at']=datetime.now(timezone.utc).isoformat();report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    save()
    with gzip.open(out/'static_properties.csv.gz','rt',encoding='utf8',newline='') as dbstream,mismatch_path.open('w',encoding='utf8') as failures:
        key=lambda r:(r['source_sha256'],r['source_file'],r['source_member'])
        for (h,file,member),group in itertools.groupby(csv.DictReader(dbstream),key=key):
            first=next(group);p=ROOT/file
            with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            assert actual==h;report={'source_sha256':h,'source_file':file,'member':member,'encoding':first['encoding'],'source_hash_match':True,'source_rows':0,'db_rows':0,'matched':0,'mismatches':0}
            with zipfile.ZipFile(p) as z:
                resolved=resolve_archive_member(member,z.namelist());lookup={n.lower():n for n in z.namelist()};raw=z.read(lookup[(resolved[:-4]+'.dbf').lower()]);reader=shapefile.Reader(dbf=io.BytesIO(raw),encoding=first['encoding'],encodingErrors='strict')
                for i,(source,db) in enumerate(itertools.zip_longest(reader.iterRecords(),itertools.chain([first],group))):
                    report['source_rows']+=source is not None;report['db_rows']+=db is not None;checks={'row_exists_both':source is not None and db is not None}
                    if all(checks.values()):checks.update(properties=source.as_dict()==json.loads(db['properties']),row_index=int(db['row_index'])==i,source_id=db['source_id']=='dataset_record:'+hashlib.sha256(f'{h}:{member}:{i}'.encode()).hexdigest())
                    if all(checks.values()):report['matched']+=1
                    else:report['mismatches']+=1;failures.write(json.dumps({'source_sha256':h,'member':member,'row_index':i,'checks':checks},ensure_ascii=False)+'\n')
            result['sources'].append(report);save();print(json.dumps(report,ensure_ascii=True),flush=True)
    result['status']='COMPLETED';result['counts']={k:sum(r[k] for r in result['sources']) for k in ('source_rows','db_rows','matched','mismatches')};save()
if __name__=='__main__':run(output_argument())
