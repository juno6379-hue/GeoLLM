# Accident Spatial History Performance Review

Date: 2026-09-17

## Query

`독도 부근 사고 이력`

## Problem Observed

Before the fix, this query stayed in `RECEIVED` for more than 60 seconds and one status poll timed out. The query was a multi-label request:

- place anchor: `독도`
- spatial relation: `부근`
- accident domain: `사고 이력`

The existing accident fast path handled row-level text filters such as jurisdiction, cause, and accident type. It did not handle place-anchor plus nearby accident history, so the query could fall through toward the broader spatial/context path.

## Fix

Added a dedicated fast path:

- analysis_type: `accident_spatial_history_lookup`
- fast_path: `accident_spatial_history_lookup`
- tool capability: `tool.accident_spatial_history_lookup`
- authority table: `serving.accident_events`
- geometry authority: resolved place registry/gazetteer anchor plus `serving.accident_events.geom`
- query method: `ST_DWithin` with a 2500 ms statement timeout
- default radius: `10,000m` when the query says nearby/around but gives no explicit distance

The path now resolves the place anchor, applies an explicit or default radius, and directly queries accident events by distance.

## Verification

API smoke result after the change:

- elapsed: about `2.05s`
- status: `COMPLETED`
- fast_path: `accident_spatial_history_lookup`
- location: `독도`
- radius_m: `10000`
- total_count: `6`
- returned_count: `6`
- top capability: `tool.accident_spatial_history_lookup`

Summary produced:

`독도 기준 반경 10000m 이내 해상조난사고 이력 6건`

## Bottleneck Notes

Two different bottlenecks were observed:

1. Query execution bottleneck: caused by falling through to the broad orchestration path instead of a deterministic spatial accident fast path.
2. Server startup bottleneck: after backend restart, `ContextResolver vector store built successfully` appeared twice and startup took roughly 50 seconds before `/health` returned OK.

The query execution bottleneck is fixed by this fast path. The startup bottleneck remains a separate architectural issue: heavy resolver/vector-store initialization should be made lazy or cached outside the request-serving import path.

## Extension Policy

For future compound domain queries:

1. Add a registry lexical signal for the domain action, such as `accident_history`.
2. Register a capability with explicit inputs and outputs.
3. Keep pgvector as candidate retrieval only.
4. Verify authority through registry/KG references.
5. Implement a deterministic tool path when the required slots can be resolved without LLM ambiguity.
6. Add a broker test and an API smoke result.
