# 098 Accident Event Fast Path Limitations

Date: 2026-09-17

## Issue

Query:

`창원 정비불량 사건을 찾아줘`

The query was previously routed as a place lookup and returned a blocked gazetteer response. It could also fall through to broad RAG/document retrieval, which is slow and does not guarantee row-level accident evidence.

## Root Cause

- The router only recognized `feature_instance_id=` accident relation requests.
- A plain accident event request such as `창원 + 정비불량 + 사건` was not treated as a structured accident row lookup.
- Korean particles attached to search tokens, for example `사건을`, could become mandatory database filters and produce zero matches.
- Embedding/RAG evidence is not the correct authority for accident event count, map coordinates, or row attributes.

## Policy

For accident event discovery:

1. Use deterministic routing when the query contains accident/event terms and cause/type terms.
2. Use `serving.accident_events` as the authoritative row and geometry source.
3. Return map features, table rows, summary, and evidence from the same row set.
4. Do not infer causality between accident cause and S-101 chart objects from this lookup.
5. Use embeddings only for candidate discovery or supplemental evidence, not as the source of truth for counts or coordinates.

## Fix

- Added `_looks_like_accident_event_lookup_query()`.
- Added `fast_accident_event_lookup_node()`.
- Added token normalization for Korean particles in `_accident_event_terms()`.
- Added a new graph route: `fast_accident_event_lookup`.
- Returned:
  - `structured_result.total_count`
  - `structured_result.returned_count`
  - `structured_result.events`
  - `features` GeoJSON
  - `map_layers`
  - separated accident evidence bundle entries

## Verification

API query:

`창원 정비불량 사건을 찾아줘`

Observed result:

- route: `accident_event_structured_lookup`
- source: `serving.accident_events`
- total_count: `59`
- returned_count: `59`
- map feature_count: `59`

The result now completes through the structured accident event fast path instead of the slower general RAG path or the incorrect place lookup path.
