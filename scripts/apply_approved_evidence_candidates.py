"""Phase 8.7 승인된 evidence 후보만 registry로 승격한다.

승격 대상은 `decision: approved`인 항목뿐이다. `review_required` 후보는
검토자가 `review_required_accepted: true`를 명시해야 승인될 수 있다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVIDENCE = ROOT / "outputs" / "evidence"
REVIEW = ROOT / "outputs" / "review"
DEFAULT_DECISIONS = REVIEW / "evidence_candidate_review_decisions.yaml"
DEFAULT_REGISTRY = DATA / "evidence_registry.yaml"
DEFAULT_INPUTS = [
    EVIDENCE / "kg_provenance_candidates.jsonl",
    EVIDENCE / "rag_evidence_candidates.jsonl",
    EVIDENCE / "regulatory_evidence_candidates.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path)


def stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def load_candidates(paths: list[Path]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in load_jsonl(path):
            if row.get("evidence_id"):
                rows[row["evidence_id"]] = row
    return rows


def approved_decisions(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = doc.get("decisions") or {}
    return {
        evidence_id: decision
        for evidence_id, decision in decisions.items()
        if decision.get("decision") == "approved"
    }


def validate_decision(evidence_id: str, decision: dict[str, Any], candidate: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not candidate:
        errors.append(f"{evidence_id}: candidate not found")
        return errors
    if not decision.get("reviewer"):
        errors.append(f"{evidence_id}: approved decision requires reviewer")
    if not decision.get("reviewed_at"):
        errors.append(f"{evidence_id}: approved decision requires reviewed_at")
    if not decision.get("reason"):
        errors.append(f"{evidence_id}: approved decision requires reason")
    if candidate.get("review_required") and not decision.get("review_required_accepted"):
        errors.append(f"{evidence_id}: review_required candidate requires review_required_accepted=true")
    if candidate.get("partition") not in {"kg_provenance", "rag_evidence", "regulatory_evidence"}:
        errors.append(f"{evidence_id}: unsupported partition={candidate.get('partition')}")
    return errors


def registry_item(candidate: dict[str, Any], decision: dict[str, Any], decision_source: Path, input_sources: list[Path]) -> dict[str, Any]:
    data = deepcopy(candidate.get("data") if isinstance(candidate.get("data"), dict) else {})
    data.setdefault("score", candidate.get("score"))
    data.setdefault("review_required", candidate.get("review_required"))
    data.setdefault("partition", candidate.get("partition"))
    verification_status = decision.get("verification_status_override") or "VERIFIED"
    return {
        "partition": candidate.get("partition"),
        "evidence_type": candidate.get("evidence_type"),
        "summary": candidate.get("summary"),
        "source_ref": candidate.get("source_ref"),
        "score": candidate.get("score"),
        "verification_status": verification_status,
        "review_status": "approved",
        "reviewer": decision.get("reviewer"),
        "reviewed_at": decision.get("reviewed_at"),
        "review_reason": decision.get("reason"),
        "data": data,
        "provenance": {
            "candidate_sources": [relpath(path) for path in input_sources],
            "decision_source": relpath(decision_source),
            "original_evidence_id": candidate.get("evidence_id"),
        },
    }


def kg_edges_for(evidence_id: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    edges = []
    for edge in data.get("edge_candidates") or []:
        if not isinstance(edge, dict):
            continue
        subject = edge.get("subject")
        predicate = edge.get("predicate")
        obj = edge.get("object")
        if not subject or not predicate or not obj:
            continue
        payload = {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "verification_status": item.get("verification_status"),
            "evidence_id": evidence_id,
            "source_ref": item.get("source_ref"),
        }
        payload["edge_id"] = stable_id("approved_evidence_edge", payload)
        edges.append(payload)
    return edges


def apply_approved(args: argparse.Namespace) -> dict[str, Any]:
    candidates = load_candidates(args.inputs)
    decisions_doc = load_yaml(args.decisions)
    approved = approved_decisions(decisions_doc)
    registry = load_yaml(args.registry)
    registry.setdefault("version", "0.1")
    registry.setdefault("evidence_items", {})
    registry.setdefault("kg_edge_promotions", {})

    errors: list[str] = []
    actions: list[dict[str, Any]] = []
    for evidence_id, decision in approved.items():
        candidate = candidates.get(evidence_id)
        item_errors = validate_decision(evidence_id, decision, candidate)
        errors.extend(item_errors)
        if not candidate:
            continue
        if item_errors:
            continue
        item = registry_item(candidate, decision, args.decisions, args.inputs)
        existed = evidence_id in registry["evidence_items"]
        if existed and not args.overwrite:
            actions.append({"evidence_id": evidence_id, "result": "skipped_existing"})
            continue
        registry["evidence_items"][evidence_id] = item
        registry["kg_edge_promotions"][evidence_id] = kg_edges_for(evidence_id, item)
        actions.append({
            "evidence_id": evidence_id,
            "partition": candidate.get("partition"),
            "edge_promotions": len(registry["kg_edge_promotions"][evidence_id]),
            "result": "overwritten" if existed else "merged",
        })

    if errors:
        return {"status": "FAILED", "approved_count": len(approved), "errors": errors, "actions": actions}
    if args.write:
        write_yaml(args.registry, registry)
    return {
        "status": "PASS",
        "mode": "write" if args.write else "dry_run",
        "approved_count": len(approved),
        "registry": relpath(args.registry),
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 8.7 승인된 evidence 후보만 registry로 승격한다.")
    parser.add_argument("--inputs", nargs="*", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--write", action="store_true", help="지정하지 않으면 dry-run만 수행한다.")
    parser.add_argument("--overwrite", action="store_true", help="기존 evidence registry 항목 덮어쓰기를 허용한다.")
    args = parser.parse_args()
    result = apply_approved(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
