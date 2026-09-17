"""Repair query quality JSONL by quarantining malformed lines as JSON records."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path


def repair(path: Path) -> dict:
    timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = path.with_name(f"{path.stem}.invalid_backup_{timestamp}{path.suffix}")
    shutil.copy2(path, backup)

    fixed: list[str] = []
    bad = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
            fixed.append(line)
        except Exception as exc:
            bad += 1
            fixed.append(
                json.dumps(
                    {
                        "timestamp": dt.datetime.now().isoformat(),
                        "task_id": None,
                        "query": None,
                        "issue_type": "jsonl_corrupt_line_quarantined",
                        "severity": "high",
                        "route_plan": {},
                        "quality_metrics": {},
                        "evidence_summary": {},
                        "details": {
                            "source_file": str(path),
                            "source_line_number": line_no,
                            "parse_error": str(exc),
                            "raw_line": line,
                        },
                        "status": "pending_review",
                    },
                    ensure_ascii=False,
                    default=str,
                )
            )
    path.write_text("\n".join(fixed) + "\n", encoding="utf-8")
    return {"path": str(path), "backup": str(backup), "lines": len(fixed), "bad_quarantined": bad}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/feedback/query_quality_issues.jsonl")
    args = parser.parse_args()
    print(json.dumps(repair(Path(args.path)), ensure_ascii=False))


if __name__ == "__main__":
    main()
