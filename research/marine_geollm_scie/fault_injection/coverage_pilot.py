"""No-network validator scope audit. Synthetic metadata is never GIS ground truth."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import yaml
from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from research.marine_geollm_scie.fault_injection.pilot import cases, ROOT


SPECS = [
    ("control", "CONTROL", None, None),
    ("invalid_feature", "L1", "FEATURE_CODE_MISMATCH", "target_features"),
    ("invalid_attribute", "L1", "DATA_SCHEMA_MISMATCH", "attribute ownership/code lists are not modeled by generic radius validator"),
    ("invalid_crs", "L1", "SLOT_EXTRACTION_ERROR", "crs"),
    ("missing_unit", "L1", "SLOT_EXTRACTION_ERROR", "QEC has normalized distance_m, no source-unit field to remove"),
    ("invalid_geometry", "L1", "LOCATION_RESOLUTION_ERROR", "reference_geometry"),
    ("operator_mismatch", "L1", "TOOL_CAPABILITY_MISMATCH", "spatial_relation"),
    ("missing_dataset", "L1", "DATA_LAYER_NOT_FOUND", "relation.exists"),
    ("missing_tool", "L1", "TOOL_NOT_REGISTERED", "tool_registry"),
    ("invalid_feature_and_crs", "L2", "FEATURE_CODE_MISMATCH", "target_features+crs"),
    ("missing_dataset_and_tool", "L2", "DATA_LAYER_NOT_FOUND", "relation+tool_registry"),
    ("postapproval_distance", "L3", "UNSAFE_EXECUTION", "slots.distance_m"),
    ("postapproval_crs", "L3", "SLOT_EXTRACTION_ERROR", "slots.crs"),
    ("postapproval_filters", "L3", "DATA_SCHEMA_MISMATCH", "slots.filters"),
    ("registry_version_change", "L3", "DATA_VERSION_MISMATCH", "tool_registry.version"),
    ("tool_removed_after_approval", "L3", "TOOL_NOT_REGISTERED", "tool_registry"),
    ("permission_revoked_after_approval", "L3", "UNSAFE_EXECUTION", "relation.has_select"),
    ("schema_changed_after_approval", "L3", "DATA_SCHEMA_MISMATCH", "relation.geometry"),
    ("relation_removed_after_approval", "L3", "DATA_LAYER_NOT_FOUND", "relation.exists"),
]


def issue_code(message):
    """Research trace classifier uses existing codes; never claims native typed issues."""
    text = message.lower()
    if "tool not registered" in text: return "TOOL_NOT_REGISTERED"
    if "geometry column" in text or "code column" in text: return "DATA_SCHEMA_MISMATCH"
    if "relation not found" in text: return "DATA_LAYER_NOT_FOUND"
    if "access denied" in text or "max radius" in text: return "UNSAFE_EXECUTION"
    if "geometry" in text: return "LOCATION_RESOLUTION_ERROR"
    if "distance" in text: return "SLOT_EXTRACTION_ERROR"
    if "target feature" in text: return "FEATURE_MAPPING_MISSING"
    return "UNKNOWN_FAILURE"


def diagnose(name, level, fault_code, field):
    taxonomy = yaml.safe_load((ROOT/"configs/evaluation/failure_taxonomy.yaml").read_text(encoding="utf-8"))["failure_codes"]
    assert fault_code is None or fault_code in taxonomy
    _, _, _, base, adapter, environment = next(cases())
    row = {"case_id": name, "fault_level": level, "method": "P_ExecutionValidator_scope_audit",
        "injected_fault_code": fault_code, "field": field, "review_status": "DRAFT", "label_status": "DRAFT",
        "diagnostic_only": True, "synthetic_schema": True, "execution_success": None,
        "spatial_correct": None, "expected_invalid": None, "private_model_reasoning": "not_requested",
        "scope": "generic feature_search_by_radius only; not all production gates or actual GIS execution"}
    if name in {"missing_unit", "invalid_attribute"}:
        return {**row, "status": "NOT_SUPPORTED", "reason": field, "predicted_invalid": None, "full_qec": base.model_dump(mode="json")}
    info = copy.deepcopy(environment["relation_inspection"])
    adapter._inspect_relation = lambda relation: copy.deepcopy(info)
    approved = validate_execution_context(base, binding_adapter=adapter)
    assert is_execution_authorized(approved), "baseline control must be authorized"
    qec = approved.model_copy(deep=True) if level == "L3" else base.model_copy(deep=True)
    if name in {"invalid_feature", "invalid_feature_and_crs"}: qec.slots.target_features = ["NOT_A_REAL_S101_FEATURE_SCIE"]
    if name in {"invalid_crs", "invalid_feature_and_crs", "postapproval_crs"}: qec.slots.crs = "EPSG:INVALID_SCIE"
    if name == "invalid_geometry": qec.slots.reference_geometry = "NOT_WKT"
    if name == "operator_mismatch": qec.slots.spatial_relation = "within"
    if name == "postapproval_distance": qec.slots.distance_m = 50001
    if name == "postapproval_filters": qec.slots.filters = {"scie_injected_filter": "changed"}
    if name in {"missing_dataset", "missing_dataset_and_tool", "relation_removed_after_approval"}: info["exists"] = False
    if name in {"missing_tool", "missing_dataset_and_tool", "tool_removed_after_approval"}: adapter.tool_registry["tools"].pop("postgis.dwithin", None)
    if name == "permission_revoked_after_approval": info["has_select"] = False
    if name == "schema_changed_after_approval": info["columns"] = [c for c in info["columns"] if c["name"] != "geometry"]
    if name == "registry_version_change": adapter.tool_registry["version"] = "scie-isolated-changed-version"
    row["full_qec"] = qec.model_dump(mode="json")
    row["before_approval_receipt"] = approved.provenance.get("execution_validation")
    row["receipt_authorized_without_revalidation"] = is_execution_authorized(qec) if level == "L3" else None
    start = time.perf_counter()
    checked = validate_execution_context(qec, binding_adapter=adapter)
    row.update(status="DIAGNOSTIC_COMPLETED", latency_ms=(time.perf_counter()-start)*1000,
        predicted_invalid=not is_execution_authorized(checked), final_result=checked.model_dump(mode="json"),
        environment_after={"relation_inspection": info, "tool_registry_version": adapter.tool_registry.get("version"),
            "dwithin_registered": "postgis.dwithin" in adapter.tool_registry["tools"]})
    row["typed_issues"] = []
    for blocker in checked.blockers:
        code = issue_code(blocker); definition = taxonomy[code]
        row["typed_issues"].append({"code": code, "layer": definition["layer"], "severity": definition["severity"],
            "message": blocker, "source": "research deterministic classification of native free-text blocker", "human_verified": False})
    # No automatic DRAFT fault -> expert truth or accuracy conversion.
    if name in {"invalid_feature", "invalid_crs", "invalid_feature_and_crs", "operator_mismatch"} and not row["predicted_invalid"]:
        row["interpretation"] = "NO_ENFORCEMENT_OBSERVED_AT_THIS_GATE; downstream/upstream safeguards not assessed"
    if level == "L3" and row["receipt_authorized_without_revalidation"]:
        row["interpretation"] = "Receipt hashes QEC input; external mutable registry/schema freshness requires revalidation, not established by receipt alone"
    return row


def run(output_dir):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    raw = out/"coverage_rows.jsonl"
    if raw.exists(): raise FileExistsError(raw)
    rows = []
    with raw.open("x", encoding="utf-8") as stream:
        for spec in SPECS:
            try: row = diagnose(*spec)
            except Exception as exc:
                row = {"case_id": spec[0], "status": "DIAGNOSTIC_ERROR", "error": f"{type(exc).__name__}: {exc}", "label_status": "DRAFT"}
            rows.append(row); stream.write(json.dumps(row, ensure_ascii=False)+"\n"); stream.flush()
    summary = {"label": "DIAGNOSTIC — NOT PUBLICATION ACCURACY", "rows": len(rows), "gold_count": 0,
        "db_calls": 0, "llm_calls": 0, "status_counts": {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}},
        "unblocked_probe_cases": [r["case_id"] for r in rows if r.get("predicted_invalid") is False],
        "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),
            ROOT/"services/orchestrator/execution_validator.py", ROOT/"configs/evaluation/failure_taxonomy.yaml"]}}
    (out/"coverage_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", required=True)
    run(parser.parse_args().output_dir)
