"""Graph-first retrieval planning for the v2 orchestrator."""
from __future__ import annotations

import json
import re
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NODES_PATH = ROOT / "outputs/graph/kg_nodes_v2.jsonl"
EDGES_PATH = ROOT / "outputs/graph/kg_edges_v2.jsonl"
EVIDENCE_DIR = ROOT / "outputs/evidence"
MAX_DEPTH = 3


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _text(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return " ".join(_text(item) for item in value)
    return "" if value is None else str(value)


def _tokens(value: Any) -> set[str]:
    return {part for part in re.split(r"\s+|[,/_()\[\]{}:.-]+", _text(value).lower()) if part}


@lru_cache(maxsize=1)
def _load_graph() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    if NODES_PATH.exists():
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                node = json.loads(line)
                if node.get("id"):
                    nodes[node["id"]] = node
    if EDGES_PATH.exists():
        for line in EDGES_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                edge = json.loads(line)
                if edge.get("subject_id") and edge.get("object_id"):
                    edges.append(edge)
    return nodes, edges


@lru_cache(maxsize=16)
def _load_jsonl_cached(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return tuple(rows)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(_load_jsonl_cached(str(path)))


def _candidate_sources() -> dict[str, Path]:
    return {
        "kg_provenance": EVIDENCE_DIR / "kg_provenance_candidates.jsonl",
        "rag_evidence": EVIDENCE_DIR / "rag_evidence_candidates.jsonl",
        "regulatory_evidence": EVIDENCE_DIR / "regulatory_evidence_candidates.jsonl",
    }


def _candidate_text(row: dict[str, Any]) -> str:
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    values = [
        row.get("summary"),
        row.get("source_ref"),
        row.get("evidence_type"),
        data.get("dataset_id"),
        data.get("layer_id"),
        data.get("feature_code"),
        data.get("feature_name"),
        data.get("legal_notice_id"),
        data.get("official_dataset_id"),
        data.get("authority_id"),
        data.get("basis_laws"),
        data.get("matched_proposals"),
        data.get("suggested_binding"),
    ]
    return _text(values).lower()


def _score_candidate(row: dict[str, Any], query_tokens: set[str], context_tokens: set[str]) -> float:
    candidate_tokens = _tokens(_candidate_text(row))
    if not candidate_tokens:
        return 0.0
    overlap = query_tokens & candidate_tokens
    context_overlap = context_tokens & candidate_tokens
    lexical = len(overlap) / max(1, min(len(query_tokens), 12))
    contextual = len(context_overlap) / max(1, min(len(context_tokens), 10))
    base_score = float(row.get("score") or 0.0)
    return min(1.0, base_score * 0.5 + lexical * 0.35 + contextual * 0.15)


def _compact_candidate(row: dict[str, Any], match_score: float) -> dict[str, Any]:
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    return {
        "evidence_id": row.get("evidence_id"),
        "partition": row.get("partition"),
        "evidence_type": row.get("evidence_type"),
        "summary": row.get("summary"),
        "source_ref": row.get("source_ref"),
        "score": row.get("score"),
        "match_score": round(match_score, 4),
        "review_required": row.get("review_required"),
        "data": {
            key: data.get(key)
            for key in (
                "dataset_id",
                "layer_id",
                "feature_code",
                "feature_name",
                "chunk_id",
                "page_no",
                "section",
                "legal_notice_id",
                "official_dataset_id",
                "authority_id",
                "basis_laws",
                "edge_candidates",
                "verification_status",
            )
            if key in data
        },
    }


def _phase85_candidates(query: str, context: dict[str, Any], *, limit_per_partition: int = 12) -> dict[str, list[dict[str, Any]]]:
    query_tokens = _tokens(query)
    context_tokens = _tokens([
        context.get("target_features"),
        context.get("target_layers"),
        context.get("target_dynamic_layers"),
        context.get("derived_concepts"),
        context.get("product_id"),
        context.get("candidate_documents"),
    ])
    result: dict[str, list[dict[str, Any]]] = {}
    for partition, path in _candidate_sources().items():
        scored = []
        for row in _load_jsonl(path):
            score = _score_candidate(row, query_tokens, context_tokens)
            if score <= 0:
                continue
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        result[partition] = [_compact_candidate(row, score) for score, row in scored[:limit_per_partition]]
    return result


def _candidate_values(candidates: dict[str, list[dict[str, Any]]], field: str) -> list[str]:
    values = []
    for rows in candidates.values():
        for row in rows:
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            value = data.get(field)
            if isinstance(value, list):
                values.extend(_text(item) for item in value if item)
            elif value:
                values.append(_text(value))
    return list(dict.fromkeys(values))


def _search_text(node: dict[str, Any]) -> str:
    props = node.get("properties") or {}
    values = [node.get("id"), node.get("name"), props.get("canonical_name")]
    values.extend(props.get(key) for key in ("aliases", "alias", "keywords", "labels", "maps_to_features", "maps_to_concepts"))
    return " ".join(_text(value) for value in values).lower()


def _matches(nodes: dict[str, dict[str, Any]], value: Any, types: set[str] | None = None) -> list[str]:
    needle = _text(value).strip().lower()
    if not needle:
        return []
    needle_tokens = _tokens(needle)
    result = []
    for node_id, node in nodes.items():
        if types and node.get("node_type") not in types:
            continue
        haystack = _search_text(node)
        if needle == node_id.lower() or needle in haystack or needle_tokens.issubset(_tokens(haystack)):
            result.append(node_id)
    return result


def _query_seeds(nodes: dict[str, dict[str, Any]], query: str) -> list[str]:
    types = {"MarineTerm", "DerivedConcept", "Feature", "DataLayer", "DynamicTrafficLayer", "Product"}
    result = []
    query_lower = query.lower()
    query_compact = re.sub(r"\s+", "", query_lower)
    for node_id, node in nodes.items():
        if node.get("node_type") not in types:
            continue
        props = node.get("properties") or {}
        aliases = props.get("aliases") or []
        labels = [_text(node.get("name")), _text(props.get("canonical_name"))] + [_text(alias) for alias in _list(aliases)]
        def label_matches(label: str) -> bool:
            if not label:
                return False
            compact = re.sub(r"\s+", "", label.lower())
            parts = [part for part in re.split(r"\s+", label.lower()) if len(part) >= 2]
            return label.lower() in query_lower or compact in query_compact or (len(parts) >= 2 and sum(part in query_compact for part in parts) >= 2)

        if any(label_matches(label) for label in labels):
            result.append(node_id)
    return result


def _walk(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], seeds: list[str]):
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        subject, object_id = edge["subject_id"], edge["object_id"]
        adjacency.setdefault(subject, []).append(object_id)
        adjacency.setdefault(object_id, []).append(subject)
    distances = {seed: 0 for seed in dict.fromkeys(seeds) if seed in nodes}
    paths = {seed: [seed] for seed in distances}
    queue = deque(distances)
    while queue:
        current = queue.popleft()
        if distances[current] >= MAX_DEPTH:
            continue
        for target in adjacency.get(current, []):
            if target in nodes and target not in distances:
                distances[target] = distances[current] + 1
                paths[target] = paths[current] + [target]
                queue.append(target)
    return distances, paths


def _names(nodes: dict[str, dict[str, Any]], ids: list[str], node_type: str) -> list[str]:
    return list(dict.fromkeys(_text(nodes[item].get("name", item)) for item in ids if item in nodes and nodes[item].get("node_type") == node_type))


def _related_ids(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], sources: set[str], predicates: set[str], node_types: set[str]) -> list[str]:
    result = []
    for edge in edges:
        if edge.get("predicate") not in predicates:
            continue
        if edge.get("subject_id") in sources and edge.get("object_id") in nodes and nodes[edge["object_id"]].get("node_type") in node_types:
            result.append(edge["object_id"])
        if edge.get("object_id") in sources and edge.get("subject_id") in nodes and nodes[edge["subject_id"]].get("node_type") in node_types:
            result.append(edge["subject_id"])
    return list(dict.fromkeys(result))


def _seed_ids(nodes: dict[str, dict[str, Any]], context: dict[str, Any], query: str) -> list[str]:
    types_by_key = {
        "target_features": {"Feature", "MarineTerm"},
        "derived_concepts": {"DerivedConcept", "MarineTerm"},
        "target_layers": {"DataLayer"},
        "target_dynamic_layers": {"DynamicTrafficLayer"},
        "product_id": {"Product"},
        "candidate_documents": {"StandardDocument", "LawDocument", "DocumentChunk"},
    }
    seeds = []
    for key, types in types_by_key.items():
        for value in _list(context.get(key)):
            seeds.extend(_matches(nodes, value, types))
    return list(dict.fromkeys(seeds or _query_seeds(nodes, query)))


def discover_graph_context(graph_context: dict[str, Any] | None = None, query: str = "") -> dict[str, Any]:
    context = graph_context or {}
    nodes, edges = _load_graph()
    seeds = _seed_ids(nodes, context, query)
    distances, paths = _walk(nodes, edges, seeds)
    document_ids = [item for item in distances if nodes[item].get("node_type") in {"StandardDocument", "LawDocument", "DocumentChunk"}]
    graph_paths = [{"seed": seed, "path": paths[seed], "node_names": [_text(nodes[item].get("name", item)) for item in paths[seed]]} for seed in seeds if seed in paths]
    return {
        "candidate_document_ids": document_ids,
        "graph_paths": graph_paths,
        "graph_supported": bool(nodes),
        "provenance": {"graph_nodes": "outputs/graph/kg_nodes_v2.jsonl", "graph_edges": "outputs/graph/kg_edges_v2.jsonl", "method": f"undirected_bfs_depth_{MAX_DEPTH}", "seed_count": len(seeds)},
    }


class GraphRAGRetriever:
    """Resolve a normalized query into a graph-scoped RAG and execution plan."""

    def retrieve(self, query: str, graph_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = graph_context or {}
        nodes, edges = _load_graph()
        evidence_candidates = _phase85_candidates(query, context)
        seed_ids = _seed_ids(nodes, context, query)
        distances, paths = _walk(nodes, edges, seed_ids)
        related_ids = list(distances)
        feature_ids = _related_ids(nodes, edges, set(related_ids), {"includesFeature", "mapsToFeature"}, {"Feature"})
        layer_ids = _related_ids(nodes, edges, set(related_ids), {"usesLayer", "requiresData", "overlapsLayer"}, {"DataLayer"})
        dynamic_ids = _related_ids(nodes, edges, set(related_ids), {"usesDynamicLayer", "overlapsLayer"}, {"DynamicTrafficLayer"})
        requested_feature_ids = _related_ids(nodes, edges, set(seed_ids), {"mapsToFeature", "includesFeature"}, {"Feature"})
        candidate_features = _candidate_values(evidence_candidates, "feature_code")
        candidate_layers = _candidate_values(evidence_candidates, "layer_id")
        candidate_chunk_ids = _candidate_values(evidence_candidates, "chunk_id")
        target_features = list(dict.fromkeys(_names(nodes, list(dict.fromkeys(requested_feature_ids + feature_ids)), "Feature") + candidate_features))
        target_layers = list(dict.fromkeys(_names(nodes, list(dict.fromkeys(layer_ids)), "DataLayer") + candidate_layers))
        dynamic_layers = _names(nodes, list(dict.fromkeys(dynamic_ids)), "DynamicTrafficLayer")
        documents = _names(nodes, related_ids, "StandardDocument") + _names(nodes, related_ids, "LawDocument") + _names(nodes, related_ids, "DocumentChunk")
        filters = {
            "product_id": list(dict.fromkeys(_text(x) for x in _list(context.get("product_id")))) or _names(nodes, related_ids, "Product"),
            "related_features": list(dict.fromkeys(_text(x) for x in _list(context.get("target_features")))) or target_features,
            "related_concepts": list(dict.fromkeys(_text(x) for x in _list(context.get("derived_concepts")))) or _names(nodes, related_ids, "DerivedConcept"),
            "document_type": list(dict.fromkeys(_text(x) for x in _list(context.get("document_type")))),
            "candidate_document_ids": candidate_chunk_ids,
        }
        lowered = query.lower()
        spatial = bool(target_features or target_layers or context.get("target_features")) or any(x in lowered for x in ("km", "반경", "거리", "이내", "near", "overlap", "dwithin"))
        traffic = bool(dynamic_layers or context.get("target_dynamic_layers")) or any(x in lowered for x in ("ais", "v-pass", "vpass", "교통", "통항로"))
        accident = bool(context.get("accident_events")) or any(x in lowered for x in ("사고", "위험", "accident", "risk", "조난"))
        graph_paths = [{"seed": seed, "path": paths[seed], "node_names": [_text(nodes[item].get("name", item)) for item in paths[seed]]} for seed in seed_ids if seed in paths]
        return {
            "resolved_terms": _names(nodes, related_ids, "MarineTerm"),
            "derived_concepts": _names(nodes, related_ids, "DerivedConcept"),
            "target_features": target_features or [_text(x) for x in _list(context.get("target_features"))],
            "target_layers": target_layers or [_text(x) for x in _list(context.get("target_layers"))],
            "target_dynamic_layers": dynamic_layers or [_text(x) for x in _list(context.get("target_dynamic_layers"))],
            "candidate_documents": documents,
            "evidence_candidates": evidence_candidates,
            "candidate_agents": _names(nodes, related_ids, "Agent"),
            "candidate_tools": _names(nodes, related_ids, "Tool"),
            "candidate_query_templates": _names(nodes, related_ids, "QueryTemplate"),
            "rag_filters": filters,
            "execution_hints": {"requires_data_discovery": True, "requires_spatial_analysis": spatial, "requires_traffic_analysis": traffic, "requires_accident_analysis": accident, "requires_rag": True},
            "graph_paths": graph_paths,
            "explanation": "질의를 KG seed로 해석하고 bounded BFS로 Feature, Concept, Layer, Agent, Tool, 문서 후보를 제한했습니다.",
            "graph_supported": bool(nodes),
            "provenance": {
                **discover_graph_context(context, query)["provenance"],
                "query": query,
                "candidate_document_ids": [item for item in distances if nodes[item].get("node_type") in {"StandardDocument", "LawDocument", "DocumentChunk"}],
                "evidence_candidate_sources": {key: str(path.relative_to(ROOT)).replace("\\", "/") for key, path in _candidate_sources().items()},
                "evidence_candidate_counts": {key: len(value) for key, value in evidence_candidates.items()},
            },
        }
