"""Fail-closed prerequisite gate for the eight-method GOLD v2 comparison."""
METHODS = ('B0', 'B1', 'B2', 'B3', 'B4', 'P0', 'H', 'P1')


def comparison_gate(cases, methods, gold_manifest_sha256):
    errors = []
    expected = {f'PILOT_Q{group}_{case:02}' for group in range(1, 7) for case in range(1, 4)}
    if len(cases) != 18 or {r.get('case_id') for r in cases} != expected:
        errors.append('BENCHMARK_CASE_SET_MISMATCH')
    if not isinstance(gold_manifest_sha256, str) or len(gold_manifest_sha256) != 64:
        errors.append('GOLD_MANIFEST_HASH_REQUIRED')
    for row in cases:
        if row.get('oracle_status') != 'VERIFIED' or row.get('scope_frozen') is not True:
            errors.append(f"ORACLE_NOT_READY:{row.get('case_id')}")
    if set(methods) != set(METHODS):
        errors.append('EIGHT_DISTINCT_METHODS_REQUIRED')
    fingerprints = set()
    for name, method in methods.items():
        if method.get('adapter_validated') is not True:
            errors.append('ADAPTER_NOT_VALIDATED:'+name)
        if method.get('gold_manifest_sha256') != gold_manifest_sha256:
            errors.append('GOLD_VERSION_MISMATCH:'+name)
        if not method.get('input_condition_sha256'):
            errors.append('INPUT_CONDITION_MISSING:'+name)
        else:
            fingerprints.add(method['input_condition_sha256'])
        if name == 'B0' and method.get('domain_tools_enabled') is not False:
            errors.append('B0_IS_NOT_DIRECT_LLM')
        if method.get('execution_observation_validated') is not True:
            errors.append('EXECUTION_OBSERVATION_UNVERIFIED:'+name)
    if len(fingerprints) != 1:
        errors.append('INPUT_CONDITIONS_DIFFER')
    return {'ready':not errors,'errors':errors,'models_started':False}


def replay_decision(previous, current, *, required_observations_present):
    # Generation identity intentionally excludes evaluation/GOLD hashes.
    keys = ('system_source_sha256','adapter_sha256','model_profile_sha256',
            'source_snapshot_sha256','benchmark_inputs_sha256','method_definitions_sha256')
    changed = [k for k in keys if not previous.get(k) or previous.get(k) != current.get(k)]
    if changed:
        return {'action':'FULL_BENCHMARK_RERUN','changed_or_unknown':changed}
    if not required_observations_present:
        return {'action':'NEW_OBSERVATIONS_REQUIRED','old_missing_values':'UNMEASURED'}
    return {'action':'RESCORE_IMMUTABLE_RAW','new_output_directory_required':True}
