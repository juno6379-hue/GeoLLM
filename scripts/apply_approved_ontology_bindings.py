"""승인된 온톨로지 바인딩 후보만 registry에 병합한다.

이 스크립트는 Phase 8.3 승인 gate이다. `decision: approved`가 아니면
아무 registry에도 반영하지 않는다. 또한 기본적으로 `executable` 승격을
차단한다.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_PROPOSALS = ROOT / "outputs" / "ontology" / "ontology_binding_proposals.jsonl"
DEFAULT_DECISIONS = ROOT / "outputs" / "review" / "ontology_binding_review_decisions.yaml"
SPATIAL_REGISTRY = DATA / "spatial_layer_registry.yaml"
DATA_REGISTRY = DATA / "data_registry.yaml"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def approved_decisions(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = doc.get("decisions") or {}
    approved: dict[str, dict[str, Any]] = {}
    for proposal_id, decision in decisions.items():
        if decision.get("decision") == "approved":
            approved[proposal_id] = decision
    return approved


def validate_decision(proposal_id: str, decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not decision.get("reviewer"):
        errors.append(f"{proposal_id}: approved decision requires reviewer")
    if not decision.get("reviewed_at"):
        errors.append(f"{proposal_id}: approved decision requires reviewed_at")
    if not decision.get("reason"):
        errors.append(f"{proposal_id}: approved decision requires reason")
    if decision.get("decision") not in {"approved", "rejected", "hold"}:
        errors.append(f"{proposal_id}: unsupported decision={decision.get('decision')}")
    return errors


def candidate_for(proposal: dict[str, Any], target_registry: str) -> tuple[str, dict[str, Any]]:
    candidate = proposal.get("registry_patch_candidate") or {}
    if target_registry not in candidate:
        raise ValueError(f"{proposal['proposal_id']}: target_registry={target_registry} 후보가 없다.")
    registry_items = candidate[target_registry]
    if len(registry_items) != 1:
        raise ValueError(f"{proposal['proposal_id']}: registry 후보는 정확히 1개여야 한다.")
    item_id, item = next(iter(registry_items.items()))
    return item_id, deepcopy(item)


def enrich_candidate(item: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    item = deepcopy(item)
    item["verification_status"] = decision.get("verification_status_override") or item.get("verification_status") or proposal.get("verification_status")
    item["review_status"] = "approved"
    item["reviewer"] = decision.get("reviewer")
    item["reviewed_at"] = decision.get("reviewed_at")
    item["review_reason"] = decision.get("reason")
    item["proposal_id"] = proposal.get("proposal_id")
    item["source_provenance"] = {
        "source_asset": proposal.get("source_asset"),
        "proposal_source": "outputs/ontology/ontology_binding_proposals.jsonl",
        "decision_source": "outputs/review/ontology_binding_review_decisions.yaml",
    }
    return item


def merge_item(
    registry_doc: dict[str, Any],
    collection_key: str,
    item_id: str,
    item: dict[str, Any],
    *,
    overwrite: bool,
) -> str:
    registry_doc.setdefault(collection_key, {})
    collection = registry_doc[collection_key]
    existed = item_id in collection
    if existed and not overwrite:
        return "skipped_existing"
    collection[item_id] = item
    return "overwritten" if existed else "merged"


def apply_approved(args: argparse.Namespace) -> dict[str, Any]:
    proposals = {row["proposal_id"]: row for row in load_jsonl(args.proposals)}
    decisions_doc = load_yaml(args.decisions)
    approved = approved_decisions(decisions_doc)
    spatial_doc = load_yaml(SPATIAL_REGISTRY)
    data_doc = load_yaml(DATA_REGISTRY)

    errors: list[str] = []
    actions: list[dict[str, Any]] = []
    for proposal_id, decision in approved.items():
        errors.extend(validate_decision(proposal_id, decision))
        proposal = proposals.get(proposal_id)
        if not proposal:
            errors.append(f"{proposal_id}: proposal not found")
            continue
        target_registry = decision.get("target_registry")
        try:
            item_id, item = candidate_for(proposal, target_registry)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        item = enrich_candidate(item, proposal, decision)
        if item.get("execution_status") == "executable" and not args.allow_executable:
            errors.append(f"{proposal_id}: executable 승격은 Phase 8.3 기본 정책에서 금지된다.")
            continue
        if target_registry == "spatial_layer_registry":
            result = merge_item(spatial_doc, "layers", item_id, item, overwrite=args.overwrite)
        elif target_registry == "data_registry":
            result = merge_item(data_doc, "datasets", item_id, item, overwrite=args.overwrite)
        else:
            errors.append(f"{proposal_id}: unsupported target_registry={target_registry}")
            continue
        actions.append({"proposal_id": proposal_id, "target_registry": target_registry, "item_id": item_id, "result": result})

    if errors:
        return {"status": "FAILED", "errors": errors, "actions": actions, "approved_count": len(approved)}
    if args.write:
        write_yaml(SPATIAL_REGISTRY, spatial_doc)
        write_yaml(DATA_REGISTRY, data_doc)
    return {
        "status": "PASS",
        "mode": "write" if args.write else "dry_run",
        "approved_count": len(approved),
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="승인된 온톨로지 바인딩 후보만 registry에 병합한다.")
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--write", action="store_true", help="지정하지 않으면 dry-run만 수행한다.")
    parser.add_argument("--overwrite", action="store_true", help="기존 registry 항목 덮어쓰기를 허용한다.")
    parser.add_argument("--allow-executable", action="store_true", help="검증된 물리 테이블이 있는 경우에만 별도 단계에서 사용한다.")
    args = parser.parse_args()
    result = apply_approved(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
