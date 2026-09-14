# KG Authority And Paths

Status: PARTIAL

## Policy

KG and dictionaries are treated as semantic candidate sources, not as physical execution authority.

Execution authority is split as follows:

- Dictionary/KG: semantic candidates and graph-path provenance.
- Registry: approved layer/tool/template IDs.
- SchemaBindingAdapter: actual DB relation/column existence.
- ExecutionValidator: final deterministic readiness gate.
- Specialist agent: execution only after contract readiness.

## Implemented Guardrails

- `QueryExecutionContext` keeps KG/RAG context separately from `data_bindings` and `tool_bindings`.
- Schema binding is built from registry + DB inspection, not from KG text.
- Execution readiness is set by `ExecutionValidator`, not by agent existence alone.
- Agent dispatch revalidates the contract and blocks Spatial Agent execution when readiness is not `EXECUTION_READY`.

## Still Partial

- KG graph paths are still stored as existing graph retriever payloads; edge IDs and verification status need normalization into `EvidenceItem`.
- `DEFERRED`, `CANDIDATE`, `NEEDS_REVIEW`, and `VERIFIED` edge policies are not yet fully enforced.
- KG-derived tool/template candidates are not yet independently reconciled with all registry metadata.

