"""Read-only current operational aggregate export; never access a research DB."""
from __future__ import annotations
import json, os, hashlib
from pathlib import Path

def export(out):
    import psycopg2
    from psycopg2.extensions import parse_dsn, make_dsn
    from scripts import build_s101_catalogue_db_rag as builder
    out.mkdir(parents=True,exist_ok=True)
    for name in ['gbhd_s101','S100_dev']:
        target=out/(name+'_current.json')
        if target.exists():raise RuntimeError('Refuse overwrite')
        dsn=parse_dsn(os.environ['S101_DB_URL']);dsn['dbname']=name
        def readonly(url):
            conn=psycopg2.connect(url)
            conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout='120s'")
                cur.execute('select current_database()')
                if cur.fetchone()[0]!=name:raise RuntimeError('database identity mismatch')
            return conn
        builder.connect=readonly
        try:
            rows=builder.fetch_db_chunks(make_dsn(**dsn))
            result=dict(database=name,read_only=True,rows=rows)
        except Exception as exc:result=dict(database=name,read_only=True,error_type=type(exc).__name__,error=str(exc).splitlines()[0])
        target.write_text(json.dumps(result,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
        print(json.dumps(dict(database=name,rows=len(result.get('rows',[])),error_type=result.get('error_type'),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))

if __name__=='__main__':
    export(Path('/app/outputs/dataset_unverified_followup_20261102/locator/db'))
