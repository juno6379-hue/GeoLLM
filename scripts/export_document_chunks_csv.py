"""Export generated RAG chunks for COPY into the pgvector database."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    rows=[]
    for path in sorted((ROOT/'outputs/rag').glob('*_chunks.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            if line:
                item=json.loads(line); m=item['metadata']
                rows.append([item['chunk_id'],item['text'],json.dumps(m,ensure_ascii=False),m['source_id'],m['source_sha256']])
    out=ROOT/'outputs/rag/document_chunks_load.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['chunk_id','content','metadata','source_id','source_sha256']); w.writerows(rows)
    print(f'chunk_exported count={len(rows)}')
if __name__=='__main__': main()
