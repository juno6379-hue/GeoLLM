"""Apply the common document-chunk metadata contract to accident chunks."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "outputs/rag/accident_chunks.jsonl"
rows = []
for line in path.read_text(encoding="utf-8").splitlines():
    if not line:
        continue
    row = json.loads(line)
    metadata = row.setdefault("metadata", {})
    source_file = metadata.get("source_path") or metadata.get("source_file") or "Dataset/accident_source"
    metadata.update({
        "document_id": metadata.get("document_id") or hashlib.sha256(source_file.encode()).hexdigest()[:24],
        "document_type": "accident_data",
        "product_id": None,
        "standard_type": None,
        "title": metadata.get("title") or source_file,
        "section": metadata.get("section") or f"chunk_{metadata.get('chunk_index', 0)}",
        "version": metadata.get("version"),
        "language": "ko",
        "source_file": source_file,
        "page_no": None,
        "related_features": metadata.get("related_features", []),
        "related_concepts": metadata.get("related_concepts") or ["accident_hotspot", "navigation_hazard_object"],
        "clearance_level": "PUBLIC",
        "source_url": None,
    })
    rows.append(row)
path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
print(json.dumps({"normalized": len(rows)}, ensure_ascii=False))
