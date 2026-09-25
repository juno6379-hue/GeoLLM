"""Export unlabelled, model-blind development review forms; never invent human gold."""
import argparse
import json
import re
from pathlib import Path

from services.orchestrator.intent_shadow import fingerprint


def reference_candidates(case, units):
    from services.orchestrator.korean_query_analysis import constraints
    from services.orchestrator.semantic_slot_binding import bind_semantic_slots
    binding=bind_semantic_slots(case['query'],{'constraints':constraints(case['query'])},[])
    codes=set(binding['target_features'])
    terms={t['raw_text'] for t in binding['term_bindings'] if not t['excluded']}
    lexical = [t for t in binding['maritime_terminology']['candidates'] if not t['excluded'] and not t['quoted']]
    source_units = {t['reference']['unit_id'] for t in lexical}
    hits=[]
    for unit in units:
        canonical=codes.intersection(unit['canonical_ids'])
        names={re.sub(r'(?<=[a-z])(?=[A-Z])',' ',code) for code in codes}
        matches=sorted(t for t in terms|codes|names if t.casefold() in unit['text'].casefold())
        heading=any(re.search(r'^\s*\d+(?:\.\d+)+\s+'+re.escape(name)+r'\s*$',unit['text'][:1800],re.I|re.M)
                    for name in names)
        direct_relation = unit['unit_id'] in source_units
        if not canonical and not matches and not direct_relation:
            continue
        hits.append((4 if direct_relation else 3 if canonical else 2 if heading else 1,len(matches),unit,matches))
    hits.sort(key=lambda h:(-h[0],-h[1],h[2]['source_id'],h[2]['locator'].get('page_1based',0),json.dumps(h[2]['locator'],sort_keys=True)))
    # Diversify sources; this is a review aid, not automatic evidence selection gold.
    selected=[]; source_counts={}
    for _,_,unit,matches in hits:
        source=unit['source_id']
        if source_counts.get(source,0)>=2:
            continue
        selected.append({**{k:unit[k] for k in ('unit_id','source_id','source_sha256','edition','locator','text_sha256','source_review_status')},
                         'canonical_ids':unit['canonical_ids'],'matched_query_terms':matches,
                         'extraction_flags':unit.get('extraction_flags',[]),
                         'status':'RETRIEVAL_CANDIDATE_NOT_GOLD'})
        source_counts[source]=source_counts.get(source,0)+1
        if len(selected)>=8:
            break
    return selected,binding


def review_forms(snapshot, units=None):
    for case in snapshot['cases']:
        form={'sample': case['sample'], 'query': case['query'], 'context': case['context'],
               'input_sha256': fingerprint(case['inputs']),
               'dataset_role': 'DEVELOPMENT_NOT_INDEPENDENT_HOLDOUT',
               'review_status': 'UNREVIEWED', 'reviewer_ids': [],
               'reference_policy_version': 'maritime-reference-v1',
               'reference_bindings': [], 'expected_claims': [],
               'reference_review_status': 'UNREVIEWED',
               'required_tasks': [], 'slots': {}, 'needs_clarification': None,
               'forbidden_capabilities': [], 'candidate_gap': None,
               'rationale': None, 'capability_contracts': case['inputs']['capability_contracts'],
               'candidate_issue': case['candidate_issue']}
        if units is not None:
            candidates,binding=reference_candidates(case,units)
            form.update(reference_candidates=candidates,
                        concept_bindings=binding['term_bindings'],kg_seed_ids=binding['kg_seed_ids'],
                        semantic_registry_sha256=binding['source_sha256'])
            form.update(maritime_terminology=binding['maritime_terminology'],
                        unresolved_terminology=binding['unresolved_terminology'])
        yield form


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-index', type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    units=None
    if args.reference_index:
        from services.orchestrator.reference_evaluation import load_reference_index
        units=load_reference_index(args.reference_index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        for form in review_forms(snapshot,units):
            stream.write(json.dumps(form, ensure_ascii=False)+'\n')
    print(json.dumps({'forms':len(snapshot['cases']), 'human_gold':False, 'model_outputs_included':False}))


if __name__ == '__main__':
    main()
