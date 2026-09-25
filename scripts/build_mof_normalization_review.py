"""Bind proposed Korean preferred labels to exact brochure spans; no automatic query rewrite."""
import argparse
import json
from pathlib import Path

from services.orchestrator.reference_evaluation import load_reference_index


def build(seeds, units):
    matches=[u for u in units if u['source_id']==seeds['source_id'] and
             u['locator']=={'kind':'pdf_page','page_1based':seeds['page_1based']}]
    if len(matches)!=1:
        raise ValueError('A unique source page is required')
    unit=matches[0]
    if unit.get('extraction_flags') or unit['source_review_status']=='GOLD_APPROVAL_BLOCKED':
        raise ValueError('Source page needs extraction/edition repair')
    text=unit['text']; results=[]
    for pair in seeds['pairs']:
        start=text.find(pair['original'])
        variants=[pair['preferred'],pair['preferred'].replace(' ','^')]
        found=[(text.find(v,start),v) for v in variants if start>=0 and text.find(v,start)>=0]
        if not found:
            raise ValueError('Preferred label not found in source')
        pos,variant=min(found)
        if pos-start>180:
            raise ValueError('Label pair exceeds local table context; manual review needed')
        end=pos+len(variant)
        results.append({'original':pair['original'],'preferred':pair['preferred'],
                        'relation':seeds['relation'],'review_status':'AI_REVIEW_REQUIRED',
                        'reviewer_ids':[],'source_span':[start,end],'quote':text[start:end],
                        'reference':{k:unit[k] for k in ('unit_id','source_id','source_sha256','edition','locator','text_sha256')},
                        'ontology_equivalence_verified':False,'execution_authorized':False})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=Path,required=True)
    parser.add_argument('--reference-index',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=build(json.loads(args.seeds.read_text(encoding='utf-8')),load_reference_index(args.reference_index))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        for row in rows: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(json.dumps({'source_bound_candidates':len(rows),'human_gold':False,'query_rewrite_enabled':False}))


if __name__=='__main__':
    main()
