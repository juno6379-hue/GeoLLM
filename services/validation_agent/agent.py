"""Deterministic validation for Graph-RAG orchestration results."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus

ROOT = Path(__file__).resolve().parents[2]
NODES = ROOT / "outputs/graph/kg_nodes_v2.jsonl"
EDGES = ROOT / "outputs/graph/kg_edges_v2.jsonl"


def _ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def validate_graph_paths(graph_context: dict[str, Any]) -> dict[str, Any]:
    node_ids = _ids(NODES)
    edge_pairs: set[tuple[str, str]] = set()
    if EDGES.exists():
        for line in EDGES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                edge = json.loads(line)
                edge_pairs.add((edge.get("subject_id"), edge.get("object_id")))
                edge_pairs.add((edge.get("object_id"), edge.get("subject_id")))
    paths = graph_context.get("graph_paths", []) if isinstance(graph_context, dict) else []
    invalid = []
    for item in paths:
        path = item.get("path", [])
        if any(node_id not in node_ids for node_id in path):
            invalid.append({"path": path, "reason": "node_not_found"})
        if any(pair not in edge_pairs for pair in zip(path, path[1:])):
            invalid.append({"path": path, "reason": "edge_not_found"})
    return {"status": "PASS" if not invalid else "FAILED", "path_count": len(paths), "invalid_paths": invalid, "node_source": "outputs/graph/kg_nodes_v2.jsonl", "edge_source": "outputs/graph/kg_edges_v2.jsonl"}


def validate_provenance(graph_context: dict[str, Any], result_provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    graph_provenance = graph_context.get("provenance", {}) if isinstance(graph_context, dict) else {}
    result_provenance = result_provenance or {}
    required_graph = bool(graph_provenance.get("graph_nodes") and graph_provenance.get("graph_edges"))
    has_result_source = bool(result_provenance.get("source_file") or result_provenance.get("kg_context") or result_provenance.get("graph_nodes"))
    return {"status": "PASS" if required_graph and has_result_source else "PENDING_PROVENANCE", "graph_provenance": required_graph, "result_provenance": has_result_source}


def validate_execution_state(discovery: dict[str, Any]) -> dict[str, Any]:
    if discovery.get("can_execute_spatial_query"):
        return {"status": "READY", "execution_level": discovery.get("execution_level", "EXECUTION_READY"), "blocked_reason": None}
    level = discovery.get("execution_level", "UNKNOWN")
    if level == "CATALOGUE_READY_DB_PENDING" or not discovery.get("can_execute_spatial_query", False):
        reason = "PENDING_DB_RESTORE" if "DB" in "".join(discovery.get("missing_data", [])) or "S101" in "".join(discovery.get("missing_data", [])) else "PENDING_GEOMETRY"
        return {"status": reason, "execution_level": level, "blocked_reason": reason}
    return {"status": "PENDING_EXECUTION_DATA", "execution_level": level, "blocked_reason": "PENDING_EXECUTION_DATA"}


def validate_orchestration(graph_context: dict[str, Any], discovery: dict[str, Any], result_provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    graph = validate_graph_paths(graph_context or {})
    provenance = validate_provenance(graph_context or {}, result_provenance)
    execution = validate_execution_state(discovery or {})
    overall = "FAILED" if graph["status"] == "FAILED" else ("PASS" if provenance["status"] == "PASS" else "PENDING_PROVENANCE")
    return {"status": overall, "kg_path_consistency": graph, "provenance_check": provenance, "execution_state": execution, "verified_by": "Validation Agent", "llm_verification": False}


async def execute_validation(request: AgentRequest) -> AgentResult:
    outputs = request.previous_agent_outputs or {}
    validation = validate_orchestration(
        outputs.get("graph_context", {}),
        outputs.get("data_discovery_result", {}),
        outputs.get("agent_result", {}).get("provenance", {}) if isinstance(outputs.get("agent_result"), dict) else {},
    )
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Validation Agent",
        agent_version="2.0.0-deterministic",
        status=AgentStatus.COMPLETED,
        summary=f"Validation status: {validation['status']}",
        structured_result=validation,
        validation_payload=validation,
        provenance={"validator": "services.validation_agent.agent.validate_orchestration"},
        created_at=datetime.utcnow(),
    )
