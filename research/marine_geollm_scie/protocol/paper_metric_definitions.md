# Paper metric definitions

Implementation references: `../evaluation/metrics.py`, `../evaluation/statistics.py`, `../reporting/build_tables.py`. Raw measurement and correctness are separate.

Gold eligibility requires review_status (fallback annotation_status/label_status) = GOLD, nonempty annotator_ids, and adjudication_status = APPROVED. DRAFT cases may report observed latency, schema parsing, execution status and diagnostic decisions; they do not produce paper correctness rates. Missing annotations are not wrong answers and not correct answers.

EVQSR on the EXECUTE cohort uses boolean semantic_correct × plan_valid × execution_success × spatial_correct × evidence_correct for every eligible case. If any required component is missing, cohort EVQSR is null. Report each component coverage separately. Do not reinterpret API COMPLETED as execution success or validator approval as spatial correctness. Definition and clarification cohorts are distinct from actual GIS execution.

Semantic measures: feature, attribute and relation accuracy, micro/macro F1 and strict semantic match require independent labeled targets and accepted alternatives. QEC field accuracy/exact match requires reviewed production-QEC fields. Schema validity is structural only.

Spatial measures: object-set precision/recall/F1 and exact match use independent frozen-ID gold; distance errors use explicit units/tolerance; geometry validity, predicates and CRS use deterministic actual geometry evaluation. A reviewed empty set may be a valid result. LLM judging is not spatial ground truth.

Validator positive class is invalid plan. TP=invalid blocked, FN=invalid accepted, FP=valid blocked, TN=valid accepted. False Ready Rate = FN/(TP+FN); False Block Rate = FP/(FP+TN). Undefined denominators yield null. Preserve unevaluated cases and fixture origin. Injected DRAFT diagnostic decisions are not expert-gold publication performance.

Recovery needs initial failure, real repair attempts, independently verified final correctness, extra calls/tokens/latency and semantic drift. Evidence correctness requires valid references and reverse trace, not merely nonempty citations. Until these are observed, keep corresponding cells null.

Paired bootstrap implementation aggregates repeated observations per case. Exact McNemar accepts one binary value per independent case. Equivalence-group paraphrases require cluster aggregation before inference; case aggregation alone does not remove their dependence. No inferential tests should run automatically on DRAFT pilot results. Report median/P95/IQR for observed latency; missing stage times and tokens remain null.
