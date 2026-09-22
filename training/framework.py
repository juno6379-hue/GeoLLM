"""Production entrypoint for the Marine GeoLLM training-data framework."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from training.models import TrainingCase
from training.pipeline import (
    ROOT,
    canonical_query,
    dry_run as _prototype_dry_run,
    read_jsonl,
    registry_snapshot,
    validate_rows,
    write_jsonl,
)


def expand_approved_seeds(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for seed in [row for row in rows if row.get("review_status") == "APPROVED"][:limit]:
        family = re.sub(r"^MGEO-SEED-", "", seed["case_id"])
        for candidate in _prototype_dry_run(seed):
            suffix = re.sub(rf"^MGEO-DRY-{re.escape(family)}-", "", candidate["case_id"])
            candidate["case_id"] = f"MGEO-DRY-{family}-{suffix}"
            candidate["lineage"]["parent_seed_id"] = seed["case_id"]
            candidate["registry_snapshot"] = registry_snapshot()
            candidates.append(candidate)
    return candidates


def _record(case: TrainingCase) -> dict[str, Any]:
    return case.model_dump(mode="json")


def build_six_views(cases: list[TrainingCase], output: Path) -> None:
    views: dict[str, list[dict[str, Any]]] = {
        "fastpath_router": [],
        "capability_retriever": [],
        "slot_extractor": [],
        "planner": [],
        "execution_validator": [],
        "response_generator": [],
        "component_teacher_forcing": [],
        "end_to_end": [],
    }
    for case in cases:
        row = _record(case)
        raw_input = row["input"]
        routing = row["expected_routing"]
        views["fastpath_router"].append({
            "case_id": case.case_id,
            "input": raw_input,
            "target": {"fast_path": routing["fast_path"], "required_capabilities": routing["required_capabilities"]},
        })
        views["capability_retriever"].append({
            "case_id": case.case_id,
            "query": case.input.user_query,
            "positive_capabilities": routing["required_capabilities"],
            "hard_negative_capabilities": row["negative_constraints"]["forbidden_capabilities"],
            "typed_targets": {"resolvers": routing["resolver_chain"], "tools": routing["tools"], "agent": routing["primary_agent"], "datasets": row["expected_data_bindings"]["datasets"]},
        })
        views["slot_extractor"].append({"case_id": case.case_id, "input": raw_input, "target": row["expected_slots"]})
        qec = {
            "original_query": case.input.user_query,
            "normalized_query": row["expected_semantics"]["normalized_query"],
            "slots": row["expected_slots"],
            "semantic_resolution": row["expected_semantics"],
            "data_bindings": row["expected_data_bindings"],
        }
        views["planner"].append({
            "case_id": case.case_id,
            "input": {"query_execution_context": qec},
            "target": {"resolver_chain": routing["resolver_chain"], "agent_chain": [routing["primary_agent"], *routing["secondary_agents"]], "tool_chain": routing["tools"], "query_template": routing["query_template"]},
        })
        views["execution_validator"].append({
            "case_id": case.case_id,
            "input": {"slots": row["expected_slots"], "routing": routing, "data_bindings": row["expected_data_bindings"]},
            "target": row["expected_execution"],
        })
        fixture = row["execution_fixture"]
        # Dynamic response SFT requires real frozen execution/evidence. Clarification
        # cases are safe without a fixture because they make no dynamic claim.
        if fixture["fixture_id"] or not row["expected_execution"]["execution_ready"]:
            views["response_generator"].append({
                "case_id": case.case_id,
                "input": {"query": case.input.user_query, "resolved_context": qec, "route_plan": fixture["route_plan"], "execution_result": fixture["execution_result"], "evidence_bundle": fixture["evidence_bundle"], "answer_policy": row["expected_answer"]},
                "target": row["expected_answer"],
            })
        views["component_teacher_forcing"].append({
            "case_id": case.case_id,
            "input": {"gold_semantics": row["expected_semantics"], "gold_slots": row["expected_slots"]},
            "target": routing,
        })
        views["end_to_end"].append({
            "case_id": case.case_id,
            "input": raw_input,
            "target": {"semantics": row["expected_semantics"], "slots": row["expected_slots"], "routing": routing, "execution": row["expected_execution"]},
        })
    for name, records in views.items():
        write_jsonl(output / f"{name}.jsonl", records)


def leakage_issues(train: list[dict[str, Any]], holdout: list[dict[str, Any]]) -> list[str]:
    import difflib

    issues: list[str] = []
    holdout_queries = [(row.get("case_id"), canonical_query(row.get("query") or row.get("input", {}).get("user_query", ""))) for row in holdout]
    holdout_families = {row.get("seed_family_id") or row.get("lineage", {}).get("parent_seed_id") for row in holdout}
    for row in train:
        case_id = row.get("case_id")
        family = row.get("seed_family_id") or row.get("lineage", {}).get("parent_seed_id")
        if family and family in holdout_families:
            issues.append(f"{case_id}: seed-family leakage")
        query = canonical_query(row.get("query") or row.get("input", {}).get("user_query", ""))
        for other_id, other_query in holdout_queries:
            if not query or not other_query:
                continue
            score = difflib.SequenceMatcher(None, query, other_query).ratio()
            if score >= 0.92:
                issues.append(f"{case_id}: query leakage with {other_id} ({score:.3f})")
    return issues


def run(seed_path: Path, output: Path) -> dict[str, Any]:
    seeds = read_jsonl(seed_path)
    candidates = expand_approved_seeds(seeds, limit=3)
    candidate_path = output / "candidates/dry_run_candidates.jsonl"
    write_jsonl(candidate_path, candidates)
    holdout_paths = [ROOT / "tests/benchmark/benchmark_cases_v1.jsonl", ROOT / "tests/benchmark/geollm_ui_preset_cases_v1.jsonl"]
    cases, validation_errors = validate_rows(candidates, holdout_paths)
    holdout = [row for path in holdout_paths for row in read_jsonl(path)]
    leakage = leakage_issues(candidates, holdout)
    if not validation_errors and not leakage:
        build_six_views(cases, output / "views")
    report = {
        "seed_count": len(seeds),
        "approved_seed_count": sum(row.get("review_status") == "APPROVED" for row in seeds),
        "candidate_count": len(candidates),
        "validated_candidate_count": len(cases),
        "validation_errors": validation_errors,
        "leakage_issues": leakage,
        "views_generated": not validation_errors and not leakage,
        "registry_snapshot": registry_snapshot(),
    }
    report_path = output / "dry_run_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
