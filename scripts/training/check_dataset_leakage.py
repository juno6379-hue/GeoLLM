from __future__ import annotations

import argparse
import difflib
from pathlib import Path

from training.pipeline import canonical_query, read_jsonl


def query(row):
    return row.get("query") or row.get("input", {}).get("user_query", "")


def family(row):
    return row.get("seed_family_id") or row.get("lineage", {}).get("parent_seed_id") or row.get("case_id")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("train", type=Path)
    parser.add_argument("holdout", type=Path)
    parser.add_argument("--threshold", type=float, default=0.92)
    args = parser.parse_args()
    train, holdout = read_jsonl(args.train), read_jsonl(args.holdout)
    issues = []
    holdout_families = {family(row) for row in holdout}
    for left in train:
        if family(left) in holdout_families:
            issues.append(f"family leakage: {left.get('case_id')}")
        lq = canonical_query(query(left))
        for right in holdout:
            rq = canonical_query(query(right))
            ratio = difflib.SequenceMatcher(None, lq, rq).ratio()
            if lq == rq or ratio >= args.threshold:
                issues.append(f"query leakage: {left.get('case_id')} <-> {right.get('case_id')} ({ratio:.3f})")
    print("\n".join(issues) if issues else "leakage=0")
    return bool(issues)


if __name__ == "__main__":
    raise SystemExit(main())
