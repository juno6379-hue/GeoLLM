"""Regenerate law chunks with one source row assigned to one chunk."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_document_rag_chunks as builder

sources = [path for path in builder.DATASET.glob("*.csv") if any(term in path.name for term in ("법령", "행정규칙", "선박법령"))]
rows = []
for source in sorted(sources):
    rows.extend(builder.csv_chunks(source, source.stem))
path = builder.OUT / "law_chunks.jsonl"
path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
print(json.dumps({"law_chunks": len(rows), "sources": len(sources)}, ensure_ascii=False))
