"""Stream raw CSV header/value/row locator reconciliation against read-only DB hashes."""
from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import csv,gzip,hashlib,itertools,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/dataset_location_audit_20261102/spatial'
def jsonb_array_hash(values):
    return hashlib.md5(json.dumps(values,ensure_ascii=False,separators=(', ', ': ')).encode('utf8')).hexdigest()
def run(output=None):
    global OUT
    OUT=Path(output or OUT)
    refuse_existing(OUT/'csv_source_reconciliation.json')
    refuse_existing(OUT/'csv_source_mismatches.jsonl')
    csv.field_size_limit(10000000);result={'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat(),'geometry_status':'NOT_INFERRED_NOT_APPLICABLE','hash_algorithm':'MD5 of PostgreSQL JSONB array text; source file SHA256; stable ID SHA256','sources':[]}
    def save():
        result['updated_at']=datetime.now(timezone.utc).isoformat();(OUT/'csv_source_reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    save()
    with gzip.open(OUT/'csv_row_hashes.csv.gz','rt',encoding='utf8',newline='') as dbstream,(OUT/'csv_source_mismatches.jsonl').open('w',encoding='utf8') as mismatches:
        for h,dbgroup in itertools.groupby(csv.DictReader(dbstream),key=lambda r:r['source_sha256']):
            first=next(dbgroup);file=first['source_file'];path=ROOT/file
            with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            report={'source_sha256':h,'source_file':file,'encoding':first['encoding'],'source_hash_match':actual==h,'source_rows':0,'db_rows':0,'matched':0,'mismatches':0,'non_null_geometry':0};assert actual==h
            with path.open(encoding=first['encoding'],newline='') as f:
                reader=csv.reader(f);header=next(reader);hh=jsonb_array_hash(header)
                for i,(source,db) in enumerate(itertools.zip_longest(reader,itertools.chain([first],dbgroup))):
                    report['source_rows']+=source is not None;report['db_rows']+=db is not None
                    checks={'row_exists_both':source is not None and db is not None}
                    if all(checks.values()):
                        checks.update(header=hh==db['header_hash'],values=jsonb_array_hash(source)==db['values_hash'],row_index=int(db['row_index'])==i,row_number=int(db['row_number'])==i+2,source_id=db['source_id']=='dataset_csv:'+hashlib.sha256(f'{h}:{i}'.encode()).hexdigest(),no_geometry=db['no_geometry']=='t')
                        report['non_null_geometry']+=db['no_geometry']!='t'
                    if all(checks.values()):report['matched']+=1
                    else:report['mismatches']+=1;mismatches.write(json.dumps({'source_sha256':h,'row_index':i,'checks':checks})+'\n')
            result['sources'].append(report);save();print(json.dumps(report,ensure_ascii=True),flush=True)
    result['status']='COMPLETED';result['counts']={k:sum(r[k] for r in result['sources']) for k in ('source_rows','db_rows','matched','mismatches','non_null_geometry')};save()
if __name__=='__main__':run(output_argument())
