"""온톨로지 바인딩 제안서를 검토용 decision YAML로 변환한다.

기본 decision은 모두 hold이다. 이 파일에서 사람이 명시적으로
`decision: approved`를 지정한 항목만 registry 병합 대상이 된다.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROPOSALS = ROOT / "outputs" / "ontology" / "ontology_binding_proposals.jsonl"
DEFAULT_S101_MATCHES = ROOT / "outputs" / "ontology" / "s101_dceg_match_scores.jsonl"
DEFAULT_OUTPUT = ROOT / "outputs" / "review" / "ontology_binding_review_decisions.yaml"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def registry_target(proposal: dict[str, Any]) -> str:
    candidate = proposal.get("registry_patch_candidate") or {}
    if "spatial_layer_registry" in candidate:
        return "spatial_layer_registry"
    if "data_registry" in candidate:
        return "data_registry"
    return "unknown"


def compact_evidence(proposal: dict[str, Any]) -> dict[str, Any]:
    evidence = proposal.get("deterministic_evidence") or {}
    spatial = evidence.get("spatial_profile") or {}
    zip_info = evidence.get("zip") or {}
    return {
        "format": evidence.get("format"),
        "file_size": evidence.get("file_size"),
        "source_sha256": evidence.get("source_sha256"),
        "has_shapefile": spatial.get("has_shapefile"),
        "spatial_profile_status": spatial.get("profile_status"),
        "shape_types": spatial.get("shape_types"),
        "record_count": spatial.get("record_count"),
        "member_count": zip_info.get("member_count"),
        "extensions": zip_info.get("extensions"),
    }


def compact_s101_match(match: dict[str, Any] | None) -> dict[str, Any] | None:
    if not match:
        return None
    top = (match.get("top_feature_matches") or [None])[0]
    return {
        "match_status": match.get("match_status"),
        "review_required": match.get("review_required"),
        "review_reasons": match.get("review_reasons"),
        "s101_product_applicable": match.get("s101_product_applicable"),
        "missing_catalogue_hints": match.get("missing_catalogue_hints"),
        "top_feature": {
            "feature_code": top.get("feature_code"),
            "feature_name": top.get("feature_name"),
            "score": top.get("score"),
            "confidence": top.get("confidence"),
            "basis": top.get("basis"),
        }
        if top
        else None,
        "top_attributes": [
            {
                "attribute_code": item.get("attribute_code"),
                "attribute_name": item.get("attribute_name"),
                "score": item.get("score"),
                "aliases": item.get("aliases"),
            }
            for item in (match.get("top_attribute_matches") or [])[:3]
        ],
    }


def build_decision_template(proposals: list[dict[str, Any]], s101_matches: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    s101_matches = s101_matches or {}
    decisions: dict[str, Any] = {}
    for proposal in sorted(proposals, key=lambda row: row["dataset_id"]):
        proposal_id = proposal["proposal_id"]
        decisions[proposal_id] = {
            "dataset_id": proposal["dataset_id"],
            "source_asset": proposal["source_asset"],
            "decision": "hold",
            "target_registry": registry_target(proposal),
            "reviewer": None,
            "reviewed_at": None,
            "reason": "자동 생성된 검토 초안이다. 승인/반려/보류 사유를 사람이 작성한다.",
            "proposal_status": proposal.get("verification_status"),
            "execution_status_suggestion": proposal.get("execution_status_suggestion"),
            "suggested_binding": proposal.get("suggested_binding"),
            "best_rule": proposal.get("best_rule"),
            "deterministic_evidence_summary": compact_evidence(proposal),
            "s101_dceg_match": compact_s101_match(s101_matches.get(proposal_id)),
        }
    return {
        "version": "0.1",
        "status": "review_template",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DEFAULT_PROPOSALS.relative_to(ROOT)).replace("\\", "/"),
        "policy": {
            "default_decision": "hold",
            "allowed_decisions": ["approved", "rejected", "hold"],
            "approved_requires": ["reviewer", "reviewed_at", "reason"],
            "executable_auto_promotion": False,
        },
        "decisions": decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="온톨로지 바인딩 제안서를 검토 decision YAML로 변환한다.")
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--s101-matches", type=Path, default=DEFAULT_S101_MATCHES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    proposals = load_jsonl(args.proposals)
    s101_matches = {row["proposal_id"]: row for row in load_jsonl(args.s101_matches)}
    doc = build_decision_template(proposals, s101_matches)
    doc["source"] = str(args.proposals.relative_to(ROOT)).replace("\\", "/") if args.proposals.is_relative_to(ROOT) else str(args.proposals)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"decisions": len(doc["decisions"]), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
