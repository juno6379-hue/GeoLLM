"""Phase 8.5 evidence 후보를 생성한다.

S-101/DCEG 매칭 결과와 법령·고시 registry를 EvidenceItem 형태의 후보로
변환한다. 이 산출물은 검토/Graph-RAG 입력이며, registry 승인이나 Tool 실행
권한을 직접 부여하지 않는다.
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
OUT = ROOT / "outputs"
ONTOLOGY = OUT / "ontology"
EVIDENCE = OUT / "evidence"
REVIEW = OUT / "review"
DATA = ROOT / "data"

DEFAULT_MATCHES = ONTOLOGY / "s101_dceg_match_scores.jsonl"
DEFAULT_PROPOSALS = ONTOLOGY / "ontology_binding_proposals.jsonl"
DEFAULT_LEGAL_REGISTRY = DATA / "legal_notice_registry.yaml"
DEFAULT_KG = EVIDENCE / "kg_provenance_candidates.jsonl"
DEFAULT_RAG = EVIDENCE / "rag_evidence_candidates.jsonl"
DEFAULT_REGULATORY = EVIDENCE / "regulatory_evidence_candidates.jsonl"
DEFAULT_REVIEW = REVIEW / "evidence_candidate_needs_review.jsonl"
DEFAULT_SUMMARY = EVIDENCE / "phase85_evidence_candidate_summary.json"
DEFAULT_DATASET_EMBEDDINGS = OUT / "rag" / "dataset_supplemental_embeddings.jsonl"
DEFAULT_DATASET_COVERAGE = OUT / "reports" / "dataset_embedding_coverage.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def tokens(value: Any) -> set[str]:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value or "")
    return {item for item in re.findall(r"[\w/-]+", text.lower(), flags=re.UNICODE) if len(item) >= 2}


def layer_key_from_proposal(proposal: dict[str, Any]) -> str | None:
    candidate = proposal.get("registry_patch_candidate") or {}
    for registry_name in ("spatial_layer_registry", "data_registry"):
        registry_items = candidate.get(registry_name) or {}
        if registry_items:
            return next(iter(registry_items))
    return proposal.get("dataset_id")


def evidence_item(partition: str, evidence_type: str, summary: str, source_ref: str | None, data: dict[str, Any], score: float, review_required: bool) -> dict[str, Any]:
    payload = {
        "partition": partition,
        "evidence_type": evidence_type,
        "summary": summary,
        "source_ref": source_ref,
        "score": round(score, 4),
        "review_required": review_required,
        "data": data,
    }
    payload["evidence_id"] = stable_id(evidence_type, payload)
    return payload


def build_kg_and_rag_candidates(matches: list[dict[str, Any]], proposals: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kg_items: list[dict[str, Any]] = []
    rag_items: list[dict[str, Any]] = []
    for match in matches:
        proposal = proposals.get(match["proposal_id"], {})
        layer_id = layer_key_from_proposal(proposal) or match.get("dataset_id")
        top_features = match.get("top_feature_matches") or []
        for feature in top_features[:3]:
            score = float(feature.get("score") or 0.0)
            data = {
                "proposal_id": match.get("proposal_id"),
                "dataset_id": match.get("dataset_id"),
                "layer_id": layer_id,
                "feature_code": feature.get("feature_code"),
                "feature_name": feature.get("feature_name"),
                "confidence": feature.get("confidence"),
                "basis": feature.get("basis"),
                "suggested_binding": match.get("suggested_binding"),
                "verification_status": "CANDIDATE",
                "edge_candidates": [
                    {"subject": f"ontology_binding:{match.get('dataset_id')}", "predicate": "supportsFeature", "object": feature.get("feature_code")},
                    {"subject": layer_id, "predicate": "mapsToFeature", "object": feature.get("feature_code")},
                ],
                "provenance": match.get("provenance"),
            }
            kg_items.append(
                evidence_item(
                    "kg_provenance",
                    "kg_s101_feature_match_candidate",
                    f"{layer_id} -> S-101 {feature.get('feature_code')} ({feature.get('confidence')})",
                    "data/s101_feature_dictionary_v2.yaml",
                    data,
                    score,
                    match.get("review_required", True) or score < 0.65,
                )
            )
            for dceg in feature.get("dceg_evidence") or []:
                rag_score = min(1.0, score + 0.1)
                rag_items.append(
                    evidence_item(
                        "rag_evidence",
                        "rag_dceg_feature_evidence_candidate",
                        f"DCEG evidence for {feature.get('feature_code')} / {layer_id}",
                        dceg.get("source_file") or "outputs/rag/s101_dceg_chunks.jsonl",
                        {
                            "proposal_id": match.get("proposal_id"),
                            "dataset_id": match.get("dataset_id"),
                            "layer_id": layer_id,
                            "feature_code": feature.get("feature_code"),
                            "chunk_id": dceg.get("chunk_id"),
                            "page_no": dceg.get("page_no"),
                            "section": dceg.get("section"),
                            "verification_status": "CANDIDATE",
                        },
                        rag_score,
                        match.get("review_required", True),
                    )
                )
    return kg_items, rag_items


def legal_entries(registry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = registry.get("registries") or {}
    return (
        root.get("laws") or {},
        root.get("authorities") or {},
        root.get("legal_notices") or {},
        root.get("official_datasets") or {},
    )


def build_regulatory_candidates(
    proposals: dict[str, dict[str, Any]],
    legal_registry: dict[str, Any],
) -> list[dict[str, Any]]:
    laws, authorities, notices, datasets = legal_entries(legal_registry)
    items: list[dict[str, Any]] = []
    proposal_tokens = {
        proposal_id: tokens([proposal.get("dataset_id"), proposal.get("source_asset"), proposal.get("suggested_binding"), proposal.get("best_rule")])
        for proposal_id, proposal in proposals.items()
    }

    for dataset_id, dataset in datasets.items():
        governed_layers = dataset.get("governs_layers") or []
        basis_laws = dataset.get("basis_laws") or []
        authority = authorities.get(dataset.get("authority_id"), {})
        for layer_id in governed_layers:
            source_tokens = tokens([dataset_id, dataset, layer_id])
            matched_proposals = [
                proposal_id
                for proposal_id, qtokens in proposal_tokens.items()
                if layer_id.lower() in qtokens or len(qtokens & source_tokens) >= 2
            ]
            score = 0.85 if matched_proposals else 0.65
            items.append(
                evidence_item(
                    "regulatory_evidence",
                    "official_dataset_authority_candidate",
                    f"{layer_id} official dataset authority: {dataset_id}",
                    dataset.get("source_asset") or dataset.get("source_url"),
                    {
                        "layer_id": layer_id,
                        "official_dataset_id": dataset_id,
                        "authority_id": dataset.get("authority_id"),
                        "authority": authority,
                        "basis_laws": {law_id: laws.get(law_id, {}) for law_id in basis_laws},
                        "matched_proposals": matched_proposals,
                        "verification_status": dataset.get("verification_status", "CANDIDATE"),
                        "edge_candidates": [
                            {"subject": layer_id, "predicate": "authorizedBy", "object": dataset_id},
                            *[
                                {"subject": layer_id, "predicate": "definedBy", "object": law_id}
                                for law_id in basis_laws
                            ],
                        ],
                    },
                    score,
                    dataset.get("verification_status") != "VERIFIED",
                )
            )

    for notice_id, notice in notices.items():
        governed_layers = notice.get("governs_layers") or []
        basis_laws = notice.get("basis_laws") or []
        authority = authorities.get(notice.get("authority_id"), {})
        for layer_id in governed_layers:
            items.append(
                evidence_item(
                    "regulatory_evidence",
                    "legal_notice_authority_candidate",
                    f"{layer_id} legal notice authority: {notice_id}",
                    notice.get("source_url"),
                    {
                        "layer_id": layer_id,
                        "legal_notice_id": notice_id,
                        "authority_id": notice.get("authority_id"),
                        "authority": authority,
                        "basis_laws": {law_id: laws.get(law_id, {}) for law_id in basis_laws},
                        "notice": notice,
                        "verification_status": notice.get("verification_status", "CANDIDATE"),
                        "edge_candidates": [
                            {"subject": layer_id, "predicate": "authorizedBy", "object": notice_id},
                            *[
                                {"subject": layer_id, "predicate": "definedBy", "object": law_id}
                                for law_id in basis_laws
                            ],
                        ],
                    },
                    0.95 if notice.get("verification_status") == "VERIFIED" else 0.75,
                    notice.get("verification_status") != "VERIFIED",
                )
            )
    return items


def build_dataset_embedding_candidates(embeddings_path: Path, coverage_path: Path) -> list[dict[str, Any]]:
    """Expose newly embedded Dataset supplemental chunks as reviewable RAG evidence candidates."""
    rows = load_jsonl(embeddings_path)
    coverage = json.loads(coverage_path.read_text(encoding="utf-8")) if coverage_path.exists() else {}
    inventory = {
        item.get("source_file"): item
        for item in coverage.get("inventory", [])
        if isinstance(item, dict) and item.get("source_file")
    }
    items: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for row in rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        source_file = metadata.get("source_file") or metadata.get("source_path")
        if not source_file or source_file in seen_sources:
            continue
        seen_sources.add(source_file)
        source_inventory = inventory.get(source_file, {})
        document_type = metadata.get("document_type") or "dataset_profile"
        title = metadata.get("title") or Path(source_file).stem
        source_status = source_inventory.get("status") or document_type
        items.append(
            evidence_item(
                "rag_evidence",
                "dataset_embedding_coverage_candidate",
                f"Dataset embedding coverage: {title} ({document_type})",
                source_file,
                {
                    "chunk_id": row.get("chunk_id"),
                    "document_type": document_type,
                    "title": title,
                    "source_file": source_file,
                    "source_id": metadata.get("source_id"),
                    "section": metadata.get("section"),
                    "product_id": metadata.get("product_id"),
                    "related_concepts": metadata.get("related_concepts") or [],
                    "coverage_status": source_status,
                    "coverage_reason": source_inventory.get("reason"),
                    "supplemental_chunks": source_inventory.get("supplemental_chunks"),
                    "verification_status": "CANDIDATE",
                    "edge_candidates": [
                        {"subject": metadata.get("source_id") or source_file, "predicate": "supportsRagSource", "object": "knowledge.document_chunks"},
                        {"subject": metadata.get("source_id") or source_file, "predicate": "derivedFromDataset", "object": source_file},
                    ],
                },
                0.78 if document_type == "dataset_profile" else 0.72,
                True,
            )
        )
    return items


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 8.5 evidence 후보를 생성한다.")
    parser.add_argument("--matches", type=Path, default=DEFAULT_MATCHES)
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--legal-registry", type=Path, default=DEFAULT_LEGAL_REGISTRY)
    parser.add_argument("--kg-output", type=Path, default=DEFAULT_KG)
    parser.add_argument("--rag-output", type=Path, default=DEFAULT_RAG)
    parser.add_argument("--regulatory-output", type=Path, default=DEFAULT_REGULATORY)
    parser.add_argument("--review-output", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dataset-embeddings", type=Path, default=DEFAULT_DATASET_EMBEDDINGS)
    parser.add_argument("--dataset-coverage", type=Path, default=DEFAULT_DATASET_COVERAGE)
    args = parser.parse_args()

    matches = load_jsonl(args.matches)
    proposals = {row["proposal_id"]: row for row in load_jsonl(args.proposals)}
    legal_registry = load_yaml(args.legal_registry)

    kg_items, rag_items = build_kg_and_rag_candidates(matches, proposals)
    dataset_rag_items = build_dataset_embedding_candidates(args.dataset_embeddings, args.dataset_coverage)
    rag_items.extend(dataset_rag_items)
    regulatory_items = build_regulatory_candidates(proposals, legal_registry)
    review_items = [item for item in [*kg_items, *rag_items, *regulatory_items] if item.get("review_required")]
    summary = {
        "version": "0.1",
        "phase": "8.5",
        "kg_provenance_candidates": len(kg_items),
        "rag_evidence_candidates": len(rag_items),
        "dataset_embedding_candidates": len(dataset_rag_items),
        "regulatory_evidence_candidates": len(regulatory_items),
        "review_required_count": len(review_items),
        "policy": {
            "candidate_only": True,
            "registry_write": False,
            "execution_authority": False,
        },
    }

    write_jsonl(args.kg_output, kg_items)
    write_jsonl(args.rag_output, rag_items)
    write_jsonl(args.regulatory_output, regulatory_items)
    write_jsonl(args.review_output, review_items)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**summary, "summary": str(args.summary)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
