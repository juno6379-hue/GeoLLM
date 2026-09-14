import asyncio
import json

from services.data_discovery_agent.agent import execute_data_discovery
from shared.schemas.agent import AgentRequest, SecurityContext


async def main() -> None:
    request = AgentRequest(
        task_id="dd-tide",
        trace_id="trace-dd-tide",
        user_id="codex",
        organization_id="local",
        agent_name="data-discovery-agent",
        original_query="9월 인천 대조기 일정",
        security_context=SecurityContext(clearance_level="PUBLIC"),
    )
    result = await execute_data_discovery(request)
    print(json.dumps({
        "requires_external_api": result.structured_result.get("requires_external_api"),
        "api_params": result.structured_result.get("api_params"),
        "external_data_evidence": result.structured_result.get("external_data_evidence"),
        "recommended_next_actions": result.recommended_next_actions[:3],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
