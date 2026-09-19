"""Named-place workflows through the compiled graph, without database or LLM calls."""

import asyncio
from unittest.mock import Mock
from uuid import uuid4

import pytest
import requests

from services.spatial_analysis_agent import place_resolver as resolver
from shared.schemas.agent import AgentStatus


@pytest.fixture
def graph(monkeypatch):
    monkeypatch.setenv("DISABLE_LLM_API", "true")
    monkeypatch.setattr(requests.sessions.Session, "request", Mock(side_effect=AssertionError("No network in graph fixtures")))
    from services.orchestrator import graph as module

    monkeypatch.setattr(module.cache, "check_cache", Mock(side_effect=AssertionError("No embedding cache in named-place fast path")))
    monkeypatch.setattr(module.router, "route_query", Mock(side_effect=AssertionError("No semantic routing in named-place fast path")))
    monkeypatch.setattr(module, "ChatOpenAI", Mock(side_effect=AssertionError("No LLM in named-place fast path")))
    connect = Mock(side_effect=AssertionError("Only fixtures may be queried"))
    monkeypatch.setattr(resolver.psycopg2, "connect", connect)
    item = resolver._candidate("island:fixture", "테스트항", ["Fixture Port"], "POINT(127 35)", [{"source_ref": "fixture", "source_id": "fixture"}])
    catalog = {"candidates": [item], "unavailable_sources": []}
    monkeypatch.setattr(resolver, "load_catalog", lambda **kwargs: catalog)
    yield module, catalog
    connect.assert_not_called()


def invoke(graph, query, **kwargs):
    task_id = "place-fixture-" + str(uuid4())
    state = {"task_id": task_id, "query": query, "user_id": "fixture", "organization_id": "fixture", "status": AgentStatus.RECEIVED, "state_history": [], **kwargs}
    return asyncio.run(graph.build_orchestrator_graph().ainvoke(state, config={"configurable": {"thread_id": task_id}}))


@pytest.mark.parametrize("query", ["테스트항 위치를 알려줘", "Fixture Port 좌표", "Where is Fixture Port?"])
def test_place_query_returns_source_point_map_and_evidence(graph, query):
    module, catalog = graph
    result = invoke(module, query)
    final = result["final_dict"]
    assert result["status"] == AgentStatus.COMPLETED
    assert final["structured_result"]["analysis_type"] == "place_lookup"
    assert final["structured_result"]["place_id"] == catalog["candidates"][0]["place_id"]
    point = final["features"]["features"][0]
    assert point["geometry"]["coordinates"] == [127, 35]
    assert final["evidence_bundle"]["spatial_feature_evidence"][0]["data"]["place_id"] == point["id"]


def test_ambiguous_place_query_and_explicit_selection(graph):
    module, catalog = graph
    other = resolver._candidate("khoa:fixture", "테스트항", [], "POINT(128 35)", [{"source_ref": "fixture", "source_id": "other"}])
    catalog["candidates"].append(other)
    first = invoke(module, "테스트항 위치")
    assert first["status"] == AgentStatus.NEEDS_CLARIFICATION
    assert len(first["final_dict"]["structured_result"]["location_candidates"]) == 2
    selected = invoke(module, "테스트항 위치", spatial_context={key: other[key] for key in ("place_id", "place_version", "geometry", "crs")})
    assert selected["status"] == AgentStatus.COMPLETED
    assert selected["final_dict"]["structured_result"]["location_resolution"]["status"] == "CONFIRMED_SELECTION"


def test_selected_place_evidence_survives_coordinate_confirmation(graph):
    module, catalog = graph
    evidence = {
        "place_id": catalog["candidates"][0]["place_id"],
        "place_version": catalog["candidates"][0]["place_version"],
        "label": "테스트항",
        "source_ref": "fixture",
        "source_url": "https://example.test/place",
        "evidence_summary": "공식 지명 후보 근거 요약",
        "source_records": [{"source_ref": "fixture", "source_id": "fixture"}],
    }
    selected = invoke(
        module,
        "테스트항 위치",
        spatial_context={
            key: catalog["candidates"][0][key]
            for key in ("place_id", "place_version", "geometry", "crs")
        } | {"selected_place_evidence": evidence},
    )

    final = selected["final_dict"]
    assert selected["status"] == AgentStatus.COMPLETED
    assert final["structured_result"]["selected_place_evidence"]["evidence_summary"] == "공식 지명 후보 근거 요약"
    assert final["structured_result"]["location_resolution"]["selected_place_evidence"] == evidence
    feature = final["features"]["features"][0]
    assert feature["properties"]["evidence_summary"] == "공식 지명 후보 근거 요약"
    evidence_row = final["evidence_bundle"]["spatial_feature_evidence"][0]
    assert evidence_row["data"]["selected_place_evidence"] == evidence


def test_nearest_query_does_not_auto_approve_curated_reference(graph):
    module, _ = graph
    result = invoke(module, "부산항 입구에서 가장 가까운 정박지를 찾아줘")
    assert result["status"] == AgentStatus.NEEDS_CLARIFICATION
    assert result["final_dict"]["structured_result"]["analysis_type"] == "nearest_feature"
    assert result["final_dict"]["structured_result"]["location_candidates"]


def test_unrecognized_place_never_uses_hardcoded_city_coordinates(graph):
    module, _ = graph
    assert module._resolve_known_marine_place_wkt("busan invented station", {})[0] is None


def test_place_query_revision_is_preserved(graph):
    module, _ = graph
    result = invoke(module, "테스트항 위치", execution_revision=3)
    assert result["query_execution_context"]["revision"] == 3
    assert result["query_execution_context"]["plan_hash"]


@pytest.mark.parametrize("query", ["해양보호구역 위치", "부산항 주변 정박지 위치", "선박 위치 추적", "부산항 고시"])
def test_area_and_feature_queries_are_not_replaced_by_place_lookup(graph, query):
    module, _ = graph
    assert not module._looks_like_place_lookup(query)
    assert not module._looks_like_known_place_search(query)


def test_notice_query_is_legal_rag_not_place_lookup(graph):
    module, _ = graph
    query = "부산항 고시"
    state = {"query": query, "status": AgentStatus.INTENT_PARSED, "spatial_context": {}}
    assert module._looks_like_legal_rag_query(query)
    assert not module._looks_like_place_lookup(query)
    assert not module._looks_like_known_place_search(query)
    assert module.check_intent_parsed(state) == "fast_document_answer"


def test_notice_query_plan_does_not_resolve_place_problem(graph):
    module, _ = graph
    result = invoke(module, "부산항 고시", spatial_context={"base_location": "부산항"})

    assert result["final_dict"]["structured_result"]["analysis_type"] != "place_lookup"
    assert result["final_dict"].get("error_code") != "EXTERNAL_PLACE_CANDIDATES"


@pytest.mark.parametrize(
    "query, expected_title",
    [
        ("부산항 고시", "부산항 항법 등에 관한 규칙"),
        ("부산항 항법 고시 근거를 설명해줘", "부산항 항법 등에 관한 규칙"),
        ("부산항 정박지와 항로 고시 내용", "부산항 항법 등에 관한 규칙"),
        ("부산항 속력 제한 근거 고시", "부산항 항법 등에 관한 규칙"),
        ("부산항 예선운영 고시", "부산항예선운영세칙"),
        ("부산항 항만기본계획 변경 고시", "항만기본계획 변경 고시(부산항)"),
        ("부산항 항만시설 운영세칙 근거", "부산항 항만시설 운영세칙"),
        ("인천항 고시", "인천항·경인항 선박통항규칙"),
        ("인천항 항법과 속력제한 고시", "인천항·경인항 선박통항규칙"),
        ("인천항 항만기본계획 변경 고시", "항만기본계획 변경 고시(인천항)"),
        ("인천항 육상항만구역 지형도면 고시", "인천항 육상항만구역 및 지형도면 변경 고시"),
    ],
)
def test_busan_notice_queries_return_authoritative_registry_docs(graph, query, expected_title):
    module, _ = graph
    result = invoke(module, query)
    final = result["final_dict"]

    assert result["status"] == AgentStatus.COMPLETED
    assert final["structured_result"]["analysis_type"] == "document_search"
    assert final["orchestrator_v2"]["fast_path"] == "legal_notice_registry"
    assert final["structured_result"]["documents"]
    assert any(expected_title == doc["title"] for doc in final["structured_result"]["documents"])
    assert final["evidence_bundle"]["regulatory_evidence"]
    assert "요청한 법령/고시/표준 항목" not in final["summary"]


def test_nonexistent_notice_still_blocks_without_inventing_evidence(graph):
    module, _ = graph
    result = invoke(module, "존재하지 않는 해양 고시 ABC-999의 내용을 알려줘")
    final = result["final_dict"]

    assert result["status"] == AgentStatus.BLOCKED
    assert final["error_code"] == "NO_AUTHORITATIVE_EVIDENCE"
    assert final["structured_result"]["documents"] == []


def test_accident_spatial_history_extracts_registry_anchor(graph, monkeypatch):
    module, _ = graph
    monkeypatch.setattr(
        module,
        "_load_yaml_registry",
        lambda _filename: {
            "entries": {
                "dokdo": {
                    "label": "독도",
                    "aliases": ["독도"],
                    "geometry": "POINT(131.8644 37.2411)",
                    "crs": "EPSG:4326",
                }
            }
        },
    )

    query = "독도 부근 사고이력"
    assert module._registered_place_aliases()["독도"]["place_id"] == "dokdo"
    assert module._accident_spatial_anchor_query(query, {}) == "독도"
    assert module._looks_like_accident_spatial_history_query(query)
