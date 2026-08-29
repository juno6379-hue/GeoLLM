"""Validate and load completed Ollama embeddings into the v2 staging table."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / "outputs/rag"
REPORT = ROOT / "outputs/reports/document_chunks_v2_staging_report.md"


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def expected_count() -> int:
    manifest = json.loads((RAG / "rag_manifest.json").read_text(encoding="utf-8"))
    return sum(item.get("chunk_count", 0) for item in manifest.get("files", {}).values())


def validate_rows(rows: list[dict], expected: int) -> tuple[int, list[str]]:
    errors: list[str] = []
    ids = [row.get("chunk_id") for row in rows]
    if len(rows) != expected:
        errors.append(f"count mismatch: expected {expected}, received {len(rows)}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate chunk_id detected")
    dimensions = set()
    for index, row in enumerate(rows, 1):
        metadata = row.get("metadata") or {}
        content = row.get("content", "")
        embedding = row.get("embedding")
        for field in ("chunk_id", "document_id", "document_type", "source_file"):
            if not row.get(field) and not metadata.get(field):
                errors.append(f"row {index}: missing {field}")
        if not metadata.get("source_id"):
            errors.append(f"row {index}: missing source_id")
        if not row.get("source_sha256") and not metadata.get("source_sha256"):
            errors.append(f"row {index}: missing source_sha256")
        if not content.strip():
            errors.append(f"row {index}: empty content")
        if "�" in content:
            errors.append(f"row {index}: replacement character found")
        if not isinstance(embedding, list) or not embedding:
            errors.append(f"row {index}: missing embedding")
        else:
            dimensions.add(len(embedding))
        if len(errors) > 25:
            break
    if len(dimensions) > 1:
        errors.append(f"embedding dimension mismatch: {sorted(dimensions)}")
    return (next(iter(dimensions)) if len(dimensions) == 1 else 0), errors


def connect(url: str):
    import psycopg2
    return psycopg2.connect(url)


def create_table(cur, dimension: int):
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("CREATE SCHEMA IF NOT EXISTS knowledge")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge.document_chunks_v2_staging (
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
    # Upgrade a table created by the earlier minimal staging prototype.
    cur.execute("ALTER TABLE knowledge.document_chunks_v2_staging ADD COLUMN IF NOT EXISTS source_id TEXT")
    cur.execute("ALTER TABLE knowledge.document_chunks_v2_staging ADD COLUMN IF NOT EXISTS source_sha256 TEXT")


def row_values(row: dict):
    metadata = row.get("metadata") or {}
    return (
        row.get("chunk_id") or metadata.get("chunk_id"),
        row.get("document_id") or metadata.get("document_id"),
        row.get("document_type") or metadata.get("document_type"),
        row.get("product_id") or metadata.get("product_id"),
        row.get("standard_type") or metadata.get("standard_type"),
        row.get("title") or metadata.get("title"),
        row.get("section") or metadata.get("section"),
        row.get("version") or metadata.get("version"),
        row.get("language") or metadata.get("language", "ko"),
        row["content"],
        row.get("keywords") or metadata.get("keywords", []),
        row.get("related_features") or metadata.get("related_features", []),
        row.get("related_concepts") or metadata.get("related_concepts", []),
        row.get("clearance_level") or metadata.get("clearance_level", "PUBLIC"),
        row.get("source_file") or metadata.get("source_file") or metadata.get("source_path"),
        row.get("source_url") or metadata.get("source_url"),
        row.get("page_no") or metadata.get("page_no"),
        json.dumps(metadata, ensure_ascii=False),
        metadata.get("source_id", ""),
        row.get("source_sha256") or metadata.get("source_sha256", ""),
        "[" + ",".join(str(float(value)) for value in row["embedding"]) + "]",
    )


def write_report(status: str, details: dict):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# document_chunks_v2_staging Load Report", "", f"- status: `{status}`"]
    lines.extend(f"- {key}: `{value}`" for key, value in details.items())
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load(args):
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not input_path.exists() or input_path.name.endswith(".partial.jsonl"):
        raise RuntimeError("completed embeddings_v2.jsonl is required; partial output is never loadable")
    rows = read_rows(input_path)
    expected = expected_count()
    dimension, errors = validate_rows(rows, expected)
    if errors:
        write_report("REJECTED", {"input": input_path, "expected_count": expected, "received_count": len(rows), "errors": errors})
        raise RuntimeError("staging validation failed: " + "; ".join(errors[:5]))
    if dimension != args.dimension:
        raise RuntimeError(f"embedding dimension {dimension} does not match EMBEDDING_DIM {args.dimension}")

    database_url = args.database_url or os.getenv("POSTGIS_URL")
    if not database_url:
        raise RuntimeError("POSTGIS_URL or --database-url is required")
    connection = connect(database_url)
    try:
        with connection:
            with connection.cursor() as cur:
                create_table(cur, dimension)
                if args.replace_staging:
                    cur.execute("TRUNCATE knowledge.document_chunks_v2_staging")
                from psycopg2.extras import execute_batch
                sql = """INSERT INTO knowledge.document_chunks_v2_staging
                    (chunk_id, document_id, document_type, product_id, standard_type, title, section, version, language, content, keywords, related_features, related_concepts, clearance_level, source_file, source_url, page_no, metadata, source_id, source_sha256, embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector)
                    ON CONFLICT (chunk_id) DO UPDATE SET content=EXCLUDED.content, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding"""
                execute_batch(cur, sql, [row_values(row) for row in rows], page_size=100)
                cur.execute("SELECT COUNT(*) FROM knowledge.document_chunks_v2_staging")
                stored_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM knowledge.document_chunks_v2_staging WHERE content LIKE '%�%'")
                broken_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM knowledge.document_chunks_v2_staging WHERE embedding IS NULL")
                null_embedding_count = cur.fetchone()[0]
                if (stored_count, broken_count, null_embedding_count) != (expected, 0, 0):
                    raise RuntimeError(f"database validation failed: count={stored_count}, broken={broken_count}, null_embedding={null_embedding_count}")
    finally:
        connection.close()
    write_report("STAGING_READY", {"input": input_path, "expected_count": expected, "stored_count": stored_count, "embedding_dimension": dimension, "broken_character_count": broken_count, "null_embedding_count": null_embedding_count, "serving_replacement": "not executed"})
    print(json.dumps({"status": "STAGING_READY", "count": stored_count, "dimension": dimension}, ensure_ascii=False))


def promote(args):
    if os.getenv("ALLOW_DOCUMENT_CHUNKS_PROMOTION", "false").lower() not in {"1", "true", "yes"}:
        raise RuntimeError("promotion requires ALLOW_DOCUMENT_CHUNKS_PROMOTION=true")
    database_url = args.database_url or os.getenv("POSTGIS_URL")
    connection = connect(database_url)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup = f"document_chunks_v1_backup_{stamp}"
    try:
        with connection:
            with connection.cursor() as cur:
                cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL) FROM knowledge.document_chunks_v2_staging")
                count, missing = cur.fetchone()
                expected = expected_count()
                if count != expected or missing:
                    raise RuntimeError(f"promotion blocked: staging count={count}, expected={expected}, missing_embeddings={missing}")
                cur.execute("SELECT to_regclass('knowledge.document_chunks')")
                if cur.fetchone()[0]:
                    cur.execute(f'ALTER TABLE knowledge.document_chunks RENAME TO "{backup}"')
                cur.execute("ALTER TABLE knowledge.document_chunks_v2_staging RENAME TO document_chunks")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_metadata ON knowledge.document_chunks USING GIN (metadata)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_embedding ON knowledge.document_chunks USING hnsw (embedding vector_cosine_ops)")
    finally:
        connection.close()
    print(json.dumps({"status": "PROMOTED", "backup_table": f"knowledge.{backup}"}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs/rag/embeddings_v2.jsonl")
    parser.add_argument("--database-url")
    parser.add_argument("--dimension", type=int, default=int(os.getenv("EMBEDDING_DIM", "1024")))
    parser.add_argument("--replace-staging", action="store_true")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    if args.promote:
        promote(args)
    else:
        load(args)


if __name__ == "__main__":
    main()
