from unittest.mock import Mock

import pytest

from services.orchestrator import execution_validator as validator
from services.orchestrator.agent_execution_gate import validated_agent
from services.orchestrator.agent_registry import registry
from services.orchestrator.schema_binding_adapter import BindingResult, SchemaBindingAdapter
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, DataBinding, ExecutionSlots, PlanStatus, QueryExecutionContext, SecurityContext, ToolBinding


def request(agent="Standard RAG Agent", operation="document_search", *, context=True):
    query = "근거 문서를 검색해줘"
    return AgentRequest(task_id="contract-test", trace_id="trace", user_id="user", organization_id="org",
        agent_name=agent, original_query=query, security_context=SecurityContext(clearance_level="SECRET"),
        query_execution_context=QueryExecutionContext(request_id="contract-test", original_query=query,
            route_plan={"analysis_type": operation, "primary_agent": agent}) if context else None)


@pytest.fixture
def document_binding(monkeypatch):
    monkeypatch.setenv("OLLAMA_EMBEDDING_URL", "http://fixture.invalid/api/embed")
    monkeypatch.setattr(validator.schema_binding_adapter, "build_bindings", lambda *_: BindingResult(
        data_bindings=[DataBinding(dataset_id="docs", relation="knowledge.document_chunks")],
        tool_bindings=[ToolBinding(tool_id="rag.graph_scoped_retrieve", operation="document_search")]))


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", [row["agent_name"] for row in registry.agents if row["execution_contract"]["scope"] != "inspection"])
async def test_every_execution_entry_blocks_missing_qec(agent):
    result = await registry.get_execute_function(agent)(request(agent, context=False))
    assert result.status == AgentStatus.BLOCKED
    assert result.provenance["execution_validation"]["authority"] == "ExecutionValidator"
    assert not result.structured_result["query_execution_context"]["route_plan"]["execution_ready"]


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["query", "task", "agent", "operation", "source"])
async def test_direct_entry_revalidates_before_body(document_binding, monkeypatch, change):
    req = request()
    req.query_execution_context = validator.validate_agent_execution(req, "Standard RAG Agent")
    assert validator.is_execution_authorized(req.query_execution_context)
    if change == "query":
        req.original_query = "다른 질의"
    elif change == "task":
        req.task_id = "another-task"
    elif change == "agent":
        req.query_execution_context.route_plan["primary_agent"] = "AIS Analysis Agent"
    elif change == "operation":
        req.query_execution_context.route_plan["analysis_type"] = "ais_track_search"
    else:
        monkeypatch.setattr(validator.schema_binding_adapter, "build_bindings", lambda *_: BindingResult(blockers=["BLOCKED_DATA: source removed"]))
    body = Mock(side_effect=AssertionError("body must not execute"))

    @validated_agent("Standard RAG Agent")
    async def run(value):
        return body(value)

    result = await run(req)
    assert result.status == AgentStatus.BLOCKED
    body.assert_not_called()


@pytest.mark.asyncio
async def test_direct_valid_execution_preserves_partial_result(document_binding):
    @validated_agent("Standard RAG Agent")
    async def run(req):
        assert validator.is_execution_authorized(req.query_execution_context)
        return AgentResult(task_id=req.task_id, trace_id=req.trace_id, agent_name=req.agent_name,
            agent_version="test", status=AgentStatus.PARTIAL)
    result = await run(request())
    assert result.status == AgentStatus.PARTIAL
    assert result.provenance["execution_validation"]["authority"] == "ExecutionValidator"


@pytest.mark.asyncio
async def test_inspection_cannot_approve_or_replace_parent_execution():
    req = request("Validation Agent", "feature_search_by_radius")
    parent = req.query_execution_context
    result = await registry.get_execute_function("Validation Agent")(req)
    assert req.query_execution_context is parent
    assert parent.readiness == PlanStatus.DRAFT
    child = result.provenance["query_execution_context"]
    assert child["route_plan"]["analysis_type"] == "evidence_validation"
    assert child["context"]["contract_scope"] == "inspection"


def test_slot_patch_revokes_previous_approval(document_binding):
    req = request()
    approved = validator.validate_agent_execution(req, "Standard RAG Agent")
    patched = approved.merge_slot_patch({"target_term": "다른 대상"}, producer="user")
    assert patched.revision == approved.revision + 1
    assert patched.readiness == PlanStatus.DRAFT
    assert not patched.route_plan["execution_ready"]
    assert "execution_validation" not in patched.provenance
    assert validator.is_execution_authorized(approved)


def test_unknown_operation_cannot_borrow_rag_primary_agent():
    req = request(operation="unimplemented")
    result = validator.validate_agent_execution(req, "Standard RAG Agent")
    assert result.readiness == PlanStatus.BLOCKED_CONFIG


def test_rag_source_permissions_required(monkeypatch):
    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", lambda _: {"exists": True, "has_select": False,
        "columns": [{"name": key} for key in ("content", "metadata", "embedding")]})
    result = adapter.build_bindings({"analysis_type": "document_search"}, {})
    assert not result.data_bindings
    assert any("SELECT" in item for item in result.blockers)


@pytest.mark.parametrize("missing", ["chunk_id", "source_id", "source_sha256"])
def test_rag_missing_evidence_columns_cannot_execute(monkeypatch, missing):
    adapter = SchemaBindingAdapter()
    columns = {"chunk_id", "source_id", "source_sha256", "content", "metadata", "embedding"} - {missing}
    monkeypatch.setattr(adapter, "_inspect_relation", lambda _: {"exists": True, "has_select": True,
        "columns": [{"name": name} for name in columns]})
    result = adapter.build_bindings({"analysis_type": "document_search"}, {})
    assert not result.data_bindings
    assert any(item.startswith("BLOCKED_DATA") for item in result.blockers)


@pytest.mark.asyncio
async def test_discovery_does_not_fetch_csv(monkeypatch, tmp_path):
    from services.data_discovery_agent import agent
    from services.registry.catalog_service import DatasetCatalogEntry
    import pandas
    fetch = Mock(side_effect=AssertionError("metadata inspection must not fetch CSV bodies"))
    monkeypatch.setattr(pandas, "read_csv", fetch)
    monkeypatch.setattr(agent, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(agent, "llm_api_enabled", lambda: False)
    monkeypatch.setattr(agent, "build_live_catalog", lambda: [DatasetCatalogEntry("test", "1", "test", "PUBLIC", ["자료"], api_endpoint="https://fixture.invalid/private.csv")])
    monkeypatch.setattr(agent, "build_discovery_snapshot", lambda: {"blocked_relations": [], "candidate_data": [],
        "execution_level": "METADATA_ONLY", "can_execute_spatial_query": False, "required_next_actions": [], "provenance": {}})
    req = request("Data Discovery Agent", context=False)
    from shared.schemas.agent import Intent
    req.parsed_intent = Intent(intent_type="DATA_DISCOVERY", target_objects=["자료"])
    result = await agent.execute_data_discovery(req)
    fetch.assert_not_called()
    assert result.structured_result["fetched_data"] == {}
    assert result.provenance["query_execution_context"]["context"]["contract_scope"] == "inspection"


@pytest.mark.parametrize("distance,unit,allowed", [(50, "kilometers", True), (50.001, "kilometers", False),
    (50000, "meters", True), (50001, "meters", False), (0, "meters", False), (float("nan"), "meters", False)])
def test_legacy_distance_policy_matches_execution_validator(distance, unit, allowed):
    from services.spatial_analysis_agent.schemas import SpatialDSL
    from services.spatial_analysis_agent.validator import validate_dsl
    dsl = SpatialDSL.model_construct(target_layers=["enc_features_v1"], crs="EPSG:4326",
        base_geometry="POINT(129 35)", buffer_distance=distance, distance_unit=unit)
    assert validate_dsl(dsl)[0] is allowed
