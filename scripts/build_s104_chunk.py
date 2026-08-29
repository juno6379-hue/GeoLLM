"""Add the S-104 product specification PDF missed by filename selection."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_document_rag_chunks as builder

path = next(builder.DATASET.glob("S-104_Water_Level_Information_For_Surface_Navigation_Ed_2.0.0.pdf"))
rows = builder.make_chunks(path, "product_specification", "S-104", path.stem, builder.pdf_pages(path))
out = builder.OUT / "s104_chunks.jsonl"
out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
manifest = json.loads((builder.OUT / "rag_manifest.json").read_text(encoding="utf-8"))
manifest["files"][out.name] = {"chunk_count": len(rows), "product_counts": {"S-104": len(rows)}, "metadata_fields": list(builder.FIELDS), "metadata_complete": all(all(field in row["metadata"] for field in builder.FIELDS) for row in rows)}
manifest["sources"].append({"source_file": builder.rel(path), "document_type": "product_specification", "product_id": "S-104", "sha256": builder.sha256(path), "format": "pdf"})
manifest["chunk_count"] = sum(value["chunk_count"] for value in manifest["files"].values())
(builder.OUT / "rag_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"s104_chunks": len(rows), "total_chunks": manifest["chunk_count"]}, ensure_ascii=False))
