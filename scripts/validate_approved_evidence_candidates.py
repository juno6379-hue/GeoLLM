"""Phase 8.9 deterministic validation for approved evidence candidates.

The validator does not grant execution authority. It checks whether approved
evidence candidates can be safely promoted into the registry/KG layer, and
returns NEEDS_REVIEW when the current KG, RAG chunk store, or registry metadata
does not support the approval cleanly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.apply_approved_evidence_candidates import (
    DEFAULT_DECISIONS,
    DEFAULT_INPUTS,
    DEFAULT_REGISTRY,
    approved_decisions,
    kg_edges_for,
    load_candidates,
    load_yaml,
    registry_item,
    validate_decision,
)


DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
DEFAULT_NODES = OUTPUTS / "graph" / "kg_nodes_v2.jsonl"
DEFAULT_EDGES = OUTPUTS / "graph" / "kg_edges_v2.jsonl"
DEFAULT_REPORT = OUTPUTS / "review" / "approved_evidence_validation_report.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def load_yaml_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path)


def slug(value: Any) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value)).strip("_").lower() or "unknown"


def nid(kind: str, value: Any) -> str:
    return f"{slug(kind)}:{slug(value)}"


def load_registry_layers() -> dict[str, dict[str, Any]]:
    layers: dict[str, dict[str, Any]] = {}
    for path in [
        DATA / "spatial_layer_registry.yaml",
        DATA / "traffic_layer_registry.yaml",
        DATA / "data_registry.yaml",
    ]:
        doc = load_yaml_path(path)
        source_key = "datasets" if path.name == "data_registry.yaml" else "layers"
        for layer_id, meta in (doc.get(source_key) or {}).items():
            if isinstance(meta, dict):
                layers[layer_id] = {**meta, "_source": relpath(path)}
    return layers


def load_feature_codes() -> set[str]:
    path = DATA / "s101_feature_catalogue_v2_parsed.json"
    if not path.exists():
        return set()
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {item.get("code") for item in doc.get("features", []) if item.get("code")}


def load_legal_refs() -> set[str]:
    doc = load_yaml_path(DATA / "legal_notice_registry.yaml")
    registries = doc.get("registries") or {}
    refs: set[str] = set()
    for key in ["authorities", "laws", "legal_notices", "official_datasets"]:
        refs.update((registries.get(key) or {}).keys())
    return refs


def load_rag_chunks() -> set[str]:
    chunks: set[str] = set()
    rag_dir = OUTPUTS / "rag"
    if not rag_dir.exists():
        return chunks
    for path in rag_dir.glob("*.jsonl"):
        for row in load_jsonl(path):
            chunk_id = row.get("chunk_id") or row.get("id")
            if chunk_id:
                chunks.add(str(chunk_id))
    return chunks


def evidence_ref_node(ref: Any, predicate: str | None, feature_codes: set[str], legal_refs: set[str], registry_layers: dict[str, Any]) -> str:
    value = str(ref)
    if value.startswith("ontology_binding:"):
        return nid("OntologyBindingProposal", value)
    if predicate in {"supportsFeature", "mapsToFeature", "includesFeature"}:
        return nid("Feature", f"{value}:{value}")
    if predicate in {"authorizedBy", "publishedBy"} and value in legal_refs:
        if value.endswith("_dataset"):
            return nid("OfficialDataset", value)
        if value in registry_layers:
            return nid("DataLayer", value)
        return nid("Authority", value)
    if predicate == "definedBy" and value in legal_refs:
        return nid("Law", value)
    if value in feature_codes:
        return nid("Feature", f"{value}:{value}")
    if value in registry_layers:
        if registry_layers[value].get("layer_type") in {"dynamic_traffic", "ais", "vpass"}:
            return nid("DynamicTrafficLayer", value)
        return nid("DataLayer", value)
    return nid("DataLayer", value)


def load_kg_index(nodes_path: Path, edges_path: Path) -> dict[str, Any]:
    nodes = load_jsonl(nodes_path)
    edges = load_jsonl(edges_path)
    node_ids = {row.get("id") for row in nodes if row.get("id")}
    edge_triples: set[tuple[str, str, str]] = set()
    by_subject_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_object_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    for edge in edges:
        subject = edge.get("subject_id")
        predicate = edge.get("predicate")
        obj = edge.get("object_id")
        if subject and predicate and obj:
            edge_triples.add((subject, predicate, obj))
            by_subject_predicate[(subject, predicate)].add(obj)
            by_object_predicate[(obj, predicate)].add(subject)
    return {
        "node_ids": node_ids,
        "edge_triples": edge_triples,
        "by_subject_predicate": by_subject_predicate,
        "by_object_predicate": by_object_predicate,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def add_issue(issues: list[dict[str, Any]], severity: str, code: str, message: str, **extra: Any) -> None:
    issue = {"severity": severity, "code": code, "message": message}
    issue.update({k: v for k, v in extra.items() if v not in (None, "", [], {})})
    issues.append(issue)


def validate_candidate(
    evidence_id: str,
    candidate: dict[str, Any],
    decision: dict[str, Any],
    *,
    registry_layers: dict[str, dict[str, Any]],
    feature_codes: set[str],
    legal_refs: set[str],
    rag_chunks: set[str],
    kg_index: dict[str, Any],
    decisions_path: Path,
    inputs: list[Path],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for error in validate_decision(evidence_id, decision, candidate):
        add_issue(issues, "ERROR", "APPROVAL_CONTRACT_FAILED", error)
    if not candidate:
        return {"evidence_id": evidence_id, "status": "FAILED", "issues": issues}

    data = candidate.get("data") if isinstance(candidate.get("data"), dict) else {}
    partition = candidate.get("partition")

    layer_id = data.get("layer_id") or data.get("dataset_id")
    if layer_id and layer_id in registry_layers:
        layer = registry_layers[layer_id]
        execution_status = layer.get("execution_status")
        if execution_status not in {"executable", "registered"}:
            add_issue(
                issues,
                "WARNING",
                "REGISTRY_LAYER_NOT_EXECUTABLE",
                f"{layer_id} registry status is {execution_status}",
                layer_id=layer_id,
                execution_status=execution_status,
                registry_source=layer.get("_source"),
            )
        if not (layer.get("physical_table") or layer.get("expected_physical_table") or layer.get("metadata_table")):
            add_issue(issues, "WARNING", "REGISTRY_LAYER_TABLE_MISSING", f"{layer_id} has no physical/expected table", layer_id=layer_id)
    elif layer_id and partition == "regulatory_evidence":
        add_issue(issues, "ERROR", "REGISTRY_LAYER_MISSING", f"{layer_id} is not registered", layer_id=layer_id)
    elif layer_id:
        add_issue(issues, "WARNING", "REGISTRY_LAYER_UNRESOLVED", f"{layer_id} is not registered as an executable layer", layer_id=layer_id)

    feature_code = data.get("feature_code")
    if feature_code and feature_code not in feature_codes:
        add_issue(issues, "ERROR", "S101_FEATURE_MISSING", f"{feature_code} is not present in the parsed S-101 feature catalogue", feature_code=feature_code)

    chunk_id = data.get("chunk_id")
    if partition == "rag_evidence":
        if not chunk_id:
            add_issue(issues, "ERROR", "RAG_CHUNK_ID_MISSING", "RAG evidence approval requires chunk_id")
        elif str(chunk_id) not in rag_chunks:
            add_issue(issues, "ERROR", "RAG_CHUNK_NOT_FOUND", f"{chunk_id} was not found in outputs/rag JSONL chunks", chunk_id=chunk_id)

    item = registry_item(candidate, decision, decisions_path, inputs)
    edge_promotions = kg_edges_for(evidence_id, item)
    edge_results: list[dict[str, Any]] = []
    for edge in edge_promotions:
        subject = edge.get("subject")
        predicate = edge.get("predicate")
        obj = edge.get("object")
        subject_id = evidence_ref_node(subject, predicate, feature_codes, legal_refs, registry_layers)
        object_id = evidence_ref_node(obj, predicate, feature_codes, legal_refs, registry_layers)
        triple = (subject_id, predicate, object_id)
        edge_result = {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "subject_id": subject_id,
            "object_id": object_id,
            "kg_state": "new",
        }
        if triple in kg_index["edge_triples"]:
            edge_result["kg_state"] = "already_exists"
            add_issue(issues, "WARNING", "KG_EDGE_ALREADY_EXISTS", f"{subject} {predicate} {obj} already exists in KG", edge=edge_result)
        elif predicate in {"mapsToFeature", "authorizedBy", "definedBy", "derivedFrom"}:
            other_objects = sorted(kg_index["by_subject_predicate"].get((subject_id, predicate), set()))
            if other_objects and object_id not in other_objects:
                add_issue(
                    issues,
                    "WARNING",
                    "KG_SUBJECT_PREDICATE_HAS_OTHER_OBJECTS",
                    f"{subject} already has {predicate} edges to other objects",
                    subject_id=subject_id,
                    predicate=predicate,
                    existing_objects=other_objects[:10],
                    proposed_object=object_id,
                )
        edge_results.append(edge_result)

    status = "PASS"
    if any(issue["severity"] == "ERROR" for issue in issues):
        status = "FAILED"
    elif issues:
        status = "NEEDS_REVIEW"
    return {
        "evidence_id": evidence_id,
        "partition": partition,
        "status": status,
        "issue_count": len(issues),
        "issues": issues,
        "edge_promotions": edge_results,
    }


def validate_approved(args: argparse.Namespace) -> dict[str, Any]:
    decisions_doc = load_yaml(args.decisions)
    approved = approved_decisions(decisions_doc)
    registry = load_yaml(args.registry)
    if not approved:
        report = {
            "status": "PASS",
            "phase": "8.9",
            "counts": {
                "approved": 0,
                "pass": 0,
                "needs_review": 0,
                "failed": 0,
                "registry_items": len(registry.get("evidence_items") or {}),
            },
            "sources": {
                "decisions": relpath(args.decisions),
                "registry": relpath(args.registry),
                "nodes": relpath(args.nodes),
                "edges": relpath(args.edges),
            },
            "kg": {
                "node_count": count_jsonl_rows(args.nodes),
                "edge_count": count_jsonl_rows(args.edges),
            },
            "items": [],
        }
        if args.write_report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            report["report"] = relpath(args.report)
        return report

    candidates = load_candidates(args.inputs)
    registry_layers = load_registry_layers()
    feature_codes = load_feature_codes()
    legal_refs = load_legal_refs()
    rag_chunks = load_rag_chunks()
    kg_index = load_kg_index(args.nodes, args.edges)

    results = [
        validate_candidate(
            evidence_id,
            candidates.get(evidence_id),
            decision,
            registry_layers=registry_layers,
            feature_codes=feature_codes,
            legal_refs=legal_refs,
            rag_chunks=rag_chunks,
            kg_index=kg_index,
            decisions_path=args.decisions,
            inputs=args.inputs,
        )
        for evidence_id, decision in sorted(approved.items())
    ]
    counts = {
        "approved": len(approved),
        "pass": sum(1 for item in results if item["status"] == "PASS"),
        "needs_review": sum(1 for item in results if item["status"] == "NEEDS_REVIEW"),
        "failed": sum(1 for item in results if item["status"] == "FAILED"),
        "registry_items": len(registry.get("evidence_items") or {}),
    }
    status = "PASS"
    if counts["failed"]:
        status = "FAILED"
    elif counts["needs_review"]:
        status = "NEEDS_REVIEW"
    report = {
        "status": status,
        "phase": "8.9",
        "counts": counts,
        "sources": {
            "decisions": relpath(args.decisions),
            "registry": relpath(args.registry),
            "nodes": relpath(args.nodes),
            "edges": relpath(args.edges),
        },
        "kg": {
            "node_count": kg_index["node_count"],
            "edge_count": kg_index["edge_count"],
        },
        "items": results,
    }
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report"] = relpath(args.report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate approved evidence candidates before registry/KG promotion.")
    parser.add_argument("--inputs", nargs="*", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    result = validate_approved(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
