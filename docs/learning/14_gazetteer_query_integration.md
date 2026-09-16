# Dataset Gazetteer Query Integration

Date: 2026-09-15

## Implemented Contract

- Common resolver: `services/spatial_analysis_agent/place_resolver.py`.
- Read-only sources: `S101_DB_URL` / `serving.island_gazetteer_current` and
  `POSTGIS_URL` / `public.maritime_gazetteer_khoa`.
- The current source snapshot contains 1,140 and 1,232 named EPSG:4326 points.
  Same normalized name and coordinates rounded to six decimals form one candidate;
  all source records remain in provenance. Current grouped count: 1,985.
- The older merged `public.maritime_gazetteer` is deliberately not a resolution
  source: its OCEAN rows include mojibake names without replacement characters.
- Korean and English aliases use the same candidates. Distinct positions never
  collapse merely because their names match. No LIMIT 1 geocoding or implicit OSM
  fallback remains in the forward geocoding tool.
- Approved/verified registry bindings may resolve automatically. Curated registry
  points require confirmation. Unique unqualified source names resolve as
  `RESOLVED_GAZETTEER`, never as an approved registry entry.
- Entrance, boundary, offshore and between modifiers outside a matched place name
  require confirmation. A shorter extracted location cannot erase query qualifiers.
  Unknown names and conflicting locations produce clarification, not invented points.
- Candidate selections carry `place_id` and content `place_version`. The server
  reloads source records and rejects stale versions or conflicting geometry. Client
  provenance is not authority. Manual points require valid 2D EPSG:4326 coordinates.
- Source/schema/geometry-quality failures cannot turn incomplete evidence into an
  automatic unique match. An explicitly selected available source can still be
  confirmed when an unrelated source is unavailable.

## Service And UI

- `POST /api/v1/places/resolve`: `{query, spatial_context}` returns a typed resolved,
  clarification or blocked payload with source identity and candidates.
- The query stream supports direct place lookup, named hazard radius queries and
  location confirmation before nearest-feature data access. The general geocoding
  tool and planning/dispatch paths use the same resolver.
- Same-task confirmation and pagination preserve filters and source identity;
  stale geometry, source metadata and prior execution gates are cleared on changes.
- Place maps use the exact source point. There is no random coordinate movement,
  fabricated Berth classification or invented accuracy score in this path.
- Place/radius summaries are readable, while record IDs, versions and provenance
  remain expandable. Failed/blocked lookups do not display completed or empty success.
- A 30-second read cache bounds source loading; explicit selections force a refresh.
  A measured cold lookup fell from 33.26 seconds to 1.57 seconds after limiting
  regex compilation to aliases actually present in the query. These are observations,
  not a guaranteed latency bound.

## Verification

After the final backend restart, the expanded gazetteer SQL/API/stream oracle
passed 16/16 cases and the Busan radius oracle passed 11/11. The source-derived
gazetteer reference was Yusapo, with three duplicate source records at one point.
Its 3,000 m SQL and API results both contained IDs 563364, 563213 and 563211.
No expected count is hardcoded. The reports are:

`outputs/reports/execution_contract/20260915-gazetteer-query/actual_api_database.json`

`outputs/reports/execution_contract/20260915-gazetteer-query/busan_radius_actual.json`

The verifier is `scripts/verify_gazetteer_query_service.py`; it checks independent
source SQL, aliases, duplicates, ambiguity, stale IDs, geometry conflicts, modifiers,
map/table/summary/evidence identity and source stability across requests.

Direct place stream results, same-task candidate selection, rejection of stale
selection after task completion, and filtered source-identified pagination passed.
The one-object pages returned 563364 then 563213 while preserving total 3 and
advancing execution revision from 1 to 2.

Final focused Python regression: 251 passed (44 dependency warnings). Node summary
and DOM/Leaflet fixture suite: 11 passed. Python/JS syntax and git diff checks passed.
GET /health, /, /radius-results.js and /query-summary.js returned 200. Core source
hashes remained unchanged across final verification; no dataset mutation occurred.
The running service is http://localhost:8000/.

Earlier radius policy-conflict findings in document 13 are historical; they must
not be used as the acceptance result of this common-resolver implementation.

## Limits

- Neither clean source contains a place named Busan Port Entrance. A Busan Port
  source point is not evidence of its entrance. Curated test references still need
  explicit confirmation; authoritative entrance data has not been invented or added.
- Gazetteer availability does not imply that every island is named in the sources,
  or that an island polygon, port boundary or every spatial analysis is executable.
- Browser connection discovery returned no available browser. DOM/Leaflet tests
  were run, but real desktop/mobile screenshots are not claimed.
- Host `test_orchestrator.py` could not collect because `pkg_resources` is absent;
  its earlier SQLite DLL problem was diagnosed separately. Focused graph, API,
  execution and UI tests plus the running-container SQL/API oracle are the evidence.
