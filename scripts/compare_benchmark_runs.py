#!/usr/bin/env python
"""Compare two Marine GeoLLM benchmark metric files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/learning/regression_report.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = _load(args.baseline)
    candidate = _load(args.candidate)
    base_counts = baseline.get("counts", {})
    cand_counts = candidate.get("counts", {})
    base_pass = float(baseline.get("pass_rate", 0.0))
    cand_pass = float(candidate.get("pass_rate", 0.0))
    regression = cand_pass < base_pass

    lines = [
        "# Benchmark Regression Report",
        "",
        f"Baseline total: {baseline.get('total')}",
        f"Candidate total: {candidate.get('total')}",
        "",
        f"Baseline pass rate: {base_pass:.3f}",
        f"Candidate pass rate: {cand_pass:.3f}",
        f"Regression: {'YES' if regression else 'NO'}",
        "",
        "## Counts",
        "",
        "| Verdict | Baseline | Candidate |",
        "| --- | ---: | ---: |",
    ]
    for key in sorted(set(base_counts) | set(cand_counts)):
        lines.append(f"| {key} | {base_counts.get(key, 0)} | {cand_counts.get(key, 0)} |")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"regression": regression, "baseline_pass_rate": base_pass, "candidate_pass_rate": cand_pass}, indent=2))
    return 1 if regression else 0


if __name__ == "__main__":
    raise SystemExit(main())

