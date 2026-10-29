# Reproducibility gate

Each run stores manifest, raw request/response and full QEC, errors, source snapshot identity, metrics, generated tables/figures and summary. Record UTC run ID/time, actual Git HEAD/branch/dirty tree hashes, backend/model name/full digest, temperature/seed, prompt/template hashes, ontology/FC/KG hashes, S-100 and S-101 versions, capability and query-template hashes, benchmark and all gold hashes, DB snapshot/projection/SRID, Python/dependency and container runtime versions. Secrets must never be serialized.

Static `source_audit.json` is an input inventory, not a substitute for run manifest. Null runtime fields make publication reproducibility incomplete. Hash all source rows consumed by isolated GIS fixtures and identify read-only extraction query, count, CRS, geometry hash and snapshot time. A local extracted fixture is actual source data, but cannot establish nationwide completeness.

Keep results under unique run IDs. Failed/incomplete runs remain inspectable; do not overwrite latest with partial results. R1–R7 and F1–F7 derive only from saved raw observations; unsupported or unreviewed measures show N/A/null. A complete pilot report can still be PILOT_ONLY. Human gold, independent spatial oracle, full comparison methods, repeats and pinned provenance are required for publication READY.
