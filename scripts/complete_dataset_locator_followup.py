"""Supplement locator audit with explicit fragments and current DB receipts."""
from __future__ import annotations
import csv,gzip,io,json,collections
from pathlib import Path
from scripts.audit_dataset_remaining_locators import ROOT,BASE,norm,sha,token_span

def unique_fragment(content, source):
    a,b=norm(content),norm(source)
    i=b.find(a)
    if not a or i<0 or b.find(a,i+1)>=0:return None
    return [i,i+len(a)]

def main():
    out=Path.home()/'.codex/geollm-audit/20261102/locator'
    results=[json.loads(s) for s in (out/'v2/results.jsonl').open(encoding='utf-8')]
    current={x['chunk_id']:x for s in gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') if (x:=json.loads(s))['chunk_id'] in {r['chunk_id'] for r in results}}
    db={x['chunk_id']:x for s in (out/'db_comparison.jsonl').open(encoding='utf-8') if (x:=json.loads(s))}
    fc={x['chunk_id']:x for s in (out/'v2/independent_fc_field_audit.jsonl').open(encoding='utf-8') if (x:=json.loads(s))}
    cache={}
    for q in results:
        r=current[q['chunk_id']];p=ROOT/r['source_file'];typ=r['document_type']
        if q['chunk_id'] in db:
            d=db[q['chunk_id']]
            q.update(status=d['status'],reason=d['reason'],db_field_checks=d.get('field_checks'),db_export='db_v2/gbhd_s101_current.json' if r['source_file'].startswith('gbhd_s101/') else 'db_v2/S100_dev_current.json')
        elif q['chunk_id'] in fc:
            d=fc[q['chunk_id']];q.update(status='INCOMPLETE_DERIVED_FIELDS',reason=d['reason'],unchanged_definition_prefix=d['unchanged_definition_prefix'],raw_xml_field_count=len(d['raw_xml_fields']))
        elif q['reason']=='NO_CURRENT_SOURCE_ADAPTER' and p.is_file():
            key=str(p)
            if key not in cache:
                candidates=[]
                if p.suffix.lower()=='.zip':
                    from scripts.build_document_rag_chunks import zip_documents
                    for member,text in zip_documents(p):
                        candidates.append((member,text,'VERIFIED_TEXT'))
                        candidates.append((member,'Archive member: '+member+'\n'+text,'VERIFIED_TEXT'))
                elif p.suffix.lower() in {'.md','.txt'} and typ!='dataset_profile':
                    candidates=[('file:utf8-sig',p.read_text(encoding='utf-8-sig'),'VERIFIED_TEXT')]
                elif typ=='dataset_profile':
                    from scripts.build_dataset_embedding_coverage import build_rows_for
                    for state in ['embeddable_document','embeddable_structured','analytics_metadata','spatial_metadata','embeddable_archive']:
                        candidates.extend(('generated_profile',x['text'],'VERIFIED_DERIVED_FIELDS') for x in build_rows_for(p,state))
                elif typ=='accident_data' and p.suffix.lower()=='.csv':
                    from scripts.build_accident_artifacts import read_csv
                    values,encoding=read_csv(p)
                    candidates=[('CSV_JSON_SERIALIZATION',json.dumps(values,ensure_ascii=False,indent=2),'VERIFIED_DERIVED_FIELDS')]
                cache[key]=candidates
            matches={}
            for loc,text,state in cache[key]:
                span=unique_fragment(r['content'],text)
                if span:matches[(loc,state)]=(span,token_span(r['content'],text) is None,sha(text.encode()))
            if len(matches)==1:
                (loc,state),(span,fragment,digest)=next(iter(matches.items()))
                q.update(status=state,reason='UNIQUE_SOURCE_FRAGMENT' if fragment else 'UNIQUE_SOURCE_SPAN_RECOVERED',source_locator=loc,normalized_char_span=span,partial_token_boundary=fragment,source_representation_sha256=digest)
            else:q.update(reason='AMBIGUOUS_SOURCE_SPAN' if matches else 'NO_EXACT_SOURCE_SPAN',candidate_matches=len(matches))
    final=out/'v3';final.mkdir(exist_ok=True)
    path=final/'results.jsonl'
    if path.exists():raise RuntimeError('Refuse overwrite')
    path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in results),encoding='utf-8')
    summary=dict(total=len(results),counts=dict(collections.Counter(x['status'] for x in results)),reasons=dict(collections.Counter(x['reason'] for x in results)),sha256=sha(path.read_bytes()),db_modified=False,holdout_used=False)
    (final/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary))

if __name__=='__main__':main()
