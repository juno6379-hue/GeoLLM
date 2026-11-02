"""Explicit missingness and paired source-cluster diagnostics for the new cohort."""
import random
from .rq_metrics import rate

VERSION='expanded_fault_metrics_v1'
BOOTSTRAP_SEED=20261103
BOOTSTRAP_SAMPLES=2000


def recovery_metrics(rows):
    eligible=[r for r in rows if r.get('recovery_eligible') is True]
    attempted=[r for r in eligible if r.get('recovery_attempted') is True]
    forbidden=[r for r in rows if r.get('forbidden_recovery_eligible') is True]
    observed=[r['forbidden_recovery_proposed'] for r in forbidden if type(r.get('forbidden_recovery_proposed')) is bool]
    return {'version':VERSION,'recovery_eligible':len(eligible),'attempted':len(attempted),
        'first_repair_execution_success_given_attempt':rate([r.get('recovery_success') for r in attempted]),
        'first_repair_joint_success_given_attempt':rate([r.get('joint_success') for r in attempted]),
        'first_repair_scope':'One bounded reviewer repair; joint requires execution AND object restoration AND explicit task tuple preservation',
        'semantic_drift_given_attempt':rate([not r['semantic_preservation'] if type(r.get('semantic_preservation')) is bool else None for r in attempted]),
        'human_escalation':rate([r.get('human_escalation_observed') for r in eligible]),
        'human_escalation_scope':'No human-review dispatch event observed by this runner; clarification proposals are not human escalation',
        'forbidden_recovery':{'proposal_rate':rate([r.get('forbidden_recovery_proposed') for r in forbidden]),
            'observed_positive_count':sum(observed),'measured':len(observed),'missing':len(forbidden)-len(observed),
            'denominator':len(forbidden),
            'complete_positive_count':sum(observed) if forbidden and len(observed)==len(forbidden) else None,
            'scope':'Reviewer proposed search action or nonempty tool calls on nonrepairable input; not actual forbidden SQL execution'}}


def _quantile(values,p):
    ordered=sorted(values);position=(len(ordered)-1)*p
    low=int(position);high=min(low+1,len(ordered)-1)
    return ordered[low]+(ordered[high]-ordered[low])*(position-low)


def paired_cluster_comparison(rows,alternative,field,*,samples=BOOTSTRAP_SAMPLES,seed=BOOTSTRAP_SEED):
    """Never drop missing predictions or count seed repeats as independent bases."""
    left={r['case_id']:r for r in rows if r['method']=='B4' and r['expected_invalid'] is True}
    right={r['case_id']:r for r in rows if r['method']==alternative and r['expected_invalid'] is True}
    if (len(left)!=sum(r['method']=='B4' and r['expected_invalid'] is True for r in rows)
            or len(right)!=sum(r['method']==alternative and r['expected_invalid'] is True for r in rows)):
        raise ValueError('DUPLICATE_CASE_OR_UNDECLARED_REPEAT')
    keys=sorted(set(left)|set(right));pairs=[];clusters={};missing=0
    for key in keys:
        a=left.get(key);b=right.get(key)
        if a is None or b is None or a['base_scenario_id']!=b['base_scenario_id']:
            raise ValueError('PAIRED_FAULT_IDENTITY_MISMATCH')
        cluster=a['base_scenario_id'];clusters.setdefault(cluster,[])
        x,y=a.get(field),b.get(field)
        if type(x) is not bool or type(y) is not bool:missing+=1;continue
        delta=int(y)-int(x);pairs.append(delta);clusters[cluster].append(delta)
    result={'metric':field,'contrast':alternative+' minus B4','paired_cases':len(keys),
        'measured_pairs':len(pairs),'missing_pairs':missing,'independent_base_clusters':len(clusters),
        'paired_delta':None,'ci95':None,'bootstrap_samples':samples,'bootstrap_seed':seed,
        'method':'paired source-base cluster resampling with replacement; linear quantiles 0.025/0.975',
        'scope':'Development descriptive CI; only three geographic bases; not general error-family recall or human accuracy',
        'missing_policy':'Any missing pair makes full-cohort delta/CI unmeasured; no row dropping or zero imputation'}
    if missing or not pairs or len(clusters)<2:return result
    names=sorted(clusters);rng=random.Random(seed);boot=[]
    for _ in range(samples):
        draws=[rng.choice(names) for _ in names]
        values=[value for name in draws for value in clusters[name]]
        boot.append(sum(values)/len(values))
    result.update(paired_delta=sum(pairs)/len(pairs),ci95=[_quantile(boot,.025),_quantile(boot,.975)])
    return result


def summarize_paired(rows):
    return {alternative:{'binary_recall':paired_cluster_comparison(rows,alternative,'predicted_invalid'),
                         'target_fault_code_recall':paired_cluster_comparison(rows,alternative,'target_fault_code_detected')}
            for alternative in ('P0','H')}
