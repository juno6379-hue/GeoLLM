# 2026-10-29 measured pilot and next steps

The final input cohort is 31 unique DRAFT cases and 114 rows: linguistic 18×3, fault 7×3×2, spatial 6×3. These are three different component experiments; pooling them as end-to-end accuracy is invalid.

- Actual Qwen `qwen2.5:1.5b`: first two reviewer calls timed out (40-second configured request timeout); 19 later responses parsed. One valid control was incorrectly declared invalid. The other 18 parsed answers agreed with authored DRAFT labels. No publication accuracy claim.
- Actual ExecutionValidator: 21/21 DRAFT diagnostic agreements, using synthetic schema metadata only. It did not execute GIS.
- Offline linguistic component: 54 returns with Kiwi available in the isolated container, no deterministic repeat differences. Source lexical-subset mappings were zero; this narrow function does not represent the full semantic pipeline. Host venv lacks Kiwi; those observations remain separately preserved.
- Real PostGIS component: a read-only REPEATABLE READ export of valid S-101 rows intersecting bbox [128.9,34.9,129.3,35.3] yielded 25,300 source rows. The CSV, schema and transaction/digest are preserved locally. A separate `marine-scie-pilot-db` loads this subset; the production radius executor queries it read-only.
- Anchor is a point on an actual source Wreck, not a claim about the centre or entrance of Busan Harbour. 500m/0.5km each return the same 3 objects, 2km hazard query returns 5. A deterministic +0.0001° x/y offset with 0.1m radius returns zero successfully. 0m and 50,001m are not executed. Twelve successful runs agree with independent distance SQL; their authorization receipts validate. Expert spatial GOLD remains unavailable.
- Initial Windows psycopg2 connection attempts raised UnicodeDecodeError before export. Container-network execution succeeded; no source DB writes were performed. The initial spatial measurement adapter incorrectly treated COMPLETED as unsuccessful; that research-only measurement bug was fixed, raw preliminary rows retained, and the final experiment rerun. Preliminary rows are excluded from the final denominator.

## Reproduce

From repository root, keep the production source revision and dataset digest fixed. Do not overwrite prior raw runs.

```powershell
.\.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests -q
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.fault_injection.pilot --output-dir research/marine_geollm_scie/runs/NEW_RUN/validator --repeats 3
```

For offline semantic analysis use the recorded container image with `--network none`, repository mounted read-only, output separately writable, `GEOLLM_RESEARCH_GIT_SHA` set to the tested revision, and `python -m research.marine_geollm_scie.runners.semantic_pilot --output /out --repeats 3 --environment isolated_container_network_none`. No `.env` is passed. Host venv results are not equivalent when Kiwi is unavailable. The final runner automatically writes normalized rows and refuses existing artifacts; these output safeguards were added after the first pilot, whose raw component predictions remain unchanged.

`runners.launch_spatial --output-dir .../spatial` creates a new research-only container and fails if the fixed research container name already exists. To repeat against the preserved snapshot, use `--reuse-snapshot`, preserve the prior `spatial_rows.jsonl` under a distinct archival filename first, and keep the database unchanged. The runner checks the CSV digest and only permits target database `scie_pilot`. Source credentials are consumed from existing Docker configuration without printing or saving them. Existing production containers are not rebuilt or removed.

The finalizer reads only `validator/validator_rows.jsonl`, `semantic_isolated/semantic_rows.jsonl`, and `spatial/spatial_rows.jsonl`; completion summaries are required. Run `python -m research.marine_geollm_scie.runners.finalize --run-dir ...` after all three finish. It writes an explicit diagnostic-only `latest` bundle. Raw responses and 98MB source export remain under ignored `runs/`; reviewed summary artifacts and source are committed separately.

## Next execution order

1. Separate fix-agent triage: reproduce suspected production errors; preserve this baseline, classify environment/model/measurement faults separately; regression-test confirmed fixes and rerun under a new run ID.
2. Build B0–B3 and complete B4 self-generated-plan/full-P adapters with equal retrieval/tool/token budgets and full QEC/evidence receipts. Current reviewer-only B4 is not final B4.
3. Independent expert semantic/QEC/spatial/evidence annotation and adjudication, family-level split and locked holdout; expand coverage before comparative accuracy claims.
4. Isolated ablation and L1/L2/L3 fault coverage; actual bounded recovery with measured semantic drift.
5. Frozen K=5 main experiments, paired/cluster-aware statistics, source-audited R1–R7/F1–F7 publication results.

Operational P0 and Qwen calibration/QLoRA gates remain separate from these research tasks.
