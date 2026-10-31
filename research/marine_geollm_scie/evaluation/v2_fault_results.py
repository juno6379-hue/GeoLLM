"""Controlled fault metrics, separate from independent expert GOLD accuracy."""
from collections import Counter, defaultdict
from research.marine_geollm_scie.evaluation.rq_metrics import rate
from research.marine_geollm_scie.evaluation.metrics import distribution


def metrics(rows):
    counts=Counter();missing=0
    for row in rows:
        truth=row.get('expected_invalid'); verdict=row.get('predicted_invalid')
        if not isinstance(truth,bool) or not isinstance(verdict,bool):
            missing+=1;continue
        counts['TP' if truth and verdict else 'FN' if truth else 'FP' if verdict else 'TN']+=1
    invalid=[r for r in rows if r.get('expected_invalid') is True]
    valid=[r for r in rows if r.get('expected_invalid') is False]
    eligible=[r for r in rows if r.get('recovery_eligible') is True]
    attempted=[r for r in eligible if r.get('recovery_attempted') is True]
    def inverse(value):return not value if isinstance(value,bool) else None
    out={'rows':len(rows),'missing_predictions':missing,'confusion':dict(counts),
         'false_ready':rate([inverse(r.get('predicted_invalid')) for r in invalid]),
         'false_block':rate([r.get('predicted_invalid') for r in valid]),
         'recovery_eligible':len(eligible),'recovery_attempted':len(attempted),
         'recovery_attempt_rate':rate([r.get('recovery_attempted') for r in eligible]),
         'recovery_success_given_attempt':rate([r.get('recovery_success') for r in attempted]),
         'semantic_preservation_given_attempt':rate([r.get('semantic_preservation') for r in attempted]),
         'spatial_correct_given_attempt':rate([r.get('spatial_correct') for r in attempted]),
         'joint_recovery_given_attempt':rate([r.get('joint_success') for r in attempted]),
         'joint_recovery_all_eligible':rate([False if r.get('recovery_attempted') is False else r.get('joint_success') for r in eligible]),
         'forbidden_recovery_proposals':sum(r.get('forbidden_recovery_proposed') is True for r in rows),
         'costs':{}}
    for key in ('input_tokens','output_tokens','review_latency_ms','initial_validator_latency_ms',
                'post_recovery_validator_latency_ms','execution_latency_ms','standalone_latency_ms','tool_calls','model_calls'):
        out['costs'][key]=distribution([(r.get('costs') or {}).get(key) for r in rows])
    return out


def summarize_faults(rows):
    by_method=defaultdict(list);by_type=defaultdict(list)
    for row in rows:
        by_method[row['method']].append(row)
        by_type[row['method']+'|'+row['error_type']].append(row)
    paired={}
    for alternative in ('P0','H'):
        base={r.get('case_id'):r for r in rows if r['method']=='B4'}
        comparison={r.get('case_id'):r for r in rows if r['method']==alternative}
        gains=[];latency=[]
        for case in sorted(set(base)&set(comparison),key=str):
            a,b=base[case],comparison[case]
            observed=all(isinstance(r.get('predicted_invalid'),bool) for r in (a,b))
            gains.append(int(b['predicted_invalid']==b['expected_invalid'])-int(a['predicted_invalid']==a['expected_invalid']) if observed else None)
            av=(a.get('costs') or {}).get('standalone_latency_ms');bv=(b.get('costs') or {}).get('standalone_latency_ms')
            latency.append(bv-av if type(av) in (int,float) and type(bv) in (int,float) else None)
        paired[alternative+'_minus_B4']={'paired_cases':len(gains),
            'detection_correctness_gain':sum(gains)/len(gains) if gains and all(v is not None for v in gains) else None,
            'missing_detection_pairs':sum(v is None for v in gains),
            'standalone_latency_delta_ms':distribution(latency),
            'scope':'Controlled-label paired descriptive difference; not independent expert accuracy or significance'}
    return {'status':'CONTROLLED_PROTOCOL_DIAGNOSTICS',
        'independent_expert_gold':False,'semantic_preservation_scope':'EXPLICIT_TASK_TUPLE_NOT_FULL_NATURAL_LANGUAGE_MEANING',
        'overall_by_method':{k:metrics(v) for k,v in by_method.items()},
        'by_method_error_type':{k:metrics(v) for k,v in by_type.items()},
        'reliability_cost_pairs':paired,
        'hybrid_detection':'OR of both initial-plan verdicts; recovery uses reviewed plan followed by Validator',
        'no_recovery_method':'P0 validation only; not included in recovery eligible denominator',
        'shared_review_costs':'B4/H standalone cost allocation; do not sum as independent model calls'}
