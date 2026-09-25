"""Exact-label metrics with explicit denominators and alternative tool plans."""
from itertools import product


def classification_metrics(references, predictions):
    if len(references) != len(predictions):
        raise ValueError('Reference and prediction lengths differ')
    pairs = [(set(a), set(b)) for a,b in zip(references,predictions)]
    labels = set().union(*(a | b for a,b in pairs)) if pairs else set()
    per_class = {}
    for label in sorted(labels, key=str):
        tp = sum(label in a and label in b for a,b in pairs)
        fp = sum(label not in a and label in b for a,b in pairs)
        fn = sum(label in a and label not in b for a,b in pairs)
        per_class[str(label)] = counts_metrics(tp,fp,fn)
    totals = {key:sum(item[key] for item in per_class.values()) for key in ('tp','fp','fn')}
    f1s = [item['f1'] for item in per_class.values() if item['f1'] is not None]
    return {'cases':len(pairs), 'exact_match_accuracy':sum(a==b for a,b in pairs)/len(pairs) if pairs else None,
            'micro':counts_metrics(**totals), 'macro_f1':sum(f1s)/len(f1s) if f1s else None,
            'per_class':per_class, 'zero_denominator_policy':'null'}


def counts_metrics(tp, fp, fn):
    return {'tp':tp,'fp':fp,'fn':fn, 'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn) if tp+fn else None, 'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}


def closest_allowed_plan(tasks, predicted):
    """Score against a valid whole-plan alternative, never the union of all alternatives."""
    choices = [task['allowed_capability_sets'] or [[]] for task in tasks]
    size = 1
    for alternatives in choices:
        size *= len(alternatives)
        if size > 4096:
            raise ValueError('Gold plan alternatives exceed 4096 combinations')
    combinations = [set().union(*map(set, combination)) for combination in product(*choices)]
    def score(expected):
        tp = len(expected & predicted)
        denominator = len(expected)+len(predicted)
        return (2*tp/denominator if denominator else 1, tp, -len(expected ^ predicted))
    return max(combinations or [set()],key=score)


def reviewed_metrics(rows, gold):
    indexed = {str(row['sample']):row for row in rows}
    intent_refs, intent_preds, tool_refs, tool_preds = [],[],[],[]
    slot_refs, slot_preds, question_refs, question_preds = [],[],[],[]
    failed = 0
    for reference in gold:
        row = indexed.get(str(reference['sample']),{})
        judgement = row.get('judgement') or {} if row.get('accepted') else {}
        failed += not bool(judgement)
        predicted = set(judgement.get('steps',[]))
        tool_refs.append(closest_allowed_plan(reference['required_tasks'],predicted))
        tool_preds.append(predicted)
        # Intent F1 is only meaningful for explicitly annotated unambiguous labels.
        # Related/alternative routes must not be forced into a single-label gold.
        if reference.get('intent'):
            intent_refs.append({reference['intent']})
            intent_preds.append({judgement['primary']} if judgement.get('primary') not in (None,'ABSTAIN') else set())
        expected_slots = reference['slots']
        observed_slots = judgement.get('slots',{})
        slot_refs.append({(key,value) for key,value in expected_slots.items() if value is not None})
        slot_preds.append({(key,value) for key,value in observed_slots.items() if value is not None})
        question_refs.append({'ASK' if reference['needs_clarification'] else 'NO_ASK'})
        question_preds.append({'ASK' if judgement['needs_clarification'] else 'NO_ASK'} if judgement else set())
    return {'intent':classification_metrics(intent_refs,intent_preds),
            'tool_plan':classification_metrics(tool_refs,tool_preds),
            'slot_raw_value':classification_metrics(slot_refs,slot_preds),
            'clarification':classification_metrics(question_refs,question_preds),
            'failed_or_rejected_cases':failed,
            'tool_reference_policy':'Best matching allowed complete plan; missing-capability tasks remain in separate task-coverage denominator.',
            'intent_scope':'Only explicitly annotated unambiguous intent labels; composite requests use task/tool metrics.',
            'slot_scope':'Exact (slot type, original value) entities; not character-span or normalized-value F1.'}
