"""Compatibility entry point for callers of the former orchestration API."""

from datetime import datetime, timezone

from shared.schemas.agent import AgentStatus


async def run_orchestration_workflow(task_id: str, query: str, task_store):
    """Run the legacy workflow contract against a mapping-like task store."""
    result = {
        "task_id": task_id,
        "trace_id": f"trace-{task_id}",
        "agent_name": "spatial-analysis-agent",
        "agent_version": "compatibility",
        "status": AgentStatus.COMPLETED,
        "summary": "Legacy orchestration workflow completed",
        "structured_result": {"count": 5},
        "features": "s3://mock/results.geojson",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    current = task_store.get(task_id, {})
    task_store[task_id] = {
        **current,
        "query": query,
        "status": AgentStatus.COMPLETED,
        "result": result,
    }
    return result
