"""Export embedding JSONL to COPY-compatible CSV."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    rows=[json.loads(line) for line in (ROOT/'outputs/rag/embeddings_v2.jsonl').read_text(encoding='utf-8-sig').splitlines() if line]
    with (ROOT/'outputs/rag/embeddings_load.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['chunk_id','content','metadata','embedding','source_id','source_sha256'])
        for row in rows:
            w.writerow([row['chunk_id'],row['content'],json.dumps(row['metadata'],ensure_ascii=False),json.dumps(row['embedding'],separators=(',',':')),row['metadata']['source_id'],row['source_sha256']])
    print(f'embeddings_exported count={len(rows)}')
if __name__=='__main__': main()
