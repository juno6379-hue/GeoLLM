"""Bind proposed Korean preferred labels to exact brochure spans; no automatic query rewrite."""
import argparse
import json
import re
from pathlib import Path

from services.orchestrator.reference_evaluation import load_reference_index, make_unit


def build(seeds, units):
    matches=[u for u in units if u['source_id']==seeds['source_id'] and
             u['locator']=={'kind':'pdf_page','page_1based':seeds['page_1based']}]
    if len(matches)!=1:
        raise ValueError('A unique source page is required')
    unit=matches[0]
    expected=make_unit({'artifact_id':unit['source_id'],'sha256':unit['source_sha256'],
                        'edition':unit['edition']},unit['locator'],unit['text'])
    if any(unit[k]!=expected[k] for k in ('unit_id','text_sha256')):
        raise ValueError('Source unit identity mismatch')
    if unit.get('extraction_flags') or unit['source_review_status']=='GOLD_APPROVAL_BLOCKED':
        raise ValueError('Source page needs extraction/edition repair')
    text=unit['text']; results=[]
    for pair in seeds['pairs']:
        # A nearby label in a different table row is not evidence for this relation.
        row_matches=list(re.finditer(r'(?m)^\d{1,2}(?=\s)',text))
        rows=[(m.start(),row_matches[i+1].start() if i+1<len(row_matches) else len(text))
              for i,m in enumerate(row_matches)]
        matching=[(a,b) for a,b in rows if re.search(
            r'(?<![가-힣A-Za-z])'+re.escape(pair['original'])+r'(?![가-힣A-Za-z])',text[a:b])]
        if len(matching)!=1:
            raise ValueError('A unique numbered source row is required')
        row_start,row_end=matching[0]
        start=text.index(pair['original'],row_start,row_end)
        variants=[pair['preferred'],pair['preferred'].replace(' ','^')]
        found=[(text.find(v,start,row_end),v) for v in variants if text.find(v,start,row_end)>=0]
        if not found:
            raise ValueError('Preferred label not found in source')
        pos,variant=min(found)
        if pos-start>180:
            raise ValueError('Label pair exceeds local table context; manual review needed')
        end=pos+len(variant)
        results.append({'original':pair['original'],'preferred':pair['preferred'],
                        'relation':seeds['relation'],'review_status':'AI_REVIEW_REQUIRED',
                        'reviewer_ids':[],'source_span':[start,end],'quote':text[start:end],
                        'optional_spacing':'^' in variant,
                        'reference':{k:unit[k] for k in ('unit_id','source_id','source_sha256','edition','locator','text_sha256')},
                        'ontology_equivalence_verified':False,'execution_authorized':False})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=Path,required=True)
    parser.add_argument('--reference-index',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bundle',type=Path,help='Optional source-bound runtime advisory registry')
    args=parser.parse_args()
    seeds=json.loads(args.seeds.read_text(encoding='utf-8'))
    units=load_reference_index(args.reference_index)
    rows=build(seeds,units)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        for row in rows: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    if args.bundle:
        selected={row['reference']['unit_id'] for row in rows}
        bundle={'schema_version':'marine_terminology.v1','seeds':seeds,
                'units':[u for u in units if u['unit_id'] in selected], 'relations':rows,
                'mode':'ADVISORY_ONLY','human_gold':False,'query_rewrite_enabled':False}
        args.bundle.parent.mkdir(parents=True,exist_ok=True)
        with args.bundle.open('x',encoding='utf-8') as stream:
            json.dump(bundle,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'source_bound_candidates':len(rows),'human_gold':False,'query_rewrite_enabled':False}))


if __name__=='__main__':
    main()
