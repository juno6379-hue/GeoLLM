"""Read-only follow-up of generated and locator-less operational passages.

Never publishes receipts, changes DB rows, or consumes research/holdout data.
Generated-field reproducibility is deliberately distinct from literal source text.
"""
from __future__ import annotations
import argparse, collections, gzip, hashlib, io, json, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/dataset_location_audit_20261102/source/revision_v2'
OUT=ROOT/'outputs/dataset_unverified_followup_20261102/locator'

def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return ' '.join(s.split())
def local(t): return t.rsplit('}',1)[-1]
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

def token_span(content, source):
    """Whitespace-run normalization only: does not join separated numbers/words."""
    a,b=norm(content),norm(source)
    start=b.find(a)
    if start<0 or (start and not b[start-1].isspace()) or (start+len(a)<len(b) and not b[start+len(a)].isspace()): return None
    if b.find(a,start+1)>=0: return None
    return [start,start+len(a)]

def docx_text(path):
    from scripts.docx_source_text import docx_source_text
    return docx_source_text(path.read_bytes())

def fc_expected(path, out):
    # Fresh parse plus independent XML node uniqueness and raw element hashes.
    from scripts.parse_s101_feature_catalogue import parse
    from scripts.build_s101_catalogue_db_rag import load_catalogue_chunks
    parsed=parse(path); tmp=out/'fresh_catalogue_fields.json';write(tmp,parsed)
    rows=load_catalogue_chunks(tmp)
    root=ET.parse(path).getroot(); nodes={}
    for node in root.iter():
        if local(node.tag) not in {'S100_FC_FeatureType','S100_FC_SimpleAttribute','S100_FC_ComplexAttribute'}: continue
        code=next((c.text for c in node if local(c.tag)=='code'),None)
        nodes.setdefault(code,[]).append(node)
    result={}
    for row in rows:
        m=row['metadata'];code=m.get('feature_code') or m.get('attribute_code'); ns=nodes.get(code,[])
        if len(ns)!=1: continue
        result[row['section']]={'content':row['content'],'locator':f'XML/{local(ns[0].tag)}[code={code}]','element_sha256':sha(ET.tostring(ns[0]))}
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=OUT);a=ap.parse_args();out=a.output
    out.mkdir(parents=True,exist_ok=True)
    if (out/'results.jsonl').exists(): raise RuntimeError('Refuse overwrite completed audit')
    receipts=[json.loads(s) for s in (BASE/'compact_receipts.jsonl').open(encoding='utf-8')]
    target={r['chunk_id']:r for r in receipts if r['status']=='UNVERIFIED' and r.get('retrieval_status')!='SUPERSEDED' and 'VARIATION' not in r['reason']}
    rows=[r for s in gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') if (r:=json.loads(s))['chunk_id'] in target]
    cache={};results=[];candidates=[]
    for r in rows:
        typ=r['document_type'];p=ROOT/r['source_file'];content=r['content'];m=r['metadata'] or {}
        q=dict(chunk_id=r['chunk_id'],content_sha256=sha(content.encode()),source_sha256=r['source_sha256'],source_file=r['source_file'],document_type=typ,status='UNVERIFIED',reason='NO_CURRENT_SOURCE_ADAPTER',semantic_authority=False,coordinate_authority=False)
        try:
            if p.is_file():
                key=str(p)
                if key not in cache: cache[key]={'sha':sha(p.read_bytes())}
                c=cache[key];q['observed_source_sha256']=c['sha']
                source_matches=c['sha']==r['source_sha256']
                if r['source_sha256'].startswith('partial:'):
                    from scripts.build_dataset_embedding_coverage import sha256
                    source_matches=sha256(p)==r['source_sha256'];q['historical_partial_hash_matches']=source_matches
                if not source_matches: q['reason']='SOURCE_HASH_CHANGED'
                elif typ in {'attribute_catalogue','feature_catalogue'}:
                    if 'fc' not in c: c['fc']=fc_expected(p,out)
                    expected=c['fc'].get(r['section'])
                    if expected:
                        q.update(expected_locator=expected['locator'],element_sha256=expected['element_sha256'])
                        if expected['content']==content: q.update(status='VERIFIED_DERIVED_FIELDS',reason='XML_UNIQUE_NODE_ALL_GENERATED_FIELDS_MATCH')
                        else:
                            q.update(status='REEXTRACTION_REQUIRED',reason='CATALOGUE_GENERATED_FIELDS_DIFFER')
                            candidates.append(dict(**q,proposed_content=expected['content'],proposed_content_sha256=sha(expected['content'].encode())))
                elif typ=='legal_notice':
                    from scripts.build_legal_notice_registry_chunks import read_registry,build_chunks
                    if 'legal' not in c:c['legal']={x['chunk_id']:x for x in build_chunks(read_registry(p),p)}
                    e=c['legal'].get(r['chunk_id'])
                    if e and e['text']==content:q.update(status='VERIFIED_DERIVED_FIELDS',reason='REGISTRY_FIELDS_MATCH_NOT_LEGAL_ORIGINAL',source_locator='registries.legal_notices.'+m['notice_id'])
                elif typ=='dataset_profile':
                    from scripts.build_dataset_embedding_coverage import build_rows_for
                    if 'profiles' not in c:
                        c['profiles']=[]
                        for state in ['embeddable_document','embeddable_structured','analytics_metadata','spatial_metadata','embeddable_archive']:
                            c['profiles']+=build_rows_for(p,state)
                    e=next((x for x in c['profiles'] if x['text']==content),None)
                    if e:q.update(status='VERIFIED_DERIVED_FIELDS',reason='SOURCE_PROFILE_REPRODUCED_NOT_FULL_BODY',source_locator='profile:'+str(m.get('section')))
                elif p.suffix.lower()=='.docx':
                    if 'text' not in c:c['text']=docx_text(p)
                    span=token_span(content,c['text'])
                    if span:q.update(status='VERIFIED_TEXT',reason='UNIQUE_DOCX_TOKEN_SPAN',source_locator='word/document.xml',normalized_char_span=span)
                elif p.suffix.lower() in {'.md','.txt'}:
                    from scripts.build_document_rag_chunks import decode_best
                    if 'text' not in c:c['text']=decode_best(p.read_bytes())[0]
                    span=token_span(content,c['text'])
                    if span:q.update(status='VERIFIED_TEXT',reason='UNIQUE_TEXT_TOKEN_SPAN',source_locator='file',normalized_char_span=span)
                elif p.suffix.lower()=='.zip':
                    from scripts.build_document_rag_chunks import zip_documents
                    if 'members' not in c:c['members']=zip_documents(p)
                    matches=[]
                    for member,text in c['members']:
                        for prefix in [f'Archive member: {member}\n',f'Archive member: {member}. ']:
                            span=token_span(content,prefix+text)
                            if span: matches.append((member,span,sha(text.encode())))
                    if len(matches)==1:q.update(status='VERIFIED_TEXT',reason='UNIQUE_ARCHIVE_MEMBER_TOKEN_SPAN',source_locator=matches[0][0],normalized_char_span=matches[0][1],extracted_member_text_sha256=matches[0][2])
            else:q['reason']='DATABASE_SOURCE_REQUIRES_CURRENT_READONLY_AGGREGATE' if '/' in r['source_file'] and not r['source_file'].startswith('Dataset') else 'SOURCE_NOT_FOUND'
        except Exception as e:q['reason']='ADAPTER_ERROR';q['error']=type(e).__name__+': '+str(e)
        results.append(q)
        if len(results)%100==0:write(out/'status.json',dict(status='RUNNING',processed=len(results),total=len(rows)))
    for name,items in [('results.jsonl',results),('reextraction_candidates.jsonl',candidates)]:
        (out/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items),encoding='utf-8')
    summary=dict(status='COMPLETED_AUDIT_NOT_ALL_VERIFIED',total=len(results),counts=dict(collections.Counter(x['status'] for x in results)),reasons=dict(collections.Counter(x['reason'] for x in results)),db_modified=False,model_called=False,holdout_used=False,files={p.name:sha(p.read_bytes()) for p in out.glob('*.jsonl')})
    write(out/'summary.json',summary);write(out/'status.json',summary);print(json.dumps(summary))

if __name__=='__main__':main()
