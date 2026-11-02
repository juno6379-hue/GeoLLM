"""Prepare/compile the same RQ1 AI-review contract for old or fresh raw runs.

GOLD is read only after all reviews have passed raw-identity validation. This
runner makes no model/API/DB calls and never writes into a source run.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from research.marine_geollm_scie.evaluation.grounding_prediction_review_v2 import (
    prepare_review_template,compile_review,sha,canonical_json,CONTRACT_SHA256,POLICY,
)
from research.marine_geollm_scie.evaluation.grounding_atoms_v1 import score_atoms,paired_cluster_bootstrap


def jsonl(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def cohort(observations):
    observations=Path(observations).resolve();root=observations.parent
    rows=[r for r in jsonl(observations) if r['method'] in {'B1','B2'}]
    pairs={}
    for row in rows:
        key=(row['case_id'],row['method'])
        if key in pairs:raise ValueError('DUPLICATE_CASE_METHOD; invoke separately per repeat')
        path=(root/row['raw_artifact_path']).resolve()
        if not path.is_relative_to(root):raise ValueError('RAW_PATH_ESCAPE')
        raw=path.read_bytes()
        if sha(raw)!=row['raw_artifact_sha256']:raise ValueError('RAW_RECEIPT_HASH_CHANGED')
        pairs[key]=(row,raw,path)
    ids={key[0] for key in pairs}
    if not ids or any({key[1] for key in pairs if key[0]==cid}!={'B1','B2'} for cid in ids):raise ValueError('INCOMPLETE_PAIRED_COHORT')
    if any(len({row['query'] for (cid2,_),(row,_,_) in pairs.items() if cid2==cid})!=1 for cid in ids):raise ValueError('PAIRED_QUERY_MISMATCH')
    return pairs


def run(observations,output,*,reviews=None,gold=None):
    pairs=cohort(observations);output=Path(output)
    if output.resolve().is_relative_to(Path(observations).resolve().parent):
        raise ValueError('MEASUREMENT_MUST_NOT_WRITE_INTO_SOURCE_RUN')
    if output.exists():raise FileExistsError('New measurement directory required')
    output.mkdir(parents=True)
    write(output/'contract.json',POLICY)
    raw_inventory=[{'case_id':key[0],'method':key[1],'path':str(path),'sha256':sha(raw)}
                   for key,(row,raw,path) in sorted(pairs.items())]
    write(output/'raw_preservation.json',raw_inventory)
    if reviews is None:
        templates=[prepare_review_template(raw,case_id=key[0],method=key[1],query=row['query'])
                   for key,(row,raw,_) in sorted(pairs.items())]
        with (output/'reviews_REQUIRED.jsonl').open('x',encoding='utf-8') as stream:
            for row in templates:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        write(output/'status.json',{'status':'AI_REVIEW_REQUIRED','observations':len(templates),
            'measured':False,'contract_sha256':CONTRACT_SHA256,'failures_retained':True})
        return
    supplied=jsonl(reviews);indexed={(r['case_id'],r['method']):r for r in supplied}
    if len(indexed)!=len(supplied) or indexed.keys()!=pairs.keys():raise ValueError('REVIEW_COHORT_MISMATCH')
    compiled={key:compile_review(raw,indexed[key]) for key,(_,raw,_) in pairs.items()}
    with (output/'prediction_atoms.jsonl').open('x',encoding='utf-8') as stream:
        for key in sorted(compiled):stream.write(json.dumps(compiled[key],ensure_ascii=False)+'\n')
    if gold is None:raise ValueError('SCORING_GOLD_REQUIRED_AFTER_REVIEW_COMPILATION')
    gold=Path(gold);gold_raw=gold.read_bytes();gold_rows={r['case_id']:r for r in jsonl(gold)}
    if set(gold_rows)!={key[0] for key in pairs}:raise ValueError('GOLD_COHORT_MISMATCH')
    scores=[]
    for key,predicted in sorted(compiled.items()):
        expected=gold_rows[key[0]]
        if expected['query_sha256']!=predicted['query_sha256']:raise ValueError('GOLD_QUERY_IDENTITY_MISMATCH')
        atoms=predicted['prediction_atoms']
        optional=expected.get('optional_atoms',[])
        optional_matches=score_atoms(optional,atoms)
        neutral={match['prediction_id'] for match in optional_matches['matches']}
        required=[a for a in atoms if a['prediction_id'] not in neutral]
        scored=score_atoms(expected['atoms'],required)
        scores.append({'case_id':key[0],'method':key[1],'repeat_id':0,
            'equivalence_group':expected['equivalence_group'],
            'terminology_condition':expected['terminology_condition'],
            'query_sha256':predicted['query_sha256'],'gold_sha256':sha(gold_raw),
            'contract_sha256':CONTRACT_SHA256,'raw_sha256':predicted['raw_sha256'],
            'raw_status':predicted['raw_status'],'score':scored,
            'optional_matched_neutral_ids':sorted(neutral)})
    all_conditions=sorted({c for r in scores for c in r['terminology_condition']}|{'UNSEEN_SYNONYM'})
    tables={}
    for condition in ['OVERALL',*all_conditions]:
        subset=[r for r in scores if condition=='OVERALL' or condition in r['terminology_condition']]
        if not subset:
            tables[condition]={'status':'NO_CASES','cases':0,'a_micro_f1':None,'b_micro_f1':None,'ci95':None};continue
        tables[condition]=paired_cluster_bootstrap([r for r in subset if r['method']=='B1'],
            [r for r in subset if r['method']=='B2'],samples=2000,seed=20261103)
    write(output/'scores.json',scores);write(output/'condition_comparison.json',tables)
    write(output/'status.json',{'status':'AI_REVIEWED_RQ1_MEASURED','observations':len(scores),
        'cases':len(gold_rows),'raw_status_counts':dict(Counter(r['raw_status'] for r in scores)),
        'human_prediction_review_complete':False,'gold_atom_annotation_status':'AI_SOURCE_LINKED_ANNOTATION_NOT_NEW_HUMAN_APPROVAL',
        'contract_sha256':CONTRACT_SHA256,'gold_sha256':sha(gold_raw),
        'review_file_sha256':sha(Path(reviews).read_bytes()),'measured':True,
        'scope':'POST_HOC_DEVELOPMENT_ATOM_MATCH_NOT_INDEPENDENT_HUMAN_SEMANTIC_ACCURACY',
        'conditions':'OVERLAPPING_LABELS_FROM_EXISTING_DEVELOPMENT_ANNOTATIONS; UNSEEN_N0',
        'limitations':['AI semantic adjudication; witness checks are not independent semantic verification',
            'Few clusters; descriptive paired CI only','No run regeneration; no holdout used',
            'Source-bound atom correctness is separate from actual object truth and execution success']})
    for item in raw_inventory:
        if sha(Path(item['path']).read_bytes())!=item['sha256']:raise ValueError('ORIGINAL_RAW_CHANGED_DURING_SCORING')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--observations',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--reviews');parser.add_argument('--gold')
    args=parser.parse_args();run(args.observations,args.output,reviews=args.reviews,gold=args.gold)
