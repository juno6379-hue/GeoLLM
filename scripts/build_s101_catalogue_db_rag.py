"""Build and upsert S-101 Feature Catalogue + S100_dev DB text RAG chunks.

This script intentionally embeds semantic descriptions, not every S-101
feature instance. Geometry-heavy feature rows remain in PostGIS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "data/s101_feature_catalogue_v2_parsed.json"
DEFAULT_CHUNKS = ROOT / "outputs/rag/s101_catalogue_db_chunks.jsonl"
DEFAULT_EMBEDDINGS = ROOT / "outputs/rag/s101_catalogue_db_embeddings.jsonl"
DEFAULT_REPORT = ROOT / "outputs/reports/17_s101_catalogue_db_embedding_report.md"

SOURCE_IDS = {
    "feature_catalogue": "s101_feature_catalogue_v2_xml",
    "attribute_catalogue": "s101_attribute_catalogue_v2_xml",
    "db_feature_profile": "s100_dev_s101_db_feature_profile",
    "db_text_values": "s100_dev_s101_db_text_values",
}


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def keywords_from_text(text: str, extra: list[str] | None = None) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[가-힣]{2,}", text)
    seen: set[str] = set()
    result: list[str] = []
    for word in (extra or []) + words:
        key = word.lower()
        if key not in seen:
            result.append(word)
            seen.add(key)
        if len(result) >= 24:
            break
    return result


def chunk_row(
    *,
    chunk_id: str,
    content: str,
    metadata: dict[str, Any],
    related_features: list[str] | None = None,
    related_concepts: list[str] | None = None,
) -> dict[str, Any]:
    content = clean_text(content)
    if not content:
        raise ValueError("empty chunk content")
    source_id = metadata["source_id"]
    metadata = {
        "document_id": metadata.get("document_id", source_id),
        "document_type": metadata["document_type"],
        "product_id": "S-101",
        "standard_type": "S-101",
        "title": metadata["title"],
        "section": metadata["section"],
        "version": metadata.get("version", "2.0.0"),
        "language": metadata.get("language", "en"),
        "source_file": metadata["source_file"],
        "page_no": None,
        "related_features": related_features or [],
        "related_concepts": related_concepts or [],
        "clearance_level": "PUBLIC",
        "source_url": None,
        "source_id": source_id,
        "source_sha256": metadata["source_sha256"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in metadata.items() if k not in {"document_type", "title", "section", "source_file", "source_id", "source_sha256"}},
    }
    return {
        "chunk_id": chunk_id,
        "text": content,
        "content": content,
        "metadata": metadata,
        "document_id": metadata["document_id"],
        "document_type": metadata["document_type"],
        "product_id": "S-101",
        "standard_type": "S-101",
        "title": metadata["title"],
        "section": metadata["section"],
        "version": metadata["version"],
        "language": metadata["language"],
        "keywords": keywords_from_text(content, [metadata["document_type"], metadata["section"]]),
        "related_features": metadata["related_features"],
        "related_concepts": metadata["related_concepts"],
        "clearance_level": "PUBLIC",
        "source_file": metadata["source_file"],
        "source_url": None,
        "page_no": None,
        "source_id": source_id,
        "source_sha256": metadata["source_sha256"],
    }


def load_catalogue_chunks(path: Path) -> list[dict[str, Any]]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    meta = parsed.get("metadata", {})
    source_file = meta.get("source", str(path))
    source_sha = meta.get("sha256") or sha256_file(path)
    version = meta.get("versionNumber") or "2.0.0"
    rows: list[dict[str, Any]] = []

    for feature in parsed.get("features", []):
        code = clean_text(feature.get("code"))
        name = clean_text(feature.get("name"))
        definition = clean_text(feature.get("definition"))
        aliases = [clean_text(x) for x in feature.get("aliases", []) if clean_text(x)]
        primitives = [clean_text(x) for x in feature.get("permitted_primitives", []) if clean_text(x)]
        bindings = feature.get("bindings", [])
        binding_text = ", ".join(sorted({clean_text(b.get("ref")) for b in bindings if clean_text(b.get("ref"))})[:40])
        content = (
            f"S-101 Feature Catalogue feature definition. Feature code: {code}. "
            f"Feature name: {name}. Definition: {definition}. "
            f"Aliases: {', '.join(aliases) if aliases else 'none'}. "
            f"Permitted primitives: {', '.join(primitives) if primitives else 'not specified'}. "
            f"Attribute/information bindings: {binding_text if binding_text else 'not parsed from XML'}."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_feature", f"{code}|{name}|{definition}"),
            content=content,
            metadata={
                "document_type": "feature_catalogue",
                "title": "S-101 Feature Catalogue 2.0.0",
                "section": f"feature:{code or name}",
                "version": version,
                "source_file": source_file,
                "source_id": SOURCE_IDS["feature_catalogue"],
                "source_sha256": source_sha,
                "feature_code": code,
                "feature_name": name,
                "aliases": aliases,
                "permitted_primitives": primitives,
            },
            related_features=[name or code],
            related_concepts=["feature_definition"],
        ))

    for attr in parsed.get("attributes", []):
        code = clean_text(attr.get("code"))
        name = clean_text(attr.get("name"))
        definition = clean_text(attr.get("definition"))
        aliases = [clean_text(x) for x in attr.get("alias", []) if clean_text(x)]
        listed_values = [
            f"{clean_text(v.get('value'))}={clean_text(v.get('label'))}"
            for v in attr.get("listed_values", [])
            if clean_text(v.get("value")) or clean_text(v.get("label"))
        ]
        content = (
            f"S-101 Feature Catalogue attribute description. Attribute code: {code}. "
            f"Attribute name: {name}. Definition: {definition}. "
            f"Value type: {clean_text(attr.get('value_type')) or 'not specified'}. "
            f"Unit of measure: {clean_text(attr.get('uom')) or 'not specified'}. "
            f"Aliases: {', '.join(aliases) if aliases else 'none'}. "
            f"Listed values: {', '.join(listed_values[:80]) if listed_values else 'none'}."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_attribute", f"{code}|{name}|{definition}"),
            content=content,
            metadata={
                "document_type": "attribute_catalogue",
                "title": "S-101 Feature Catalogue 2.0.0",
                "section": f"attribute:{code or name}",
                "version": version,
                "source_file": source_file,
                "source_id": SOURCE_IDS["attribute_catalogue"],
                "source_sha256": source_sha,
                "attribute_code": code,
                "attribute_name": name,
                "value_type": clean_text(attr.get("value_type")),
                "aliases": aliases,
            },
            related_concepts=["attribute_description"],
        ))

    return rows


def connect(database_url: str):
    import psycopg2

    return psycopg2.connect(database_url)


def fetch_db_chunks(database_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    db_sha_seed: list[str] = []
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT feature_type_code,
                       COUNT(*) AS feature_count,
                       COUNT(geometry) AS geometry_count,
                       COALESCE(string_agg(DISTINCT GeometryType(geometry), ', '), '') AS geometry_types
                FROM projection.s101_feature_current
                GROUP BY feature_type_code
                ORDER BY feature_type_code
            """)
            feature_profiles = cur.fetchall()

            cur.execute("""
                SELECT fr.nftc,
                       fav.natc,
                       COUNT(*) AS value_count,
                       array_agg(DISTINCT left(fav.value_text, 160)) FILTER (
                           WHERE fav.value_text IS NOT NULL
                             AND fav.value_text !~ '^[0-9. ()+-]+$'
                       ) AS text_samples
                FROM canonical.feature_record fr
                JOIN canonical.feature_attribute_value fav
                  ON fav.feature_record_id = fr.feature_record_id
                GROUP BY fr.nftc, fav.natc
                ORDER BY fr.nftc, fav.natc
            """)
            attr_profiles = cur.fetchall()

            cur.execute("""
                SELECT fav.natc,
                       COUNT(*) AS value_count,
                       array_agg(DISTINCT left(fav.value_text, 180)) FILTER (
                           WHERE fav.value_text IS NOT NULL
                             AND fav.value_text !~ '^[0-9. ()+-]+$'
                       ) AS text_samples
                FROM canonical.feature_attribute_value fav
                GROUP BY fav.natc
                ORDER BY fav.natc
            """)
            text_value_profiles = cur.fetchall()

    attrs_by_nftc: dict[int, list[str]] = {}
    for nftc, natc, value_count, samples in attr_profiles:
        sample_values = [clean_text(x) for x in (samples or []) if clean_text(x)]
        text = f"NATC {natc}: {value_count} values"
        if sample_values:
            text += f"; text samples: {', '.join(sample_values[:12])}"
        attrs_by_nftc.setdefault(nftc, []).append(text)

    profile_count = 0
    for feature_type_code, feature_count, geometry_count, geometry_types in feature_profiles:
        attr_text = ". ".join(attrs_by_nftc.get(feature_type_code, [])[:80])
        content = (
            f"S100_dev S-101 database feature profile. DB feature_type_code/NFTC: {feature_type_code}. "
            f"Feature instance count: {feature_count}. Geometry count: {geometry_count}. "
            f"Geometry types: {geometry_types or 'none'}. "
            f"Observed DB attribute profile: {attr_text if attr_text else 'no attribute values observed'}."
        )
        db_sha_seed.append(content)
        rows.append(chunk_row(
            chunk_id=stable_id("s101_db_feature", content),
            content=content,
            metadata={
                "document_type": "s101_db_feature_profile",
                "title": "S100_dev S-101 DB Feature Profile",
                "section": f"feature_type_code:{feature_type_code}",
                "version": "2.0.0",
                "source_file": "S100_dev/projection.s101_feature_current + canonical.feature_attribute_value",
                "source_id": SOURCE_IDS["db_feature_profile"],
                "source_sha256": "pending",
                "feature_type_code": feature_type_code,
                "feature_count": feature_count,
                "geometry_count": geometry_count,
                "geometry_types": geometry_types,
            },
            related_concepts=["s100_dev_db_profile"],
        ))
        profile_count += 1

    for natc, value_count, samples in text_value_profiles:
        sample_values = [clean_text(x) for x in (samples or []) if clean_text(x)]
        if not sample_values:
            continue
        content = (
            f"S100_dev S-101 database textual attribute values. NATC: {natc}. "
            f"Observed value count: {value_count}. Distinct text samples: {', '.join(sample_values[:120])}."
        )
        db_sha_seed.append(content)
        rows.append(chunk_row(
            chunk_id=stable_id("s101_db_attr_text", content),
            content=content,
            metadata={
                "document_type": "s101_db_text_values",
                "title": "S100_dev S-101 DB Text Attribute Values",
                "section": f"natc:{natc}",
                "version": "2.0.0",
                "source_file": "S100_dev/canonical.feature_attribute_value",
                "source_id": SOURCE_IDS["db_text_values"],
                "source_sha256": "pending",
                "natc": natc,
                "value_count": value_count,
            },
            related_concepts=["s100_dev_db_text_values"],
        ))

    db_sha = hashlib.sha256("\n".join(db_sha_seed).encode("utf-8")).hexdigest()
    for row in rows:
        row["source_sha256"] = db_sha
        row["metadata"]["source_sha256"] = db_sha
    print(f"db_profiles={profile_count} db_text_value_chunks={len(rows) - profile_count}")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_existing_embeddings(output: Path) -> dict[str, dict[str, Any]]:
    if not output.exists():
        return {}
    existing: dict[str, dict[str, Any]] = {}
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("chunk_id") and row.get("embedding"):
            existing[row["chunk_id"]] = row
    return existing


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def embed_rows(rows: list[dict[str, Any]], output: Path, resume: bool = True) -> list[dict[str, Any]]:
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    endpoint = os.getenv(
        "OLLAMA_EMBEDDING_URL",
        os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/embed",
    )
    timeout = int(os.getenv("EMBEDDING_TIMEOUT_SEC", "600"))
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "4"))
    existing = load_existing_embeddings(output) if resume else {}
    if output.exists() and not resume:
        output.unlink()
    embedded: list[dict[str, Any]] = [existing[row["chunk_id"]] for row in rows if row["chunk_id"] in existing]
    pending = [row for row in rows if row["chunk_id"] not in existing]
    print(f"embedding_resume existing={len(embedded)} pending={len(pending)} total={len(rows)}")
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        body = json.dumps({"model": model, "input": [row["content"] for row in batch]}).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            vectors = json.load(response)["embeddings"]
        batch_embedded: list[dict[str, Any]] = []
        for row, vector in zip(batch, vectors):
            item = dict(row)
            item["embedding"] = vector
            item["model"] = model
            item["dimension"] = len(vector)
            batch_embedded.append(item)
        append_jsonl(output, batch_embedded)
        embedded.extend(batch_embedded)
        print(f"embedded={len(embedded)}/{len(rows)}")
    return embedded


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
            embedding vector({dimension}),
            created_at TIMESTAMP DEFAULT NOW(),
            source_id TEXT,
            source_sha256 TEXT
        )
    """)


def db_values(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["chunk_id"],
        row["document_id"],
        row["document_type"],
        row["product_id"],
        row["standard_type"],
        row["title"],
        row["section"],
        row["version"],
        row["language"],
        row["content"],
        row["keywords"],
        row["related_features"],
        row["related_concepts"],
        row["clearance_level"],
        row["source_file"],
        row["source_url"],
        row["page_no"],
        json.dumps(row["metadata"], ensure_ascii=False),
        "[" + ",".join(str(float(x)) for x in row["embedding"]) + "]",
        row["source_id"],
        row["source_sha256"],
    )


def upsert_rows(database_url: str, rows: list[dict[str, Any]], replace_source: bool) -> dict[str, Any]:
    if not rows:
        raise RuntimeError("no embedded rows to upsert")
    dimensions = {len(row["embedding"]) for row in rows}
    if len(dimensions) != 1:
        raise RuntimeError(f"embedding dimension mismatch: {sorted(dimensions)}")
    source_ids = sorted({row["source_id"] for row in rows})
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            ensure_table(cur, next(iter(dimensions)))
            if replace_source:
                cur.execute("DELETE FROM knowledge.document_chunks WHERE source_id = ANY(%s)", (source_ids,))
            from psycopg2.extras import execute_batch

            execute_batch(cur, """
                INSERT INTO knowledge.document_chunks
                    (chunk_id, document_id, document_type, product_id, standard_type, title, section, version,
                     language, content, keywords, related_features, related_concepts, clearance_level, source_file,
                     source_url, page_no, metadata, embedding, source_id, source_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s,%s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    document_type=EXCLUDED.document_type,
                    title=EXCLUDED.title,
                    section=EXCLUDED.section,
                    content=EXCLUDED.content,
                    keywords=EXCLUDED.keywords,
                    related_features=EXCLUDED.related_features,
                    related_concepts=EXCLUDED.related_concepts,
                    metadata=EXCLUDED.metadata,
                    embedding=EXCLUDED.embedding,
                    source_id=EXCLUDED.source_id,
                    source_sha256=EXCLUDED.source_sha256
            """, [db_values(row) for row in rows], page_size=100)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_metadata ON knowledge.document_chunks USING GIN (metadata)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_embedding ON knowledge.document_chunks USING hnsw (embedding vector_cosine_ops)")
            cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL) FROM knowledge.document_chunks")
            total_count, null_embeddings = cur.fetchone()
            cur.execute(
                "SELECT document_type, COUNT(*) FROM knowledge.document_chunks WHERE source_id = ANY(%s) GROUP BY document_type ORDER BY document_type",
                (source_ids,),
            )
            inserted_by_type = dict(cur.fetchall())
    return {
        "total_document_chunks": total_count,
        "null_embeddings": null_embeddings,
        "source_ids": source_ids,
        "inserted_by_type": inserted_by_type,
        "inserted_count": sum(inserted_by_type.values()),
    }


def write_report(path: Path, chunks: list[dict[str, Any]], embedded: list[dict[str, Any]], db_result: dict[str, Any] | None) -> None:
    counts: dict[str, int] = {}
    for row in chunks:
        counts[row["document_type"]] = counts.get(row["document_type"], 0) + 1
    lines = [
        "# S-101 Catalogue and S100_dev DB RAG Build Report",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- chunk_count: `{len(chunks)}`",
        f"- embedded_count: `{len(embedded)}`",
        f"- output_chunks: `{DEFAULT_CHUNKS.relative_to(ROOT)}`",
        f"- output_embeddings: `{DEFAULT_EMBEDDINGS.relative_to(ROOT)}`" if embedded else "- output_embeddings: `not generated`",
        "",
        "## Chunk Counts",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(counts.items()))
    if db_result:
        lines += [
            "",
            "## DB Upsert",
            "",
            f"- inserted_or_replaced_count: `{db_result['inserted_count']}`",
            f"- total_document_chunks: `{db_result['total_document_chunks']}`",
            f"- null_embeddings: `{db_result['null_embeddings']}`",
            f"- source_ids: `{', '.join(db_result['source_ids'])}`",
            f"- inserted_by_type: `{json.dumps(db_result['inserted_by_type'], ensure_ascii=False)}`",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--chunks-output", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--embeddings-output", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--database-url", default=os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL"))
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--upsert", action="store_true")
    parser.add_argument("--replace-source", action="store_true")
    args = parser.parse_args()

    chunks = load_catalogue_chunks(args.catalogue)
    if args.database_url:
        chunks.extend(fetch_db_chunks(args.database_url))
    else:
        print("database_url_missing=true; only XML catalogue chunks will be generated")
    chunks = sorted({row["chunk_id"]: row for row in chunks}.values(), key=lambda row: row["chunk_id"])
    write_jsonl(args.chunks_output, chunks)

    embedded: list[dict[str, Any]] = []
    db_result = None
    if args.embed:
        embedded = embed_rows(chunks, args.embeddings_output)
    if args.upsert:
        if not embedded:
            if not args.embeddings_output.exists():
                raise RuntimeError("--upsert requires --embed or an existing embeddings output")
            embedded = [json.loads(line) for line in args.embeddings_output.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not args.database_url:
            raise RuntimeError("--upsert requires --database-url, S101_DB_URL, or POSTGIS_URL")
        db_result = upsert_rows(args.database_url, embedded, args.replace_source)

    write_report(args.report_output, chunks, embedded, db_result)
    print(json.dumps({"chunks": len(chunks), "embedded": len(embedded), "db_result": db_result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
