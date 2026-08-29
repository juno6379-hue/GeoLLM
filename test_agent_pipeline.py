import asyncio
import os
import sys

from services.spatial_analysis_agent.tool_executor import ToolExecutor

async def main():
    print("Testing DB Connection and Tool Executor...")
    
    executor = ToolExecutor()
    tool_call = {
        "name": "gbenc.s101_feature_search",
        "arguments": {
            "query_template": "gbenc_feature_search_by_radius",
            "base_location": "부산항 입구",
            "search_radius_m": 3000,
            "target_features": ["BuoyIsolatedDanger", "Wreck", "Obstruction"]
        }
    }
    
    try:
        result = await executor.execute(tool_call)
        print("Tool Execution Result:")
        print(f"Status: {result.status}")
        print(f"Warnings: {result.warnings}")
        if result.structured_result:
            count = result.structured_result.get("count", 0)
            print(f"Feature count: {count}")
            # print sample feature
            if count > 0:
                features = result.structured_result.get("features", [])
                print(f"First feature type: {features[0].get('geometry', {}).get('type')}")
        else:
            print("No structured result!")
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
