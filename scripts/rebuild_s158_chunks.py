"""Rebuild S-158 chunks from PDF/XLSX members inside validation archives."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_document_rag_chunks as builder

entries = []
for path in sorted(builder.DATASET.glob("S-158*.zip")):
    sections = [(None, f"Archive member: {member}\n{text}") for member, text in builder.zip_documents(path)]
    entries.extend(builder.make_chunks(path, "validation", "S-158", path.stem, sections))
out = builder.OUT / "s158_validation_chunks.jsonl"
out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in entries), encoding="utf-8")
manifest = json.loads((builder.OUT / "rag_manifest.json").read_text(encoding="utf-8"))
manifest["files"][out.name] = {"chunk_count": len(entries), "product_counts": {"S-158": len(entries)}, "metadata_fields": list(builder.FIELDS), "metadata_complete": all(all(field in row["metadata"] for field in builder.FIELDS) for row in entries), "embedding_status": "pending"}
manifest["chunk_count"] = sum(value["chunk_count"] for value in manifest["files"].values())
(builder.OUT / "rag_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"s158_chunks": len(entries), "total_chunks": manifest["chunk_count"]}, ensure_ascii=False))
