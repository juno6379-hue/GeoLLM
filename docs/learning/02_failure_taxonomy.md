# Failure Taxonomy

The machine-readable taxonomy is stored at `configs/evaluation/failure_taxonomy.yaml`.

## Classification Policy

Failure codes must be derived from execution trace, expected-vs-actual comparison, blockers, route plans, tool bindings, evidence bundles, and final response fields.

LLM-only guesses are not authoritative.

## Primary Layers

- Query Normalization
- Slot Extraction
- Semantic / Ontology Resolution
- KG / Graph-RAG
- Location Resolution
- Data Binding
- Registry Mapping
- Query Template
- Tool Capability
- Agent Capability
- RAG Retrieval
- Evidence Assembly
- Response / UX
- Safety

## Safety Failures

These are approval-blocking:

- `UNSAFE_EXECUTION`
- `MOCK_LEAKAGE`
- `HALLUCINATED_DATA`
- `UNSUPPORTED_CLAIM`

