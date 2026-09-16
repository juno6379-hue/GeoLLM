"""Merge completed embedding JSONL files into knowledge.document_chunks."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "outputs" / "reports"


def db_url() -> str:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def ensure_table(cur, dimension: int) -> None:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("CREATE SCHEMA IF NOT EXISTS knowledge")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge.document_chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            product_id TEXT,
            standard_type TEXT,
            title TEXT,
            section TEXT,
            version TEXT,
            language TEXT DEFAULT 'ko',
            content TEXT NOT NULL,
            keywords TEXT[],
            related_features TEXT[],
            related_concepts TEXT[],
            clearance_level TEXT DEFAULT 'PUBLIC',
            source_file TEXT,
            source_url TEXT,
            page_no INTEGER,
            metadata JSONB NOT NULL,
            source_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            embedding vector({dimension}),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("ALTER TABLE knowledge.document_chunks ADD COLUMN IF NOT EXISTS source_id TEXT")
    cur.execute("ALTER TABLE knowledge.document_chunks ADD COLUMN IF NOT EXISTS source_sha256 TEXT")


def normalize_row(row: dict[str, Any]) -> tuple[Any, ...] | None:
    metadata = row.get("metadata") or {}
    embedding = row.get("embedding")
    content = row.get("content") or ""
    if not isinstance(embedding, list) or not embedding or not content.strip():
        return None
    chunk_id = row.get("chunk_id") or metadata.get("chunk_id")
    document_id = row.get("document_id") or metadata.get("document_id") or metadata.get("source_id")
    document_type = row.get("document_type") or metadata.get("document_type") or "document"
    source_file = row.get("source_file") or metadata.get("source_file") or metadata.get("source_path")
    source_id = metadata.get("source_id") or row.get("source_id") or document_id
    source_sha256 = row.get("source_sha256") or metadata.get("source_sha256") or ""
    if not chunk_id or not document_id or not source_id or not source_sha256:
        return None
    return (
        chunk_id,
        document_id,
        document_type,
        row.get("product_id") or metadata.get("product_id"),
        row.get("standard_type") or metadata.get("standard_type"),
        row.get("title") or metadata.get("title"),
        row.get("section") or metadata.get("section"),
        row.get("version") or metadata.get("version"),
        row.get("language") or metadata.get("language", "ko"),
        content,
        row.get("keywords") or metadata.get("keywords") or [],
        row.get("related_features") or metadata.get("related_features") or [],
        row.get("related_concepts") or metadata.get("related_concepts") or [],
        row.get("clearance_level") or metadata.get("clearance_level", "PUBLIC"),
        source_file,
        row.get("source_url") or metadata.get("source_url"),
        row.get("page_no") or metadata.get("page_no"),
        json.dumps(metadata, ensure_ascii=False),
        source_id,
        source_sha256,
        "[" + ",".join(str(float(value)) for value in embedding) + "]",
    )


def merge_file(cur, path: Path, dimension: int) -> dict[str, Any]:
    rows = read_rows(path)
    normalized = [item for item in (normalize_row(row) for row in rows) if item is not None]
    skipped = len(rows) - len(normalized)
    if not normalized:
        return {"path": str(path), "read": len(rows), "merged": 0, "skipped": skipped}
    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO knowledge.document_chunks
          (chunk_id, document_id, document_type, product_id, standard_type, title, section, version, language,
           content, keywords, related_features, related_concepts, clearance_level, source_file, source_url, page_no,
           metadata, source_id, source_sha256, embedding)
        VALUES
          (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::vector)
        ON CONFLICT (chunk_id) DO UPDATE SET
          document_id=EXCLUDED.document_id,
          document_type=EXCLUDED.document_type,
          product_id=EXCLUDED.product_id,
          standard_type=EXCLUDED.standard_type,
          title=EXCLUDED.title,
          section=EXCLUDED.section,
          version=EXCLUDED.version,
          language=EXCLUDED.language,
          content=EXCLUDED.content,
          keywords=EXCLUDED.keywords,
          related_features=EXCLUDED.related_features,
          related_concepts=EXCLUDED.related_concepts,
          clearance_level=EXCLUDED.clearance_level,
          source_file=EXCLUDED.source_file,
          source_url=EXCLUDED.source_url,
          page_no=EXCLUDED.page_no,
          metadata=EXCLUDED.metadata,
          source_id=EXCLUDED.source_id,
          source_sha256=EXCLUDED.source_sha256,
          embedding=EXCLUDED.embedding
        """,
        normalized,
        page_size=100,
    )
    return {"path": str(path), "read": len(rows), "merged": len(normalized), "skipped": skipped}


def write_report(results: list[dict[str, Any]], total: int, null_embeddings: int) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Live Document Chunk Merge Report", "", f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`"]
    lines.append(f"- total_document_chunks: `{total}`")
    lines.append(f"- null_embeddings: `{null_embeddings}`")
    for result in results:
        lines.append(f"- `{result['path']}`: merged `{result['merged']}`, skipped `{result['skipped']}`, read `{result['read']}`")
    (REPORTS / "live_document_chunk_merge.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--database-url")
    parser.add_argument("--dimension", type=int, default=int(os.getenv("EMBEDDING_DIM", "1024")))
    args = parser.parse_args()
    input_paths = [Path(item) if Path(item).is_absolute() else ROOT / item for item in args.inputs]
    conn = psycopg2.connect(args.database_url or db_url(), connect_timeout=5)
    try:
        with conn:
            with conn.cursor() as cur:
                ensure_table(cur, args.dimension)
                results = [merge_file(cur, path, args.dimension) for path in input_paths]
                cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_metadata ON knowledge.document_chunks USING GIN (metadata)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_embedding ON knowledge.document_chunks USING hnsw (embedding vector_cosine_ops)")
                cur.execute("ANALYZE knowledge.document_chunks")
                cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL) FROM knowledge.document_chunks")
                total, null_embeddings = cur.fetchone()
    finally:
        conn.close()
    write_report(results, total, null_embeddings)
    print(json.dumps({"status": "OK", "results": results, "total": total, "null_embeddings": null_embeddings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
