"""KG, RAG, 공간, 사고, 법령 근거를 typed EvidenceBundle로 변환한다."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from shared.schemas.agent import EvidenceBundle, EvidenceItem


ROOT = Path(__file__).resolve().parents[2]
KG_EDGES = ROOT / "outputs/graph/kg_edges_v2.jsonl"
EVIDENCE_OUTPUTS = ROOT / "outputs/evidence"


def _stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def evidence_candidates_to_items(
    path: Path | str,
    *,
    partition: str | None = None,
    min_score: float = 0.0,
    include_review_required: bool = True,
) -> list[EvidenceItem]:
    """Load Phase 8.5 evidence candidates as typed EvidenceItem values.

    Candidate evidence remains candidate evidence; this helper only converts the
    persisted shape into the runtime EvidenceItem model.
    """
    items: list[EvidenceItem] = []
    for row in _load_jsonl(Path(path)):
        if partition and row.get("partition") != partition:
            continue
        if float(row.get("score") or 0.0) < min_score:
            continue
        if row.get("review_required") and not include_review_required:
            continue
        data = row.get("data") if isinstance(row.get("data"), dict) else dict(row)
        data.setdefault("score", row.get("score"))
        data.setdefault("review_required", row.get("review_required"))
        data.setdefault("partition", row.get("partition"))
        items.append(EvidenceItem(
            evidence_id=row.get("evidence_id") or _stable_id(row.get("evidence_type") or "candidate", row),
            evidence_type=row.get("evidence_type") or "evidence_candidate",
            summary=row.get("summary"),
            source_ref=row.get("source_ref"),
            data=data,
        ))
    return items


def phase85_candidates_bundle(*, min_score: float = 0.0, include_review_required: bool = True) -> EvidenceBundle:
    """Build an EvidenceBundle from Phase 8.5 candidate files."""
    kg_items = evidence_candidates_to_items(
        EVIDENCE_OUTPUTS / "kg_provenance_candidates.jsonl",
        partition="kg_provenance",
        min_score=min_score,
        include_review_required=include_review_required,
    )
    rag_items = evidence_candidates_to_items(
        EVIDENCE_OUTPUTS / "rag_evidence_candidates.jsonl",
        partition="rag_evidence",
        min_score=min_score,
        include_review_required=include_review_required,
    )
    regulatory_items = evidence_candidates_to_items(
        EVIDENCE_OUTPUTS / "regulatory_evidence_candidates.jsonl",
        partition="regulatory_evidence",
        min_score=min_score,
        include_review_required=include_review_required,
    )
    return EvidenceBundle(
        kg_provenance=kg_items,
        rag_evidence=rag_items,
        regulatory_evidence=regulatory_items,
    )


def _edge_index() -> dict[tuple[str, str], dict[str, Any]]:
    if not KG_EDGES.exists():
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for line in KG_EDGES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        edge = json.loads(line)
        subject = edge.get("subject_id")
        obj = edge.get("object_id")
        if subject and obj:
            index[(subject, obj)] = edge
            index[(obj, subject)] = edge
    return index


def kg_paths_to_evidence(graph_context: dict[str, Any] | None) -> list[EvidenceItem]:
    graph_context = graph_context or {}
    paths = graph_context.get("graph_paths") or []
    edges = _edge_index()
    items: list[EvidenceItem] = []
    for idx, path_item in enumerate(paths):
        path = path_item.get("path") or []
        path_edges = []
        for source, target in zip(path, path[1:]):
            edge = edges.get((source, target))
            if edge:
                path_edges.append({
                    "edge_id": edge.get("id"),
                    "predicate": edge.get("predicate"),
                    "subject_id": edge.get("subject_id"),
                    "object_id": edge.get("object_id"),
                    "verification_status": edge.get("verification_status") or edge.get("status") or (edge.get("properties") or {}).get("verification_status"),
                    "provenance": edge.get("provenance", {}),
                })
        payload = {
            "seed": path_item.get("seed"),
            "path": path,
            "node_names": path_item.get("node_names") or [],
            "path_edges": path_edges,
            "graph_provenance": graph_context.get("provenance", {}),
        }
        items.append(EvidenceItem(
            evidence_id=path_item.get("evidence_id") or _stable_id("kg", payload),
            evidence_type="kg_path",
            summary=" > ".join(path_item.get("node_names") or path or [f"graph path {idx + 1}"]),
            source_ref=(graph_context.get("provenance") or {}).get("graph_nodes", "outputs/graph/kg_nodes_v2.jsonl"),
            data=payload,
        ))
    return items


def rag_citations_to_evidence(citations: list[dict[str, Any]] | None) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for citation in citations or []:
        source_ref = citation.get("source_file") or citation.get("source") or citation.get("source_id")
        payload = dict(citation)
        items.append(EvidenceItem(
            evidence_id=citation.get("evidence_id") or _stable_id("rag", payload),
            evidence_type="rag_citation",
            summary=citation.get("section") or citation.get("source") or citation.get("document_id") or "RAG citation",
            source_ref=source_ref,
            data=payload,
        ))
    return items


def generic_items_to_evidence(items: list[dict[str, Any]] | None, *, default_type: str = "evidence_candidate") -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        payload = item.get("data") if isinstance(item.get("data"), dict) else dict(item)
        evidence.append(EvidenceItem(
            evidence_id=item.get("evidence_id") or _stable_id(default_type, item),
            evidence_type=item.get("evidence_type") or default_type,
            summary=item.get("summary"),
            source_ref=item.get("source_ref"),
            data=payload,
        ))
    return evidence


def spatial_features_to_evidence(items: list[dict[str, Any]] | None, *, task_id: str = "") -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for idx, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        payload = item.get("data") if isinstance(item.get("data"), dict) else dict(item)
        evidence.append(EvidenceItem(
            evidence_id=item.get("evidence_id") or _stable_id("spatial", {"task_id": task_id, "idx": idx, "payload": payload}),
            evidence_type=item.get("evidence_type") or "spatial_feature",
            summary=item.get("summary") or payload.get("feature_name") or payload.get("name") or "spatial feature",
            source_ref=item.get("source_ref"),
            data=payload,
        ))
    return evidence


def spatial_layers_to_evidence(items: list[dict[str, Any]] | None, *, task_id: str = "") -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for idx, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        payload = item.get("data") if isinstance(item.get("data"), dict) else dict(item)
        evidence.append(EvidenceItem(
            evidence_id=item.get("evidence_id") or _stable_id("spatial-layer", {"task_id": task_id, "idx": idx, "payload": payload}),
            evidence_type=item.get("evidence_type") or payload.get("layer_type") or "spatial_layer",
            summary=item.get("summary") or payload.get("layer_id") or payload.get("name") or "공간 레이어 근거",
            source_ref=item.get("source_ref") or payload.get("relation") or payload.get("source_asset"),
            data=payload,
        ))
    return evidence


def accident_relations_to_evidence(relations: list[dict[str, Any]] | None) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for relation in relations or []:
        if not isinstance(relation, dict):
            continue
        evidence.append(EvidenceItem(
            evidence_id=relation.get("evidence_id") or _stable_id("accident", relation),
            evidence_type="accident_relation",
            summary=relation.get("summary") or relation.get("accident_type") or relation.get("relation") or "accident relation",
            source_ref=relation.get("source_ref") or relation.get("relation_table") or "serving.accident_s101_relation_current",
            data=dict(relation),
        ))
    return evidence


def regulatory_items_to_evidence(items: list[dict[str, Any]] | None) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        payload = item.get("data") if isinstance(item.get("data"), dict) else dict(item)
        evidence.append(EvidenceItem(
            evidence_id=item.get("evidence_id") or _stable_id("regulatory", payload),
            evidence_type=item.get("evidence_type") or payload.get("notice_type") or "regulatory_evidence",
            summary=item.get("summary") or payload.get("title_ko") or payload.get("notice_no") or "법령/고시 근거",
            source_ref=item.get("source_ref") or payload.get("source_url") or payload.get("source_asset"),
            data=payload,
        ))
    return evidence


def build_evidence_bundle(
    *,
    graph_context: dict[str, Any] | None = None,
    structured_result: dict[str, Any] | None = None,
    spatial_feature_evidence: list[dict[str, Any]] | None = None,
    task_id: str = "",
) -> EvidenceBundle:
    structured_result = structured_result or {}
    accident_relations = (
        structured_result.get("accident_relation_evidence")
        or structured_result.get("accident_feature_relations")
        or structured_result.get("relations")
    )
    kg_candidate_items = structured_result.get("kg_provenance_candidates") or []
    rag_candidate_items = structured_result.get("rag_evidence_candidates") or []
    regulatory_candidate_items = structured_result.get("regulatory_evidence_candidates") or []
    return EvidenceBundle(
        spatial_feature_evidence=spatial_features_to_evidence(spatial_feature_evidence, task_id=task_id),
        spatial_layer_evidence=spatial_layers_to_evidence(structured_result.get("spatial_layer_evidence") or [], task_id=task_id),
        accident_relation_evidence=accident_relations_to_evidence(accident_relations if isinstance(accident_relations, list) else []),
        regulatory_evidence=regulatory_items_to_evidence(structured_result.get("regulatory_evidence") or []) + generic_items_to_evidence(regulatory_candidate_items, default_type="regulatory_evidence_candidate"),
        rag_evidence=rag_citations_to_evidence(structured_result.get("citations") or structured_result.get("rag_evidence") or []) + generic_items_to_evidence(rag_candidate_items, default_type="rag_evidence_candidate"),
        kg_provenance=kg_paths_to_evidence(graph_context or structured_result.get("graph_context") or {}) + generic_items_to_evidence(kg_candidate_items, default_type="kg_provenance_candidate"),
    )
