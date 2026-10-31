"""Complete only missing source-text vectors with a pinned local model and ledger."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error

MODEL='bge-m3:latest'
DIGEST='7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab'
DIM=1024
ROOT=Path(__file__).resolve().parents[1]


def write(p,v):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)


class ModelHTTPError(RuntimeError):
    def __init__(self, code, body):
        self.code=code
        self.body_sha256=hashlib.sha256(body).hexdigest()
        # Classify known diagnostics without logging echoed input or credentials.
        message=body.decode('utf-8',errors='replace').lower()
        self.reason=next((tag for token,tag in (
            ('context length','CONTEXT_LIMIT'),('input length','INPUT_LIMIT'),
            ('out of memory','OUT_OF_MEMORY'),('nan','NONFINITE'),
            ('model not found','MODEL_NOT_FOUND')) if token in message),'UNCLASSIFIED')
        super().__init__(f'Model HTTP {code}; reason={self.reason}; body_sha256={self.body_sha256}')


def api(path,payload=None):
    base=os.getenv('OLLAMA_BASE_URL','http://host.docker.internal:11434').rstrip('/')
    req=urllib.request.Request(base+path,data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=600) as r:return json.load(r)
    except urllib.error.HTTPError as exc:
        raise ModelHTTPError(exc.code,exc.read()) from None


def embed_batch(rows,threads,output):
    payload={'model':MODEL,'input':[r[1] for r in rows],
             'truncate':False,'keep_alive':'30m','options':{'num_thread':threads}}
    for attempt in (1,2):
        try:return api('/api/embed',payload)
        except ModelHTTPError as exc:
            record={'observed_at':datetime.now(timezone.utc).isoformat(),'attempt':attempt,
                    'chunk_ids':[r[0] for r in rows],'input_sha256':[hashlib.sha256(r[1].encode()).hexdigest() for r in rows],
                    'http_status':exc.code,'reason':exc.reason,'response_body_sha256':exc.body_sha256,
                    'retry_same_input':attempt==1 and exc.code in (400,429,500,502,503,504)}
            with (output/'errors.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
            if not record['retry_same_input']:raise
            check_model()
            time.sleep(5)


def mark_failed(output,exc):
    for name in ('progress.json','manifest.json'):
        p=output/name
        if p.exists():
            state=json.loads(p.read_text(encoding='utf-8'))
            if state.get('status')=='FAILED':continue
            state.update(status='FAILED',failed_at=datetime.now(timezone.utc).isoformat(),error_type=type(exc).__name__)
            write(p,state)


def validate_vectors(vectors,n):
    if len(vectors)!=n:raise ValueError('Vector count mismatch')
    for v in vectors:
        if len(v)!=DIM or not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v) or not any(x!=0 for x in v):
            raise ValueError('Invalid embedding')


def check_model():
    row=next(r for r in api('/api/tags')['models'] if r['name']==MODEL)
    if row['digest']!=DIGEST:raise ValueError('Model digest changed')
    return row


def worker(output,batch_size,threads):
    import psycopg2
    from psycopg2.extras import Json
    output.mkdir(parents=True,exist_ok=True)
    model=check_model()
    with psycopg2.connect(os.environ['S101_DB_URL'],connect_timeout=10) as conn,conn.cursor() as cur:
        cur.execute('SELECT pg_try_advisory_lock(20261002001)')
        if not cur.fetchone()[0]:raise RuntimeError('Existing dataset embedding worker holds lock')
        cur.execute("SELECT chunk_id,source_sha256,md5(content) FROM knowledge.document_chunks WHERE document_type='dataset_source_text' AND embedding IS NULL ORDER BY chunk_id")
        pending=cur.fetchall()
        manifest_path=output/'manifest.json'
        if manifest_path.exists():
            old=json.loads(manifest_path.read_text(encoding='utf-8'))
            if old['model_digest']!=DIGEST:raise ValueError('Resume model mismatch')
            old.update(status='RUNNING',resumed_at=datetime.now(timezone.utc).isoformat(),remaining_pending=len(pending))
            write(manifest_path,old)
        else:
            write(output/'initial_pending.json',pending)
            write(manifest_path,{'status':'RUNNING','model':MODEL,'model_digest':DIGEST,'dimension':DIM,
                'initial_pending':len(pending),'batch_size':batch_size,'num_thread':threads,'truncate':False,
                'started_at':datetime.now(timezone.utc).isoformat(),'scope':'ONLY_NULL_EMBEDDING_DATASET_SOURCE_TEXT',
                'input_identity_sha256':hashlib.sha256(json.dumps(pending,ensure_ascii=False).encode()).hexdigest()})
        cur.execute("SELECT count(*),count(embedding) FROM knowledge.document_chunks WHERE document_type='dataset_source_text'")
        total,embedded=cur.fetchone()
        write(output/'progress.json',{'status':'RUNNING','total':total,'embedded':embedded,'pending':total-embedded,'completed_this_process':0})
        conn.commit();started=time.perf_counter();done=0
        with (output/'batches.jsonl').open('a',encoding='utf-8') as ledger:
            while True:
                cur.execute("SELECT chunk_id,content,source_sha256 FROM knowledge.document_chunks WHERE document_type='dataset_source_text' AND embedding IS NULL ORDER BY chunk_id LIMIT %s",(batch_size,))
                rows=cur.fetchall();conn.commit()
                if not rows:break
                before=time.perf_counter()
                result=embed_batch(rows,threads,output)
                vectors=result['embeddings'];validate_vectors(vectors,len(rows))
                check_model()
                for row,vector in zip(rows,vectors):
                    metadata={'embedding_model':MODEL,'embedding_model_digest':DIGEST,'embedding_dimension':DIM,
                        'embedding_status':'COMPLETED','embedding_input_sha256':hashlib.sha256(row[1].encode()).hexdigest(),
                        'embedding_truncate':False,'embedding_completed_at':datetime.now(timezone.utc).isoformat()}
                    cur.execute('''UPDATE knowledge.document_chunks SET embedding=%s::vector,metadata=metadata||%s::jsonb
                        WHERE chunk_id=%s AND source_sha256=%s AND content=%s AND embedding IS NULL''',
                        (json.dumps(vector),Json(metadata),row[0],row[2],row[1]))
                    if cur.rowcount!=1:raise RuntimeError('Source changed or vector concurrently written')
                conn.commit();done+=len(rows)
                record={'completed_at':datetime.now(timezone.utc).isoformat(),'chunk_ids':[r[0] for r in rows],
                    'elapsed_ms':(time.perf_counter()-before)*1000,'vectors_sha256':hashlib.sha256(json.dumps(vectors).encode()).hexdigest(),
                    'prompt_eval_count':result.get('prompt_eval_count'),'model_digest':DIGEST}
                ledger.write(json.dumps(record)+'\n');ledger.flush()
                cur.execute("SELECT count(*),count(embedding) FROM knowledge.document_chunks WHERE document_type='dataset_source_text'")
                total,embedded=cur.fetchone();conn.commit()
                progress={'status':'RUNNING','total':total,'embedded':embedded,'pending':total-embedded,
                    'completed_this_process':done,'elapsed_seconds':time.perf_counter()-started}
                write(output/'progress.json',progress);print(json.dumps(progress),flush=True)
            cur.execute('SELECT count(*),count(embedding),min(vector_dims(embedding)),max(vector_dims(embedding)) FROM knowledge.document_chunks')
            all_count,all_done,mind,maxd=cur.fetchone()
            final={'status':'COMPLETED' if all_count==all_done and mind==maxd==DIM else 'REMAINING_OTHER_SOURCES',
                'total':all_count,'embedded':all_done,'pending':all_count-all_done,'min_dim':mind,'max_dim':maxd,
                'model_digest_unchanged':check_model()['digest']==DIGEST,'finished_at':datetime.now(timezone.utc).isoformat()}
            write(output/'progress.json',final)
            manifest=json.loads(manifest_path.read_text(encoding='utf-8'));manifest.update(final);write(manifest_path,manifest)
            print(json.dumps(final),flush=True)


def launch(output,batch_size,threads):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    backend=json.loads(subprocess.check_output(['docker','inspect','geollm_backend']))[0]
    env=dict(v.split('=',1) for v in backend['Config']['Env'] if '=' in v)
    source=env['S101_DB_URL']
    net=next(iter(backend['NetworkSettings']['Networks']))
    cmd=['docker','run','--rm','--name','geollm-dataset-embedding-completion','--network',net,
        '--mount',f'type=bind,source={ROOT},target=/work,readonly','--mount',f'type=bind,source={output},target=/out',
        '--workdir','/work','--env','PYTHONDONTWRITEBYTECODE=1','--env','S101_DB_URL='+source,
        'docker-backend','python','-u','-m','scripts.complete_dataset_embeddings','--worker','--output','/out',
        '--batch-size',str(batch_size),'--threads',str(threads)]
    with (output/'worker.log').open('a',encoding='utf-8') as log:
        proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        for line in proc.stdout:
            safe=line.replace(source,'[REDACTED_DSN]');log.write(safe);log.flush();print(safe,end='',flush=True)
        code=proc.wait()
    if code:raise RuntimeError('Embedding worker failed; committed batches preserved')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true')
    p.add_argument('--batch-size',type=int,default=8);p.add_argument('--threads',type=int,default=12)
    a=p.parse_args()
    if not 1<=a.batch_size<=32 or not 1<=a.threads<=18:raise ValueError('Invalid bounded worker resources')
    try:
        (worker if a.worker else launch)(a.output,a.batch_size,a.threads)
    except Exception as exc:
        mark_failed(a.output,exc)
        raise
