# Continuous Improvement Architecture

## Runtime Flow

1. Run benchmark cases.
2. Collect structured trace and final results.
3. Compare expected vs actual.
4. Classify failures.
5. Analyze root cause.
6. Generate improvement proposals.
7. Run before/after comparison.
8. Require human approval before operational promotion.

## Artifacts

- `tests/benchmark/benchmark_cases_v1.jsonl`
- `outputs/learning/benchmark_results.jsonl`
- `outputs/learning/baseline_metrics.json`
- `outputs/learning/failure_cases.jsonl`
- `outputs/learning/improvement_proposals.jsonl`

## Modes

The runner supports:

- API mode: validates the public task streaming contract.
- Graph mode: validates the internal orchestration path with lower overhead.

