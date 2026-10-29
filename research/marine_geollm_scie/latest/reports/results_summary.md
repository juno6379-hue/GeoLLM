# PILOT — NOT FINAL PAPER RESULT

Publication status: **NOT_READY**

Cases: 31; verified expert GOLD: 0; run rows: 114.

- No final-paper claims: expert adjudication and locked holdout are required.
- Repeated trials are descriptive only; no unpaired significance test is reported.
- Missing predictions remain null; runtime completion is not semantic or spatial truth.
- R6 contains observed profiles only; causal ablation requires controlled matched runs.

Operational latency uses observed samples and lists missing counts. Fault diagnostics are separate from expert-scored results.

## Observed diagnostic runs

- `B4_LLM_Self_Reviewer`: 21 rows; states {'error': 2, 'completed': 19}.
- `PRODUCTION_LINGUISTIC_COMPONENT`: 54 rows; states {'COMPONENT_RETURNED': 54}.
- `P_ExecutionValidator`: 21 rows; states {'completed': 21}.
- `P_radius_component`: 18 rows; states {'COMPLETED': 12, 'NEEDS_CLARIFICATION': 3, 'BLOCKED': 3}. Independent SQL object-set consistency: 12/12 (same snapshot, not expert gold).

Production linguistic analysis, ExecutionValidator and radius execution are separate component cohorts, not the full proposed pipeline. B4 reviews supplied fixtures; it does not generate and repair its own plans. B0–B3, full P, controlled ablations and recovery are not executed.
