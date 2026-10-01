"""Generate embeddings for generated RAG chunks without exposing credentials."""
import argparse, json, os, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_existing(path):
    existing={}
    if not path.exists():
        return existing
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        row=json.loads(line)
        if row.get('chunk_id') and row.get('embedding'):
            existing[row['chunk_id']]=row
    return existing

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', action='append', dest='inputs', help='Chunk JSONL input. May be repeated.')
    parser.add_argument('--output', default='outputs/rag/embeddings_v2.jsonl')
    parser.add_argument('--resume', action='store_true')
    args=parser.parse_args()
    rows=[]
    input_paths=[ROOT/item if not Path(item).is_absolute() else Path(item) for item in (args.inputs or [])]
    if not input_paths:
        input_paths=sorted((ROOT/'outputs/rag').glob('*_chunks.jsonl'))
    max_chars=int(os.getenv('EMBEDDING_MAX_CHARS','1200'))
    truncate_chars=int(os.getenv('EMBEDDING_TRUNCATE_CHARS','0'))
    for path in input_paths:
        for line in path.read_text(encoding='utf-8').splitlines():
            if line:
                row=json.loads(line); text=row['text']
                if truncate_chars > 0 and len(text) > truncate_chars:
                    text=text[:truncate_chars]
                for index in range(0, max(len(text), 1), max_chars):
                    part=dict(row); part['text']=text[index:index+max_chars]
                    part['chunk_id']=row['chunk_id'] if index == 0 else f"{row['chunk_id']}-{index//max_chars}"
                    rows.append(part)
    out=ROOT/args.output if not Path(args.output).is_absolute() else Path(args.output)
    existing=load_existing(out) if args.resume else {}
    pending=[row for row in rows if row['chunk_id'] not in existing]
    model=os.getenv('EMBEDDING_MODEL','bge-m3')
    endpoint=os.getenv('OLLAMA_EMBEDDING_URL', os.getenv('OLLAMA_BASE_URL','http://host.docker.internal:11434').rstrip('/') + '/api/embed')
    batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE','2'))
    timeout=int(os.getenv('EMBEDDING_TIMEOUT_SEC','600'))
    embedded=[]
    out.parent.mkdir(parents=True,exist_ok=True)
    append_mode=bool(existing)
    handle=out.open('a' if append_mode else 'w',encoding='utf-8')
    for start in range(0,len(pending),batch_size):
        try:
            batch=pending[start:start+batch_size]
            body=json.dumps({'model':model,'input':[row['text'] for row in batch],
                             'options':{'num_thread':int(os.getenv('EMBEDDING_NUM_THREAD','4'))}}).encode()
            req=urllib.request.Request(endpoint,data=body,headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=timeout) as response:
                    vectors=json.load(response)['embeddings']
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f'Ollama embedding failed at chunk index {start}: HTTP {exc.code}') from exc
            for row,vector in zip(batch,vectors):
                item={'chunk_id':row['chunk_id'],'content':row['text'],'metadata':row['metadata'],'embedding':vector,'model':model,'dimension':len(vector),'source_sha256':row['metadata']['source_sha256']}
                embedded.append(item)
                handle.write(json.dumps(item,ensure_ascii=False)+'\n')
            handle.flush()
            print(f"embedded_progress generated={len(embedded)} pending_total={len(pending)} output={out.name}",flush=True)
        finally:
            pass
    handle.close()
    all_rows=list(load_existing(out).values())
    dimension=len(all_rows[0]['embedding']) if all_rows else 0
    if not all_rows or not all(len(row['embedding'])==dimension for row in all_rows):
        raise RuntimeError(f'Unexpected embedding dimension: {dimension}')
    meta={'status':'completed','model':model,'dimension':dimension,'count':len(all_rows),'generated':len(embedded),'skipped_existing':len(existing),'output':str(out.relative_to(ROOT)).replace('\\','/'),'endpoint_type':'ollama'}
    metadata_path=out.with_suffix('.metadata.json')
    metadata_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if out.name == 'embeddings_v2.jsonl':
        (ROOT/'outputs/rag/embedding_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"embeddings_generated count={len(all_rows)} generated={len(embedded)} skipped_existing={len(existing)} dimension={dimension} output={meta['output']}")
if __name__=='__main__': main()
