# Validation Policy

Validation covers UTF-8 text, Pydantic/JSON Schema, required-slot readiness, dynamic fixture safety, agent/tool/data/layer/template/concept references, exact duplicates, near duplicates, seed-family leakage, and protected holdouts.

Failures are not silently repaired or approved. They remain candidates or move to review-required quarantine with machine-readable notes. Tool dependency and S-101 membership checks should become stricter as those registries expose stable machine-readable relationships.
