"""Actual production graph in an isolated worker; never imports the HTTP router.

Required deployment: source mount read-only, private internal Docker network,
only research snapshot DB reachable, scratch feedback mount, no production envfile.
No graph node is substituted. No LLM is invoked in this restricted pilot profile.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
import uuid

METHOD = "P_current_production_no_llm"
SELECTED = {"PILOT_Q1_03", "PILOT_Q2_03", "PILOT_Q3_03", "PILOT_Q4_01", "PILOT_Q5_03", "PILOT_Q6_03"}


def require_isolation():
    if os.environ.get("SCIE_ISOLATED_GRAPH") != "1" or not Path("/.dockerenv").exists():
        raise RuntimeError("Requires explicitly isolated Docker research worker")
    for key in ("S101_DB_URL", "POSTGIS_URL"):
        parsed = urlsplit(os.environ.get(key, ""))
        if parsed.hostname != "marine-scie-pilot-db" or parsed.path != "/scie_pilot":
            raise RuntimeError(f"{key} must point only to isolated research snapshot")
    if os.environ.get("DISABLE_LLM_API") != "1":
        raise RuntimeError("This profile disables model APIs and is not model-matched Full P")
    if "default_transaction_read_only=on" not in os.environ.get("PGOPTIONS", ""):
        raise RuntimeError("Read-only DB transactions required")


def observable(value):
    """Serialize full observable state; never persist secrets/private model reasoning."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in {"thinking", "chain_of_thought", "reasoning_content"}:
                continue
            if lowered in {"password", "api_key", "authorization", "access_token", "dsn"}:
                result[key] = "[REDACTED]"
            else:
                result[key] = observable(item)
        return result
    if isinstance(value, (list, tuple)):
        return [observable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value"):
        return value.value
    return str(value)


def extract_artifacts(state):
    qecs, evidence, receipts = [], [], []
    def walk(value):
        if isinstance(value, dict):
            if value.get("contract_version") == "geollm.execution.v1":
                if value not in qecs: qecs.append(value)
            for key, child in value.items():
                if key in {"evidence_bundle", "evidence"} and child:
                    evidence.append(child)
                if key == "execution_validation" and isinstance(child, dict):
                    receipts.append(child)
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(state)
    return {"full_qec": qecs[-1] if qecs else None, "all_qecs": qecs,
            "evidence_bundles": evidence, "validator_receipts": receipts}


def row_base(case, repeat):
    return {"case_id": case["case_id"], "query": case["query"], "source_case": case,
        "repeat": repeat, "method": METHOD, "annotation_status": "DRAFT", "review_status": "DRAFT",
        "model_condition": "DISABLE_LLM_API=1; embedding endpoint unreachable; no model equivalence claim",
        "scope": "Actual production graph entry; restricted research snapshot and unavailable external dependencies",
        "semantic_correct": None, "plan_valid": None, "execution_success": None,
        "spatial_correct": None, "evidence_correct": None, "input_tokens": None, "output_tokens": None}


async def invoke_case(case, repeat=0):
    require_isolation()
    from services.orchestrator.graph import orchestrator_graph
    from shared.schemas.agent import AgentStatus
    row = row_base(case, repeat)
    initial = {"task_id": str(uuid.uuid4()), "query": case["query"],
        "organization_id": "scie_isolated", "user_id": "scie_research",
        "status": AgentStatus.RECEIVED, "spatial_context": case.get("spatial_context") or {}, "state_history": []}
    row["initial_state"] = observable(initial)
    start = time.perf_counter()
    try:
        state = await orchestrator_graph.ainvoke(initial,
            config={"configurable": {"thread_id": initial["task_id"]}, "recursion_limit": 30})
        state = observable(state)
        row.update(status="GRAPH_RETURNED", final_state=state,
            final_result=state.get("final_dict") or state.get("agent_result"), graph_status=state.get("status"),
            **extract_artifacts(state))
        # A graph returning/clarifying is not proof of successful spatial execution.
    except Exception as exc:
        row.update(status="GRAPH_ERROR", error=f"{type(exc).__name__}: {exc}")
    row["latency_ms"] = (time.perf_counter()-start)*1000
    return row


def run_benchmark(benchmark, output_dir, repeats=3, timeout=90):
    require_isolation()
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    raw = output / "production_rows.jsonl"
    if raw.exists(): raise FileExistsError(raw)
    cases = [json.loads(line) for line in Path(benchmark).read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = [case for case in cases if case["case_id"] in SELECTED]
    if len(selected) != len(SELECTED): raise ValueError("Six stratified benchmark cases required")
    rows = []
    with raw.open("x", encoding="utf-8") as stream:
        for case in selected:
            for repeat in range(repeats):
                prefix = output / f"{case['case_id']}_{repeat}"
                source = prefix.with_suffix(".input.json")
                result_path = prefix.with_suffix(".result.json")
                source.write_text(json.dumps(case, ensure_ascii=False), encoding="utf-8")
                command = [sys.executable, "-m", "research.marine_geollm_scie.baselines.production_adapter", "--single-case", str(source),
                    "--output", str(result_path), "--repeat", str(repeat)]
                start = time.perf_counter()
                try:
                    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
                    row = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {
                        **row_base(case, repeat), "status": "WORKER_FAILED", "exit_code": completed.returncode}
                    # No inherited production envfile; nevertheless redact configured DSNs.
                    for suffix, content in ((".stdout.log", completed.stdout), (".stderr.log", completed.stderr)):
                        for key in ("S101_DB_URL", "POSTGIS_URL"):
                            content = content.replace(os.environ.get(key, "__unset__"), "[REDACTED_RESEARCH_DSN]")
                        prefix.with_suffix(suffix).write_text(content, encoding="utf-8")
                except subprocess.TimeoutExpired:
                    row = {**row_base(case, repeat), "status": "WORKER_TIMEOUT", "timeout_seconds": timeout}
                row["wall_latency_ms"] = (time.perf_counter()-start)*1000
                rows.append(row); stream.write(json.dumps(row, ensure_ascii=False)+"\n"); stream.flush()
                print(case["case_id"], repeat, row["status"], flush=True)
    summary = {"method": METHOD, "rows": len(rows), "human_gold_count": 0,
        "status_counts": {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}},
        "full_P_completed": False, "operating_conditions_equal_to_llm_baselines": False,
        "isolated_state_paths": {"graph_checkpoint": "in-process MemorySaver; new process per case",
            "feedback": "/work/data/feedback tmpfs", "logs": str(output), "db": "marine-scie-pilot-db/scie_pilot read-only"}}
    (output/"production_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--single-case"); parser.add_argument("--output")
    parser.add_argument("--repeat", type=int, default=0)
    parser.add_argument("--benchmark"); parser.add_argument("--output-dir")
    args = parser.parse_args()
    if args.single_case:
        result = asyncio.run(invoke_case(json.loads(Path(args.single_case).read_text(encoding="utf-8")), args.repeat))
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    else:
        run_benchmark(args.benchmark, args.output_dir)
