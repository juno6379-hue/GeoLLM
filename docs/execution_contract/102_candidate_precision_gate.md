# Candidate Precision Gate

## Goal

GeoLLM should retrieve broad candidates, but it must not promote every retrieved candidate into an executable plan.

The intended contract is:

1. `Capability Retriever` maximizes recall.
2. `Ontology/KG Validator` keeps only semantically valid candidates.
3. `QueryExecutionContext` separates confirmed values from candidate values.
4. `ExecutionValidator` runs a tool only when location, distance, dataset binding, and tool readiness are all confirmed.

## Implemented Guard

GraphRAG output is now sanitized before it reaches plan creation.

- `candidate_target_features`, `candidate_target_layers`, `candidate_target_dynamic_layers`, and `candidate_derived_concepts` preserve broad recall.
- `target_features`, `target_layers`, `target_dynamic_layers`, and `derived_concepts` contain only values that are explicitly grounded or registry-verified.
- `semantic_resolution.resolved` and `semantic_resolution.candidates` are separate in `QueryExecutionContext`.
- `RoutePlanner` no longer merges `candidate_tools` or raw GraphRAG `target_features` into executable tools/slots.

## Why This Matters

S-101 catalogue and KG neighbors can include related but non-executable terms such as:

- temporary placing
- temporary storage
- fine sand
- movable body type wave converter
- transverse joints
- side thruster
- cofferdam

Those terms may remain useful as evidence candidates, but they must not become `derived_concept`, `target_features`, selected tools, or an `execution_ready` plan unless the registry and execution validator approve the path.

## Regression Checks

Added `tests/unit/test_candidate_precision_gate.py`.

The tests verify that:

- GraphRAG recall candidates remain candidate-only.
- `accident_event` can still be retained as a verified derived concept.
- raw GraphRAG S-101 candidates do not make the route planner select S-101 spatial tools.
