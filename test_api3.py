import asyncio
import sys
import json
sys.path.insert(0, '/app')

from shared.schemas.agent import AgentRequest, Intent, SpatialContext, SecurityContext
from services.spatial_analysis_agent.agent import execute_spatial_analysis

async def run_test():
    request = AgentRequest(
        task_id="test_task_fast_2",
        trace_id="trace_test_fast_2",
        user_id="user1",
        organization_id="org1",
        agent_name="spatial-analysis-agent",
        original_query="부산항 부근의 선석을 찾아줘",
        parsed_intent=Intent(
            intent_type="SPATIAL_SEARCH",
            target_objects=["선석"],
            spatial_conditions=["부산항 부근"],
            execution_plan="1. Spatial Analysis Agent 호출",
            output_format="MAP"
        ),
        spatial_context=SpatialContext(base_location="부산항", buffer_distance=3000),
        security_context=SecurityContext(clearance_level="PUBLIC"),
        previous_agent_outputs={
            "resolved_metadata": {
                "canonical_term": "선석",
                "selected_feature": "Berth",
                "nftc_codes": [10]
            },
            "resolved_nftc_codes": [10]
        }
    )
    
    import time
    start = time.time()
    res = await execute_spatial_analysis(request)
    end = time.time()
    
    print(f"Execution time: {end - start:.2f} seconds")
    print(f"Status: {res.status}")
    if res.tool_calls:
        for tc in res.tool_calls:
            print(f"Tool used: {tc.tool_name}")
    print("\n--- Structured Result ---")
    print(json.dumps(res.structured_result, ensure_ascii=False, indent=2))
    print("\n--- Output Layers ---")
    print(json.dumps([l.model_dump() if hasattr(l, 'model_dump') else l for l in res.output_layers], ensure_ascii=False, indent=2))

asyncio.run(run_test())
