"""Warm production graph once; unique MemorySaver thread IDs isolate each query."""
import argparse
import asyncio
import faulthandler
import json
from pathlib import Path
import signal
import time
from research.marine_geollm_scie.baselines.production_adapter import require_isolation, SELECTED, invoke_case, row_base


def deadline(signum, frame):
    raise TimeoutError("isolated production case deadline")


def main(benchmark, output_dir, repeats=1, import_stack_after=45):
    require_isolation()
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    raw = out / "production_rows.jsonl"
    if raw.exists(): raise FileExistsError(raw)
    start = time.perf_counter()
    # Stack frames only: no environment, local variables or exception payloads.
    # Keep the diagnostic file open until import completes or the worker ends.
    stack_path = out / "import_stack.log"
    with stack_path.open("x", encoding="utf-8") as stack_log:
        if import_stack_after > 0:
            faulthandler.dump_traceback_later(import_stack_after, repeat=False, file=stack_log)
        try:
            from services.orchestrator.graph import orchestrator_graph
        finally:
            if import_stack_after > 0:
                faulthandler.cancel_dump_traceback_later()
    (out/"warmup.json").write_text(json.dumps({"import_latency_ms": (time.perf_counter()-start)*1000,
        "cache_policy": "production singleton reused; fresh UUID checkpoint thread per request; no cross-query initial context"}), encoding="utf-8")
    cases = [json.loads(s) for s in Path(benchmark).read_text(encoding="utf-8").splitlines() if s.strip()]
    rows = []
    signal.signal(signal.SIGALRM, deadline)
    with raw.open("x", encoding="utf-8") as stream:
        for case in cases:
            if case["case_id"] not in SELECTED: continue
            for repeat in range(repeats):
                start = time.perf_counter(); signal.alarm(60)
                try:
                    row = asyncio.run(invoke_case(case, repeat))
                except Exception as exc:
                    row = {**row_base(case, repeat), "status": "SESSION_CASE_ERROR", "error": f"{type(exc).__name__}: {exc}"}
                finally:
                    signal.alarm(0)
                row["wall_latency_ms"] = (time.perf_counter()-start)*1000
                rows.append(row); stream.write(json.dumps(row, ensure_ascii=False)+"\n"); stream.flush()
                print(case["case_id"], repeat, row["status"], row.get("graph_status"), flush=True)
    summary = {"rows": len(rows), "status_counts": {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}},
        "gold_count": 0, "full_P_completed": False, "method": "P_current_production_no_llm",
        "source": "actual unchanged production orchestrator_graph.ainvoke", "cache_policy": "warm graph, unique thread IDs",
        "isolated_state_paths": {"feedback": "/work/data/feedback tmpfs", "checkpoint": "process-local MemorySaver", "output": "/out"}}
    (out/"production_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--benchmark", required=True)
    parser.add_argument("--output-dir", required=True); parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--import-stack-after", type=int, default=45,
        help="Import stack-only diagnostic delay; 0 disables it")
    args = parser.parse_args(); main(args.benchmark, args.output_dir, args.repeats, args.import_stack_after)
