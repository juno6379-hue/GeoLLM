#!/usr/bin/env python
"""Run Marine GeoLLM benchmark cases and write structured results.

The runner has two execution modes:

* api: calls POST /api/v1/tasks/stream and validates public API parameter flow.
* graph: invokes the local LangGraph orchestrator directly for faster regression checks.

LLM judging is optional and advisory. Deterministic trace checks remain authoritative.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "benchmark" / "benchmark_cases_v1.jsonl"
DEFAULT_OUTPUT = ROOT / "outputs" / "learning" / "benchmark_results.jsonl"
DEFAULT_METRICS = ROOT / "outputs" / "learning" / "baseline_metrics.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def _json_post(url: str, payload: dict[str, Any], timeout: float) -> bytes:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _parse_sse(raw: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in raw.split("\n\n"):
        lines = [line for line in block.splitlines() if line.startswith("data: ")]
        if not lines:
            continue
        data = "\n".join(line[6:] for line in lines)
        try:
            events.append(json.loads(data))
        except json.JSONDecodeError:
            events.append({"event": "parse_error", "raw": data})
    return events


def _stream_sse(url: str, payload: dict[str, Any], timeout: float) -> list[dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    events: list[dict[str, Any]] = []
    data_lines: list[str] = []
    with request.urlopen(req, timeout=timeout) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                if data_lines:
                    event_data = "\n".join(data_lines)
                    try:
                        event = json.loads(event_data)
                    except json.JSONDecodeError:
                        event = {"event": "parse_error", "raw": event_data}
                    events.append(event)
                    data_lines = []
                    if event.get("event") in {"completed", "error"}:
                        break
                continue
            if line.startswith("data: "):
                data_lines.append(line[6:])
    return events


def _make_api_payload(case: dict[str, Any], task_id: str) -> dict[str, Any]:
    api_request = dict(case.get("api_request") or {})
    payload = {
        "query": case["query"],
        "organization_id": api_request.get("organization_id", "benchmark"),
        "user_id": api_request.get("user_id", "benchmark-runner"),
        "task_id": api_request.get("task_id", task_id),
    }
    if api_request.get("spatial_context") is not None:
        payload["spatial_context"] = api_request.get("spatial_context")
    return payload


def _extract_final(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in reversed(events):
        if event.get("event") == "completed":
            return event
    return {}


def _extract_last_task_plan(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in reversed(events):
        if isinstance(event.get("task_plan"), dict):
            return event["task_plan"]
    final = _extract_final(events)
    final_result = final.get("final_result") or {}
    orch = final_result.get("orchestrator_v2") or {}
    route_plan = orch.get("route_plan") or {}
    return route_plan if isinstance(route_plan, dict) else {}


def _extract_qec(final_result: dict[str, Any]) -> dict[str, Any]:
    orch = final_result.get("orchestrator_v2") or {}
    qec = orch.get("query_execution_context") or {}
    return qec if isinstance(qec, dict) else {}


def _compact_final_result(final_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(final_result, dict):
        return {}
    structured = final_result.get("structured_result") if isinstance(final_result.get("structured_result"), dict) else {}
    orch = final_result.get("orchestrator_v2") if isinstance(final_result.get("orchestrator_v2"), dict) else {}
    qec = orch.get("query_execution_context") if isinstance(orch.get("query_execution_context"), dict) else {}
    route_plan = orch.get("route_plan") if isinstance(orch.get("route_plan"), dict) else {}
    evidence_bundle = final_result.get("evidence_bundle") if isinstance(final_result.get("evidence_bundle"), dict) else {}
    evidence_counts = {
        key: len(value)
        for key, value in evidence_bundle.items()
        if isinstance(value, list)
    }
    return {
        "status": final_result.get("status"),
        "error_code": final_result.get("error_code"),
        "agent_name": final_result.get("agent_name"),
        "summary": final_result.get("summary"),
        "answer_text": final_result.get("answer_text"),
        "external_data_requirement": final_result.get("external_data_requirement"),
        "structured_result": {
            "requires_external_api": structured.get("requires_external_api"),
            "api_params": structured.get("api_params"),
            "external_data_requirement": structured.get("external_data_requirement"),
            "count": structured.get("count"),
            "status": structured.get("status"),
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": {
                "readiness": qec.get("readiness"),
                "blockers": qec.get("blockers"),
                "warnings": qec.get("warnings"),
                "data_bindings": qec.get("data_bindings"),
                "tool_bindings": qec.get("tool_bindings"),
            },
        },
        "evidence_counts": evidence_counts,
    }


def compact_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") == "node_finished":
            item = {
                "event": "node_finished",
                "node": event.get("node"),
                "status": event.get("status"),
            }
            if isinstance(event.get("task_plan"), dict):
                item["task_plan"] = event["task_plan"]
            if event.get("normalized_query"):
                item["normalized_query"] = event.get("normalized_query")
            compacted.append(item)
        elif event.get("event") == "completed":
            compacted.append(
                {
                    "event": "completed",
                    "status": event.get("status"),
                    "debug_trace": {
                        "route": (event.get("debug_trace") or {}).get("4. 작업계획 수립"),
                    },
                    "final_result": _compact_final_result(event.get("final_result") or {}),
                }
            )
        else:
            compacted.append(event)
    return compacted


def _actual_status(final: dict[str, Any], final_result: dict[str, Any]) -> str:
    if final_result.get("status"):
        return str(final_result.get("status"))
    return str(final.get("status") or "NOT_RUN")


def _contains_forbidden_text(final_result: dict[str, Any], forbidden: list[str]) -> list[str]:
    text = json.dumps(final_result, ensure_ascii=False, default=str).lower()
    hits: list[str] = []
    if "MOCK_RESULT" in forbidden and "mock" in text:
        hits.append("MOCK_LEAKAGE")
    if "INVENTED_TIDE_DATE" in forbidden:
        # A rough deterministic guard: official external-data blocked answers
        # should not include a concrete tide schedule table.
        answer = str(final_result.get("answer_text") or "")
        if "khoa_tide_prediction" in text and any(term in answer for term in ["만조", "간조"]) and any(ch.isdigit() for ch in answer):
            hits.append("HALLUCINATED_DATA")
    return hits


def evaluate_case(case: dict[str, Any], events: list[dict[str, Any]], elapsed_ms: int) -> dict[str, Any]:
    final = _extract_final(events)
    final_result = final.get("final_result") or {}
    task_plan = _extract_last_task_plan(events)
    qec = _extract_qec(final_result)
    external_req = final_result.get("external_data_requirement") or (
        (final_result.get("structured_result") or {}).get("external_data_requirement")
        if isinstance(final_result.get("structured_result"), dict)
        else None
    )
    actual = {
        "final_event_status": final.get("status"),
        "result_status": _actual_status(final, final_result),
        "error_code": final_result.get("error_code"),
        "analysis_type": task_plan.get("analysis_type"),
        "primary_agent": task_plan.get("primary_agent"),
        "route_plan_status": task_plan.get("route_plan_status") or qec.get("readiness"),
        "execution_ready": task_plan.get("execution_ready"),
        "tools": task_plan.get("tools") or [],
        "data": task_plan.get("data") or [],
        "blockers": qec.get("blockers") or (external_req or {}).get("blockers") or [],
        "external_data_requirement": external_req,
        "answer_text": final_result.get("answer_text"),
        "elapsed_ms": elapsed_ms,
        "node_sequence": [
            {"node": event.get("node"), "status": event.get("status")}
            for event in events
            if event.get("event") == "node_finished"
        ],
    }

    failures: list[str] = []
    warnings: list[str] = []

    expected_analysis = case.get("expected_analysis_type")
    if expected_analysis and actual["analysis_type"] != expected_analysis:
        failures.append("analysis_type_mismatch")

    expected_agent = case.get("expected_agent")
    if expected_agent and actual["primary_agent"] != expected_agent:
        failures.append("agent_mismatch")

    expected_status = case.get("expected_status") or []
    if expected_status and actual["result_status"] not in expected_status:
        failures.append("result_status_mismatch")

    expected_route_status = case.get("expected_route_plan_status") or []
    if expected_route_status and actual["route_plan_status"] not in expected_route_status:
        failures.append("route_plan_status_mismatch")

    expected_external = case.get("expected_external_data") or {}
    if expected_external.get("required"):
        if not external_req:
            failures.append("missing_external_requirement")
        else:
            if expected_external.get("domain") and external_req.get("domain") != expected_external["domain"]:
                failures.append("external_domain_mismatch")
            if "web_search_performed" in expected_external and external_req.get("web_search_performed") != expected_external["web_search_performed"]:
                failures.append("web_search_flag_mismatch")
            if "local_rag_suitable" in expected_external and external_req.get("local_rag_suitable") != expected_external["local_rag_suitable"]:
                failures.append("local_rag_flag_mismatch")

    forbidden_hits = _contains_forbidden_text(final_result, case.get("forbidden_behavior") or [])
    failures.extend(forbidden_hits)

    if final.get("event") != "completed":
        failures.append("not_completed")

    verdict = "PASS" if not failures else "FAIL"
    if actual["result_status"] == "BLOCKED" and case.get("expected_behavior", "").startswith("BLOCK") and not failures:
        verdict = "PASS"
    elif actual["result_status"] == "BLOCKED" and not failures:
        verdict = "BLOCKED"

    return {
        "case_id": case["case_id"],
        "query": case["query"],
        "category": case.get("category"),
        "domains": case.get("domains", []),
        "verdict": verdict,
        "failures": failures,
        "warnings": warnings,
        "actual": actual,
        "expected": {
            "analysis_type": case.get("expected_analysis_type"),
            "agent": case.get("expected_agent"),
            "status": case.get("expected_status"),
            "route_plan_status": case.get("expected_route_plan_status"),
            "behavior": case.get("expected_behavior"),
            "external_data": case.get("expected_external_data"),
        },
        "events": events,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0}
    categories: dict[str, int] = {}
    failure_counts: dict[str, int] = {}
    latencies = sorted(
        int((row.get("actual") or {}).get("elapsed_ms") or 0)
        for row in results
        if (row.get("actual") or {}).get("elapsed_ms") is not None
    )
    for row in results:
        counts[row.get("verdict", "NOT_RUN")] = counts.get(row.get("verdict", "NOT_RUN"), 0) + 1
        categories[row.get("category", "unknown")] = categories.get(row.get("category", "unknown"), 0) + 1
        for failure in row.get("failures") or []:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1
    total = len(results)
    def percentile(values: list[int], p: float) -> int | None:
        if not values:
            return None
        idx = min(len(values) - 1, max(0, round((len(values) - 1) * p)))
        return values[idx]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "counts": counts,
        "pass_rate": counts["PASS"] / total if total else 0.0,
        "category_distribution": categories,
        "failure_distribution": failure_counts,
        "latency_ms": {
            "min": latencies[0] if latencies else None,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "max": latencies[-1] if latencies else None,
        },
    }


def run_api_case(case: dict[str, Any], base_url: str, timeout: float) -> tuple[list[dict[str, Any]], int]:
    task_id = f"bench-{case['case_id']}-{uuid.uuid4().hex[:8]}"
    payload = _make_api_payload(case, task_id)
    url = base_url.rstrip("/") + "/api/v1/tasks/stream"
    started = time.time()
    try:
        events = _stream_sse(url, payload, timeout)
        elapsed_ms = int((time.time() - started) * 1000)
        return events, elapsed_ms
    except error.HTTPError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return [{"event": "error", "message": f"HTTP {exc.code}: {body}"}], elapsed_ms
    except error.URLError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return [{"event": "error", "message": str(exc)}], elapsed_ms
    except TimeoutError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return [{"event": "error", "message": f"timeout: {exc}"}], elapsed_ms
    except OSError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return [{"event": "error", "message": f"os_error: {exc}"}], elapsed_ms


async def run_graph_case(case: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], int]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from shared.schemas.agent import AgentStatus
    from services.orchestrator.graph import orchestrator_graph
    from services.orchestrator.router import build_debug_trace

    task_id = f"bench-{case['case_id']}-{uuid.uuid4().hex[:8]}"
    api_payload = _make_api_payload(case, task_id)
    initial_state = {
        "task_id": task_id,
        "query": api_payload["query"],
        "organization_id": api_payload["organization_id"],
        "user_id": api_payload["user_id"],
        "status": AgentStatus.RECEIVED,
        "spatial_context": api_payload.get("spatial_context"),
        "state_history": [],
    }
    config = {"configurable": {"thread_id": task_id}}
    events: list[dict[str, Any]] = [{"event": "started", "task_id": task_id}]
    started = time.time()

    async def _run() -> None:
        async for chunk in orchestrator_graph.astream(initial_state, config=config, stream_mode="updates"):
            for node_name, state_update in chunk.items():
                event = {
                    "event": "node_finished",
                    "node": node_name,
                    "status": state_update.get("status"),
                }
                task_plan = state_update.get("task_plan")
                if task_plan:
                    event["task_plan"] = task_plan.model_dump(mode="json") if hasattr(task_plan, "model_dump") else task_plan
                events.append(event)

    try:
        await asyncio.wait_for(_run(), timeout=timeout)
        snapshot = orchestrator_graph.get_state(config)
        values = snapshot.values if snapshot else {}
        final = {
            "event": "completed",
            "status": values.get("status", "FAILED"),
            "debug_trace": build_debug_trace(values),
        }
        if values.get("status") == AgentStatus.COMPLETED:
            final["final_result"] = values.get("final_dict")
        elif values.get("agent_result"):
            agent_result = values["agent_result"]
            final["final_result"] = agent_result.model_dump(mode="json") if hasattr(agent_result, "model_dump") else agent_result
        events.append(final)
    except asyncio.TimeoutError:
        events.append({"event": "error", "message": f"timeout after {timeout}s"})
    elapsed_ms = int((time.time() - started) * 1000)
    return events, elapsed_ms


def maybe_llm_judge(result: dict[str, Any], ollama_url: str, model: str, timeout: float) -> dict[str, Any] | None:
    case_judge = (result.get("case") or {}).get("llm_judge") or {}
    if not case_judge.get("enabled"):
        return None
    prompt = {
        "case_id": result.get("case_id"),
        "query": result.get("query"),
        "rubric": case_judge.get("rubric"),
        "answer_text": (result.get("actual") or {}).get("answer_text"),
        "deterministic_failures": result.get("failures", []),
    }
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "prompt": (
            "Return compact JSON with keys pass(boolean), notes(string), safety_flags(array). "
            "Do not override deterministic failures. Evaluate this Marine GeoLLM answer:\n"
            + json.dumps(prompt, ensure_ascii=False)
        ),
    }
    try:
        raw = _json_post(ollama_url.rstrip("/") + "/api/generate", body, timeout)
        payload = json.loads(raw.decode("utf-8", errors="replace"))
        response = payload.get("response", "{}")
        return json.loads(response)
    except Exception as exc:  # advisory only
        return {"pass": None, "notes": f"LLM judge unavailable: {exc}", "safety_flags": []}


async def async_main(args: argparse.Namespace) -> int:
    cases = _load_jsonl(args.cases)
    if args.case_id:
        wanted = set(args.case_id)
        cases = [case for case in cases if case.get("case_id") in wanted]
    if args.category:
        wanted_categories = set(args.category)
        cases = [case for case in cases if case.get("category") in wanted_categories]
    if args.domain:
        wanted_domains = set(args.domain)
        cases = [
            case for case in cases
            if wanted_domains.intersection(set(case.get("domains") or []))
        ]
    if args.limit:
        cases = cases[: args.limit]

    results: list[dict[str, Any]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['case_id']} :: {case['query']}", flush=True)
        if args.mode == "api":
            events, elapsed_ms = run_api_case(case, args.base_url, args.timeout)
        else:
            events, elapsed_ms = await run_graph_case(case, args.timeout)
        if not args.full_events:
            events = compact_events(events)
        result = evaluate_case(case, events, elapsed_ms)
        result["case"] = case
        if args.llm_judge:
            result["llm_judge"] = maybe_llm_judge(result, args.ollama_url, args.ollama_model, args.llm_timeout)
        results.append(result)
        with args.output.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
        print(f"  -> {result['verdict']} {result['actual'].get('result_status')} {result['actual'].get('analysis_type')} {result['actual'].get('primary_agent')} {elapsed_ms}ms", flush=True)

    metrics = summarize(results)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0 if not any(row["verdict"] == "FAIL" for row in results) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--mode", choices=["api", "graph"], default="api")
    parser.add_argument("--base-url", default=os.environ.get("GEOLLM_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--category", action="append")
    parser.add_argument("--domain", action="append")
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--ollama-model", default=os.environ.get("LLM_MODEL", "gemma2"))
    parser.add_argument("--llm-timeout", type=float, default=10.0)
    parser.add_argument("--full-events", action="store_true")
    return parser.parse_args()


def main() -> int:
    return asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
