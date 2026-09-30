"""Exercise the stream route's general clarification boundary, without live tools."""
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("restored", [False, True])
async def test_general_resume_replans_from_live_or_persisted_checkpoint(monkeypatch, tmp_path, restored):
    from services.orchestrator import router
    from services.orchestrator.task_store import PersistentTaskStore

    state = {"task_id": "resume-test", "query": "문서 검색", "status": "NEEDS_CLARIFICATION",
             "task_plan": {"analysis_type": "document_search"}, "approval_granted": True,
             "query_execution_context": {"revision": 7, "readiness": "EXECUTION_READY"},
             "agent_request": {"old": True}, "agent_result": {"old": True}}
    store = PersistentTaskStore(str(tmp_path / "tasks.sqlite3"))
    store["resume-test"] = {"query": state["query"], "status": "NEEDS_CLARIFICATION", "snapshot": state}
    captured = []

    async def stream(initial, **kwargs):
        captured.append(initial)
        yield {"test": {"status": "NEEDS_CLARIFICATION"}}

    calls = []
    def snapshot(config):
        calls.append(config)
        return SimpleNamespace(values={} if restored and len(calls) == 1 else state, next=("execute_agent",))

    monkeypatch.setattr(router, "TASK_STORE", store)
    monkeypatch.setattr(router, "orchestrator_graph", SimpleNamespace(get_state=snapshot, astream=stream))
    monkeypatch.setattr(router, "comparison_store", lambda: SimpleNamespace(submit=lambda *_: "comparison"))
    monkeypatch.setattr(router, "observe_comparison", lambda *_: None)
    monkeypatch.setattr(router, "build_debug_trace", lambda *_: {})
    response = await router.stream_task(router.TaskCreateRequest(task_id="resume-test", query="항만 안전 기준", user_id="admin"))
    events = [item async for item in response.body_iterator]
    assert not any('"event": "error"' in item for item in events)
    assert len(captured) == 1
    restarted = captured[0]
    assert restarted["execution_revision"] == 8
    for key in ("query_execution_context", "task_plan", "agent_request", "agent_result", "approval_granted"):
        assert restarted[key] is None
