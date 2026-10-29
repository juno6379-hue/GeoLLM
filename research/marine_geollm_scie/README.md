# Marine GeoLLM SCIE research

Research-only pilot infrastructure based on the root SCIE Results framework. Production is unchanged by protocol/benchmark work. See `protocol/experimental_protocol.md`, `protocol/current_system_audit.md` and `RESULTS_READINESS.md` before interpreting results.

Actual pilot: 31 unique DRAFT cases, 114 component-run records. See `latest/reports/results_summary.md` and `protocol/pilot_findings_20261029.md`. GOLD is zero; full baseline comparison, recovery and ablations are still pending. Raw responses and source export stay under ignored `runs/`; `latest` retains audited summary artifacts and provenance.

Experiment findings are handed to a separate repair agent through `issues/findings.json` and `issues/triage_20261029.md`. A research-only model/reviewer failure is not automatically a production defect. Confirmed fixes require reproduction, regression tests and a new before/after run; baseline raw results are never overwritten.

Benchmark: `benchmark/query_cases_v1.jsonl` has 18 DRAFT queries (Q1–Q6, three each); gold files are empty. Schema also supports Q7 fault specifications; Q8 has no verified cross-product dataset and is unsupported. No invented spatial coordinates or expert labels. Default pilot stochastic repeat count is three; final is five.

`protocol/source_audit.json` records source hashes. Actual runtime manifests/results are produced by research runners. An execution/validator diagnostic is not publication accuracy. Runner commands and current measured outcomes are recorded in per-run reports; inspect supported CLI options before running.

## Observed component pilot

Run from repository root: `.venv/Scripts/python.exe research/marine_geollm_scie/runners/semantic_pilot.py`. This executes the unchanged production linguistic-evidence and source-backed lexical-mapping components without Ollama or DB. Output defaults to `runs/20261029_pilot/semantic/`; choose a fresh `--output` directory for later runs.

2026-10-29 host run: 18 queries × 3 deterministic repeats = 54 returned component records, no repeat disagreement; Kiwi unavailable in all 54 and no mappings from this narrow source-backed lexical subset. This does not test full semantic routing, Qwen, QEC, GIS, answers or accuracy. See raw records and manifest; GOLD remains zero.

Backend container rerun: `runs/20261029_pilot/semantic_container/` contains 54/54 COMPONENT_RETURNED with Kiwi AVAILABLE, deterministic repeat disagreement 0. Host and container are distinct environment runs, not 108 independent observations. No source mappings in the narrow advisory lexical subset; no accuracy claim. Container runner/cases were copied only under `/tmp/scie_component`; production source was not changed.

Authoritative component pilot for report aggregation: `runs/20261029_pilot/semantic_isolated/semantic_rows.jsonl` and `summary.json`. This separate docker-backend container used `--network none`, read-only repository mount, only explicit research environment variables and no env-file. 54 component records, Kiwi AVAILABLE, no deterministic repeat disagreements. Host and live-container probes remain separate and are excluded from this denominator.
