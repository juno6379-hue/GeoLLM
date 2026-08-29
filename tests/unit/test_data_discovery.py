import pytest
from shared.schemas.agent import AgentRequest, Intent, SpatialContext, SecurityContext, OrchestratorContext
from shared.security.context import ClearanceLevel
from services.data_discovery_agent.agent import execute_data_discovery

@pytest.mark.asyncio
async def test_data_discovery_with_public_clearance():
    request = AgentRequest(
        task_id="test1",
        trace_id="tr1",
        user_id="u1",
        organization_id="org1",
        agent_name="data-discovery-agent",
        original_query="부산항 위험객체",
        parsed_intent=Intent(intent_type="SPATIAL", target_objects=["위험객체"]),
        spatial_context=SpatialContext(base_location="부산항", crs="EPSG:4326"),
        security_context=SecurityContext(clearance_level=ClearanceLevel.PUBLIC)
    )
    
    result = await execute_data_discovery(request)
    
    assert result.status == "COMPLETED"
    # PUBLIC can only see "enc-busan-001", not the RESTRICTED or SECRET ones.
    assert len(result.source_dataset_versions) == 1
    assert result.source_dataset_versions[0].dataset_id == "enc-busan-001"

@pytest.mark.asyncio
async def test_data_discovery_with_secret_clearance():
    request = AgentRequest(
        task_id="test2",
        trace_id="tr2",
        user_id="u1",
        organization_id="org1",
        agent_name="data-discovery-agent",
        original_query="부산항 제한구역",
        parsed_intent=Intent(intent_type="SPATIAL", target_objects=["제한구역"]),
        spatial_context=SpatialContext(base_location="부산항", crs="EPSG:4326"),
        security_context=SecurityContext(clearance_level=ClearanceLevel.SECRET)
    )
    
    result = await execute_data_discovery(request)
    
    assert result.status == "COMPLETED"
    # SECRET can see PUBLIC, RESTRICTED, and SECRET datasets that match keywords.
    # enc-busan-001 matches "부산항"
    # ais-busan-2026 matches "부산항"
    # mil-zone-001 matches "부산항", "제한구역"
    assert len(result.source_dataset_versions) == 3

@pytest.mark.asyncio
async def test_data_discovery_no_match():
    request = AgentRequest(
        task_id="test3",
        trace_id="tr3",
        user_id="u1",
        organization_id="org1",
        agent_name="data-discovery-agent",
        original_query="제주도 날씨",
        parsed_intent=Intent(intent_type="SEARCH", target_objects=["날씨"]),
        spatial_context=SpatialContext(base_location="제주도", crs="EPSG:4326"),
        security_context=SecurityContext(clearance_level=ClearanceLevel.PUBLIC)
    )
    
    result = await execute_data_discovery(request)
    
    assert result.status == "COMPLETED"
    # 제주도/날씨 키워드가 없으므로 0개 발견
    assert len(result.source_dataset_versions) == 0
