import asyncio

from services.standard_rag_agent.agent import execute_rag_search
from shared.schemas.agent import AgentRequest, SecurityContext


async def main() -> None:
    request = AgentRequest(
        task_id="rag-smoke",
        trace_id="trace-rag-smoke",
        user_id="codex",
        organization_id="local",
        agent_name="standard-rag-agent",
        original_query="DepthArea definition",
        security_context=SecurityContext(clearance_level="PUBLIC"),
    )
    result = await execute_rag_search(request)
    print("status=", result.status)
    print("mode=", result.provenance.get("llm_mode"))
    print("retrieved=", result.structured_result.get("retrieved_count"))
    print("answer=", (result.answer_text or "")[:500])


if __name__ == "__main__":
    asyncio.run(main())
