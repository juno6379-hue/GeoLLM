"""Compatibility adapter to the real orchestration graph."""
from services.orchestrator.graph import orchestrator_graph

async def run_orchestration_workflow(task_id: str, query: str, task_store):
    current = task_store.get(task_id, {})
    state = await orchestrator_graph.ainvoke(
        {"task_id": task_id, "query": query,
         "organization_id": current.get("organization_id", "default_org"),
         "user_id": current.get("user_id", "default_user"),
         "spatial_context": current.get("spatial_context") or {},
         "status": "RECEIVED", "state_history": []},
        config={"configurable": {"thread_id": task_id}},
    )
    result = state.get("final_dict")
    task_store[task_id] = {**current, "query": query, "status": state.get("status", "FAILED"),
                           "result": result, "error_message": state.get("error_message")}
    return result
