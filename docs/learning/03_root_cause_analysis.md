# Root Cause Analysis

## Initial Analyzer

The initial analyzer is implemented in `scripts/analyze_benchmark_failures.py`.

It reads benchmark result JSONL files, inspects deterministic traces, and emits:

- `failure_cases.jsonl`
- `improvement_proposals.jsonl`
- `failure_analysis.md`

## Inputs

- benchmark case expectations
- SSE node events
- final task status
- route plan
- query execution context
- blockers and warnings
- final evidence fields

## Root Cause Output

Each failure should include:

```json
{
  "case_id": "...",
  "root_cause": "...",
  "root_cause_layer": "...",
  "failure_categories": [],
  "supporting_trace": [],
  "recommended_fix_level": "..."
}
```

## Fix Level Mapping

- Level 1: Dictionary / Alias
- Level 2: Slot Extractor / Normalizer
- Level 3: Ontology Mapping
- Level 4: KG Edge / Metadata
- Level 5: Registry Mapping
- Level 6: Data Binding Adapter
- Level 7: Query Template
- Level 8: Tool Capability
- Level 9: Existing Agent Capability
- Level 10: New Agent Proposal
- Level 11: Model Learning Candidate

