"""Actual local embeddings + frozen DB retrieval; no GOLD input or answer generation."""
import argparse
import json
import math
from pathlib import Path
import time
import urllib.request
from research.marine_geollm_scie.runners.binding_snapshot import ROOT, TARGET_DATABASE, digest, psql, verify_files, write


def call(path,payload=None):
    data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    req=urllib.request.Request('http://127.0.0.1:11434'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)


def run(snapshot,output):
    if output.exists():raise FileExistsError(output)
    m=json.loads(snapshot.read_text(encoding='utf-8'))
    if m['status']!='LOADED_VERIFIED' or m['db_identity']['database']!=TARGET_DATABASE:raise ValueError('Research DB required')
    verify_files(m,snapshot.parent)
    benchmark=ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl'
    cases=[r for r in map(json.loads,benchmark.read_text(encoding='utf-8').splitlines()) if r['case_id'].split('_')[1] in {'Q1','Q2','Q6'}]
    if len(cases)!=9:raise ValueError('Nine original document queries required')
    model=next(r for r in call('/api/tags')['models'] if r['name']=='bge-m3:latest')
    output.mkdir(parents=True)
    rows=[]
    with (output/'retrieval_rows.jsonl').open('x',encoding='utf-8') as stream:
        for case in cases:
            row={'case_id':case['case_id'],'query':case['query'],'model':model['name'],'model_digest':model['digest'],
                 'semantic_correct':None,'evidence_correct':None,'gold_used':False,'answer_generated':False,
                 'stored_embedding_model_profile_verified':False}
            start=time.perf_counter()
            try:
                vectors=call('/api/embed',{'model':model['name'],'input':[case['query']]})
                vector=vectors['embeddings'][0]
                if len(vector)!=1024 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vector):raise ValueError('Invalid embedding')
                write(output/(case['case_id']+'.embedding.json'),vectors)
                row['embedding_sha256']=digest(output/(case['case_id']+'.embedding.json'))
                vector_literal=json.dumps(vector,separators=(',',':'))
                sql="""BEGIN TRANSACTION READ ONLY; SET LOCAL statement_timeout='60s';
SELECT coalesce(json_agg(t),'[]'::json) FROM (
SELECT chunk_id,source_id,source_sha256,metadata,content,1-(embedding <=> '"""+vector_literal+"""'::vector) AS similarity
FROM knowledge.document_chunks WHERE embedding IS NOT NULL
AND metadata @> '{"product_id":"S-101","version":"2.0.0","product_specification":"INT.IHO.S-101.2.0"}'::jsonb
ORDER BY embedding <=> '"""+vector_literal+"""'::vector,chunk_id LIMIT 3) t;
ROLLBACK;"""
                (output/(case['case_id']+'.sql')).write_text(sql,encoding='utf-8')
                row['results']=json.loads(psql(sql,TARGET_DATABASE))
                row['status']='RETRIEVAL_COMPLETED';row['result_count']=len(row['results'])
            except Exception as e:
                row.update(status='PROBE_ERROR',error_type=type(e).__name__)
            row['elapsed_ms']=(time.perf_counter()-start)*1000
            rows.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            print(case['case_id'],row['status'],row.get('result_count'),flush=True)
    model_after=next(r for r in call('/api/tags')['models'] if r['name']==model['name'])
    write(output/'manifest.json',{'scope':'ACTUAL_EMBEDDING_RETRIEVAL_COMPONENT_NOT_FULL_GRAPH',
        'snapshot_sha256':digest(snapshot),'benchmark_sha256':digest(benchmark),'rows_sha256':digest(output/'retrieval_rows.jsonl'),
        'model':model,'model_digest_unchanged':model_after['digest']==model['digest'],'rows':len(rows),
        'completed':sum(r['status']=='RETRIEVAL_COMPLETED' for r in rows),'model_generation_calls':0,
        'embedding_calls':len(rows),'gold_used':False,'production_database_writes':False,
        'stored_embedding_model_profile_verified':False,'evidence_correct':None})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.snapshot,a.output)
