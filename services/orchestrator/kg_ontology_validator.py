"""Deterministic checks for the Phase 5.5 KG ontology contract."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - import-time fallback for minimal environments
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "data/kg_ontology_contract.yaml"
DEFAULT_NODES = ROOT / "outputs/graph/kg_nodes_v2.jsonl"
DEFAULT_EDGES = ROOT / "outputs/graph/kg_edges_v2.jsonl"


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load the KG ontology contract")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_line_no"] = line_no
        rows.append(row)
    return rows


def _status(edge: dict[str, Any], edge_contract: dict[str, Any]) -> str:
    props = edge.get("properties") if isinstance(edge.get("properties"), dict) else {}
    return str(edge.get("verification_status") or edge.get("status") or props.get("verification_status") or props.get("status") or edge_contract.get("default_status") or "CANDIDATE")


def _has_provenance(item: dict[str, Any]) -> bool:
    provenance = item.get("provenance")
    return isinstance(provenance, dict) and any(value not in (None, "", [], {}) for value in provenance.values())


def validate_kg_ontology(
    *,
    contract_path: Path | str = DEFAULT_CONTRACT,
    nodes_path: Path | str = DEFAULT_NODES,
    edges_path: Path | str = DEFAULT_EDGES,
) -> dict[str, Any]:
    """Validate KG node/edge rows against the Phase 5.5 ontology contract."""
    contract_path = Path(contract_path)
    nodes_path = Path(nodes_path)
    edges_path = Path(edges_path)
    contract = _load_yaml(contract_path)
    node_contracts = contract.get("node_types", {})
    edge_contracts = contract.get("edge_types", {})
    status_contracts = contract.get("verification_statuses", {})
    nodes = _load_jsonl(nodes_path)
    edges = _load_jsonl(edges_path)
    node_by_id = {node.get("id"): node for node in nodes if node.get("id")}
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("node_type")
        if not node_id:
            errors.append({"code": "NODE_ID_MISSING", "line": node.get("_line_no")})
            continue
        if node_type not in node_contracts:
            errors.append({"code": "NODE_TYPE_UNKNOWN", "node_id": node_id, "node_type": node_type})
            continue
        if node_contracts[node_type].get("provenance_required") and not _has_provenance(node):
            errors.append({"code": "NODE_PROVENANCE_MISSING", "node_id": node_id, "node_type": node_type})

    for edge in edges:
        edge_id = edge.get("id")
        predicate = edge.get("predicate")
        subject_id = edge.get("subject_id")
        object_id = edge.get("object_id")
        edge_contract = edge_contracts.get(predicate)
        if not edge_id:
            errors.append({"code": "EDGE_ID_MISSING", "line": edge.get("_line_no")})
        if not edge_contract:
            errors.append({"code": "EDGE_TYPE_UNKNOWN", "edge_id": edge_id, "predicate": predicate})
            continue
        subject = node_by_id.get(subject_id)
        object_node = node_by_id.get(object_id)
        if not subject:
            errors.append({"code": "EDGE_SUBJECT_NOT_FOUND", "edge_id": edge_id, "subject_id": subject_id})
            continue
        if not object_node:
            errors.append({"code": "EDGE_OBJECT_NOT_FOUND", "edge_id": edge_id, "object_id": object_id})
            continue
        subject_type = subject.get("node_type")
        object_type = object_node.get("node_type")
        if subject_type not in set(edge_contract.get("subject_types", [])):
            errors.append({"code": "EDGE_SUBJECT_TYPE_INVALID", "edge_id": edge_id, "predicate": predicate, "subject_type": subject_type})
        if object_type not in set(edge_contract.get("object_types", [])):
            errors.append({"code": "EDGE_OBJECT_TYPE_INVALID", "edge_id": edge_id, "predicate": predicate, "object_type": object_type})
        status = _status(edge, edge_contract)
        if status not in status_contracts:
            errors.append({"code": "EDGE_STATUS_UNKNOWN", "edge_id": edge_id, "status": status})
        if status == "VERIFIED" and not _has_provenance(edge):
            errors.append({"code": "VERIFIED_EDGE_PROVENANCE_MISSING", "edge_id": edge_id, "predicate": predicate})
        if status != edge_contract.get("default_status") and not edge.get("verification_status") and not edge.get("status"):
            warnings.append({"code": "EDGE_STATUS_IMPLICIT_FROM_CONTRACT", "edge_id": edge_id, "predicate": predicate, "status": status})

    return {
        "status": "PASS" if not errors else "FAILED",
        "contract_id": contract.get("contract_id"),
        "contract_version": contract.get("version"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "errors": errors,
        "warnings": warnings,
        "sources": {
            "contract": str(contract_path),
            "nodes": str(nodes_path),
            "edges": str(edges_path),
        },
    }
