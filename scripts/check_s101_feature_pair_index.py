"""Verify operational name/code lookup before/after an optional covering index."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import psycopg2
import yaml

ROOT=Path(__file__).resolve().parents[1]
QUERY='SELECT DISTINCT feature_type_name, feature_type_code FROM projection.s101_feature_current WHERE feature_type_name = ANY(%s) AND feature_type_code = ANY(%s)'
DDL='CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_s101_feature_current_type_pair ON projection.s101_feature_current (feature_type_name, feature_type_code)'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    profile=yaml.safe_load((ROOT/'data/derived_concept_registry_v2.yaml').read_text(encoding='utf-8'))['derived_concepts']['navigation_hazard_object']['execution_profiles']['s101_hazard_radius']
    targets=profile['target_features'];codes=sorted({int(c) for values in profile['feature_code_map'].values() for c in (values if isinstance(values,list) else [values])})
    report={'source_rows_modified':False,'research_db_modified':False,'query':QUERY,'targets':targets,'codes':codes,'apply_requested':args.apply}
    conn=psycopg2.connect(os.environ['S101_DB_URL'],connect_timeout=3)
    try:
        conn.set_session(readonly=True)
        with conn.cursor() as cursor:
            cursor.execute('SELECT current_database(), current_user')
            database,user=cursor.fetchone();report['database']=database;report['db_role']=user
            if database.startswith('scie_'):raise RuntimeError('Refuse research database mutation')
            cursor.execute("SELECT c.relkind FROM pg_class c WHERE c.oid='projection.s101_feature_current'::regclass")
            if cursor.fetchone()[0]!='m':raise RuntimeError('Expected operational materialized view')
            cursor.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='projection' AND tablename='s101_feature_current'")
            report['indexes_before']=[{'name':n,'definition':d} for n,d in cursor.fetchall()]
        conn.rollback()
        def probe(label):
            with conn.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout='30000ms'")
                started=time.perf_counter();cursor.execute(QUERY,(targets,codes));pairs=sorted(cursor.fetchall())
                elapsed=time.perf_counter()-started
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+QUERY,(targets,codes))
                plan=cursor.fetchone()[0]
                result={'pairs':pairs,'pair_count':len(pairs),'pairs_sha256':hashlib.sha256(json.dumps(pairs).encode()).hexdigest(),'elapsed_seconds':elapsed,'explain':plan}
                report[label]=result
            conn.rollback();return result
        before=probe('before')
        if args.apply:
            conn.set_session(readonly=False,autocommit=True)
            with conn.cursor() as cursor:
                cursor.execute("SET lock_timeout='5s'")
                cursor.execute(DDL)
            report['index_created_by_run']=not any(x['name']=='idx_s101_feature_current_type_pair' for x in report['indexes_before'])
            conn.set_session(readonly=True,autocommit=False)
        after=probe('after')
        with conn.cursor() as cursor:
            cursor.execute("SELECT i.indisvalid,i.indisready,pg_get_indexdef(i.indexrelid) FROM pg_index i WHERE i.indexrelid=to_regclass('projection.idx_s101_feature_current_type_pair')")
            report['index_after']=cursor.fetchone()
        report['pair_sets_identical']=before['pairs_sha256']==after['pairs_sha256']
        if not report['pair_sets_identical']:raise RuntimeError('Pair results changed')
        report['status']='VERIFIED'
    except Exception as exc:
        report.update(status='FAILED',error_type=type(exc).__name__,sqlstate=getattr(exc,'pgcode',None))
        raise
    finally:
        conn.close()
        (args.output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','database','pair_sets_identical','index_after')},ensure_ascii=True))


if __name__=='__main__':main()
