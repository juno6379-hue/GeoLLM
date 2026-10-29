# Results readiness — actual pilot 2026-10-29

| Area | Status | Blocking requirement |
|---|---|---|
| Benchmark | PILOT_ONLY | 18 DRAFT Q1–Q6 queries + 7 fault fixtures + 6 spatial probes; 114 component-run rows |
| Gold annotation | NOT_READY | Zero independent human GOLD labels |
| Spatial execution | PILOT_ONLY | 25,300 frozen source rows; 18 calls, 12 completed (3 valid empty), 6 not executed; independent SQL sets agree 12/12 |
| Spatial correctness | NOT_READY | Same-source consistency is not independently reviewed spatial gold |
| Linguistic component | PILOT_ONLY | 54 isolated returns, Kiwi available, repeat disagreement 0; not full grounding |
| Validator experiment | PILOT_ONLY | 21 actual calls with synthetic metadata; DRAFT expectation agreement 21 |
| B4 LLM reviewer | PILOT_ONLY | 21 actual requests: parsed 19, timeout 2, observed false block 1; supplied fixtures, not self-generated-plan B4 |
| B0–B3 / full P | NOT_READY | End-to-end budget-matched adapters and actual runs not implemented |
| Recovery | NOT_READY | Measured bounded repair + final correctness + drift |
| Ablation | NOT_READY | Isolated adapters for each removal not implemented |
| Repeated trials | PILOT_ONLY | Actual K=3; deterministic repeats not independent samples; final K=5 pending |
| Statistical tests | NOT_READY | Independent gold cases, pairing and cluster-aware design |
| Manifest | PILOT_ONLY | Source/input/snapshot/model provenance recorded; missing metadata explicit |
| Tables | PILOT_ONLY | R1–R7 generated; publication metrics null without expert GOLD |
| Figures | PILOT_ONLY | F1–F7 show NOT_READY; D1 shows actual operational counts/latency |
| System feedback | PILOT_ONLY | Separate fix-agent triage; before/after cohorts kept distinct |

Overall **PILOT_ONLY**, final paper **NOT_READY**. Expert GOLD = 0. See `protocol/pilot_findings_20261029.md`, `latest/reports/results_summary.md` and `issues/triage_20261029.md`. Source availability, API success and synthetic fault labels are not substitutes for expert correctness. Production execution authority and Qwen shadow policy remain unchanged.
