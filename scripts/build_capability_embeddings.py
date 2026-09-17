"""Build and upsert pgvector capability embeddings for QueryCandidateBroker."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs" / "rag"
REPORTS = ROOT / "outputs" / "reports"
REGISTRY = DATA / "capability_registry.yaml"


def db_url() -> str:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def embedding_endpoint() -> str:
    return os.getenv("OLLAMA_EMBEDDING_URL", os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/embed")


def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def capability_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("capability_id", "object_type", "label", "description", "authority_ref", "registry_ref"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    for key in ("routes", "input_slots", "output_slots", "deterministic_hints"):
        values = item.get(key) or []
        if isinstance(values, list):
            parts.extend(str(value) for value in values if value)
    return "\n".join(parts)


def build_chunks(registry: dict[str, Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for item in registry.get("capabilities") or []:
        capability_id = str(item.get("capability_id") or "").strip()
        if not capability_id:
            continue
        text = capability_text(item)
        source_sha = hashlib.sha256(json.dumps(item, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        chunks.append({
            "id": capability_id,
            "object_type": item.get("object_type") or "capability",
            "object_id": capability_id,
            "label": item.get("label") or capability_id,
            "description": text,
            "route_tags": item.get("routes") or [],
            "input_slots": item.get("input_slots") or [],
            "output_slots": item.get("output_slots") or [],
            "authority_ref": item.get("authority_ref"),
            "registry_ref": item.get("registry_ref"),
            "metadata": {
                "source": "data/capability_registry.yaml",
                "role": item.get("role"),
                "deterministic_hints": item.get("deterministic_hints") or [],
                "raw": item,
                "source_sha256": source_sha,
            },
        })
    return chunks


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    body = json.dumps({"model": model, "input": texts}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(embedding_endpoint(), data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=int(os.getenv("EMBEDDING_TIMEOUT_SEC", "600"))) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama embedding failed: HTTP {exc.code}") from exc
    return payload["embeddings"], model


def ensure_table(cur, dimension: int) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS knowledge")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS knowledge.capability_embeddings (
            id text primary key,
            object_type text not null,
            object_id text not null,
            label text not null,
            description text not null,
            route_tags text[] not null default '{{}}',
            input_slots text[] not null default '{{}}',
            output_slots text[] not null default '{{}}',
            authority_ref text,
            registry_ref text,
            metadata jsonb not null default '{{}}'::jsonb,
            embedding vector({dimension}),
            updated_at timestamptz not null default now()
        )
        """
    )
    cur.execute(f"ALTER TABLE knowledge.capability_embeddings ADD COLUMN IF NOT EXISTS embedding vector({dimension})")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_capability_embeddings_type ON knowledge.capability_embeddings (object_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_capability_embeddings_routes ON knowledge.capability_embeddings USING GIN (route_tags)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_capability_embeddings_metadata ON knowledge.capability_embeddings USING GIN (metadata)")


def upsert(rows: list[dict[str, Any]], embeddings: list[list[float]]) -> dict[str, Any]:
    if len(rows) != len(embeddings):
        raise RuntimeError("row/embedding count mismatch")
    dimension = len(embeddings[0]) if embeddings else 0
    with psycopg2.connect(db_url(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            ensure_table(cur, dimension)
            psycopg2.extras.execute_batch(
                cur,
                """
                INSERT INTO knowledge.capability_embeddings
                    (id, object_type, object_id, label, description, route_tags, input_slots,
                     output_slots, authority_ref, registry_ref, metadata, embedding, updated_at)
                VALUES
                    (%(id)s, %(object_type)s, %(object_id)s, %(label)s, %(description)s,
                     %(route_tags)s, %(input_slots)s, %(output_slots)s, %(authority_ref)s,
                     %(registry_ref)s, %(metadata)s::jsonb, %(embedding)s::vector, now())
                ON CONFLICT (id) DO UPDATE SET
                    object_type = EXCLUDED.object_type,
                    object_id = EXCLUDED.object_id,
                    label = EXCLUDED.label,
                    description = EXCLUDED.description,
                    route_tags = EXCLUDED.route_tags,
                    input_slots = EXCLUDED.input_slots,
                    output_slots = EXCLUDED.output_slots,
                    authority_ref = EXCLUDED.authority_ref,
                    registry_ref = EXCLUDED.registry_ref,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = now()
                """,
                [
                    {
                        **row,
                        "metadata": json.dumps(row["metadata"], ensure_ascii=False),
                        "embedding": embeddings[index],
                    }
                    for index, row in enumerate(rows)
                ],
                page_size=100,
            )
            cur.execute("ANALYZE knowledge.capability_embeddings")
            try:
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_capability_embeddings_embedding "
                    "ON knowledge.capability_embeddings USING hnsw (embedding vector_cosine_ops)"
                )
            except psycopg2.Error:
                conn.rollback()
                with conn.cursor() as cur2:
                    cur2.execute("ANALYZE knowledge.capability_embeddings")
            cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL) FROM knowledge.capability_embeddings")
            total, nulls = cur.fetchone()
    return {"live_total": int(total), "live_null_embeddings": int(nulls), "dimension": dimension}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="outputs/rag/capability_chunks.jsonl")
    parser.add_argument("--embeddings", default="outputs/rag/capability_embeddings.jsonl")
    parser.add_argument("--no-upsert", action="store_true")
    args = parser.parse_args()

    chunks = build_chunks(load_registry())
    chunk_path = ROOT / args.chunks
    embedding_path = ROOT / args.embeddings
    write_jsonl(chunk_path, chunks)
    vectors, model = embed_texts([row["description"] for row in chunks])
    embedded_rows = [
        {
            **row,
            "embedding": vectors[index],
            "model": model,
            "dimension": len(vectors[index]),
        }
        for index, row in enumerate(chunks)
    ]
    write_jsonl(embedding_path, embedded_rows)
    db_result = {"live_total": None, "live_null_embeddings": None, "dimension": len(vectors[0]) if vectors else 0}
    if not args.no_upsert:
        db_result = upsert(chunks, vectors)
    report = {
        "status": "OK",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chunk_count": len(chunks),
        "embedding_count": len(vectors),
        "model": model,
        "dimension": db_result["dimension"],
        "chunk_output": str(chunk_path.relative_to(ROOT)).replace("\\", "/"),
        "embedding_output": str(embedding_path.relative_to(ROOT)).replace("\\", "/"),
        **db_result,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "capability_embedding_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "capability_embedding_validation.md").write_text(
        "\n".join([
            "# Capability Embedding Validation",
            "",
            f"- status: `{report['status']}`",
            f"- generated_at: `{report['generated_at']}`",
            f"- chunks: `{report['chunk_count']}`",
            f"- embeddings: `{report['embedding_count']}`",
            f"- model: `{report['model']}`",
            f"- dimension: `{report['dimension']}`",
            f"- live_total: `{report['live_total']}`",
            f"- live_null_embeddings: `{report['live_null_embeddings']}`",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
