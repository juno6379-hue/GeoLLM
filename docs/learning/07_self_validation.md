# Self Validation

Every benchmark-driven change should be checked against:

- unit tests
- schema contract tests
- ontology validation
- registry integrity tests
- QueryExecutionContext contract tests
- agent routing tests
- spatial DB tests
- RAG retrieval tests
- evidence validation
- negative and exception tests
- conversation context tests
- benchmark regression

Approval blockers:

- mock leakage
- unsafe execution
- hallucinated data
- unsupported claim
- regression in existing benchmark cases

