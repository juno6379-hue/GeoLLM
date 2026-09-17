"""Verify Dataset embedding coverage artifacts and live pgvector merge."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "outputs" / "reports"
RAG = ROOT / "outputs" / "rag"


def db_url() -> str:
    return os.getenv("S101_DB_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8-sig") if line.strip())


def main() -> None:
    coverage_path = REPORTS / "dataset_embedding_coverage.json"
    chunks_path = RAG / "dataset_supplemental_chunks.jsonl"
    embeddings_path = RAG / "dataset_supplemental_embeddings.jsonl"
    metadata_path = RAG / "dataset_supplemental_embeddings.metadata.json"
    if not coverage_path.exists():
        raise RuntimeError(f"missing coverage report: {coverage_path}")
    if not chunks_path.exists():
        raise RuntimeError(f"missing supplemental chunks: {chunks_path}")
    if not embeddings_path.exists():
        raise RuntimeError(f"missing supplemental embeddings: {embeddings_path}")

    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    dataset_files = len(coverage.get("inventory") or [])
    already_embedded_files = sum(1 for item in coverage.get("inventory") or [] if item.get("status") == "embedded")
    chunk_count = count_jsonl(chunks_path)
    embedding_count = count_jsonl(embeddings_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    expected_chunks = int(coverage["supplemental_chunk_count"])
    if chunk_count != expected_chunks:
        raise RuntimeError(f"chunk count mismatch: coverage={expected_chunks}, jsonl={chunk_count}")
    if embedding_count != expected_chunks:
        raise RuntimeError(f"embedding count mismatch: chunks={expected_chunks}, embeddings={embedding_count}")

    with psycopg2.connect(db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL)
                FROM knowledge.document_chunks
            """)
            total, null_embeddings = cur.fetchone()
            cur.execute("""
                SELECT COUNT(*)
                FROM knowledge.document_chunks
                WHERE document_type IN ('dataset_profile', 'supplemental_document')
                  AND COALESCE(metadata->>'extraction_status', '') = 'dataset_embedding_coverage'
            """)
            supplemental_live = cur.fetchone()[0]
            cur.execute("""
                SELECT document_type, COUNT(*)
                FROM knowledge.document_chunks
                GROUP BY document_type
                ORDER BY COUNT(*) DESC, document_type
            """)
            by_type = cur.fetchall()
    if supplemental_live < expected_chunks:
        raise RuntimeError(f"supplemental live rows too low: live={supplemental_live}, expected_at_least={expected_chunks}")
    if null_embeddings:
        raise RuntimeError(f"null embeddings remain: {null_embeddings}")

    lines = [
        "# Dataset Embedding Validation",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- coverage_files: `{dataset_files}`",
        f"- coverage_already_embedded_files: `{already_embedded_files}`",
        f"- supplemental_chunks: `{chunk_count}`",
        f"- supplemental_embeddings: `{embedding_count}`",
        f"- supplemental_embedding_model: `{metadata.get('model')}`",
        f"- supplemental_embedding_dimension: `{metadata.get('dimension')}`",
        f"- live_document_chunks_total: `{total}`",
        f"- live_null_embeddings: `{null_embeddings}`",
        f"- live_dataset_supplemental_rows: `{supplemental_live}`",
        "",
        "## Live Counts By Document Type",
        "",
    ]
    for document_type, count in by_type:
        lines.append(f"- `{document_type}`: `{count}`")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "dataset_embedding_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "OK",
        "coverage_files": dataset_files,
        "supplemental_chunks": chunk_count,
        "supplemental_embeddings": embedding_count,
        "live_total": total,
        "live_null_embeddings": null_embeddings,
        "live_dataset_supplemental_rows": supplemental_live,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
