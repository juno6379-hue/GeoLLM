"""Paired inference aggregates repeats per case; repeats are never new samples."""
import math
import random
from collections import defaultdict
from .metrics import quantile


def paired_bootstrap(rows_a, rows_b, *, field, samples=2000, seed=20261029):
    def group(rows):
        out=defaultdict(list)
        for r in rows:
            if r.get(field) is None or not isinstance(r[field], (int,float)) or not math.isfinite(r[field]):
                raise ValueError('Missing values cannot be silently excluded from paired inference')
            out[r['case_id']].append(float(r[field]))
        return {k:sum(v)/len(v) for k,v in out.items()}
    a,b=group(rows_a),group(rows_b)
    if not a or a.keys()!=b.keys():
        raise ValueError('Identical nonempty case cohorts required')
    differences=[a[k]-b[k] for k in sorted(a)]
    if samples<100:
        raise ValueError('At least 100 bootstrap samples required')
    rng=random.Random(seed)
    boot=[sum(rng.choice(differences) for _ in differences)/len(differences) for _ in range(samples)]
    return {'paired_cases':len(a),'difference':sum(differences)/len(differences),
            'ci95':[quantile(boot,.025),quantile(boot,.975)],'seed':seed,'bootstrap_samples':samples}


def mcnemar_exact(a, b):
    """Input one predeclared binary outcome per case, never pooled repeated trials."""
    if not a or a.keys()!=b.keys() or not all(isinstance(v,bool) for v in [*a.values(),*b.values()]):
        raise ValueError('Identical nonempty binary case mappings required')
    ab=sum(a[k] and not b[k] for k in a)
    ba=sum(not a[k] and b[k] for k in a)
    n=ab+ba
    p=min(1.,2*sum(math.comb(n,k) for k in range(min(ab,ba)+1))/(2**n)) if n else 1.
    return {'paired_cases':len(a),'a_only':ab,'b_only':ba,'p_value':p,'test':'two-sided exact McNemar'}
