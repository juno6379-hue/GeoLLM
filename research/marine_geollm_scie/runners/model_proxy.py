"""연구 graph 전용 Ollama allowlist proxy. 운영 소스/DB를 읽지 않는다."""
import argparse
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import select
import socket
import time
import urllib.request
import urllib.error
import uuid
from urllib.parse import urlsplit

MODELS = {'qwen2.5:1.5b', 'bge-m3:latest'}
POST_PATHS = {'/api/chat','/api/generate','/api/embed','/api/embeddings','/api/show','/v1/chat/completions','/v1/embeddings'}
GET_PATHS = {'/api/tags','/api/ps','/api/version'}

def canonical_model(name):
    return 'bge-m3:latest' if name == 'bge-m3' else name

def validate_digests(tags, expected):
    actual={canonical_model(x['name']):x['digest'] for x in tags.get('models',[])}
    if any(actual.get(k)!=v for k,v in expected.items()):
        raise ValueError('Pinned model digest changed or missing')

def validate_request(method, path, payload, digests):
    if path not in (GET_PATHS if method == 'GET' else POST_PATHS):
        raise ValueError('Endpoint is not allowlisted')
    if method == 'POST':
        model = canonical_model(payload.get('model', ''))
        if model not in MODELS or model not in digests:
            raise ValueError('Model is not allowlisted and pinned')
        embedding_path = path in {'/api/embed','/api/embeddings','/v1/embeddings'}
        if path != '/api/show' and ((embedding_path and model != 'bge-m3:latest') or (not embedding_path and model != 'qwen2.5:1.5b')):
            raise ValueError('Model role mismatch')

def clean(value):
    if isinstance(value,dict):
        return {k:clean(v) for k,v in value.items() if k.lower() not in {'thinking','reasoning_content','chain_of_thought','authorization','api_key','password'}}
    if isinstance(value,list): return [clean(v) for v in value]
    return value

def serve(profile_path, output, upstream='http://host.docker.internal:11434', port=11434):
    profile=json.loads(Path(profile_path).read_text(encoding='utf-8'))
    digests=profile['model_digests']; output=Path(output); lock=threading.Lock()
    def emit(row):
        with lock:
            with (output/'model_calls.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self): self.forward('GET')
        def do_POST(self): self.forward('POST')
        def forward(self, method):
            start=time.perf_counter(); row={'call_id':str(uuid.uuid4()),'path':self.path,'method':method,'started_unix':time.time()}
            try:
                current=output/'current_case.json'
                row['case']=json.loads(current.read_text()) if current.exists() else {'case_id':'IMPORT_WARMUP'}
                length=int(self.headers.get('Content-Length',0))
                if length>4*1024*1024: raise ValueError('Request exceeds research limit')
                body=self.rfile.read(length) if length else b''
                payload=json.loads(body) if body else {}
                validate_request(method,self.path,payload,digests)
                row.update(model=payload.get('model'),request=clean(payload),prompt_sha256=hashlib.sha256(body).hexdigest())
                # Check immutable model identity before every generation/embedding.
                with urllib.request.urlopen(upstream+'/api/tags',timeout=10) as response: tags=json.load(response)
                validate_digests(tags,digests)
                row['model_digests']=digests
                address=urlsplit(upstream)
                connection=http.client.HTTPConnection(address.hostname,address.port,timeout=360)
                connection.connect()
                upstream_socket=connection.sock
                stopped=threading.Event()
                def cancel_on_disconnect():
                    while not stopped.wait(.2):
                        try:
                            readable,_,_=select.select([self.connection],[],[],0)
                            if readable and not self.connection.recv(1,socket.MSG_PEEK):
                                row['client_disconnected']=True
                                upstream_socket.shutdown(socket.SHUT_RDWR)
                                return
                        except OSError:return
                watcher=threading.Thread(target=cancel_on_disconnect,daemon=True);watcher.start()
                try:
                    connection.request(method,self.path,body=body if method=='POST' else None,headers={'Content-Type':'application/json'})
                    response=connection.getresponse()
                    self.send_response(response.status); self.send_header('Content-Type',response.headers.get('Content-Type','application/json')); self.send_header('Connection','close'); self.end_headers()
                    chunks=[]
                    while True:
                        chunk=response.readline()
                        if not chunk: break
                        chunks.append(chunk)
                        self.wfile.write(chunk); self.wfile.flush()
                    raw=b''.join(chunks)
                    row['upstream_http_status']=response.status
                finally:
                    stopped.set(); connection.close()
                if self.path in {'/api/embed','/api/embeddings','/v1/embeddings'}:
                    obj=json.loads(raw); vectors=obj.get('embeddings') or ([obj['embedding']] if 'embedding' in obj else [x['embedding'] for x in obj.get('data',[])])
                    row['response']={'vector_count':len(vectors),'dimensions':[len(x) for x in vectors], 'sha256':hashlib.sha256(raw).hexdigest()}
                else:
                    try: row['response']=clean(json.loads(raw))
                    except ValueError:
                        parsed=[]
                        for line in raw.decode('utf-8').splitlines():
                            item=line.removeprefix('data: ').strip()
                            if not item or item=='[DONE]':continue
                            try:parsed.append(clean(json.loads(item)))
                            except ValueError:pass
                        row['response_chunks']=parsed
                row['status']='RETURNED' if row['upstream_http_status'] < 400 else 'UPSTREAM_HTTP_ERROR'
            except Exception as exc:
                row.update(status='PROXY_ERROR',error_type=type(exc).__name__)
                try:self.send_error(502,'Research model proxy request failed')
                except OSError:pass
            finally:
                row['latency_ms']=(time.perf_counter()-start)*1000; emit(row)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();serve(a.profile,a.output)
