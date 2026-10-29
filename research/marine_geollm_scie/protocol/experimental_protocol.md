# Experimental protocol v1 — DRAFT pilot

Scope: research adapters and outputs under this directory only. Production must never import research code, expose validator bypass flags, or use experiment labels to change authority. Reuse production QueryExecutionContext verbatim. Existing regression benchmark remains unchanged.

## Research questions and hypotheses

Test whether ontology grounding, explicit execution contracts and deterministic validation improve semantic correctness and reduce false-ready decisions compared with B0–B4. Direction and magnitude are unknown. Failure, null and unsupported results are valid observations; do not replace them with expected success.

Pilot: 18 AI-authored DRAFT queries, three each Q1–Q6; zero human GOLD. Q4 has three meaning-equivalent phrasings and is one equivalence cluster. Q7 injected plans are a separate diagnostic population. Q8 unsupported until actual cross-product data and independent oracle exist. This is a convenience pilot, not a representative publication benchmark. No spatial coordinates are invented; named-place resolution must capture its source or remain unresolved. Selected-area query intentionally lacks context to test clarification.

## Conditions and execution

B0 direct LLM, B1 document RAG, B2 KG grounded without deterministic validator, B3 generic typed tool planner, B4 LLM reviewer, P existing production adapter. Identical model digest, prompt policy, frozen source snapshot and query input should be recorded. Mark unavailable baselines NOT_IMPLEMENTED instead of substituting P. P must be called current-production-path, not Full Proposed, until postvalidation/recovery/evidence components are verified.

Use K=3 independent invocations per stochastic query/method in pilot; K=5 in final. Save seed, temperature, request/response, actual model digest and usage. Do not count three copies of deterministic validation as three samples. Interleave method order where feasible and record schedule, cache, warm-up and failures; serialized Ollama avoids contention but limits latency generalization.

Start with frozen pilot; no prompt tuning using holdout. Final train/validation/holdout splits must assign all near-duplicates and equivalence-group members to one split. Expert annotations and adjudication are prerequisites for accuracy claims. Final benchmark target is at least 300 reviewed normal cases plus separately reviewed fault cases, subject to source coverage.

## Analysis and exclusions

Primary unit is unique case/equivalence cluster, not repeated row. Average stochastic repeats within case before paired comparison; bootstrap clusters, preserve pairing. McNemar needs paired independent gold-labeled binary case outcomes under a preregistered aggregation rule. Report missingness and timeout denominator, never silently drop errors. Distinguish runtime error, unsupported operation, unmet input, empty-valid result, wrong result and invalid plan accepted.

EVQSR requires measured S,P,X,G,E; absent gold or execution means null, not zero or one. API completed or validator ready is not spatial correctness. Fault diagnostics with injected fixtures are labeled diagnostics; mock geometry never becomes GIS oracle. If a method cannot execute comparable tasks, report coverage separately.

Recovery needs recorded initial failure, real revision, bounded iteration, final oracle and drift comparison. Without this chain report not measured. Evidence generation is not evidence correctness. No private chain-of-thought capture; only structured observable plans and evidence.
