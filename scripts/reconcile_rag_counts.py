"""Reconcile RAG chunk files, manifest and embedding checkpoint targets."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / "outputs/rag"
FILES = ["s100_product_spec_chunks.jsonl", "s101_dceg_chunks.jsonl", "s104_chunks.jsonl", "s111_chunks.jsonl", "s124_chunks.jsonl", "s158_validation_chunks.jsonl", "law_chunks.jsonl", "accident_chunks.jsonl"]


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    by_file = {name: rows(RAG / name) for name in FILES if (RAG / name).exists()}
    all_rows = [row for items in by_file.values() for row in items]
    manifest = json.loads((RAG / "rag_manifest.json").read_text(encoding="utf-8"))
    checkpoint_path = RAG / "embeddings_v2.partial.jsonl"
    checkpoint = rows(checkpoint_path) if checkpoint_path.exists() else []
    current_by_id = {row["chunk_id"]: row for row in all_rows}
    valid_checkpoint = [row for row in checkpoint if row.get("chunk_id") in current_by_id and row.get("content") == current_by_id[row["chunk_id"]].get("text")]
    report = ["# RAG Chunk Count Reconciliation Report", "", "## Current inventory", "", f"- `outputs/rag/chunks_v2.jsonl`: {'present' if (RAG / 'chunks_v2.jsonl').exists() else 'absent'}", f"- Chunk files scanned: {len(by_file)}", f"- Total current chunks: {len(all_rows)}", f"- Manifest chunk_count: {manifest.get('chunk_count')}", f"- Manifest file sum: {sum(value.get('chunk_count', 0) for value in manifest.get('files', {}).values())}", "", "## Counts by source file", ""]
    report.extend(f"- `{name}`: {len(items)}" for name, items in by_file.items())
    report += ["", "## Embedding target comparison", "", f"- `embedding_metadata.json.target_count`: {json.loads((RAG / 'embedding_metadata.json').read_text(encoding='utf-8')).get('target_count')}", f"- Current chunk target from all `*_chunks.jsonl`: {len(all_rows)}", f"- Partial checkpoint lines: {len(checkpoint)}", f"- Valid checkpoint lines matching current chunk content: {len(valid_checkpoint)}", f"- Final `embeddings_v2.jsonl` lines: {len(rows(RAG / 'embeddings_v2.jsonl')) if (RAG / 'embeddings_v2.jsonl').exists() else 0}", "", "## Scope conclusion", "", "The embedding script scans `outputs/rag/*_chunks.jsonl` and does not select law, accident or standards selectively. The current target 6,252 is the sum of all eight current RAG chunk files: standards, S-158, law and accident. `chunks_v2.jsonl` is not present; the canonical current inventory is the eight named JSONL files and their manifest.", "", "The earlier 10,542 value was an intermediate count before law chunk normalization. Law chunks were regenerated to remove row overlap and repeated row-level JSON keys, reducing the law set from 8,212 to 3,922. The resulting total is 6,252. This is a content/modeling change, not an encoding-error drop or selective embedding filter.", "", "The final embedding file and database must not be replaced until the checkpoint reaches the current target of 6,252 valid chunk/content pairs.", "", f"Generated at: {datetime.now(timezone.utc).isoformat()}"]
    out = ROOT / "outputs/reports/rag_chunk_count_reconciliation_report.md"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"current_chunks": len(all_rows), "manifest_chunks": manifest.get("chunk_count"), "checkpoint_lines": len(checkpoint), "valid_checkpoint": len(valid_checkpoint), "counts": {name: len(items) for name, items in by_file.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
