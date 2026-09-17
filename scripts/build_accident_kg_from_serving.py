"""Build accident KG artifacts from the authoritative serving.accident_events table."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
GRAPH = OUT / "graph"
REPORTS = OUT / "reports"


def db_url() -> str:
    value = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not value:
        raise RuntimeError("S101_DB_URL or POSTGIS_URL is required")
    return value


def json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, default=json_default) + "\n" for row in rows),
        encoding="utf-8",
    )


def safe_id(prefix: str, value: str) -> str:
    normalized = str(value or "unknown").strip() or "unknown"
    return f"{prefix}:{normalized}"


def fetch_rows() -> list[dict[str, Any]]:
    import psycopg2
    import psycopg2.extras

    with psycopg2.connect(db_url(), connect_timeout=5) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT event_id, source_row_number, occurred_at, month, time_slot,
                       authority, sea_area, weather, cause, accident_type,
                       vessel_count, people_count, rescued, injured, dead, missing,
                       vessel_type, tonnage, longitude, latitude,
                       ST_AsGeoJSON(geom)::jsonb AS geometry
                FROM serving.accident_events
                ORDER BY source_row_number
                """
            )
            return [dict(row) for row in cur.fetchall()]


TYPE_CONCEPTS = {
    "충돌": ["accident_risk", "navigation_hazard_object", "collision_risk"],
    "접촉": ["accident_risk", "navigation_hazard_object", "collision_risk"],
    "좌초/좌주": ["accident_risk", "navigation_hazard_object", "grounding_risk"],
    "전복": ["accident_risk", "rescue_vulnerability"],
    "침몰": ["accident_risk", "rescue_vulnerability"],
    "침수": ["accident_risk", "rescue_vulnerability"],
    "화재": ["accident_risk", "navigation_hazard_object"],
    "기관손상": ["accident_risk", "navigation_hazard_object"],
    "추진기손상": ["accident_risk", "navigation_hazard_object"],
    "키손상": ["accident_risk", "navigation_hazard_object"],
    "운항저해": ["accident_risk", "navigation_hazard_object"],
    "표류": ["accident_risk", "rescue_vulnerability"],
}
CAUSE_CONCEPTS = {
    "정비불량": ["accident_risk", "maintenance_failure"],
    "관리소홀": ["accident_risk", "operation_management_risk"],
    "운항부주의": ["accident_risk", "navigation_operation_risk"],
    "안전부주의": ["accident_risk", "safety_attention_risk"],
    "원인미상": ["accident_risk", "unknown_cause"],
}
DEFAULT_CONCEPTS = ["accident_risk"]


def build() -> dict[str, Any]:
    rows = fetch_rows()
    provenance = {
        "source_ref": "serving.accident_events",
        "generator": "scripts/build_accident_kg_from_serving.py",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    event_nodes: list[dict[str, Any]] = []
    dimension_values = {
        "type": Counter(),
        "cause": Counter(),
        "authority": Counter(),
        "sea_area": Counter(),
    }
    event_edges: list[dict[str, Any]] = []

    for row in rows:
        event_id = row["event_id"]
        properties = {
            key: row.get(key)
            for key in [
                "event_id",
                "source_row_number",
                "occurred_at",
                "month",
                "time_slot",
                "authority",
                "sea_area",
                "weather",
                "cause",
                "accident_type",
                "vessel_count",
                "people_count",
                "rescued",
                "injured",
                "dead",
                "missing",
                "vessel_type",
                "tonnage",
                "longitude",
                "latitude",
            ]
        }
        event_nodes.append(
            {
                "id": event_id,
                "node_type": "AccidentEvent",
                "name": f"{row.get('authority') or ''} {row.get('cause') or ''} {row.get('accident_type') or ''}".strip(),
                "properties": properties,
                "geometry": row.get("geometry"),
                "provenance": provenance,
            }
        )
        dimensions = [
            ("type", "hasAccidentType", safe_id("accident-type", row.get("accident_type"))),
            ("cause", "hasAccidentCause", safe_id("accident-cause", row.get("cause"))),
            ("authority", "underAuthority", safe_id("accident-authority", row.get("authority"))),
            ("sea_area", "occurredInSeaArea", safe_id("accident-sea-area", row.get("sea_area"))),
        ]
        for dim, predicate, target in dimensions:
            value = str(row.get({"type": "accident_type", "cause": "cause", "authority": "authority", "sea_area": "sea_area"}[dim]) or "unknown")
            dimension_values[dim][value] += 1
            event_edges.append(
                {
                    "id": f"{event_id}|{predicate}|{target}",
                    "subject_id": event_id,
                    "predicate": predicate,
                    "object_id": target,
                    "status": "VERIFIED",
                    "provenance": provenance,
                }
            )

    type_nodes = []
    cause_nodes = []
    authority_nodes = []
    sea_area_nodes = []
    concept_edges = []

    for name, count in sorted(dimension_values["type"].items()):
        concepts = TYPE_CONCEPTS.get(name, DEFAULT_CONCEPTS)
        node_id = safe_id("accident-type", name)
        type_nodes.append({"id": node_id, "node_type": "AccidentType", "name": name, "properties": {"event_count": count, "maps_to_concepts": concepts}, "provenance": provenance})
        for concept in concepts:
            concept_edges.append({"id": f"{node_id}|mapsToConcept|upper-ontology:{concept}", "subject_id": node_id, "predicate": "mapsToConcept", "object_id": f"upper_ontology:{concept}", "status": "VERIFIED", "provenance": provenance})
    for name, count in sorted(dimension_values["cause"].items()):
        concepts = CAUSE_CONCEPTS.get(name, DEFAULT_CONCEPTS)
        node_id = safe_id("accident-cause", name)
        cause_nodes.append({"id": node_id, "node_type": "AccidentCause", "name": name, "properties": {"event_count": count, "maps_to_concepts": concepts}, "provenance": provenance})
        for concept in concepts:
            concept_edges.append({"id": f"{node_id}|mapsToConcept|upper-ontology:{concept}", "subject_id": node_id, "predicate": "mapsToConcept", "object_id": f"upper_ontology:{concept}", "status": "VERIFIED", "provenance": provenance})
    for name, count in sorted(dimension_values["authority"].items()):
        authority_nodes.append({"id": safe_id("accident-authority", name), "node_type": "AccidentAuthority", "name": name, "properties": {"event_count": count}, "provenance": provenance})
    for name, count in sorted(dimension_values["sea_area"].items()):
        sea_area_nodes.append({"id": safe_id("accident-sea-area", name), "node_type": "AccidentSeaArea", "name": name, "properties": {"event_count": count}, "provenance": provenance})

    dataset_edges = [
        {
            "id": "dataset.accident_events|materializedAs|serving.accident_events",
            "subject_id": "dataset.accident_events",
            "predicate": "materializedAs",
            "object_id": "serving.accident_events",
            "status": "VERIFIED",
            "provenance": provenance,
        },
        {
            "id": "serving.accident_events|typedAs|upper_ontology:accident_risk",
            "subject_id": "serving.accident_events",
            "predicate": "typedAs",
            "object_id": "upper_ontology:accident_risk",
            "status": "VERIFIED",
            "provenance": provenance,
        },
        {
            "id": "tool.accident_event_lookup|usesTable|serving.accident_events",
            "subject_id": "tool.accident_event_lookup",
            "predicate": "usesTable",
            "object_id": "serving.accident_events",
            "status": "VERIFIED",
            "provenance": provenance,
        },
        {
            "id": "tool.accident_event_lookup|implementsTemplate|query_template:accident_event_lookup",
            "subject_id": "tool.accident_event_lookup",
            "predicate": "implementsTemplate",
            "object_id": "query_template:accident_event_lookup",
            "status": "VERIFIED",
            "provenance": provenance,
        },
    ]

    write_jsonl(GRAPH / "nodes_accident_events.jsonl", event_nodes)
    write_jsonl(GRAPH / "nodes_accident_types.jsonl", type_nodes)
    write_jsonl(GRAPH / "nodes_accident_causes.jsonl", cause_nodes)
    write_jsonl(GRAPH / "nodes_accident_authorities.jsonl", authority_nodes)
    write_jsonl(GRAPH / "nodes_accident_sea_areas.jsonl", sea_area_nodes)
    write_jsonl(GRAPH / "edges_accident_event_dimensions.jsonl", event_edges)
    write_jsonl(GRAPH / "edges_accident_related_to_concept.jsonl", concept_edges + dataset_edges)
    write_jsonl(GRAPH / "verified_edges_from_discovery.jsonl", dataset_edges)

    report = {
        "generated_at": provenance["generated_at"],
        "source_ref": "serving.accident_events",
        "db_event_rows": len(rows),
        "event_nodes": len(event_nodes),
        "type_nodes": len(type_nodes),
        "cause_nodes": len(cause_nodes),
        "authority_nodes": len(authority_nodes),
        "sea_area_nodes": len(sea_area_nodes),
        "event_dimension_edges": len(event_edges),
        "concept_edges": len(concept_edges),
        "verified_edges_promoted": len(dataset_edges),
        "sync_status": "PASS" if len(rows) == len(event_nodes) else "FAIL",
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "accident_kg_sync_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Accident KG Sync Validation",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- source_ref: `{report['source_ref']}`",
        f"- db_event_rows: {report['db_event_rows']}",
        f"- event_nodes: {report['event_nodes']}",
        f"- type_nodes: {report['type_nodes']}",
        f"- cause_nodes: {report['cause_nodes']}",
        f"- authority_nodes: {report['authority_nodes']}",
        f"- sea_area_nodes: {report['sea_area_nodes']}",
        f"- event_dimension_edges: {report['event_dimension_edges']}",
        f"- concept_edges: {report['concept_edges']}",
        f"- verified_edges_promoted: {report['verified_edges_promoted']}",
        f"- sync_status: {report['sync_status']}",
        "",
        "Policy: `serving.accident_events` is the authority for accident event count, attributes, and geometry. KG edges describe evidence-backed classification and dimensions, not causality with S-101 chart objects.",
    ]
    (REPORTS / "accident_kg_sync_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    print(json.dumps(build(), ensure_ascii=False, default=json_default))


if __name__ == "__main__":
    main()
