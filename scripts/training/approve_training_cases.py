from __future__ import annotations

import argparse
from pathlib import Path

from training.pipeline import read_jsonl, validate_rows, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicit human approval gate; never changes registry or ontology state")
    parser.add_argument("candidates", type=Path)
    parser.add_argument("master", type=Path)
    parser.add_argument("--case-id", action="append", required=True)
    parser.add_argument("--reviewer", required=True)
    args = parser.parse_args()
    selected = []
    for row in read_jsonl(args.candidates):
        if row.get("case_id") in args.case_id:
            row["review_status"] = "APPROVED"
            row.setdefault("quality", {})["human_verified"] = True
            row["quality"]["reviewer"] = args.reviewer
            selected.append(row)
    _, errors = validate_rows(selected)
    if errors:
        print("\n".join(errors))
        return 1
    existing = read_jsonl(args.master) if args.master.exists() else []
    write_jsonl(args.master, [*existing, *selected])
    print(f"approved={len(selected)} reviewer={args.reviewer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
