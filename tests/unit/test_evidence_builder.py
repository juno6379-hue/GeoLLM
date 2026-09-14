from services.orchestrator.evidence_builder import build_evidence_bundle


def test_build_evidence_bundle_partitions_sources():
    bundle = build_evidence_bundle(
        graph_context={
            "graph_paths": [
                {
                    "seed": "marine_term:wreck",
                    "path": ["marine_term:wreck", "feature:wreck_wreck"],
                    "node_names": ["침선", "Wreck"],
                }
            ],
            "provenance": {"graph_nodes": "outputs/graph/kg_nodes_v2.jsonl"},
        },
        structured_result={
            "citations": [
                {
                    "document_id": "doc1",
                    "source_file": "Dataset/S-101_Annex_A_DCEG_Ed_2.0.0.pdf",
                    "section": "page_1",
                    "chunk_id": "chunk1",
                }
            ],
            "accident_feature_relations": [
                {
                    "event_id": "acc1",
                    "feature_instance_id": 123,
                    "distance_meters": 250,
                    "relation_table": "serving.accident_s101_relation_current",
                }
            ],
            "regulatory_evidence": [
                {
                    "title_ko": "선박교통관제에 관한 규정",
                    "notice_no": "해양경찰청고시 제2024-5호",
                    "source_url": "https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000246366",
                }
            ],
        },
        spatial_feature_evidence=[
            {
                "summary": "Wreck",
                "source_ref": "layer1",
                "data": {"feature_instance_id": 123, "feature_type_name": "Wreck"},
            }
        ],
        task_id="task1",
    )

    assert len(bundle.kg_provenance) == 1
    assert bundle.kg_provenance[0].evidence_type == "kg_path"
    assert len(bundle.rag_evidence) == 1
    assert bundle.rag_evidence[0].source_ref.endswith(".pdf")
    assert len(bundle.spatial_feature_evidence) == 1
    assert bundle.spatial_feature_evidence[0].evidence_type == "spatial_feature"
    assert len(bundle.accident_relation_evidence) == 1
    assert bundle.accident_relation_evidence[0].evidence_type == "accident_relation"
    assert len(bundle.regulatory_evidence) == 1
    assert bundle.regulatory_evidence[0].source_ref.startswith("https://www.law.go.kr")
