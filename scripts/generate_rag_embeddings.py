"""Generate embeddings for all generated RAG chunks without exposing credentials."""
import json, os, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    rows=[]
    for path in sorted((ROOT/'outputs/rag').glob('*_chunks.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            if line:
                row=json.loads(line); text=row['text']
                for index in range(0, max(len(text), 1), 1200):
                    part=dict(row); part['text']=text[index:index+1200]
                    part['chunk_id']=row['chunk_id'] if index == 0 else f"{row['chunk_id']}-{index//1200}"
                    rows.append(part)
    model=os.getenv('EMBEDDING_MODEL','bge-m3')
    endpoint=os.getenv('OLLAMA_EMBEDDING_URL', os.getenv('OLLAMA_BASE_URL','http://host.docker.internal:11434').rstrip('/') + '/api/embed')
    batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE','2'))
    timeout=int(os.getenv('EMBEDDING_TIMEOUT_SEC','600'))
    vectors=[]
    for start in range(0,len(rows),batch_size):
        batch=rows[start:start+batch_size]
        body=json.dumps({'model':model,'input':[row['text'] for row in batch]}).encode()
        req=urllib.request.Request(endpoint,data=body,headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response: vectors.extend(json.load(response)['embeddings'])
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'Ollama embedding failed at chunk index {start}: HTTP {exc.code}') from exc
    dimension=len(vectors[0]) if vectors else 0
    if not vectors or not all(len(vector)==dimension for vector in vectors):
        raise RuntimeError(f'Unexpected embedding dimension: {dimension}')
    out=ROOT/'outputs/rag/embeddings_v2.jsonl'
    out.write_text(''.join(json.dumps({'chunk_id':row['chunk_id'],'content':row['text'],'metadata':row['metadata'],'embedding':vector,'model':model,'dimension':len(vector),'source_sha256':row['metadata']['source_sha256']},ensure_ascii=False)+'\n' for row,vector in zip(rows,vectors)),encoding='utf-8')
    meta={'status':'completed','model':model,'dimension':dimension,'count':len(rows),'output':'outputs/rag/embeddings_v2.jsonl','endpoint_type':'ollama'}
    (ROOT/'outputs/rag/embedding_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'embeddings_generated count={len(rows)} dimension={dimension}')
if __name__=='__main__': main()
