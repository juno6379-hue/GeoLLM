# Current system audit — 2026-10-29

Static source audit at commit `6aa70271a37a7382b2f0217f746a384e41759879`, branch `main`; dirty tree preserved. Exact file sizes and SHA-256 hashes are in `source_audit.json`. This is not a runtime success assertion.

| Component | Status | Evidence and limitation |
|---|---|---|
| Existing typed QEC | IMPLEMENTED | `shared/schemas/agent.py`, contract geollm.execution.v1; slots, bindings, provenance, revision, patch invalidation exist. Reuse this class. |
| Semantic grounding / FC | PARTIALLY_IMPLEMENTED | Parsed S-101 FC 2.0.0, KG contract 0.1, registry and graph available; correctness has no expert gold. S-100 edition not independently pinned. |
| Deterministic execution gate | PARTIALLY_IMPLEMENTED | `execution_validator.py` contains operation-specific binding, geometry, distance and policy checks; universal S-100 attribute/code/CRS validation must be measured, not assumed. |
| QEC full fidelity | PARTIALLY_IMPLEMENTED | QEC carries structured fields; runner must preserve them and identify absent receipt/input_hash. Presence does not establish meaningful field population. |
| KG integrity | IMPLEMENTED_BUT_NOT_MEASURABLE | `kg_ontology_validator.py` checks structure/provenance; not independent semantic accuracy. |
| Actual spatial execution | IMPLEMENTED_BUT_NOT_MEASURABLE | `s101_radius_execution.py` exists; this static audit does not prove live DB coverage. Parent run must record isolated snapshot and actual results. |
| Post-execution independent correctness | MISSING | No reviewed object-set/geometry gold supplied; executable metric functions cannot establish correctness without oracle. |
| Recovery / replanning | PARTIALLY_IMPLEMENTED | Retry/resume mechanisms do not establish a general bounded semantic repair loop. No measured recovery benefit yet. |
| Evidence | PARTIALLY_IMPLEMENTED | `evidence_builder.py` and EvidenceBundle exist; reference validity and reverse object→tool→QEC→concept→source trace need independent checks. |
| Timing/token instrumentation | PARTIALLY_IMPLEMENTED | Preserve observed API usage/timing; unobserved stage values remain null. |
| Publication benchmark | MISSING | Existing operational regression tests are not publication gold. New 18-case DRAFT pilot is infrastructure only. |

Runtime/model/database/package measurements remain pending in per-run manifest; no values inferred from old roadmap. Startup daemon was unavailable in initial parent probe; later parent measurements supersede this observation. Hashes of top-level KG files do not establish their semantic quality or completeness. Existing user edits and runtime feedback were not changed by this protocol task.

P0 operational contract limitations remain in the roadmap. P1 Ollama stays shadow candidate evaluation; calibration and independent gold are prerequisites for execution authority or QLoRA. Research priority does not mark these operational tasks complete.
