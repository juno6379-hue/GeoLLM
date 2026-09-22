from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.framework import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=Path, default=Path("training/generated/seed_cases.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("training"))
    args = parser.parse_args()
    report = run(args.seeds, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return bool(report["validation_errors"] or report["leakage_issues"])


if __name__ == "__main__":
    raise SystemExit(main())
