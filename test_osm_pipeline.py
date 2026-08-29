import os
import asyncio
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.schemas.agent import AgentRequest
from services.spatial_analysis_agent.agent import execute_spatial_analysis

async def test_pipeline():
    # 1. Forward Geocoding (OSM Fallback Test)
    from shared.schemas.agent import SecurityContext
    
    sec = SecurityContext(clearance_level="PUBLIC")
    
    print("=== Test 1: Forward Geocoding (OSM) ===")
    req1 = AgentRequest(
        task_id="test_osm_forward",
        trace_id="test_trace",
        user_id="test_user",
        organization_id="test_org",
        agent_name="spatial_analysis_agent",
        security_context=sec,
        original_query="제주공항 반경 5km 이내의 등대(Beacon)를 찾아줘"
    )
    res1 = await execute_spatial_analysis(req1)
    print(f"Status: {res1.status}")
    print(f"Summary: {res1.summary}")
    print(f"Provenance: {res1.provenance}")
    
    # 2. Reverse Geocoding (OSM Fallback Test)
    print("\n=== Test 2: Reverse Geocoding (OSM) ===")
    req2 = AgentRequest(
        task_id="test_osm_reverse",
        trace_id="test_trace",
        user_id="test_user",
        organization_id="test_org",
        agent_name="spatial_analysis_agent",
        security_context=sec,
        original_query="이 좌표(POINT(126.49 33.51)) 근처에 어떤 곳이 있어?"
    )
    res2 = await execute_spatial_analysis(req2)
    print(f"Status: {res2.status}")
    print(f"Summary: {res2.summary}")
    print(f"Provenance: {res2.provenance}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
