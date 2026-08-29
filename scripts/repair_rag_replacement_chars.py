"""Remove undecodable PDF replacement glyphs from generated RAG text."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
changed = 0
for path in (ROOT / "outputs/rag").glob("*_chunks.jsonl"):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        count = row.get("text", "").count("\ufffd")
        if count:
            row["text"] = row["text"].replace("\ufffd", " ")
            row.setdefault("metadata", {})["text_normalization"] = "U+FFFD replaced with whitespace; source provenance retained"
            changed += count
        rows.append(row)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
print(json.dumps({"replacement_chars_removed": changed}, ensure_ascii=False))
