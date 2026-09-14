import json

from services.orchestrator.kg_ontology_validator import validate_kg_ontology


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_kg_ontology_validator_passes_minimal_contract(tmp_path):
    contract = tmp_path / "contract.yaml"
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    contract.write_text(
        """
version: '0.1'
contract_id: test.kg
verification_statuses:
  VERIFIED: {}
  CANDIDATE: {}
node_types:
  MarineTerm:
    provenance_required: true
  Feature:
    provenance_required: true
edge_types:
  mapsToFeature:
    subject_types: [MarineTerm]
    object_types: [Feature]
    default_status: CANDIDATE
""",
        encoding="utf-8",
    )
    _write_jsonl(
        nodes,
        [
            {"id": "marine_term:danger", "node_type": "MarineTerm", "name": "위험객체", "provenance": {"source_path": "terms"}},
            {"id": "feature:wreck", "node_type": "Feature", "name": "Wreck", "provenance": {"source_path": "catalogue"}},
        ],
    )
    _write_jsonl(
        edges,
        [
            {
                "id": "e1",
                "subject_id": "marine_term:danger",
                "predicate": "mapsToFeature",
                "object_id": "feature:wreck",
                "provenance": {"source_path": "terms"},
            }
        ],
    )

    result = validate_kg_ontology(contract_path=contract, nodes_path=nodes, edges_path=edges)

    assert result["status"] == "PASS"
    assert result["node_count"] == 2
    assert result["edge_count"] == 1


def test_kg_ontology_validator_rejects_wrong_edge_domain(tmp_path):
    contract = tmp_path / "contract.yaml"
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    contract.write_text(
        """
version: '0.1'
contract_id: test.kg
verification_statuses:
  VERIFIED: {}
  CANDIDATE: {}
node_types:
  MarineTerm:
    provenance_required: true
  Feature:
    provenance_required: true
edge_types:
  mapsToFeature:
    subject_types: [MarineTerm]
    object_types: [Feature]
    default_status: CANDIDATE
""",
        encoding="utf-8",
    )
    _write_jsonl(
        nodes,
        [
            {"id": "feature:a", "node_type": "Feature", "name": "A", "provenance": {"source_path": "catalogue"}},
            {"id": "feature:b", "node_type": "Feature", "name": "B", "provenance": {"source_path": "catalogue"}},
        ],
    )
    _write_jsonl(
        edges,
        [
            {
                "id": "e1",
                "subject_id": "feature:a",
                "predicate": "mapsToFeature",
                "object_id": "feature:b",
                "provenance": {"source_path": "bad"},
            }
        ],
    )

    result = validate_kg_ontology(contract_path=contract, nodes_path=nodes, edges_path=edges)

    assert result["status"] == "FAILED"
    assert any(error["code"] == "EDGE_SUBJECT_TYPE_INVALID" for error in result["errors"])
