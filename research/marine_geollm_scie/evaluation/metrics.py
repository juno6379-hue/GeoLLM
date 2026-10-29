"""Research metrics with explicit missingness and independently reviewed gold gates."""
from collections import Counter
import math
import statistics


def is_gold(row):
    return (row.get('review_status', row.get('annotation_status', row.get('label_status'))) == 'GOLD'
            and bool(row.get('annotator_ids')) and row.get('adjudication_status') == 'APPROVED')


def ratio(n, d):
    return n / d if d else None


def mean_complete(values):
    """Missing measurements make the declared cohort metric unavailable, not better."""
    return statistics.mean(values) if values and all(v is not None for v in values) else None


def quantile(values, p):
    values = sorted(values)
    if not values:
        return None
    at = (len(values) - 1) * p
    low, high = math.floor(at), math.ceil(at)
    return values[low] + (values[high] - values[low]) * (at - low)


def distribution(values):
    valid = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)]
    return {'measured': len(valid), 'missing': len(values)-len(valid),
            'mean': statistics.mean(valid) if valid else None, 'p50': quantile(valid,.5),
            'p95': quantile(valid,.95), 'iqr': quantile(valid,.75)-quantile(valid,.25) if valid else None}


def object_sets(expected, observed):
    """Use only with independently reviewed sets. None is unobserved; [] is valid empty."""
    if expected is None or observed is None:
        return {'precision':None,'recall':None,'f1':None,'exact_match':None,'status':'NOT_EVALUATED'}
    a,b = set(expected),set(observed)
    tp = len(a & b)
    precision = tp/len(b) if b else (1.0 if not a else 0.0)
    recall = tp/len(a) if a else (1.0 if not b else 0.0)
    return {'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0.0,
            'exact_match':a==b,'status':'VALID_EMPTY_RESULT' if not a and not b else 'EVALUATED'}


def distance_error(expected, observed, tolerance):
    if any(v is None for v in (expected,observed,tolerance)):
        return {'absolute_error':None,'relative_error':None,'within_tolerance':None}
    if not all(math.isfinite(v) for v in (expected,observed,tolerance)) or tolerance < 0:
        raise ValueError('Finite distances and nonnegative tolerance required')
    error = abs(expected-observed)
    return {'absolute_error':error,'relative_error':error/abs(expected) if expected else None,
            'within_tolerance':error<=tolerance}


def polygon_iou(expected, observed):
    """Inputs must already share a declared suitable projected CRS; no reprojection inferred."""
    if expected is None or observed is None:
        return None
    if not expected.is_valid or not observed.is_valid:
        return None
    union = expected.union(observed).area
    return expected.intersection(observed).area/union if union else float(expected.equals(observed))


def validator_metrics(rows, *, require_gold=True):
    eligible = [r for r in rows if is_gold(r) or not require_gold]
    labelled = [r for r in eligible if isinstance(r.get('expected_invalid'), bool)]
    complete = [r for r in labelled if isinstance(r.get('predicted_invalid'), bool)]
    counts = Counter(('TP' if r['predicted_invalid'] else 'FN') if r['expected_invalid'] else
                     ('FP' if r['predicted_invalid'] else 'TN') for r in complete)
    tp,fp,fn,tn = (counts[k] for k in ('TP','FP','FN','TN'))
    all_measured = bool(labelled) and len(complete)==len(labelled)
    precision,recall = ratio(tp,tp+fp),ratio(tp,tp+fn)
    return {'cohort':len(rows),'eligible':len(labelled),'measured':len(complete),
            'missing_predictions':len(labelled)-len(complete), **{k:counts[k] for k in ('TP','FP','FN','TN')},
            'precision':precision if all_measured else None,'recall':recall if all_measured else None,
            'f1':ratio(2*tp,2*tp+fp+fn) if all_measured else None,
            'false_ready_rate':ratio(fn,tp+fn) if all_measured else None,
            'false_block_rate':ratio(fp,fp+tn) if all_measured else None,
            'status':'PILOT_ONLY' if all_measured else 'NOT_READY'}


COMPONENTS = ('semantic_correct','plan_valid','execution_success','spatial_correct','evidence_correct')


def evqsr(rows):
    eligible = [r for r in rows if is_gold(r) and r.get('expected_behavior')=='EXECUTE']
    values = [all(r.get(k) is True for k in COMPONENTS) if all(isinstance(r.get(k),bool) for k in COMPONENTS) else None for r in eligible]
    return {'value':mean_complete(values),'eligible':len(eligible),'measured':sum(v is not None for v in values),
            'components':{k:mean_complete([r.get(k) if isinstance(r.get(k),bool) else None for r in eligible]) for k in COMPONENTS},
            'status':'PILOT_ONLY' if eligible and all(v is not None for v in values) else 'NOT_READY'}


def semantic_metrics(rows):
    gold = [r for r in rows if is_gold(r)]
    result = {k:mean_complete([r.get(k) if isinstance(r.get(k),bool) else None for r in gold])
              for k in ('feature_correct','attribute_correct','relation_correct','semantic_correct')}
    pairs=[(r.get('gold_semantic_set'),r.get('predicted_semantic_set')) for r in gold]
    if not pairs or any(a is None or b is None for a,b in pairs):
        result.update(micro_f1=None,macro_f1=None)
    else:
        labels=set().union(*(set(a)|set(b) for a,b in pairs))
        counts=[(sum(x in a and x in b for a,b in pairs),sum(x not in a and x in b for a,b in pairs),sum(x in a and x not in b for a,b in pairs)) for x in labels]
        sums=[sum(x[i] for x in counts) for i in range(3)]
        result.update(micro_f1=ratio(2*sums[0],2*sums[0]+sums[1]+sums[2]),
                      macro_f1=mean_complete([ratio(2*t,2*t+f+n) for t,f,n in counts]))
    return result


def recovery_metrics(rows):
    eligible=[r for r in rows if is_gold(r) and r.get('recovery_eligible') is True]
    success=[r.get('recovered') if isinstance(r.get('recovered'),bool) else None for r in eligible]
    return {'eligible':len(eligible),'recovered':sum(v is True for v in success),
            'recovery_rate':mean_complete(success),
            'first_repair_success':mean_complete([r.get('recovered') and r.get('repair_iterations')==1 if isinstance(r.get('recovered'),bool) and r.get('repair_iterations') is not None else None for r in eligible]),
            'iterations':distribution([r.get('repair_iterations') for r in eligible]),
            'escalation_rate':mean_complete([r.get('human_escalation') if isinstance(r.get('human_escalation'),bool) else None for r in eligible]),
            'semantic_drift_rate':mean_complete([r.get('semantic_drift') if isinstance(r.get('semantic_drift'),bool) else None for r in eligible])}
