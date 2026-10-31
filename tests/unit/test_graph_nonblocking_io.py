import ast
import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace


def load_node(name, namespace):
    source = Path("services/orchestrator/graph.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    namespace["OrchestratorState"] = dict
    exec(compile(ast.Module(body=[node], type_ignores=[]), "graph.py", "exec"), namespace)
    return namespace[name]


def test_graph_retrieval_does_not_block_other_async_requests():
    started, release = threading.Event(), threading.Event()
    def retrieve(query, seed):
        started.set()
        assert release.wait(2), "event loop was blocked by retrieval"
        return {"observed": query}
    ns = {"graph_rag_retriever": SimpleNamespace(retrieve=retrieve),
          "_valid_derived_concept": lambda x: x,
          "_sanitize_graph_context_for_execution": lambda result, *args: result,
          "AgentStatus": SimpleNamespace(INTENT_PARSED="INTENT_PARSED"),
          "log_transition": lambda *args, **kwargs: []}
    node = load_node("graph_rag_node", ns)
    async def run():
        task = asyncio.create_task(node({"query": "lookup"}))
        for _ in range(100):
            if started.is_set(): break
            await asyncio.sleep(.005)
        assert started.is_set()
        release.set()
        assert (await task)["graph_context"] == {"observed": "lookup"}
    asyncio.run(run())


def test_policy_stops_before_any_analysis_or_execution_import():
    calls = []
    async def block(state):
        calls.append(state["query"])
        return {"status": "BLOCKED"}
    node = load_node("parse_intent_node", {
        "logger": SimpleNamespace(info=lambda *a, **k: None),
        "_looks_like_policy_block_query": lambda q: True,
        "fast_spatial_or_traffic_block_node": block})
    result = asyncio.run(node({"task_id": "t", "query": "private request"}))
    assert calls == ["private request"]
    assert result["status"] == "BLOCKED" and result["query_contract_blocked"] is True
