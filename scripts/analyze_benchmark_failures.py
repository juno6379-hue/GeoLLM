#!/usr/bin/env python
"""Analyze Marine GeoLLM benchmark failures and create improvement proposals."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "outputs" / "learning" / "benchmark_results.jsonl"
DEFAULT_FAILURES = ROOT / "outputs" / "learning" / "failure_cases.jsonl"
DEFAULT_PROPOSALS = ROOT / "outputs" / "learning" / "improvement_proposals.jsonl"
DEFAULT_REPORT = ROOT / "outputs" / "learning" / "failure_analysis.md"
DEFAULT_TAXONOMY = ROOT / "configs" / "evaluation" / "failure_taxonomy.yaml"
DEFAULT_RULES = ROOT / "configs" / "evaluation" / "root_cause_rules.yaml"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _taxonomy_layers(taxonomy: dict[str, Any]) -> dict[str, str]:
    return {
        code: (body or {}).get("layer", "unknown")
        for code, body in (taxonomy.get("failure_codes") or {}).items()
    }


def _map_expectation_failure(name: str, rules: dict[str, Any]) -> str:
    expectation_rules = rules.get("expectation_rules") or {}
    if name in expectation_rules:
        return expectation_rules[name]
    if name == "analysis_type_mismatch":
        return "AGENT_ROUTING_ERROR"
    if name == "agent_mismatch":
        return "AGENT_ROUTING_ERROR"
    if name == "missing_external_requirement":
        return "DATASET_NOT_REGISTERED"
    if name in {"not_completed", "result_status_mismatch"}:
        return "TOOL_EXECUTION_FAILED"
    if name in {"MOCK_LEAKAGE", "HALLUCINATED_DATA", "UNSAFE_EXECUTION", "UNSUPPORTED_CLAIM"}:
        return name
    return "UNKNOWN_FAILURE"


def classify_failure(row: dict[str, Any], taxonomy: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    layers = _taxonomy_layers(taxonomy)
    actual = row.get("actual") or {}
    blockers = [str(item) for item in actual.get("blockers") or []]
    failure_codes: list[str] = []
    supporting_trace: list[dict[str, Any]] = []

    for blocker in blockers:
        blocker_lower = blocker.lower()
        matched = False
        for rule in rules.get("blocker_rules") or []:
            needle = str(rule.get("contains", "")).lower()
            if needle and needle in blocker_lower:
                failure_codes.append(rule["failure_code"])
                supporting_trace.append({"source": "blocker", "text": blocker, "failure_code": rule["failure_code"]})
                matched = True
                break
        if not matched:
            failure_codes.append("UNKNOWN_FAILURE")
            supporting_trace.append({"source": "blocker", "text": blocker, "failure_code": "UNKNOWN_FAILURE"})

    for failure in row.get("failures") or []:
        code = _map_expectation_failure(failure, rules)
        failure_codes.append(code)
        supporting_trace.append({"source": "expectation", "text": failure, "failure_code": code})

    if row.get("verdict") == "FAIL" and not failure_codes:
        failure_codes.append("UNKNOWN_FAILURE")

    failure_codes = list(dict.fromkeys(failure_codes))
    primary = failure_codes[0] if failure_codes else None
    layer = layers.get(primary or "", "none")
    fix_level = {
        "query_normalization": "LEVEL 1 Dictionary / Alias or LEVEL 2 Normalizer",
        "slot_extraction": "LEVEL 2 Slot Extractor",
        "semantic_resolution": "LEVEL 3 Ontology Mapping",
        "ontology": "LEVEL 3 Ontology Mapping",
        "kg": "LEVEL 4 KG Edge / Metadata",
        "location_resolution": "LEVEL 2 Slot or LEVEL 5 Gazetteer/Registry",
        "data_registry": "LEVEL 5 Registry Mapping",
        "data_binding": "LEVEL 6 Data Binding Adapter",
        "query_template": "LEVEL 7 Query Template",
        "tool_registry": "LEVEL 8 Tool Capability",
        "tool_capability": "LEVEL 8 Tool Capability",
        "agent_routing": "LEVEL 9 Existing Agent Capability",
        "agent_capability": "LEVEL 10 New Agent Proposal Candidate",
        "rag": "LEVEL 11 RAG Retrieval/Evidence",
        "evidence": "LEVEL 12 Evidence Assembly",
        "response_ux": "LEVEL 13 Response / UX",
        "safety": "STOP: safety fix before promotion",
    }.get(layer, "Investigate trace manually")

    return {
        "case_id": row.get("case_id"),
        "query": row.get("query"),
        "category": row.get("category"),
        "verdict": row.get("verdict"),
        "root_cause": primary or "none",
        "root_cause_layer": layer,
        "failure_categories": failure_codes,
        "supporting_trace": supporting_trace,
        "recommended_fix_level": fix_level,
        "actual": actual,
    }


def build_proposals(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for failure in failures:
        grouped[(failure.get("root_cause_layer", "unknown"), failure.get("root_cause", "UNKNOWN_FAILURE"))].append(failure)

    proposals: list[dict[str, Any]] = []
    for idx, ((layer, code), rows) in enumerate(sorted(grouped.items()), start=1):
        proposals.append(
            {
                "proposal_id": f"IMPROVE-{idx:04d}",
                "status": "PROPOSED",
                "root_cause_layer": layer,
                "failure_code": code,
                "supporting_cases": [row["case_id"] for row in rows],
                "frequency": len(rows),
                "recommended_fix_level": rows[0].get("recommended_fix_level"),
                "summary": f"{len(rows)} benchmark case(s) indicate {code} at {layer}.",
                "requires_human_approval": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return proposals


def analyze_metamorphic_groups(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        case = row.get("case") or {}
        group_id = case.get("metamorphic_group")
        if group_id:
            groups[group_id].append(row)

    findings: list[dict[str, Any]] = []
    for group_id, rows in groups.items():
        if len(rows) < 2:
            continue
        comparable = []
        for row in rows:
            actual = row.get("actual") or {}
            comparable.append({
                "case_id": row.get("case_id"),
                "analysis_type": actual.get("analysis_type"),
                "primary_agent": actual.get("primary_agent"),
                "route_plan_status": actual.get("route_plan_status"),
                "result_status": actual.get("result_status"),
            })
        analysis_types = {item["analysis_type"] for item in comparable}
        agents = {item["primary_agent"] for item in comparable}
        if len(analysis_types) > 1 or len(agents) > 1:
            findings.append({
                "case_id": group_id,
                "query": f"Metamorphic group {group_id}",
                "category": "metamorphic",
                "verdict": "FAIL",
                "root_cause": "CONVERSATION_CONTEXT_LOSS" if "CONV" in group_id else "TERM_RESOLUTION_ERROR",
                "root_cause_layer": "semantic_resolution",
                "failure_categories": ["TERM_RESOLUTION_ERROR"],
                "supporting_trace": comparable,
                "recommended_fix_level": "LEVEL 1 Dictionary / Alias or LEVEL 2 Normalizer",
                "actual": {"metamorphic_group": group_id, "cases": comparable},
            })
    return findings


def write_report(path: Path, failures: list[dict[str, Any]], proposals: list[dict[str, Any]]) -> None:
    counts = Counter(failure.get("root_cause") for failure in failures)
    layer_counts = Counter(failure.get("root_cause_layer") for failure in failures)
    lines = [
        "# Benchmark Failure Analysis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Failure Codes",
        "",
    ]
    for code, count in counts.most_common():
        lines.append(f"- `{code}`: {count}")
    lines.extend(["", "## Layers", ""])
    for layer, count in layer_counts.most_common():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Improvement Proposals", ""])
    for proposal in proposals:
        lines.append(f"- `{proposal['proposal_id']}` {proposal['summary']} ({proposal['recommended_fix_level']})")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--failures", type=Path, default=DEFAULT_FAILURES)
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = _load_jsonl(args.results)
    taxonomy = _load_yaml(args.taxonomy)
    rules = _load_yaml(args.rules)
    failures = [
        classify_failure(row, taxonomy, rules)
        for row in results
        if row.get("verdict") in {"FAIL", "BLOCKED"} or row.get("failures")
    ]
    failures.extend(analyze_metamorphic_groups(results))
    proposals = build_proposals(failures)
    _write_jsonl(args.failures, failures)
    _write_jsonl(args.proposals, proposals)
    write_report(args.report, failures, proposals)
    print(json.dumps({"failures": len(failures), "proposals": len(proposals)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
