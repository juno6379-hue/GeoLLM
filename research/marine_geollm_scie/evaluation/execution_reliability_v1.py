"""Explicit E/S reliability accounting without equating transport and GIS success."""
from __future__ import annotations

from collections import Counter
import json


CONTRACT_VERSION = 'execution_spatial_reliability.v1.proposed'


def _rate(values):
    measured = sum(type(v) is bool for v in values)
    return dict(value=sum(v is True for v in values)/len(values) if values and measured == len(values) else None,
                denominator=len(values), measured=measured, missing=len(values)-measured)


def summarize_execution(rows):
    """Summarize caller-observed booleans, never derive them from API status.

    Input: case_id, repeat_id, equivalence_group, eligible (bool),
    execution_success (bool/None), spatial_correct (bool/None).
    Eligibility and source/Oracle verification must be established upstream.
    Missing eligibility is rejected; abstention/definition cohorts are excluded.
    """
    included, excluded, seen = [], [], set()
    groups = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Observation must be an object')
        cid, group, repeat = row.get('case_id'), row.get('equivalence_group'), row.get('repeat_id')
        if not isinstance(cid, str) or not cid.strip() or not isinstance(group, str) or not group.strip():
            raise ValueError('Explicit case_id and equivalence_group required')
        if isinstance(repeat, bool) or not isinstance(repeat, (int, str)) or repeat == '':
            raise ValueError('Explicit repeat_id required')
        key = cid, json.dumps(repeat)
        if key in seen:
            raise ValueError('Duplicate case/repeat')
        seen.add(key)
        if groups.setdefault(cid, group) != group:
            raise ValueError('Equivalence group changed across repeats')
        if type(row.get('eligible')) is not bool:
            raise ValueError('Explicit boolean execution eligibility required')
        for field in ('execution_success', 'spatial_correct'):
            if field not in row or (row[field] is not None and type(row[field]) is not bool):
                raise ValueError(f'{field} must be explicit bool or None')
        if row['eligible']:
            included.append(row)
        else:
            excluded.append(row)
    execution = [r['execution_success'] for r in included]
    spatial = [r['spatial_correct'] for r in included]
    joint = [False if r['execution_success'] is False else r['spatial_correct']
             if r['execution_success'] is True else None for r in included]
    succeeded = [r for r in included if r['execution_success'] is True]
    esr, raw, joint_rate = _rate(execution), _rate(spatial), _rate(joint)
    cge = _rate([r['spatial_correct'] for r in succeeded])
    ssfr = _rate([not r['spatial_correct'] if type(r['spatial_correct']) is bool else None for r in succeeded])
    # Unknown execution observations may belong to the successful cohort. Do
    # not report an apparently complete conditional rate after excluding them.
    unknown_membership = sum(e is None for e in execution)
    for metric in (cge, ssfr):
        metric['unknown_success_membership'] = unknown_membership
        if unknown_membership:
            metric['value'] = None
    gap = esr['value']-joint_rate['value'] if esr['value'] is not None and joint_rate['value'] is not None else None
    return dict(contract_version=CONTRACT_VERSION,
                scope='CALLER_OBSERVED_EXECUTION_AND_ORACLE_BOOLEANS_NOT_SELF_REPORTED_API_STATUS',
                observations=len(included), excluded_observations=len(excluded),
                distinct_cases=len({r['case_id'] for r in included}),
                equivalence_groups=len({r['equivalence_group'] for r in included}),
                repeats_per_case=dict(Counter(r['case_id'] for r in included)),
                ESR=esr, raw_spatial_correctness=raw, joint_execution_spatial_success=joint_rate,
                SCR_joint=joint_rate, CGE=cge, SSFR=ssfr, execution_correctness_gap=gap,
                successful_execution_observations=len(succeeded),
                evqsr=None, evqsr_missing_reason='SEMANTIC_PLAN_AND_CLAIM_EVIDENCE_COMPONENTS_NOT_PROVIDED',
                limitations=['CGE is conditional spatial correctness, not ESR minus SCR.',
                             'No success denominator means CGE/SSFR unavailable, not zero.',
                             'Repeated or equivalent cases are not independent inferential samples.',
                             'Eligibility, actual GIS observation and independent Oracle provenance must be verified upstream.'])
