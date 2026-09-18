#!/usr/bin/env python
"""Verify the GeoLLM UI preset queries against the local task SSE API."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "benchmark" / "geollm_ui_preset_cases_v1.jsonl"
DEFAULT_OUTPUT = ROOT / "outputs" / "learning" / "geollm_ui_preset_verification.json"


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return cases


def stream_events(base_url: str, query: str, timeout: float) -> tuple[list[dict[str, Any]], int]:
    payload = {
        "query": query,
        "organization_id": "preset-verification",
        "user_id": "preset-verifier",
        "task_id": f"preset-{uuid.uuid4().hex[:12]}",
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        base_url.rstrip("/") + "/api/v1/tasks/stream",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    events: list[dict[str, Any]] = []
    lines: list[str] = []
    started = time.time()
    with request.urlopen(req, timeout=timeout) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                if lines:
                    text = "\n".join(lines)
                    try:
                        event = json.loads(text)
                    except json.JSONDecodeError:
                        event = {"event": "parse_error", "raw": text}
                    events.append(event)
                    lines = []
                    if event.get("event") in {"completed", "error"}:
                        break
                continue
            if line.startswith("data: "):
                lines.append(line[6:])
    return events, int((time.time() - started) * 1000)


def wait_for_health(base_url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with request.urlopen(base_url.rstrip("/") + "/health", timeout=3) as resp:
                if resp.status == 200:
                    return
        except (OSError, error.URLError) as exc:
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"health check did not pass within {timeout:g}s: {last_error}")


def final_event(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in reversed(events):
        if event.get("event") == "completed":
            return event
    return {}


def node_names(events: list[dict[str, Any]]) -> list[str]:
    return [str(event.get("node")) for event in events if event.get("event") == "node_finished" and event.get("node")]


def evaluate(case: dict[str, Any], events: list[dict[str, Any]], elapsed_ms: int) -> dict[str, Any]:
    final = final_event(events)
    final_result = final.get("final_result") if isinstance(final.get("final_result"), dict) else {}
    result_status = str(final_result.get("status") or final.get("status") or "NOT_COMPLETED")
    serialized = json.dumps({"events": events, "final": final, "final_result": final_result}, ensure_ascii=False, default=str)
    nodes = node_names(events)

    failures: list[str] = []
    if final.get("event") != "completed":
        failures.append("not_completed")
    if case.get("expected_status") and result_status not in case["expected_status"]:
        failures.append(f"status:{result_status}")
    for node in case.get("expected_nodes") or []:
        if node not in nodes:
            failures.append(f"missing_node:{node}")
    for node in case.get("forbidden_nodes") or []:
        if node in nodes:
            failures.append(f"forbidden_node:{node}")
    for needle in case.get("expected_text") or []:
        if needle not in serialized:
            failures.append(f"missing_text:{needle}")
    for needle in case.get("forbidden_text") or []:
        if needle and needle in serialized:
            failures.append(f"forbidden_text:{needle[:60]}")
    if case.get("max_elapsed_ms") and elapsed_ms > int(case["max_elapsed_ms"]):
        failures.append(f"slow:{elapsed_ms}ms")

    return {
        "case_id": case["case_id"],
        "query": case["query"],
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "elapsed_ms": elapsed_ms,
        "status": result_status,
        "nodes": nodes,
        "summary": final_result.get("summary") or final_result.get("answer_text"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--health-timeout", type=float, default=90.0)
    args = parser.parse_args()

    wait_for_health(args.base_url, args.health_timeout)

    results: list[dict[str, Any]] = []
    cases = load_cases(args.cases)

    def write_summary() -> dict[str, Any]:
        summary = {
            "total": len(results),
            "planned_total": len(cases),
            "passed": sum(1 for row in results if row["verdict"] == "PASS"),
            "failed": sum(1 for row in results if row["verdict"] != "PASS"),
            "results": results,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return summary

    for case in cases:
        try:
            events, elapsed_ms = stream_events(args.base_url, case["query"], args.timeout)
            result = evaluate(case, events, elapsed_ms)
        except Exception as exc:
            result = {
                "case_id": case["case_id"],
                "query": case["query"],
                "verdict": "FAIL",
                "failures": [f"exception:{type(exc).__name__}:{exc}"],
                "elapsed_ms": None,
                "status": "ERROR",
                "nodes": [],
                "summary": None,
            }
        results.append(result)
        print(f"{result['verdict']:4} {result['case_id']} {result['status']} {result['elapsed_ms']}ms", flush=True)
        if result["failures"]:
            print("     " + "; ".join(result["failures"]), flush=True)
        write_summary()

    summary = write_summary()
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
