import asyncio

import pytest

from services.orchestrator.definition_response import build_definition_response
from services.orchestrator.definition_router import (
    definition_entries,
    is_definition_query,
    resolve_definition,
)


@pytest.mark.parametrize(
    "query,canonical",
    [
        ("조석예보란", "조석예보"),
        ("S-101 Feature란", "S-101 Feature"),
        ("Obstruction이란", "Obstruction"),
        ("정박지란", "정박지"),
    ],
)
def test_registered_terms_use_general_definition_intent(query, canonical):
    assert is_definition_query(query) is True
    assert resolve_definition(query)["canonical_term"] == canonical


@pytest.mark.parametrize(
    "query",
    [
        "9월 인천 조석예보",
        "오늘 부산 만조 시간을 알려줘",
        "부산항 주변 S-101 Feature를 찾아줘",
        "Obstruction 3km 이내 검색",
    ],
)
def test_operational_slots_override_definition_terms(query):
    assert is_definition_query(query) is False


def test_definition_sources_are_not_limited_to_curated_examples():
    entries = definition_entries()
    assert len(entries) > 100
    assert resolve_definition("정박지란")["source_kind"] == "marine_term_dictionary"
    assert resolve_definition("Obstruction이란")["source_kind"] == "s101_feature_catalogue"


def test_definition_response_is_grounded_and_not_external_prediction():
    result = build_definition_response({"task_id": "definition-test", "query": "조석예보란"})
    final = result["final_dict"]
    assert final["status"] == "COMPLETED"
    assert final["structured_result"]["analysis_type"] == "definition_lookup"
    assert final["orchestrator_v2"]["fast_path"] == "verified_definition_registry"
    assert final["evidence_bundle"]["rag_evidence"]
    assert "khoa_tide_prediction 공식 외부 데이터 연동" not in final["answer_text"]
