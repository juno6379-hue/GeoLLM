"""Research report gate; never grants production execution authorization.

Caller supplies independently verified receipts. This is a contract checker,
not a substitute for hashing raw files, running adapters, or expert review.
"""
from research.marine_geollm_scie.runners.gold_v2_gate import METHODS, replay_decision


def report_gate(*, case_ids, repeats, observations, execution_identity,
                benchmark_sha256, raw_integrity_verified=False,
                independent_gold_review_complete=False):
    errors = []
    case_ids = list(case_ids)
    repeats = list(repeats)
    if not case_ids or len(case_ids) != len(set(case_ids)):
        errors.append('INVALID_CASE_SET')
    if not repeats or len(repeats) != len(set(repeats)):
        errors.append('INVALID_REPEAT_SET')
    expected = {(c, m, r) for c in case_ids for m in METHODS for r in repeats}
    seen = set()
    paired = {}
    if raw_integrity_verified is not True:
        errors.append('RAW_INTEGRITY_NOT_VERIFIED')
    if not benchmark_sha256:
        errors.append('BENCHMARK_HASH_REQUIRED')
    for row in observations:
        key = (row.get('case_id'), row.get('method'), row.get('repeat'))
        if key in seen:
            errors.append('DUPLICATE_OBSERVATION:'+str(key))
        seen.add(key)
        if row.get('benchmark_sha256') != benchmark_sha256:
            errors.append('BENCHMARK_MISMATCH:'+str(key))
        identity = replay_decision(row.get('execution_identity', {}), execution_identity,
                                   required_observations_present=True)
        if identity['action'] != 'RESCORE_IMMUTABLE_RAW':
            errors.append('FULL_RERUN_REQUIRED:'+str(key))
        # Failed model/tool observations are valid data, provided raw evidence exists.
        if not row.get('raw_artifact_sha256') or not row.get('raw_artifact_path'):
            errors.append('RAW_EVIDENCE_MISSING:'+str(key))
        if row.get('method') in ('B3', 'B4', 'P0', 'H'):
            paired.setdefault((key[0], key[2]), {})[key[1]] = row
        if row.get('method') == 'B0' and row.get('domain_tools_enabled') is not False:
            errors.append('B0_NOT_DIRECT_LLM:'+str(key))
    if seen != expected:
        errors.append('OBSERVATION_SET_INCOMPLETE_OR_EXTRA')
    for key, rows in paired.items():
        hashes = {r.get('initial_plan_sha256') for r in rows.values()}
        if set(rows) != {'B3', 'B4', 'P0', 'H'} or None in hashes or '' in hashes or len(hashes) != 1:
            errors.append('PAIRED_INITIAL_PLAN_MISMATCH:'+str(key))
        b4, hybrid = rows.get('B4', {}), rows.get('H', {})
        if not b4.get('review_artifact_sha256') or b4.get('review_artifact_sha256') != hybrid.get('review_artifact_sha256'):
            errors.append('SHARED_REVIEW_MISMATCH:'+str(key))
        for method in ('P0', 'H'):
            if rows.get(method, {}).get('lossless_compilation_verified') is not True:
                errors.append('LOSSLESS_COMPILATION_UNVERIFIED:'+str(key)+':'+method)
    return {
        'observation_comparison_complete': not errors,
        'independent_gold_review_complete': independent_gold_review_complete is True,
        'human_semantic_accuracy_claim_allowed': False,  # Requires a separate scored review artifact.
        'production_release_approved': False,
        'rq1_to_rq5_complete': False,  # Separate metric/fault/recovery receipts are still required.
        'errors': errors,
    }
