"""Paired grounded-shadow observations; semantic metrics require reviewed gold."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path


def percentile(values, fraction):
    return sorted(values)[math.ceil(len(values)*fraction)-1] if values else None


def summarize(rows, gold=None):
    called=[r for r in rows if r.get('called')]
    slots=[s for r in rows for s in r.get('slot_reviews',[]) if s.get('raw') is not None]
    result={'cases':len(rows),'called':len(called),'accepted_structure_and_grounding':sum(bool(r.get('accepted')) for r in rows),
            'errors':dict(Counter(r.get('error') for r in rows if r.get('error'))),
            'non_null_slots_reviewed':len(slots),'rejected_slot_count':sum(s['status']=='REJECTED' for s in slots),
            'called_cases_without_slot_review':sum('slot_reviews' not in r for r in called),
            'p50_seconds':percentile([r['elapsed_s'] for r in called],.5),
            'p95_seconds':percentile([r['elapsed_s'] for r in called],.95),
            'gold_status':'UNAVAILABLE', 'semantic_metrics':None,
            'limitation':'Grounding acceptance is not semantic accuracy. Missing candidate traces and failed calls remain in total cases.'}
    if gold is None:
        return result
    by_id={str(g['sample']):g for g in gold}
    if len(by_id)!=len(gold):
        raise ValueError('Duplicate gold IDs')
    if any(g.get('review_status')!='HUMAN_VERIFIED' or not g.get('reviewer_ids') for g in gold):
        raise ValueError('Human-reviewed gold with reviewer attribution is required')
    for g in gold:
        if not isinstance(g.get('needs_clarification'), bool) or not isinstance(g.get('slots'), dict):
            raise ValueError('Reviewed clarification and slots are required')
        for task in g['required_tasks']:
            options = task.get('allowed_capability_sets')
            # [] explicitly means no registered capability can satisfy this task.
            # An empty alternative [[]] would otherwise earn credit vacuously.
            if not isinstance(options, list) or any(not isinstance(option, list) or not option for option in options):
                raise ValueError('Capability alternatives must be non-empty lists; use [] for a candidate gap')
    required=sum(len(g['required_tasks']) for g in gold)
    fulfilled=exact_slots=slot_total=unneeded=missed=excess=0
    question_not_needed=sum(g['needs_clarification'] is False for g in gold)
    question_needed=sum(g['needs_clarification'] is True for g in gold)
    indexed={str(r['sample']):r for r in rows}
    if len(indexed)!=len(rows):
        raise ValueError('Duplicate response IDs')
    for identifier,g in by_id.items():
        row=indexed.get(identifier,{})
        # A rejected/failed response does not count as a valid semantic result.
        judgement=row.get('judgement',{}) if row.get('accepted') else {}
        steps=set(judgement.get('steps',[]))
        fulfilled+=sum(any(set(option).issubset(steps) for option in task['allowed_capability_sets']) for task in g['required_tasks'])
        for key,value in g['slots'].items():
            slot_total+=1
            exact_slots+=bool(judgement) and key in judgement.get('slots',{}) and judgement['slots'][key]==value
        if judgement:
            unneeded+=judgement['needs_clarification'] and not g['needs_clarification']
            missed+=not judgement['needs_clarification'] and g['needs_clarification']
            excess+=bool(steps & set(g.get('forbidden_capabilities',[])))
        elif g['needs_clarification']:
            missed+=1
    ratio=lambda a,b:a/b if b else None
    result.update(gold_status='HUMAN_VERIFIED',semantic_metrics={
        'required_task_plan_coverage':ratio(fulfilled,required),
        'slot_raw_exact_match':ratio(exact_slots,slot_total),
        'unnecessary_clarification_rate':ratio(unneeded,question_not_needed),
        'missing_clarification_rate':ratio(missed,question_needed),
        'proposed_forbidden_execution_rate':ratio(excess,len(gold)),
        'actual_execution_completion_rate':None,
        'actual_execution_note':'Shadow proposals are not executed. Actual completion requires separate tool evidence.',
        'denominators':{'tasks':required,'slots':slot_total,'no_question_needed':question_not_needed,'question_needed':question_needed,'cases':len(gold)}})
    from scripts.grounded_metrics import reviewed_metrics
    result['semantic_metrics']['classification'] = reviewed_metrics(rows,gold)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',nargs='+',type=Path,required=True)
    p.add_argument('--gold',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    gold=[json.loads(line) for line in args.gold.read_text(encoding='utf-8').splitlines()] if args.gold else None
    reports={}
    snapshot=None
    paired={}
    for path in args.runs:
        manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        if snapshot is not None and snapshot!=manifest['snapshot_sha256']:
            raise ValueError('Paired comparison requires identical frozen inputs')
        snapshot=manifest['snapshot_sha256']
        rows=[json.loads(line) for line in (path/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
        reports[str(path)]=summarize(rows,gold)
        for row in rows:
            paired.setdefault(str(row['sample']),{})[str(path)]={k:row.get(k) for k in ('accepted','error','elapsed_s','judgement','slot_reviews')}
    output={'snapshot_sha256':snapshot,'reports':reports,'paired_cases':paired,
            'qlora_decision':'DEFER: independent reviewed training/calibration/holdout, recurrent-error and rollback conditions not yet verified'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2)
    print(json.dumps(reports,ensure_ascii=False))


if __name__=='__main__':
    main()
