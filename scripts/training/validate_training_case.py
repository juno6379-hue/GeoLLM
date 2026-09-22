from __future__ import annotations

import argparse
from pathlib import Path

from training.pipeline import read_jsonl, validate_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--holdout", action="append", type=Path, default=[])
    args = parser.parse_args()
    cases, errors = validate_rows(read_jsonl(args.input), args.holdout)
    for error in errors:
        print(error)
    print(f"valid={len(cases)} errors={len(errors)}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
