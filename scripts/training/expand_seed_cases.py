from __future__ import annotations

import argparse
from pathlib import Path

from training.pipeline import dry_run, read_jsonl, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic dry-run adapter for the seed expansion prompt")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    seeds = read_jsonl(args.input)
    approved = [row for row in seeds if row.get("review_status") == "APPROVED"][: args.limit]
    candidates = [candidate for seed in approved for candidate in dry_run(seed)]
    write_jsonl(args.output, candidates)
    print(f"approved_seeds={len(approved)} candidates={len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
