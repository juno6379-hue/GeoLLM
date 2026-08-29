"""Repair RAG source previews and regenerate embeddings."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "outputs/rag"


def decode_best(raw: bytes):
    candidates = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            value = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        replacement_count = value.count("\ufffd")
        hangul_count = sum(1 for char in value if 0xAC00 <= ord(char) <= 0xD7A3)
        score = hangul_count - replacement_count * 10000
        candidates.append((score, encoding, value))
    if not candidates:
        return raw.decode("utf-8", errors="replace"), "utf-8-replace"
    _, encoding, value = max(candidates, key=lambda item: item[0])
    return value, encoding


def repair_chunks():
    groups = {}
    for path in sorted(OUT.glob("*_chunks.jsonl")):
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            row = json.loads(line)
            metadata = row.get("metadata", {})
            source = DATASET / metadata.get("source_path", "")
            if metadata.get("extraction_status") == "metadata_only" and source.suffix.lower() == ".csv" and source.exists():
                raw = source.read_bytes()
                text, encoding = decode_best(raw)
                row["text"] = text[:4000]
                metadata["extraction_status"] = "text_preview"
                metadata["encoding"] = encoding
                metadata.setdefault("provenance", {})["content_sha256"] = hashlib.sha256(raw).hexdigest()
            rows.append(row)
        groups[path.name] = rows
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return groups


def build_embedding_rows(groups):
    rows = []
    for filename in sorted(groups):
        for original in groups[filename]:
            content = original.get("text", "")
            row = dict(original)
            row["text"] = content
            rows.append(row)
    return rows


def embed(rows):
    endpoint = os.getenv(
        "OLLAMA_EMBEDDING_URL",
        os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/embed",
    )
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    timeout_sec = int(os.getenv("EMBEDDING_TIMEOUT_SEC", "180"))
    split_chars = int(os.getenv("EMBEDDING_SPLIT_CHARS", "1800"))
    resume = os.getenv("EMBEDDING_RESUME", "true").lower() in {"1", "true", "yes", "y"}
    def request_texts(texts):
        body = json.dumps({"model": model, "input": texts}).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout_sec) as response:
                return json.load(response)["embeddings"]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Ollama embedding HTTP {exc.code}: {detail}") from exc

    def average_vectors(vectors):
        return [sum(values) / len(values) for values in zip(*vectors)]

    def request_batch(batch):
        try:
            return request_texts([row["text"] for row in batch])
        except RuntimeError as exc:
            if len(batch) > 1:
                # Reduce a rejected batch to isolate an oversized or invalid input.
                vectors = []
                for row in batch:
                    vectors.extend(request_batch([row]))
                return vectors
            row = batch[0]
            text = row["text"]
            parts = [text[start:start + split_chars] for start in range(0, len(text), split_chars)]
            if len(parts) <= 1:
                raise RuntimeError(f"Ollama rejected chunk {row['chunk_id']}: {exc}") from exc
            part_vectors = request_texts(parts)
            if len(part_vectors) != len(parts):
                raise RuntimeError(f"Split embedding count mismatch for chunk {row['chunk_id']}")
            return [average_vectors(part_vectors)]

    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
    batches = [rows[start:start + batch_size] for start in range(0, len(rows), batch_size)]
    partial = OUT / "embeddings_v2.partial.jsonl"
    checkpoint_path = OUT / "embedding_checkpoint.json"
    report_path = ROOT / "outputs/reports/embedding_v2_report.md"
    completed = {}
    row_by_id = {row["chunk_id"]: row for row in rows}
    if resume and partial.exists():
        for line in partial.read_text(encoding="utf-8").splitlines():
            if line:
                item = json.loads(line)
                current = row_by_id.get(item.get("chunk_id"))
                if current and item.get("content") == current.get("text"):
                    completed[item["chunk_id"]] = item
    total = len(rows)
    def write_progress(status, dimension=None):
        progress = {"status": status, "model": model, "dimension": dimension, "completed": len(completed), "target": total, "remaining": total - len(completed), "batch_size": batch_size, "split_chars": split_chars, "timeout_sec": timeout_sec, "resume": resume, "concurrency": 1, "partial_output": "outputs/rag/embeddings_v2.partial.jsonl"}
        checkpoint_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Embedding v2 Report\n\n" + "\n".join(f"- {key}: {value}" for key, value in progress.items()) + "\n", encoding="utf-8")
        (OUT / "embedding_metadata.json").write_text(json.dumps({"status": status, "model": model, "dimension": dimension, "count": len(completed), "target_count": total, "checkpoint": "outputs/rag/embeddings_v2.partial.jsonl", "timeout_sec": timeout_sec, "resume": resume, "concurrency": 1}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_progress("running")
    for index, batch in enumerate(batches, 1):
        pending = [row for row in batch if row["chunk_id"] not in completed]
        if pending:
            batch_vectors = request_batch(pending)
            if len(batch_vectors) != len(pending):
                raise RuntimeError(f"Embedding count mismatch in batch {index}: expected {len(pending)}, received {len(batch_vectors)}")
            with partial.open("a", encoding="utf-8") as stream:
                for row, vector in zip(pending, batch_vectors):
                    item = {"chunk_id": row["chunk_id"], "content": row["text"], "metadata": row["metadata"], "embedding": vector, "model": model, "dimension": len(vector), "source_sha256": row["metadata"]["source_sha256"]}
                    stream.write(json.dumps(item, ensure_ascii=False) + "\n")
                    completed[item["chunk_id"]] = item
                stream.flush()
        write_progress("running", len(next(iter(completed.values()))["embedding"]) if completed else None)
        print(f"embedded={len(completed)}/{total}", flush=True)
    if len(completed) != total:
        raise RuntimeError(f"Checkpoint has {len(completed)} embeddings, expected {total}")
    ordered = [completed[row["chunk_id"]] for row in rows]
    dimension = len(ordered[0]["embedding"]) if ordered else 0
    output = OUT / "embeddings_v2.jsonl"
    output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8")
    write_progress("completed", dimension)
    (OUT / "embedding_metadata.json").write_text(json.dumps({"status": "completed", "model": model, "dimension": dimension, "count": len(ordered), "encoding_repaired": True, "output": "outputs/rag/embeddings_v2.jsonl", "checkpoint": "outputs/rag/embeddings_v2.partial.jsonl", "endpoint_type": "ollama", "timeout_sec": timeout_sec, "resume": resume, "concurrency": 1}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dimension


def main():
    groups = repair_chunks()
    rows = build_embedding_rows(groups)
    dimension = embed(rows)
    with (OUT / "document_chunks_load.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["chunk_id", "content", "metadata", "source_id", "source_sha256"])
        for row in rows:
            metadata = row["metadata"]
            writer.writerow([row["chunk_id"], row["text"], json.dumps(metadata, ensure_ascii=False), metadata["source_id"], metadata["source_sha256"]])
    print(json.dumps({"source_files": len(groups), "embedding_rows": len(rows), "dimension": dimension}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed", action="store_true", help="Generate or resume embeddings")
    parser.parse_args()
    main()
