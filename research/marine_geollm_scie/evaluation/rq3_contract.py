"""RQ3 fixed-cohort metrics; missing observations are never discarded."""
from collections import defaultdict
import random
from .execution_reliability_v1 import summarize_execution

VERSION='rq3_execution_spatial.v2'
METHODS=('B0','B1','B2','B3','B4','P0','H','P1')


def conjunction(values):
    return all(values) if all(type(v) is bool for v in values) else None


def summarize(rows):
    result=summarize_execution(rows)
    eligible=[r for r in rows if r['eligible']]
    values=[conjunction([r['execution_success'],r['spatial_correct'],r.get('semantic_correct'),r.get('evidence_correct')]) for r in eligible]
    result.update(contract_version=VERSION,
        EVQSR={'value':sum(v is True for v in values)/len(values) if values and all(type(v) is bool for v in values) else None,
               'denominator':len(values),'measured':sum(type(v) is bool for v in values),'missing':sum(v is None for v in values)},
        Spatial_Correct=result['joint_execution_spatial_success'],
        EVQSR_definition='E AND object/geometry/relation correctness AND independently assessed semantic correctness AND evidence correctness; unknown component remains unmeasured')
    return result


def metric(result,name):
    return result[name] if name=='execution_correctness_gap' else result[name]['value']


def paired_ci(a,b,*,samples=2000,seed=20261103):
    """Paired cluster bootstrap on identical case/repeat/hash cohorts; descriptive."""
    if type(samples) is not int or samples<100:raise ValueError('At least 100 bootstrap samples required')
    def index(rows):
        out={}
        for r in rows:
            key=(r['case_id'],r['repeat_id'])
            if key in out:raise ValueError('Duplicate paired observation')
            for k in ('query_sha256','oracle_sha256','contract_sha256'):
                if not isinstance(r.get(k),str) or len(r[k])!=64:raise ValueError('Pinned paired identity required')
            out[key]=r
        return out
    ai,bi=index(a),index(b)
    if not ai or ai.keys()!=bi.keys():raise ValueError('Same nonempty paired cohort required')
    for k in ai:
        if any(ai[k].get(f)!=bi[k].get(f) for f in ('equivalence_group','eligible','query_sha256','oracle_sha256','contract_sha256')):
            raise ValueError('Paired identity mismatch')
    repeat_sets=defaultdict(set)
    for case,repeat in ai:repeat_sets[case].add(repeat)
    if len({tuple(sorted(v)) for v in repeat_sets.values()})!=1:raise ValueError('Unbalanced repeat cohort')
    groups=defaultdict(list)
    for k in sorted(ai):groups[ai[k]['equivalence_group']].append(k)
    names=('ESR','raw_spatial_correctness','Spatial_Correct','CGE','SSFR','EVQSR','execution_correctness_gap')
    sa,sb=summarize(a),summarize(b)
    result={'clusters':len(groups),'paired_observations':len(ai),'resampling_unit':'equivalence_group',
            'scope':'DESCRIPTIVE_DEVELOPMENT_NOT_CONFIRMATORY','seed':seed,'samples':samples,'metrics':{}}
    for name in names:
        x,y=metric(sa,name),metric(sb,name)
        result['metrics'][name]={'difference_B_minus_A':y-x if x is not None and y is not None else None,'ci95':None,'undefined_draws':0}
    if len(groups)<2:
        result['reason']='FEWER_THAN_TWO_EQUIVALENCE_GROUPS';return result
    rng=random.Random(seed);keys=sorted(groups);draws=defaultdict(list)
    for _ in range(samples):
        ra,rb=[],[]
        for occurrence in range(len(keys)):
            for key in groups[rng.choice(keys)]:
                # Relabel duplicated resampled cases so cohort validation does not deduplicate them.
                ra.append(dict(ai[key],case_id=f'{occurrence}:{key[0]}'))
                rb.append(dict(bi[key],case_id=f'{occurrence}:{key[0]}'))
        aa,bb=summarize(ra),summarize(rb)
        for name in names:
            x,y=metric(aa,name),metric(bb,name)
            if x is None or y is None:result['metrics'][name]['undefined_draws']+=1
            else:draws[name].append(y-x)
    for name in names:
        values=sorted(draws[name]);entry=result['metrics'][name]
        if values and not entry['undefined_draws'] and entry['difference_B_minus_A'] is not None:
            entry['ci95']=[values[int((len(values)-1)*.025)],values[int((len(values)-1)*.975)]]
    result['limitation']=f'Only {len(groups)} development equivalence groups; CI unstable' if len(groups)<10 else None
    return result


def method_table(rows,cases,*,repeat_ids=(1,),methods=METHODS,contract_sha256=None):
    """Fill absent method observations as unknown, keeping the same denominator."""
    known={};case_index={c['case_id']:c for c in cases}
    for r in rows:
        key=(r['method'],r['case_id'],r['repeat_id'])
        if key in known or r['case_id'] not in case_index or r['method'] not in methods or r['repeat_id'] not in repeat_ids:
            raise ValueError('Unexpected or duplicate method observation')
        case=case_index[r['case_id']]
        if not contract_sha256 or r.get('contract_sha256')!=contract_sha256:
            raise ValueError('Method contract identity required')
        if any(not case.get(k) or r.get(k)!=case[k] for k in ('query_sha256','oracle_sha256')):
            raise ValueError('Method query/Oracle identity mismatch')
        known[key]=r
    out={}
    for method in methods:
        batch=[]
        for case in cases:
            for repeat in repeat_ids:
                r=known.get((method,case['case_id'],repeat))
                if r and (r['equivalence_group']!=case['equivalence_group'] or r['eligible']!=case['eligible']):
                    raise ValueError('Method changed cohort eligibility/group')
                batch.append(r or {'case_id':case['case_id'],'repeat_id':repeat,'equivalence_group':case['equivalence_group'],
                                  'eligible':case['eligible'],'execution_success':None,'spatial_correct':None})
        out[method]=summarize(batch)
    return out
