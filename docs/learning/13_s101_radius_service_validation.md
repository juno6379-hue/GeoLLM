# Flexible S-101 Radius Service Verification

Date: 2026-09-15

## Status

PARTIAL: the explicit-reference radius workflow is implemented and verified.
Final acceptance is blocked by concurrent edits to the location approval policy.
Do not interpret the passing API report as verification of later source changes.

## Implemented

- Isolated radius execution module behind the graph adapter and common execution gate.
- Navigation-safety target allowlist from the configured execution profile. Ontology
  candidates are not automatically added. Explicit target and exclusion filters survive.
- Confirmed WKT point / EPSG:4326 input; positive finite radius, bounded pagination,
  valid layer/template/schema/tool binding, read-only SQL and bounded query timeouts.
- Conservative bounding envelope plus exact geography ST_DWithin. One SQL statement
  produces total count, type totals, ordered page and search area from one snapshot.
- One returned row set drives map, table, summary and typed evidence. Total and displayed
  counts are separate. Claims reference evidence IDs; source dataset/version are retained.
- Candidate confirmation, safe filter resubmission, fresh-task pagination, and same-task
  confirmed resume with revision increment. Missing/failed results are not reported as zero.
- UI candidate selection and explicit coordinate/radius input, with no invented defaults.

## Actual Database/API Evidence

Reference supplied explicitly by the verifier: POINT(129.075 35.075), EPSG:4326, 3000 m.
This is a test request reference, not a claim that its registered place label has been
independently certified as the official Busan entrance coordinate.

Last completed oracle run: 11/11 checks passed against the loaded backend snapshot.
The independent SQL omits the service's bounding-box prefilter and SQL template.
Expected counts and ordered IDs come from the database, never a hardcoded assertion.

- All configured targets: 119 total, first page 30 displayed.
- Wreck only: 2 total.
- Excluding Wreck: 117 total.
- Type totals: Obstruction 103, UnderwaterAwashRock 14, Wreck 2.
- First/next pages, natural-language and explicit filters, unknown-place clarification,
  denied user, same-task confirmation, and cross-request source stability were checked.
- Map/table/summary/evidence IDs, counts, source versions and distances matched SQL.

Report: `outputs/reports/execution_contract/20260915-radius-service/actual_api_database.json`.
No DB feature, embedding or dataset changes were made by the reviewing session.

## Current Regression And Coordination Block

The other shared-workspace session repeatedly changed resolve_reference to accept
`curated` as `APPROVED_REGISTRY`. The curated place registry has local provenance,
not recorded approval. Root restored candidate confirmation, but the promotion was
written again. An associated test was also changed to expect automatic approval;
the test was aligned with the user's explicit confirmation requirement afterward.
Unrelated result_surface/source metadata additions from that session were preserved.

Latest full regression run: 183 passed, 6 failed. All six failures concern the
unconfirmed-location policy, including compiled graph and filter-resubmission tests.
Artifact: `outputs/reports/execution_contract/20260915-radius-service/unit-tests.xml`.
Earlier focused validation passed before the concurrent policy changes.

The passing API report represents a previously loaded policy snapshot; current source
must be stabilized and reloaded before final acceptance. Do not weaken those tests
or relabel curated coordinates approved merely to make the benchmark pass.

Coordination channel: `docs/learning/12_codex_collaboration_status.md`.
Direct receipt by the external session remains unconfirmed; the user was asked to
pause its overlapping edits or explicitly settle the test-reference approval policy.

## Remaining Verification

1. Agree ownership and whether the registered coordinates are actually approved test
   references. Without explicit approval, keep curated locations as confirmation candidates.
2. Stabilize the radius executor/tests, reload backend and rerun the regression/oracle.
3. Browser screenshot/visual QA remains unavailable. Node DOM/Leaflet checks passed;
   container-local GET / and /radius-results.js returned HTTP 200. Host-side HTTP checks
   intermittently failed even after escalation; no browser rendering claim is made.

The two earlier unrelated task-plan failures recorded in the collaboration document
were not resolved by this radius-specific work. Whole-repository test success is not claimed.
