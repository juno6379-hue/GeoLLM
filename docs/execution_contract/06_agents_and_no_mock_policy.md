# Agents And No Mock Policy

Status: PARTIAL

## Implemented

Spatial Agent now enforces the shared execution contract at the agent boundary.

Rules:

- `query_execution_context` is required.
- `query_execution_context.readiness` must be `EXECUTION_READY`.
- If readiness is not ready, the agent returns `NEEDS_CLARIFICATION` for user-fixable blockers or `BLOCKED`/`FAILED` for non-user-fixable contract failures.
- The production execution path builds `QueryPlan` from `QueryExecutionContext` only.
- LLM spatial DSL extraction, geocoding fallback, parsed-intent distance fallback, resolved metadata fallback, and default target code fallback are skipped on the contract-enforced path.
- Specialist KG context is optional provenance only; failure to load KG context does not mutate the execution plan.

## SQL Compiler Guardrail

`feature_dwithin` no longer defaults to `distance_m=1000`.

If a caller tries to compile a radius query without `distance_m`, SQL compilation fails with:

```text
distance_m is required for feature_dwithin
```

## Mock Policy

Existing synthetic feature generation blocks in `tool_executor.py` remain disabled by hardcoded false branches. Production execution now reaches the tool executor only after the orchestrator validator and the agent-level contract check pass.

## Still Partial

- Legacy code remains in the Spatial Agent for non-contract paths, but it is bypassed by the contract-enforced production path.
- `tool_executor.py` still contains disabled mock-generation code that should be removed or moved to explicit test fixtures.
- `AgentResult.evidence_bundle` is not yet populated with stable spatial feature evidence IDs directly by the agent.
- Accident relation lookup has validation but not a specialist execution adapter yet.

