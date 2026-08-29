"""Finalize RAG manifest and report after document chunk extraction."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
RAG = OUT / "rag"
REQUIRED = ["document_id", "document_type", "product_id", "standard_type", "title", "section", "version", "language", "source_file", "page_no", "related_features", "related_concepts", "clearance_level", "source_url"]
FILES = ["s100_product_spec_chunks.jsonl", "s101_dceg_chunks.jsonl", "s104_chunks.jsonl", "s111_chunks.jsonl", "s124_chunks.jsonl", "s158_validation_chunks.jsonl", "law_chunks.jsonl", "accident_chunks.jsonl"]


def load_rows(name):
    path = RAG / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line] if path.exists() else []


def main():
    manifest = {"version": "3.0", "generated_at": datetime.now(timezone.utc).isoformat(), "chunk_policy": {"document_target_words": 900, "document_overlap_words": 120, "pdf_docx_requested_tokens": "800-1200 approximate word/token units", "csv_policy": "50-row semantic units for large law CSVs; row-level source provenance retained"}, "embedding_status": "pending", "embedding_note": "New document chunks require embedding generation before pgvector replacement.", "files": {}, "sources": []}
    total = 0
    document_counts = Counter(); product_counts = Counter(); missing_fields = Counter(); relation_features = Counter(); relation_concepts = Counter(); chunk_sizes = []
    document_sizes = []
    for name in FILES:
        rows = load_rows(name)
        total += len(rows)
        for row in rows:
            metadata = row.get("metadata", {})
            document_counts[metadata.get("document_type") or "unknown"] += 1
            product_counts[metadata.get("product_id") or "LAW/ACCIDENT"] += 1
            relation_features.update(metadata.get("related_features") or [])
            relation_concepts.update(metadata.get("related_concepts") or [])
            chunk_sizes.append(len(row.get("text", "").split()))
            if metadata.get("document_type") in {"product_specification", "dceg", "validation"}:
                document_sizes.append(len(row.get("text", "").split()))
            for field in REQUIRED:
                if field not in metadata:
                    missing_fields[field] += 1
        manifest["files"][name] = {"chunk_count": len(rows), "metadata_fields": REQUIRED, "metadata_complete": all(all(field in row.get("metadata", {}) for field in REQUIRED) for row in rows), "embedding_status": "pending"}
    manifest["chunk_count"] = total
    manifest["embedding_status"] = "pending"
    (RAG / "embedding_metadata.json").write_text(json.dumps({"status": "pending", "reason": "RAG document chunks were regenerated; embeddings must be rebuilt before pgvector replacement", "chunk_count": total, "source_manifest": "outputs/rag/rag_manifest.json"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RAG / "rag_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = ["# RAG Chunk Report", "", "## 1. Chunk count by document", ""]
    report += [f"- `{name}`: {value['chunk_count']}" for name, value in manifest["files"].items()]
    report += ["", "## 2. Chunk count by product_id", ""]
    report += [f"- `{key}`: {value}" for key, value in sorted(product_counts.items())]
    report += ["", "## 3. related_features extraction", "", f"- Chunks with at least one feature relation: {sum(1 for name in FILES for row in load_rows(name) if row.get('metadata', {}).get('related_features'))}", f"- Unique related_features: {len(relation_features)}"]
    report += ["", "## 4. related_concepts extraction", "", f"- Chunks with at least one concept relation: {sum(1 for name in FILES for row in load_rows(name) if row.get('metadata', {}).get('related_concepts'))}", f"- Unique related_concepts: {', '.join(sorted(relation_concepts)) if relation_concepts else 'none'}"]
    report += ["", "## 5. Missing metadata", "", f"- Total chunks: {total}", f"- Required metadata missing: {dict(missing_fields) if missing_fields else 'none'}", "- Required fields: document_id, document_type, product_id, standard_type, title, section, version, language, source_file, page_no, related_features, related_concepts, clearance_level, source_url"]
    report += ["", "## 6. pgvector readiness", "", "- Chunk JSONL: ready", "- UTF-8 source text: ready", "- provenance/source_sha256: included", "- Embeddings: pending for regenerated document chunks", "- Database load: requires embedding generation, then full replacement", f"- PDF/DOCX/S-158 chunk word range: {min(document_sizes)}-{max(document_sizes)}" if document_sizes else "- PDF/DOCX/S-158 chunk word range: none", f"- Overall average word count: {sum(chunk_sizes) / len(chunk_sizes):.1f}" if chunk_sizes else "- Overall average word count: 0"]
    report += ["", "## Processing policy", "", "PDF/DOCX uses page or paragraph boundaries with an approximately 900-word target and 120-word overlap. CSV law sources use 50-row semantic units and retain the row range in section metadata. S-158 PDF/XLSX archive members retain source archive provenance and member metadata."]
    report_path = OUT / "reports/12_rag_chunk_report.md"; report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"chunk_count": total, "product_counts": dict(product_counts), "missing_metadata": dict(missing_fields)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
