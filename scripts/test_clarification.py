import asyncio
from services.orchestrator.graph import parse_intent_node
from shared.schemas.agent import AgentStatus

async def run_test():
    queries = [
        "부산항 주변 등대 찾아줘", # Missing distance, Ambiguous '등대'
        "부산항 반경 500m 내의 위험객체 분석해봐", # Ambiguous '위험객체'
        "제한구역 반경 500m 내의 암초 표시해", # Ambiguous '제한구역'
        "부산항 반경 500m 내의 정박지 찾아줘" # Valid
    ]
    
    for q in queries:
        print(f"\n[{'='*50}]")
        print(f"QUERY: {q}")
        
        state = {
            "task_id": "test-123",
            "query": q,
            "organization_id": "org-1",
            "user_id": "user-1",
            "status": AgentStatus.RECEIVED,
            "state_history": []
        }
        
        result_state = await parse_intent_node(state)
        
        status = result_state.get("status")
        print(f"STATUS: {status}")
        
        agent_result = result_state.get("agent_result")
        if agent_result and status == AgentStatus.NEEDS_CLARIFICATION:
            print("CLARIFICATION QUESTIONS:")
            for question in agent_result.clarification_questions:
                print(f" - {question}")
        else:
            print("PASS - Routing Proceeds")
            
if __name__ == "__main__":
    asyncio.run(run_test())
