"""Compare real radius preprocessing to direct generic validation, without I/O."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from services.orchestrator.s101_radius_execution import prepare_radius_request, select_targets, RadiusProblem
from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from research.marine_geollm_scie.fault_injection.pilot import cases, ROOT
import yaml


def compare_case(name):
    _, _, _, qec, adapter, _ = next(cases())
    qec.original_query = "침선 반경 3000m"
    spatial = {"geometry": "POINT(129.05 35.1)", "crs": "EPSG:4326", "target_features": ["Wreck"]}
    if name == "invalid_feature":
        spatial["target_features"] = ["NOT_A_REAL_S101_FEATURE_SCIE"]
        qec.slots.target_features = spatial["target_features"]
    elif name == "invalid_crs":
        spatial["crs"] = "EPSG:INVALID_SCIE"; qec.slots.crs = spatial["crs"]
    elif name == "operator_mismatch":
        spatial["spatial_relation"] = "within"; qec.slots.spatial_relation = "within"
    elif name != "control": raise ValueError(name)
    state = {"task_id": "research-"+name, "query": qec.original_query, "spatial_context": spatial}
    registry = yaml.safe_load((ROOT/"data/derived_concept_registry_v2.yaml").read_text(encoding="utf-8"))
    profile = registry["derived_concepts"]["navigation_hazard_object"]["execution_profiles"]["s101_hazard_radius"]
    row = {"case_id": name, "label_status": "DRAFT", "diagnostic_only": True,
        "point_basis": "synthetic explicit diagnostic point; not verified named-place coordinate",
        "state_input": copy.deepcopy(state), "direct_validator_input": qec.model_dump(mode="json"),
        "execution_success": None, "spatial_correct": None, "unsafe_execution_demonstrated": False}
    # Only real select_targets and prepare_radius_request logic execute. Any DB or
    # socket attempt fails the diagnostic instead of supplying simulated results.
    with patch("psycopg2.connect", side_effect=AssertionError("DB access prohibited")), \
         patch("socket.socket.connect", side_effect=AssertionError("Network access prohibited")):
        try:
            targets, exclusions = select_targets(state["query"], spatial, profile)
            row["select_targets"] = {"status": "RETURNED", "targets": targets, "exclusions": exclusions}
        except RadiusProblem as exc:
            row["select_targets"] = {"status": "REJECTED", "code": exc.code, "message": str(exc)}
        try:
            prepared, layer, template, params = prepare_radius_request(state)
            row["prepare_radius_request"] = {"status": "RETURNED", "full_qec": prepared.model_dump(mode="json"),
                "spatial_relation_preserved": prepared.slots.spatial_relation == spatial.get("spatial_relation"),
                "operation": prepared.route_plan.get("analysis_type"), "params": params}
        except RadiusProblem as exc:
            row["prepare_radius_request"] = {"status": "REJECTED", "code": exc.code, "message": str(exc)}
        checked = validate_execution_context(qec, binding_adapter=adapter)
        row["direct_generic_validator"] = {"authorized": is_execution_authorized(checked), "full_qec": checked.model_dump(mode="json")}
    return row


def run(output_dir):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    raw = out/"preprocessing_rows.jsonl"
    with raw.open("x", encoding="utf-8") as stream:
        for name in ["control", "invalid_feature", "invalid_crs", "operator_mismatch"]:
            try: row = compare_case(name)
            except Exception as exc:
                row = {"case_id": name, "status": "DIAGNOSTIC_ERROR", "error": f"{type(exc).__name__}: {exc}", "label_status": "DRAFT"}
            stream.write(json.dumps(row, ensure_ascii=False)+"\n"); stream.flush()
    metadata = {"rows": 4, "gold_count": 0, "db_calls": 0, "llm_calls": 0,
        "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),
            ROOT/"services/orchestrator/s101_radius_execution.py", ROOT/"services/orchestrator/execution_validator.py",
            ROOT/"data/derived_concept_registry_v2.yaml"]}}
    (out/"preprocessing_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", required=True)
    run(parser.parse_args().output_dir)
