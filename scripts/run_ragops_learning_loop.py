"""Run the RAGOps/LLMOps learning loop.

This script operationalizes the contract in
docs/execution_contract/103_ragops_llmops_retraining_loop.md.

It is intentionally conservative:
- pgvector retrieval remains candidate discovery only.
- registry/KG changes are emitted as review candidates, not auto-promoted.
- fine-tuning outputs are candidate datasets, not automatic training jobs.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEEDBACK = ROOT / "data" / "feedback"
OUTPUTS = ROOT / "outputs"
LEARNING = OUTPUTS / "learning"
REPORTS = OUTPUTS / "reports"
MODEL_LEARNING = OUTPUTS / "model_learning"
RAG = OUTPUTS / "rag"
REJECTED_TRAINING_CANDIDATES: list[dict[str, Any]] = []


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            rows.append({
                "source_file": str(path.relative_to(ROOT)),
                "line_no": line_no,
                "parse_error": str(exc),
                "raw": line,
            })
    return rows


def read_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def severity_rank(value: str | None) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(value or "").lower(), 0)


def collect_failed_queries() -> list[dict[str, Any]]:
    quality_rows = read_jsonl(FEEDBACK / "query_quality_issues.jsonl")
    routing_rows = read_json_array(FEEDBACK / "routing_failures.json")
    benchmark_failures = read_jsonl(LEARNING / "failure_cases.jsonl")

    collected: list[dict[str, Any]] = []
    for index, row in enumerate(quality_rows, start=1):
        collected.append({
            "issue_id": f"quality-{index:05d}",
            "source": "query_quality_issues",
            "source_file": "data/feedback/query_quality_issues.jsonl",
            "query": row.get("query"),
            "task_id": row.get("task_id"),
            "timestamp": row.get("timestamp"),
            "issue_type": row.get("issue_type"),
            "severity": row.get("severity"),
            "route_plan": row.get("route_plan") or {},
            "quality_metrics": row.get("quality_metrics") or {},
            "evidence_summary": row.get("evidence_summary") or {},
            "details": row.get("details") or {},
            "status": row.get("status", "pending_review"),
        })
    for index, row in enumerate(routing_rows, start=1):
        collected.append({
            "issue_id": f"routing-{index:05d}",
            "source": "routing_failures",
            "source_file": "data/feedback/routing_failures.json",
            "query": row.get("query"),
            "task_id": row.get("task_id"),
            "timestamp": row.get("timestamp"),
            "issue_type": "routing_failure",
            "severity": "high",
            "route_plan": {
                "predicted_agent": row.get("predicted_agent"),
                "correct_agent": row.get("correct_agent"),
            },
            "quality_metrics": {},
            "evidence_summary": {},
            "details": {
                "failure_reason": row.get("failure_reason"),
                "fix": row.get("fix"),
            },
            "status": row.get("status", "pending_review"),
        })
    for index, row in enumerate(benchmark_failures, start=1):
        collected.append({
            "issue_id": f"benchmark-{index:05d}",
            "source": "benchmark_failure_analysis",
            "source_file": "outputs/learning/failure_cases.jsonl",
            "query": row.get("query"),
            "task_id": row.get("case_id"),
            "timestamp": row.get("created_at"),
            "issue_type": row.get("root_cause") or "benchmark_failure",
            "severity": "high",
            "route_plan": row.get("actual") or {},
            "quality_metrics": {},
            "evidence_summary": {},
            "details": row,
            "status": "pending_review",
        })
    return collected


def _contains_any(text: str, needles: list[str]) -> bool:
    folded = text.lower()
    return any(needle.lower() in folded for needle in needles)


def label_issue(row: dict[str, Any]) -> dict[str, Any]:
    issue_type = str(row.get("issue_type") or "")
    route_plan = row.get("route_plan") or {}
    details = row.get("details") or {}
    quality = row.get("quality_metrics") or {}
    text = json.dumps(row, ensure_ascii=False, default=str)

    labels: list[str] = []
    treatments: list[str] = []

    if issue_type == "routing_failure" or _contains_any(issue_type, ["routing", "agent"]):
        labels.append("intent.routing")
        treatments.append("Add or adjust capability registry signals and benchmark route expectations.")
    if _contains_any(issue_type, ["quality_metrics_unavailable"]):
        labels.append("evidence.quality_metrics_missing")
        treatments.append("Emit deterministic quality metrics for the selected fast path.")
    if _contains_any(issue_type, ["low_kg_similarity"]):
        labels.append("kg.low_similarity")
        treatments.append("Improve KG/capability descriptions or add reviewed KG edges.")
    if _contains_any(issue_type, ["low_evidence_similarity", "no_authoritative_evidence"]):
        labels.append("evidence.low_or_missing")
        treatments.append("Check evidence domain, chunk coverage, metadata filters, and source provenance.")
    if _contains_any(issue_type, ["execution_not_ready", "blocked", "BLOCKED_DATA"]):
        labels.append("execution.readiness")
        treatments.append("Keep ExecutionValidator blocking until required slots, tool, and data binding are confirmed.")
    if route_plan.get("execution_ready") is True and (
        not route_plan.get("slots") and not route_plan.get("data") and not route_plan.get("tools")
    ):
        labels.append("execution.unsafe_ready")
        treatments.append("Require QueryExecutionContext to separate confirmed values from candidates before execution.")
    if _contains_any(text, ["location_text\": \"\"", "anchor_geometry", "spatial tool", "부근", "nearby"]):
        labels.append("slot.spatial_relation_or_anchor")
        treatments.append("Treat nearby terms as spatial relations and require a resolved place anchor.")
    if _contains_any(text, ["map", "geojson", "layer", "popup", "legend", "object lists"]):
        labels.append("output.map_table_evidence_consistency")
        treatments.append("Log and compare canonical object IDs across map, table, and evidence outputs.")
    if _contains_any(text, ["timeout", "RECEIVED", "CONTEXT_RESOLVED"]):
        labels.append("performance.timeout_or_stuck")
        treatments.append("Add terminal timeout handling and prefer deterministic fast path for ready compound queries.")
    if _contains_any(text, ["mojibake", "�", "encoding", "utf"]):
        labels.append("normalization.encoding")
        treatments.append("Preserve UTF-8 raw and normalized query text in every trace.")
    if quality.get("method") == "quality_unavailable":
        labels.append("evidence.quality_metrics_missing")
    if float(quality.get("estimated_accuracy") or 0.0) < 0.55:
        labels.append("quality.low_estimated_accuracy")

    if not labels:
        labels.append("manual_review.unknown")
        treatments.append("Review route trace, evidence bundle, and execution context manually.")

    labels = list(dict.fromkeys(labels))
    treatments = list(dict.fromkeys(treatments))
    primary_label = labels[0]
    recommended_stage = {
        "intent.routing": "3.registry_capability_kg_improvement",
        "slot.spatial_relation_or_anchor": "2.error_labeling_and_slot_fix",
        "execution.readiness": "3.registry_capability_kg_improvement",
        "execution.unsafe_ready": "3.registry_capability_kg_improvement",
        "kg.low_similarity": "3.registry_capability_kg_improvement",
        "evidence.low_or_missing": "4.embedding_regeneration",
        "evidence.quality_metrics_missing": "3.registry_capability_kg_improvement",
        "quality.low_estimated_accuracy": "6.benchmark_regression",
        "output.map_table_evidence_consistency": "6.benchmark_regression",
        "performance.timeout_or_stuck": "6.benchmark_regression",
        "normalization.encoding": "2.error_labeling_and_slot_fix",
    }.get(primary_label, "1.failed_query_collection")

    return {
        **row,
        "labels": labels,
        "primary_label": primary_label,
        "recommended_stage": recommended_stage,
        "recommended_treatments": treatments,
        "review_status": "pending_human_review",
        "labelled_at": utc_now(),
    }


def build_improvement_candidates(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in labels:
        key = (row.get("recommended_stage") or "unknown", row.get("primary_label") or "unknown")
        grouped.setdefault(key, []).append(row)

    applied_controls = {
        "evidence.quality_metrics_missing": [
            "fast_path_default_quality_metrics",
            "authoritative_no_evidence_quality_metrics",
        ],
        "execution.readiness": [
            "blocked_route_not_counted_as_readiness_error",
            "unsafe_execution_ready_without_bindings_detection",
        ],
        "kg.low_similarity": [
            "capability_registry_hints_expanded",
            "capability_embeddings_regenerated",
        ],
        "evidence.low_or_missing": [
            "dataset_evidence_domain_precedence",
            "document_chunk_pgvector_upsert_validation",
        ],
        "intent.routing": [
            "registry_driven_hints_for_hazard_gazetteer_accident_routes",
            "capability_embeddings_regenerated",
        ],
        "normalization.encoding": [
            "raw_and_normalized_query_preservation_candidate",
        ],
        "slot.spatial_relation_or_anchor": [
            "spatial_relation_not_concept_registry_hint",
        ],
        "quality.low_estimated_accuracy": [
            "benchmark_regression_required",
        ],
        "output.map_table_evidence_consistency": [
            "canonical_object_id_regression_required",
        ],
    }
    candidates: list[dict[str, Any]] = []
    for index, ((stage, label), rows) in enumerate(sorted(grouped.items()), start=1):
        queries = [row.get("query") for row in rows if row.get("query")]
        max_severity = max((severity_rank(row.get("severity")) for row in rows), default=0)
        candidate_type = "registry_capability_candidate"
        if stage.startswith("4."):
            candidate_type = "embedding_refresh_candidate"
        elif stage.startswith("6."):
            candidate_type = "benchmark_regression_candidate"
        elif stage.startswith("2."):
            candidate_type = "normalizer_or_slot_candidate"
        candidates.append({
            "candidate_id": f"RAGOPS-CAND-{index:04d}",
            "status": "APPLIED_PENDING_FRESH_LOG_VALIDATION" if applied_controls.get(label) else "PROPOSED",
            "candidate_type": candidate_type,
            "stage": stage,
            "primary_label": label,
            "frequency": len(rows),
            "severity_rank": max_severity,
            "supporting_issue_ids": [row["issue_id"] for row in rows],
            "sample_queries": queries[:5],
            "recommended_treatments": list(dict.fromkeys(
                treatment
                for row in rows
                for treatment in row.get("recommended_treatments") or []
            )),
            "applied_controls": applied_controls.get(label, []),
            "authority_gate": "human_review_required_before_registry_or_kg_promotion",
            "created_at": utc_now(),
        })
    return candidates


def build_training_candidates(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_primary = {
        "intent.routing",
        "slot.spatial_relation_or_anchor",
        "normalization.encoding",
        "quality.low_estimated_accuracy",
    }
    blocked_terms = [
        "coordinate",
        "coordinates",
        "좌표",
        "count",
        "건수",
        "법령",
        "조항",
        "S-101",
        "feature definition",
    ]
    rows: list[dict[str, Any]] = []
    for row in labels:
        query = str(row.get("query") or "").strip()
        if not query or row.get("primary_label") not in allowed_primary:
            continue
        text = json.dumps(row, ensure_ascii=False, default=str)
        authority_sensitive = _contains_any(text, blocked_terms)
        if authority_sensitive:
            REJECTED_TRAINING_CANDIDATES.append({
                "candidate_id": f"FT-REJECT-{len(REJECTED_TRAINING_CANDIDATES) + 1:04d}",
                "status": "REJECTED_AUTHORITY_SENSITIVE",
                "source_issue_id": row.get("issue_id"),
                "query": query,
                "primary_label": row.get("primary_label"),
                "reason": "Authority-sensitive facts must be fixed in RAG/KG/Registry/serving tables, not model weights.",
                "created_at": utc_now(),
            })
            continue
        rows.append({
            "candidate_id": f"FT-CAND-{len(rows) + 1:04d}",
            "status": "REVIEW_ELIGIBLE",
            "source_issue_id": row.get("issue_id"),
            "query": query,
            "primary_label": row.get("primary_label"),
            "allowed_use": "linguistic_intent_slot_style_only",
            "authority_sensitive": False,
            "exclude_from_training_until_reviewed": True,
            "reason": (
                "Candidate may improve linguistic routing/slot behavior. "
                "Do not train factual coordinates, counts, legal citations, feature definitions, or evidence."
            ),
            "created_at": utc_now(),
        })
    return rows


def run_command(name: str, command: list[str], continue_on_failure: bool = True) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=None,
        )
        status = "OK" if proc.returncode == 0 else "FAILED"
        result = {
            "name": name,
            "status": status,
            "returncode": proc.returncode,
            "command": command,
            "started_at": started.isoformat(),
            "finished_at": utc_now(),
            "output_tail": proc.stdout[-4000:],
        }
        if proc.returncode != 0 and not continue_on_failure:
            raise RuntimeError(f"{name} failed with code {proc.returncode}\n{proc.stdout}")
        return result
    except Exception as exc:
        result = {
            "name": name,
            "status": "ERROR",
            "returncode": None,
            "command": command,
            "started_at": started.isoformat(),
            "finished_at": utc_now(),
            "output_tail": str(exc),
        }
        if not continue_on_failure:
            raise
        return result


def write_reports(
    collected: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    improvement_candidates: list[dict[str, Any]],
    training_candidates: list[dict[str, Any]],
    command_results: list[dict[str, Any]],
) -> dict[str, Any]:
    label_counts = Counter(row.get("primary_label") for row in labels)
    stage_counts = Counter(row.get("recommended_stage") for row in labels)
    command_status = {row["name"]: row["status"] for row in command_results}
    report = {
        "status": "OK" if all(row["status"] == "OK" for row in command_results) else "COMPLETED_WITH_WARNINGS",
        "generated_at": utc_now(),
        "failed_queries_collected": len(collected),
        "labelled_issues": len(labels),
        "improvement_candidates": len(improvement_candidates),
        "training_candidates": len(training_candidates),
        "rejected_training_candidates": len(REJECTED_TRAINING_CANDIDATES),
        "label_counts": dict(label_counts),
        "stage_counts": dict(stage_counts),
        "command_status": command_status,
        "outputs": {
            "failed_queries": "outputs/learning/ragops_failed_queries.jsonl",
            "error_labels": "outputs/learning/ragops_error_labels.jsonl",
            "improvement_candidates": "outputs/learning/ragops_improvement_candidates.jsonl",
            "training_candidates": "outputs/model_learning/training_dataset_candidate.jsonl",
            "rejected_training_candidates": "outputs/model_learning/training_dataset_rejected.jsonl",
            "training_report": "outputs/model_learning/training_candidate_report.md",
            "report_json": "outputs/reports/ragops_learning_loop_report.json",
            "report_md": "outputs/reports/ragops_learning_loop_report.md",
        },
    }
    write_json(REPORTS / "ragops_learning_loop_report.json", report)

    lines = [
        "# RAGOps/LLMOps Learning Loop Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: `{report['status']}`",
        f"- failed_queries_collected: `{len(collected)}`",
        f"- labelled_issues: `{len(labels)}`",
        f"- improvement_candidates: `{len(improvement_candidates)}`",
        f"- fine_tuning_candidates: `{len(training_candidates)}`",
        f"- rejected_fine_tuning_candidates: `{len(REJECTED_TRAINING_CANDIDATES)}`",
        "",
        "## Stage Counts",
        "",
    ]
    for stage, count in stage_counts.most_common():
        lines.append(f"- `{stage}`: `{count}`")
    lines.extend(["", "## Label Counts", ""])
    for label, count in label_counts.most_common():
        lines.append(f"- `{label}`: `{count}`")
    lines.extend(["", "## Command Results", ""])
    for result in command_results:
        lines.append(f"- `{result['name']}`: `{result['status']}`")
    lines.extend([
        "",
        "## Fine-Tuning Gate",
        "",
        "Fine-tuning candidates were generated only as `REVIEW_ELIGIBLE` records.",
        "No model training job is executed by this loop.",
        "Authority-sensitive facts must remain in RAG/KG/Registry/serving tables.",
    ])
    (REPORTS / "ragops_learning_loop_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    training_lines = [
        "# Fine-Tuning Candidate Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- candidate_count: `{len(training_candidates)}`",
        "- status: `REVIEW_ELIGIBLE`",
        f"- rejected_authority_sensitive_candidates: `{len(REJECTED_TRAINING_CANDIDATES)}`",
        "",
        "## Policy",
        "",
        "- Do not train coordinates, counts, legal citations, S-101 definitions, or dataset provenance into model weights.",
        "- Use candidates only for linguistic intent, slot style, and clarification behavior after human review.",
        "- Exclude benchmark/test answer leakage before any fine-tuning job.",
        "",
        "## Candidates By Label",
        "",
    ]
    ft_counts = Counter(row.get("primary_label") for row in training_candidates)
    for label, count in ft_counts.most_common():
        training_lines.append(f"- `{label}`: `{count}`")
    training_lines.extend(["", "## Rejected Authority-Sensitive Candidates", ""])
    rejected_counts = Counter(row.get("primary_label") for row in REJECTED_TRAINING_CANDIDATES)
    if rejected_counts:
        for label, count in rejected_counts.most_common():
            training_lines.append(f"- `{label}`: `{count}`")
    else:
        training_lines.append("- none")
    (MODEL_LEARNING / "training_candidate_report.md").parent.mkdir(parents=True, exist_ok=True)
    (MODEL_LEARNING / "training_candidate_report.md").write_text("\n".join(training_lines) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--skip-document-upsert", action="store_true")
    parser.add_argument("--skip-benchmark", action="store_true")
    parser.add_argument("--benchmark-mode", choices=["api", "graph"], default="api")
    parser.add_argument("--benchmark-limit", type=int, default=12)
    parser.add_argument("--benchmark-timeout", type=float, default=90.0)
    parser.add_argument("--continue-on-failure", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    collected = collect_failed_queries()
    labels = [label_issue(row) for row in collected]
    improvement_candidates = build_improvement_candidates(labels)
    training_candidates = build_training_candidates(labels)

    write_jsonl(LEARNING / "ragops_failed_queries.jsonl", collected)
    write_jsonl(LEARNING / "ragops_error_labels.jsonl", labels)
    write_jsonl(LEARNING / "ragops_improvement_candidates.jsonl", improvement_candidates)
    write_jsonl(MODEL_LEARNING / "training_dataset_candidate.jsonl", training_candidates)
    write_jsonl(MODEL_LEARNING / "training_dataset_rejected.jsonl", REJECTED_TRAINING_CANDIDATES)

    command_results: list[dict[str, Any]] = []
    if not args.skip_embeddings:
        command_results.append(run_command(
            "capability_embedding_regeneration_and_upsert",
            [sys.executable, "scripts/build_capability_embeddings.py"],
            continue_on_failure=args.continue_on_failure,
        ))
    if not args.skip_document_upsert and (RAG / "dataset_supplemental_embeddings.jsonl").exists():
        command_results.append(run_command(
            "document_chunk_pgvector_upsert",
            [sys.executable, "scripts/merge_document_embeddings_to_live.py", "outputs/rag/dataset_supplemental_embeddings.jsonl"],
            continue_on_failure=args.continue_on_failure,
        ))
        command_results.append(run_command(
            "dataset_embedding_live_validation",
            [sys.executable, "scripts/verify_dataset_embedding_coverage.py"],
            continue_on_failure=args.continue_on_failure,
        ))
    if not args.skip_benchmark:
        benchmark_cmd = [
            sys.executable,
            "scripts/run_marine_benchmark.py",
            "--mode",
            args.benchmark_mode,
            "--timeout",
            str(args.benchmark_timeout),
        ]
        if args.benchmark_limit:
            benchmark_cmd.extend(["--limit", str(args.benchmark_limit)])
        command_results.append(run_command(
            "benchmark_regression",
            benchmark_cmd,
            continue_on_failure=True,
        ))
        command_results.append(run_command(
            "benchmark_failure_analysis",
            [sys.executable, "scripts/analyze_benchmark_failures.py"],
            continue_on_failure=args.continue_on_failure,
        ))

    report = write_reports(collected, labels, improvement_candidates, training_candidates, command_results)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
