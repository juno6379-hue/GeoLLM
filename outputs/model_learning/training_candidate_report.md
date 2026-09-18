# Fine-Tuning Candidate Report

- generated_at: `2026-09-18T01:43:42.524038+00:00`
- candidate_count: `7`
- status: `REVIEW_ELIGIBLE`
- rejected_authority_sensitive_candidates: `1`

## Policy

- Do not train coordinates, counts, legal citations, S-101 definitions, or dataset provenance into model weights.
- Use candidates only for linguistic intent, slot style, and clarification behavior after human review.
- Exclude benchmark/test answer leakage before any fine-tuning job.

## Candidates By Label

- `intent.routing`: `4`
- `normalization.encoding`: `1`
- `quality.low_estimated_accuracy`: `1`
- `slot.spatial_relation_or_anchor`: `1`

## Rejected Authority-Sensitive Candidates

- `quality.low_estimated_accuracy`: `1`
