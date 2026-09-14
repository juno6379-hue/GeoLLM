# Agent Expansion Policy

New agents are proposal-only until human approval.

An agent proposal may be created only when all conditions in `configs/evaluation/agent_expansion_policy.yaml` are satisfied.

The benchmark system should prefer these remedies before proposing a new Agent:

1. Dictionary or alias correction
2. Slot extraction improvement
3. Ontology or concept mapping
4. KG or metadata enrichment
5. Registry mapping
6. Data binding adapter change
7. Query template update
8. Tool capability expansion
9. Existing Agent capability expansion

Agent proposals are written to:

`outputs/agent_learning/agent_capability_proposals.jsonl`

