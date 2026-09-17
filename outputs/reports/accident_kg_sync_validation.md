# Accident KG Sync Validation

- generated_at: 2026-09-17T06:56:54.227740Z
- source_ref: `serving.accident_events`
- db_event_rows: 4636
- event_nodes: 4636
- type_nodes: 21
- cause_nodes: 12
- authority_nodes: 21
- sea_area_nodes: 6
- event_dimension_edges: 18544
- concept_edges: 53
- verified_edges_promoted: 4
- sync_status: PASS

Policy: `serving.accident_events` is the authority for accident event count, attributes, and geometry. KG edges describe evidence-backed classification and dimensions, not causality with S-101 chart objects.
