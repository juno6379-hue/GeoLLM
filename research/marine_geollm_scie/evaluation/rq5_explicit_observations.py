"""New-run RQ5 contract: explicit observations only; no frozen-result inference.

Callers supply the complete declared cohort, including failed/missing rows.
This module reads no files, starts no models and never edits a historical run.
"""
import math
from collections import defaultdict

COMPONENTS = ('semantic_correct', 'plan_valid', 'execution_success', 'spatial_correct', 'evidence_correct')
MODULES = ('ontology', 'bounded_kg', 'qec', 'validator', 'post_validation_recovery')
FROZEN_KEYS = ('benchmark_sha256', 'gold_sha256', 'snapshot_sha256', 'model_digest', 'budget_sha256', 'evaluation_contract_sha256')
COST_FIELDS = ('input_tokens', 'output_tokens', 'tool_calls')


def metric(values, *, unknown_membership=0):
    measured = [v for v in values if isinstance(v, bool)]
    n = len(values)
    missing = n-len(measured)
    complete = n > 0 and not missing and not unknown_membership
    return dict(value=sum(measured)/n if complete else None, numerator=sum(measured),
                denominator=n, measured=len(measured), missing=missing,
                unknown_membership=unknown_membership,
                status='MEASURED' if complete else 'UNDEFINED' if n == 0 and not unknown_membership else 'UNMEASURED')


def cohort_rate(rows, eligibility, field):
    selected = [r for r in rows if r.get(eligibility) is True]
    unknown = sum(not isinstance(r.get(eligibility), bool) for r in rows)
    return metric([r.get(field) for r in selected], unknown_membership=unknown)


def reliability_summary(rows):
    """Eligibility must be explicitly joined to the same answer/GOLD observation."""
    material = []
    for row in rows:
        r = dict(row)
        vals = [r.get(k) for k in COMPONENTS]
        r['evqsr'] = all(vals) if all(isinstance(v, bool) for v in vals) else None
        material.append(r)
    result = {name:cohort_rate(material, eligible, field) for name,eligible,field in (
        ('evqsr','evqsr_eligible','evqsr'),
        ('spatial_correctness','spatial_eligible','spatial_correct'),
        ('human_escalation','escalation_eligible','human_escalation'),
        ('evidence_complete','evidence_eligible','evidence_complete'),
        ('provenance_complete','provenance_eligible','provenance_complete'))}
    result['evqsr_components'] = {k:cohort_rate(material,'evqsr_eligible',k) for k in COMPONENTS}
    for name,invalid in (('false_ready',True),('false_block',False)):
        selected = [r for r in rows if r.get('expected_invalid') is invalid]
        decisions = [r.get('predicted_invalid') for r in selected]
        outcomes = [not v if invalid else v if isinstance(v,bool) else None for v in decisions]
        # A missing invalid-plan decision must not become True via `not None`.
        outcomes = [out if isinstance(v,bool) else None for out,v in zip(outcomes,decisions)]
        result[name] = metric(outcomes, unknown_membership=sum(not isinstance(r.get('expected_invalid'),bool) for r in rows))
    return result


def number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value >= 0


def distribution(values):
    valid = [v for v in values if number(v)]
    complete = bool(values) and len(valid)==len(values)
    def q(p):
        ordered = sorted(valid); at = (len(ordered)-1)*p
        lo,hi = math.floor(at),math.ceil(at)
        return ordered[lo]+(ordered[hi]-ordered[lo])*(at-lo)
    return dict(measured=len(valid), missing=len(values)-len(valid), denominator=len(values),
        mean=sum(valid)/len(valid) if complete else None,
        p50=q(.5) if complete else None, p95=q(.95) if complete else None,
        status='MEASURED' if complete else 'UNDEFINED' if not values else 'UNMEASURED')


def cost_summary(rows, events, allocation_contract=None):
    """Global actual event totals deduplicate shared calls by event_id.

    Each row declares cost_events_complete and event_ids. Each event declares
    its actual counters, including explicit zero for inapplicable counters.
    Optional allocation is {contract_id, weights:{observation_id:{event_id:w}}}.
    Without a complete mass-conserving contract no per-observation token/tool
    estimate is invented. End-to-end latency is independently measured on rows.
    """
    ids = [r['observation_id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate observation_id')
    ledger = {}
    for event in events:
        eid = event['event_id']
        if not isinstance(eid,str) or not eid:
            raise ValueError('Missing event identity')
        if eid in ledger and ledger[eid] != event:
            raise ValueError('Conflicting shared event')
        ledger[eid] = event
    refs = set()
    complete = bool(rows)
    for r in rows:
        references = r.get('event_ids')
        if not isinstance(references,list) or len(references)!=len(set(references)):
            complete=False
            continue
        refs.update(references)
        complete &= r.get('cost_events_complete') is True
    complete &= refs == set(ledger)
    totals = {}
    for field in COST_FIELDS:
        values=[e.get(field) for e in ledger.values()]
        valid=all(number(v) and float(v).is_integer() for v in values)
        totals[field] = dict(value=sum(values) if complete and valid else None,
            status='MEASURED' if complete and valid else 'UNMEASURED', unique_events=len(ledger))
    allocations = {f:distribution([None]*len(rows)) for f in COST_FIELDS}
    reason='ALLOCATION_CONTRACT_MISSING'
    if allocation_contract:
        weights=allocation_contract.get('weights',{})
        if not allocation_contract.get('contract_id') or set(weights)!=set(ids):
            raise ValueError('Incomplete allocation contract')
        mass=defaultdict(float)
        for r in rows:
            weights_row=weights[r['observation_id']]
            if set(weights_row)!=set(r.get('event_ids',[])):
                raise ValueError('Allocation references differ')
            for eid,w in weights_row.items():
                if not number(w) or w>1:
                    raise ValueError('Invalid allocation weight')
                mass[eid]+=w
        if set(mass)!=set(ledger) or any(not math.isclose(w,1,rel_tol=0,abs_tol=1e-9) for w in mass.values()):
            raise ValueError('Shared event cost must be allocated once')
        for f in COST_FIELDS:
            if totals[f]['status']=='MEASURED':
                allocations[f]=distribution([sum(ledger[eid][f]*w for eid,w in weights[r['observation_id']].items()) for r in rows])
        reason='ALLOCATED_ACTUAL_COST_NOT_STANDALONE_REPLAY_COST'
    return dict(latency_seconds=distribution([r.get('latency_seconds') for r in rows]),
        actual_unique_event_totals=totals, allocated_observation_costs=allocations,
        allocation_basis=reason, declared_observations=len(rows), unique_events=len(ledger))


def paired_ablation_delta(full_rows, variant_rows, full_profile, variant_profile, *, field):
    """Descriptive paired delta only; never rename baseline methods as ablations.

    Eligibility and boolean outcome must be explicit. Every case/repeat must
    pair. Repeats are averaged per case then cases per equivalence group; the
    returned delta is variant minus Full. No synthetic confidence interval.
    """
    missing = dict(value=None,status='UNMEASURED',ci95=None)
    if not full_profile or not variant_profile or not full_rows or not variant_rows:
        return {**missing,'reason':'ACTUAL_ABLATION_PROFILE_OR_OBSERVATIONS_MISSING'}
    for p in (full_profile,variant_profile):
        if p.get('execution_kind')!='MODULE_ABLATION' or not p.get('configuration_id') or any(not p.get(k) for k in FROZEN_KEYS):
            raise ValueError('Explicit frozen ablation profile required')
    if any(full_profile[k]!=variant_profile[k] for k in FROZEN_KEYS):
        raise ValueError('Frozen conditions differ')
    a,b=full_profile.get('modules',{}),variant_profile.get('modules',{})
    if set(a)!=set(MODULES) or set(b)!=set(MODULES) or not all(v is True for v in a.values()):
        raise ValueError('Full module profile invalid')
    disabled=[k for k in MODULES if b[k] is False]
    if len(disabled)!=1 or any(not isinstance(v,bool) for v in b.values()):
        raise ValueError('Exactly one module removal required')
    if full_profile['configuration_id']==variant_profile['configuration_id']:
        raise ValueError('Distinct configuration IDs required')
    def index(rows,profile):
        out={}
        for r in rows:
            key=(r['case_id'],r['repeat'])
            if key in out:raise ValueError('Duplicate paired observation')
            if r.get('configuration_id')!=profile['configuration_id'] or not r.get('equivalence_group'):
                raise ValueError('Observation profile/group mismatch')
            out[key]=r
        return out
    left,right=index(full_rows,full_profile),index(variant_rows,variant_profile)
    if left.keys()!=right.keys():return {**missing,'reason':'INCOMPLETE_PAIRING'}
    grouped=defaultdict(lambda:defaultdict(list));eligible=0
    for key,l in left.items():
        r=right[key]
        if l['equivalence_group']!=r['equivalence_group']:raise ValueError('Equivalence groups differ')
        le,re=l.get('metric_eligible'),r.get('metric_eligible')
        if not isinstance(le,bool) or not isinstance(re,bool) or le!=re:
            return {**missing,'reason':'MISSING_OR_DIFFERENT_ELIGIBILITY'}
        if not le:continue
        eligible+=1
        if not isinstance(l.get(field),bool) or not isinstance(r.get(field),bool):
            return {**missing,'reason':'MISSING_PAIRED_OUTCOME'}
        grouped[l['equivalence_group']][key[0]].append(int(r[field])-int(l[field]))
    differences=[sum(sum(v)/len(v) for v in cases.values())/len(cases) for cases in grouped.values()]
    return dict(value=sum(differences)/len(differences) if differences else None,
        status='MEASURED' if differences else 'UNDEFINED',ci95=None,
        direction='variant_minus_full',disabled_module=disabled[0],paired_observations=eligible,
        paired_cases=sum(len(c) for c in grouped.values()),equivalence_groups=len(grouped),
        inference='DESCRIPTIVE_ONLY_NO_CI')
