from __future__ import annotations

import argparse
from pathlib import Path

from training.pipeline import derive_views, read_jsonl, validate_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cases, errors = validate_rows(read_jsonl(args.input))
    if errors:
        print("\n".join(errors))
        return 1
    derive_views(cases, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
