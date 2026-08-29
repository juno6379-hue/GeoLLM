# -*- coding: utf-8 -*-
import asyncio
import json
from services.orchestrator.graph import orchestrator_graph
from shared.schemas.agent import AgentStatus

queries = [
    "부산항 입구 3km 이내 위험객체를 찾아줘",
]

async def run_tests():
    for idx, query in enumerate(queries):
        print(f"\n=======================================================")
        print(f"--- Test {idx+1}: {query} ---")
        initial_state = {
            "task_id": f"test-task-new-{idx}",
            "query": query,
            "status": AgentStatus.RECEIVED,
            "state_history": [AgentStatus.RECEIVED],
            "user_id": "test_user",
            "organization_id": "test_org"
        }
        
        config = {"configurable": {"thread_id": f"test-task-new-{idx}"}}
        
        async for chunk in orchestrator_graph.astream(initial_state, config=config, stream_mode="updates"):
            for node, state_update in chunk.items():
                if "task_plan" in state_update:
                    print(f"Task Plan generated:")
                    tp = state_update['task_plan']
                    if hasattr(tp, 'model_dump'):
                        tp = tp.model_dump()
                    
                    print(json.dumps(tp, ensure_ascii=False, indent=2))
                    
        # Verify clarification if needed
        state_snapshot = orchestrator_graph.get_state(config)
        final_status = state_snapshot.values.get("status")
        print(f"Final Status: {final_status}")

if __name__ == '__main__':
    asyncio.run(run_tests())
