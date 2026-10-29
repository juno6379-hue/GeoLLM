"""Bounded diagnostic pilot; production QEC/validator, synthetic schema inspection.

No SQL or GIS query executes. Authored fault labels are DRAFT, never human gold.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
import urllib.request

import yaml
from shared.schemas.agent import ExecutionSlots, QueryExecutionContext
from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
from research.marine_geollm_scie.baselines.self_reviewer import review

ROOT = Path(__file__).resolve().parents[3]


def cases():
    # Production unit-test seed: test_execution_validator.py radius contract.
    base = QueryExecutionContext(original_query="부산항 3km 이내 침선을 찾아줘",
        route_plan={"analysis_type": "feature_search_by_radius"},
        slots=ExecutionSlots(location_text="부산항", reference_geometry="POINT(129.05 35.1)",
            crs="EPSG:4326", distance_m=3000, target_features=["Wreck"]))
    specs = [("valid_control", None, False),
        ("missing_distance", "SLOT_EXTRACTION_ERROR", True),
        ("radius_over_limit", "UNSAFE_EXECUTION", True),
        ("missing_reference", "LOCATION_RESOLUTION_ERROR", True),
        ("missing_relation", "DATA_LAYER_NOT_FOUND", True),
        ("missing_tool", "TOOL_NOT_REGISTERED", True),
        ("missing_geometry_and_tool", "DATA_SCHEMA_MISMATCH", True)]
    taxonomy = yaml.safe_load((ROOT / "configs/evaluation/failure_taxonomy.yaml").read_text(encoding="utf-8"))["failure_codes"]
    for name, code, invalid in specs:
        assert code is None or code in taxonomy
        qec = base.model_copy(deep=True)
        if name == "missing_distance": qec.slots.distance_m = None
        if name == "radius_over_limit": qec.slots.distance_m = 50001
        if name == "missing_reference": qec.slots.reference_geometry = None
        adapter = SchemaBindingAdapter()
        info = {"exists": name != "missing_relation", "has_select": True, "count": None,
            "columns": [{"name": n, "type": t} for n, t in [
                ("feature_instance_id", "bigint"), ("feature_type_code", "integer"),
                ("feature_type_name", "text"), ("geometry", "geometry")]]}
        if name == "missing_geometry_and_tool":
            info["columns"] = [col for col in info["columns"] if col["name"] != "geometry"]
        if name in {"missing_tool", "missing_geometry_and_tool"}:
            adapter.tool_registry["tools"].pop("postgis.dwithin", None)
        # Override only this instance; production files and global singleton untouched.
        adapter._inspect_relation = lambda relation, metadata=info: copy.deepcopy(metadata)
        environment = {"diagnostic_only": True, "relation_inspection": info,
            "required_tools": ["gbenc.s101_feature_search_by_radius", "postgis.dwithin"],
            "registered_tools": list(adapter.tool_registry.get("tools", {})),
            "radius_max_m": 50000, "inspection_source": "synthetic unit-test metadata; no GIS rows"}
        yield name, code, invalid, qec, adapter, environment


def run_validator_pilot(output_dir, model="qwen2.5:1.5b", repeats=3):
    if not 1 <= repeats <= 5: raise ValueError("repeats must be 1..5")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "validator_rows.jsonl"
    if path.exists(): raise FileExistsError(path)
    rows = []
    with path.open("x", encoding="utf-8") as stream:
        for name, code, invalid, qec, adapter, environment in cases():
            for repeat in range(repeats):
                common = {"case_id": name, "repeat": repeat, "full_qec": qec.model_dump(mode="json"),
                    "environment": environment, "expected_invalid": invalid, "failure_code": code,
                    "label_status": "DRAFT", "review_status": "DRAFT", "diagnostic_only": True,
                    "execution_success": None, "semantic_correct": None, "plan_valid": None,
                    "spatial_correct": None, "evidence_correct": None}
                start = time.perf_counter()
                checked = validate_execution_context(qec, binding_adapter=adapter)
                deterministic = {**common, "method": "P_ExecutionValidator", "status": "completed",
                    "latency_ms": (time.perf_counter()-start)*1000, "input_tokens": None, "output_tokens": None,
                    "predicted_invalid": not is_execution_authorized(checked),
                    "final_result": checked.model_dump(mode="json")}
                rows.append(deterministic)
                stream.write(json.dumps(deterministic, ensure_ascii=False) + "\n"); stream.flush()
                llm = review(common["full_qec"], environment, model=model)
                result = {**common, "method": "B4_LLM_Self_Reviewer", "model": model, **llm,
                    "final_result": {"response": llm.get("response"), "error": llm.get("error")}}
                rows.append(result)
                stream.write(json.dumps(result, ensure_ascii=False) + "\n"); stream.flush()
                print(f"{name} repeat={repeat} validator_invalid={deterministic['predicted_invalid']} B4={llm['predicted_invalid']} {llm['status']}", flush=True)
    summary = {"label": "PILOT — NOT FINAL PAPER RESULT", "human_gold_count": 0,
        "diagnostic_only": True, "gis_execution_count": 0, "repeats": repeats,
        "limitations": ["Synthetic relation metadata; no spatial correctness evidence.",
            "DRAFT authored fault labels; diagnostic agreements are not validated accuracy.",
            "Repeated deterministic validations are not independent samples.",
            "B4 input is a fixed production fixture, not a self-generated plan; reviewer-only diagnostic."],
        "methods": {}}
    for method in sorted({row["method"] for row in rows}):
        subset = [r for r in rows if r["method"] == method]
        summary["methods"][method] = {"rows": len(subset), "failures": sum(r["status"] != "completed" for r in subset),
            "draft_label_agreements": sum(r["predicted_invalid"] == r["expected_invalid"] for r in subset),
            "publication_accuracy": None}
    summary["source_hashes"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        ROOT/"services/orchestrator/execution_validator.py", ROOT/"shared/schemas/agent.py",
        ROOT/"configs/evaluation/failure_taxonomy.yaml", Path(__file__)]}
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
            summary["model_metadata"] = [m for m in json.load(response).get("models", []) if m["name"] == model]
    except Exception as exc: summary["model_metadata_error"] = str(exc)
    (output/"validator_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    run_validator_pilot(args.output_dir, args.model, args.repeats)
