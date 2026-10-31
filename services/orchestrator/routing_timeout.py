"""Bound the optional intent-model fallback, including transport retries."""
import asyncio
import math
import os


def routing_timeout_seconds() -> float:
    try:
        value = float(os.environ.get('GEOLLM_ROUTING_FALLBACK_TIMEOUT_SEC', '15'))
    except ValueError:
        return 15.0
    return min(60.0, max(0.1, value)) if math.isfinite(value) else 15.0


async def invoke_routing_fallback(llm, messages, timeout_seconds: float):
    # Transport timeout alone does not bound retry/backoff or a stalled model
    # adapter. The outer deadline covers the entire awaitable.
    return await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout_seconds)
