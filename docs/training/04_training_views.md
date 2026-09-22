# Training Views

Generated views are:

- `fastpath_router.jsonl`: raw query/context to fast path and capabilities
- `capability_retriever.jsonl`: positives, structured hard negatives, typed targets
- `slot_extractor.jsonl`: raw query/context to sourced slots
- `planner.jsonl`: QueryExecutionContext-shaped input to resolver/agent/tool/template chain
- `execution_validator.jsonl`: slots/routing/data bindings to readiness and outcomes
- `response_generator.jsonl`: actual fixture result/evidence inputs plus answer policy
- `component_teacher_forcing.jsonl`: gold intermediate labels for isolated component training only
- `end_to_end.jsonl`: raw input to the complete semantic, slot, route, and execution contract

Gold intermediate labels are never inputs to the production-shaped router or end-to-end view.
Dynamic execution cases without a frozen result/evidence fixture are excluded from the response-generator view.
