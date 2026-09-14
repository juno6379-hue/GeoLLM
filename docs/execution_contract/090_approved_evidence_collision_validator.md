# Phase 8.9 Approved Evidence Collision Validator

## Purpose

Approved evidence candidates are still evidence, not execution authority. Phase 8.9 adds a deterministic pre-promotion validator that checks approved candidates against the current RAG chunk store, KG edge/object state, and registry layer/schema metadata before they are merged into `data/evidence_registry.yaml`.

## Added Components

- `scripts/validate_approved_evidence_candidates.py`
- `POST /api/v1/evidence-candidates/validate`
- `POST /api/v1/evidence-candidates/apply` now validates by default before merging approved evidence.

## Checks

The validator reports item-level `PASS`, `NEEDS_REVIEW`, or `FAILED`.

- Approval contract:
  - approved items require reviewer, reviewed_at, and reason
  - review_required candidates require `review_required_accepted: true`
- RAG evidence:
  - `chunk_id` must exist in `outputs/rag/*.jsonl`
- KG evidence:
  - proposed edge promotions are compared with `outputs/graph/kg_edges_v2.jsonl`
  - already-existing edges are flagged
  - selected predicates with existing subject/predicate mappings to other objects are flagged for review
- Registry state:
  - registered layer status is checked
  - missing physical, expected, or metadata table bindings are flagged
  - missing regulatory layer references fail validation
- S-101 feature references:
  - `feature_code` must exist in `data/s101_feature_catalogue_v2_parsed.json`

## Commands

```powershell
python -m py_compile services\orchestrator\router.py scripts\apply_approved_evidence_candidates.py scripts\validate_approved_evidence_candidates.py scripts\build_marine_kg.py
python scripts\validate_approved_evidence_candidates.py --write-report
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/evidence-candidates/validate" -Method Post | ConvertTo-Json -Depth 8
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/evidence-candidates/apply" -Method Post -ContentType "application/json" -Body '{"write":false,"overwrite":true,"validate":true}' | ConvertTo-Json -Depth 8
```

## Current Baseline

- Approved evidence candidates: `0`
- Validation status: `PASS`
- KG index used by validator:
  - nodes: `8846`
  - edges: `9642`
- Report path: `outputs/review/approved_evidence_validation_report.json`

## Policy

If validation returns `FAILED` or `NEEDS_REVIEW`, the default apply API rejects promotion and returns the validation report in the HTTP 400 detail. Operators can still call the lower-level script manually for investigation, but automated registry promotion should keep `validate: true`.
