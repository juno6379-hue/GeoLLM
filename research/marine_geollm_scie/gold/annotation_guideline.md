# Expert annotation guideline

All 18 generated queries are DRAFT; the four gold JSONL files deliberately contain zero rows. Do not copy expected_behavior into gold or accept LLM self-review as ground truth.

Two domain reviewers independently annotate without seeing method answers. Record reviewer IDs, timestamp, source snapshot, product/FC concept and attribute ownership, accepted capability combinations, required slots/units/CRS, clarification conditions and evidence references. Resolve disagreements with a third reviewer or documented consensus. Preserve independent labels and adjudication history. Compute agreement only from actual independent labels.

Gold semantics: case_id, annotation_status=GOLD, intent, domain_concept, surface_term, canonical_concept_id, product, feature, fc_reference, attributes/codelists, relation, metric/unit, geometry_type/crs, required_dataset/capability, allowed_tools, annotator_ids, adjudication_status.
Gold QEC: same provenance plus expected production-QEC field values, permitted alternatives and expected_execution_behavior. Do not invent a second QEC class.
Gold spatial: same provenance plus frozen source query, snapshot hash, returned object IDs, independently executed reference spatial operation, geometry/tolerance/CRS. Independently inspect SQL semantics; using the evaluated tool's own outputs is circular. Valid empty set must be explicitly reviewed.
Gold evidence: same provenance plus required source references, valid source anchors and reverse provenance chain assertions. Text plausibility is insufficient.

Unsupported questions can have reviewed blocking behavior but are not successful GIS result cases. Version all edits and prevent equivalence-group leakage between splits. Publish no confidential annotation material or connection credentials.
