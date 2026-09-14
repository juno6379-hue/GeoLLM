"""Dataset 프로파일에서 온톨로지/도메인/S-100 바인딩 후보를 제안한다.

출력은 실행 권한이 없는 제안서와 NEEDS_REVIEW 큐다. 실제 registry 반영은
사람 검토 또는 별도 승인 절차 이후에만 수행한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_PROFILES = ROOT / "outputs" / "ontology" / "dataset_profiles.jsonl"
DEFAULT_PROPOSALS = ROOT / "outputs" / "ontology" / "ontology_binding_proposals.jsonl"
DEFAULT_PATCH = ROOT / "outputs" / "ontology" / "registry_patch_proposals.yaml"
DEFAULT_REVIEW = ROOT / "outputs" / "review" / "ontology_binding_needs_review.jsonl"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_profiles(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def normalize_text(values: list[Any]) -> str:
    text = " ".join(str(value) for value in values if value)
    return re.sub(r"\s+", " ", text).lower()


def score_rule(profile: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    haystack = normalize_text(profile.get("text_signals") or [])
    matched = [kw for kw in rule.get("keywords", []) if str(kw).lower() in haystack]
    excluded = [kw for kw in rule.get("exclude_keywords", []) if str(kw).lower() in haystack]
    score = len(matched) - (len(excluded) * 2)
    return {"rule_id": rule["rule_id"], "score": score, "matched_keywords": matched, "excluded_keywords": excluded}


def infer_execution_status(profile: dict[str, Any], policy: dict[str, str]) -> str:
    fmt = profile.get("format")
    spatial = profile.get("spatial_profile") or {}
    if fmt == "zip" and spatial.get("has_shapefile") and spatial.get("profile_status") == "SKIPPED_LARGE_ARCHIVE":
        return policy.get("binary_or_grid_archive", "metadata_only")
    if fmt == "zip" and spatial.get("has_shapefile"):
        return policy.get("shapefile_with_geometry", "needs_ingestion")
    if fmt in {"tabular", "spreadsheet"}:
        return policy.get("tabular_accident_or_law", "rag_or_table_review")
    if fmt in {"document", "structured_document"}:
        return policy.get("standard_document", "rag_ready_after_chunking")
    return policy.get("unknown", "NEEDS_REVIEW")


def choose_review_status(scores: list[dict[str, Any]], thresholds: dict[str, int], execution_status: str) -> str:
    best = scores[0] if scores else {"score": 0}
    if best["score"] < thresholds.get("auto_candidate_min_score", 2):
        return "NEEDS_REVIEW"
    if execution_status in {"metadata_only", "rag_or_table_review", "NEEDS_REVIEW"}:
        return "NEEDS_REVIEW"
    return "CANDIDATE"


def expected_table(dataset_id: str) -> str:
    safe = re.sub(r"[^0-9a-zA-Z_]+", "_", dataset_id).strip("_").lower()
    if not safe:
        safe = "dataset_" + hashlib.sha256(dataset_id.encode("utf-8")).hexdigest()[:10]
    elif safe != dataset_id.lower():
        safe = f"{safe}_{hashlib.sha256(dataset_id.encode('utf-8')).hexdigest()[:8]}"
    return f"serving.{safe}_current"


def empty_binding() -> dict[str, Any]:
    return {
        "upper_class": None,
        "semantic_mapping": None,
        "domain_candidates": [],
        "product_candidates": [],
        "layer_type": "unclassified",
    }


def registry_candidate(
    layer_id: str,
    profile: dict[str, Any],
    binding: dict[str, Any],
    execution_status: str,
    status: str,
) -> dict[str, Any]:
    fmt = profile.get("format")
    layer_type = binding.get("layer_type")
    if layer_type == "document_reference" or fmt in {"document", "structured_document"}:
        return {
            "data_registry": {
                layer_id: {
                    "zone": "raw",
                    "dataset_type": layer_type or "document_reference",
                    "execution_status": execution_status,
                    "source_asset": profile["source_asset"],
                    "verification_status": status,
                }
            }
        }
    return {
        "spatial_layer_registry": {
            layer_id: {
                "zone": "standardized",
                "layer_type": layer_type or "unclassified",
                "execution_status": execution_status,
                "source_asset": profile["source_asset"],
                "expected_physical_table": expected_table(layer_id),
                "geometry_column": "geometry",
                "srid": 4326,
                "supported_operations": ["intersects", "dwithin"],
                "verification_status": status,
            }
        }
    }


def build_proposal(profile: dict[str, Any], rules_doc: dict[str, Any]) -> dict[str, Any]:
    rules = rules_doc.get("classification_rules", [])
    scores = [score_rule(profile, rule) for rule in rules]
    scores.sort(key=lambda item: item["score"], reverse=True)
    by_id = {rule["rule_id"]: rule for rule in rules}
    best_score = scores[0] if scores else {"rule_id": "unknown", "score": 0, "matched_keywords": [], "excluded_keywords": []}
    best_rule = by_id.get(best_score["rule_id"], {}) if best_score["score"] > 0 else {}
    execution_status = infer_execution_status(profile, rules_doc.get("execution_status_policy", {}))
    status = choose_review_status(scores, rules_doc.get("review_thresholds", {}), execution_status)
    layer_id = profile["dataset_id"]
    binding = (
        {
            "upper_class": best_rule.get("upper_class"),
            "semantic_mapping": best_rule.get("semantic_mapping"),
            "domain_candidates": best_rule.get("domain_candidates", []),
            "product_candidates": best_rule.get("product_candidates", []),
            "layer_type": best_rule.get("layer_type", "unclassified"),
        }
        if best_rule
        else empty_binding()
    )
    proposal = {
        "proposal_id": f"ontology_binding:{layer_id}",
        "dataset_id": layer_id,
        "source_asset": profile["source_asset"],
        "verification_status": status,
        "execution_status_suggestion": execution_status,
        "best_rule": best_score,
        "alternate_rules": scores[1:4],
        "suggested_binding": binding,
        "deterministic_evidence": {
            "format": profile.get("format"),
            "file_size": profile.get("file_size"),
            "modified_at": profile.get("modified_at"),
            "source_sha256": profile.get("source_sha256"),
            "spatial_profile": profile.get("spatial_profile"),
            "zip": profile.get("zip"),
        },
        "registry_patch_candidate": registry_candidate(layer_id, profile, binding, execution_status, status),
        "review_required": status != "CANDIDATE",
    }
    if not best_rule:
        proposal["review_reason"] = "분류 규칙과 충분히 매칭되지 않았다."
    elif execution_status != "needs_ingestion":
        proposal["review_reason"] = "공간 실행 레이어로 바로 승격할 수 없는 포맷 또는 대용량/문서형 자산이다."
    return proposal


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset 프로파일에서 온톨로지 바인딩 후보를 생성한다.")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--rules", type=Path, default=DATA / "ontology_ingestion_rules.yaml")
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    args = parser.parse_args()

    rules_doc = load_yaml(args.rules)
    profiles = load_profiles(args.profiles)
    proposals = [build_proposal(profile, rules_doc) for profile in profiles]
    review_rows = [row for row in proposals if row.get("review_required")]
    patch_doc = {
        "version": "0.1",
        "status": "proposal_only",
        "description": "자동 생성된 registry 후보이다. 검토 전에는 data/spatial registry에 병합하지 않는다.",
        "spatial_layer_registry_candidates": {
            proposal["dataset_id"]: proposal["registry_patch_candidate"]["spatial_layer_registry"][proposal["dataset_id"]]
            for proposal in proposals
            if "spatial_layer_registry" in proposal["registry_patch_candidate"]
            and proposal["suggested_binding"].get("layer_type") not in {None, "document_reference", "unclassified"}
        },
        "data_registry_candidates": {
            proposal["dataset_id"]: proposal["registry_patch_candidate"]["data_registry"][proposal["dataset_id"]]
            for proposal in proposals
            if "data_registry" in proposal["registry_patch_candidate"]
        },
    }

    write_jsonl(args.proposals, proposals)
    write_jsonl(args.review, review_rows)
    args.patch.parent.mkdir(parents=True, exist_ok=True)
    with args.patch.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(patch_doc, fh, allow_unicode=True, sort_keys=True)

    print(
        json.dumps(
            {
                "profiles": len(profiles),
                "proposals": len(proposals),
                "review_required": len(review_rows),
                "proposals_path": str(args.proposals),
                "review_path": str(args.review),
                "patch_path": str(args.patch),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
