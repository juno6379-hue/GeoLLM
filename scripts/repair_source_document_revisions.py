"""Staged one-to-one operational source repairs with resumable embeddings.

Export/prepare/embedding never write DB. Apply requires a reviewed artifact SHA.
The existing CSV repair and all frozen research inputs remain untouched.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from scripts.repair_csv_document_revision import connect,fetch_rows,archived,digest,read,write_new,check_current_model
from scripts.complete_dataset_embeddings import MODEL,DIGEST,DIM,api,validate_vectors

ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def old_id(row):return row.get('old_chunk_id') or row.get('original_chunk_id')
def old_hash(row):return row.get('old_content_sha256') or row.get('original_content_sha256')
def local(tag):return tag.rsplit('}',1)[-1]


def validate_candidates(rows):
    if not rows or any(not old_id(r) or not old_hash(r) or not r.get('text') for r in rows):raise ValueError('Missing revision identity')
    if len({old_id(r) for r in rows})!=len(rows) or len({r['chunk_id'] for r in rows})!=len(rows):raise ValueError('Duplicate one-to-one mapping')
    if {old_id(r) for r in rows}&{r['chunk_id'] for r in rows}:raise ValueError('Old/new identity collision')


def export(candidates_file,output):
    rows=read(candidates_file)['rows'];validate_candidates(rows)
    ids=sorted(old_id(r) for r in rows)
    with connect() as conn,conn.cursor() as cur:before=fetch_rows(cur,ids)
    if [r['chunk_id'] for r in before]!=ids:raise ValueError('Original rows missing')
    write_new(output,dict(database='gbhd_s101',rows=before,rows_sha256=digest(before),candidates_sha256=sha(Path(candidates_file).read_bytes())))


def verify_source(candidate,old,cache):
    if old['chunk_id']!=old_id(candidate) or sha(old['content'].encode())!=old_hash(candidate):raise ValueError('Original identity changed')
    for field in ['source_file','source_sha256','source_id','document_type','title','section','page_no']:
        if candidate.get(field)!=old.get(field):raise ValueError('Source/lookup identity changed: '+field)
    if old['metadata'].get('retrieval_status','ACTIVE')!='ACTIVE' or not old.get('embedding'):raise ValueError('Original row inactive or unembedded')
    p=ROOT/candidate['source_file'];key=str(p)
    if key not in cache:cache[key]={'sha':sha(p.read_bytes())}
    source=cache[key]
    if source['sha']!=candidate['source_sha256']:raise ValueError('Full source hash changed')
    meta=candidate['metadata'];text=candidate['text'];method=meta.get('extraction_method')
    if sha(text.encode())!=meta.get('content_sha256'):raise ValueError('New content hash mismatch')
    if method=='fc_direct_xml_fields_v3':
        if 'nodes' not in source:
            nodes={}
            for n in ET.parse(p).getroot().iter():
                if local(n.tag) in {'S100_FC_FeatureType','S100_FC_SimpleAttribute','S100_FC_ComplexAttribute'}:
                    code=next((c.text for c in n if local(c.tag)=='code'),None);nodes.setdefault(code,[]).append(n)
            source['nodes']=nodes
        nodes=source['nodes'].get(candidate['section'].split(':',1)[1],[])
        if len(nodes)!=1 or sha(ET.tostring(nodes[0]))!=meta['source_element_sha256']:raise ValueError('XML element identity changed')
        facts=[];attr=candidate['document_type']=='attribute_catalogue'
        node=nodes[0]
        def field(name):
            child=next((c for c in node if local(c.tag)==name),None)
            return ' '.join(''.join(child.itertext()).split()) if child is not None else ''
        aliases=[' '.join(''.join(c.itertext()).split()) for c in node.iter() if local(c.tag)=='alias']
        if attr:
            prefix=(f"S-101 Feature Catalogue attribute description. Attribute code: {field('code')}. "
                    f"Attribute name: {field('name')}. Definition: {field('definition')}. "
                    f"Value type: {field('valueType') or 'not specified'}. "
                    f"Unit of measure: {field('uom') or 'not specified'}. "
                    f"Aliases: {', '.join(aliases) if aliases else 'none'}. ")
        else:
            primitives=[' '.join(''.join(c.itertext()).split()) for c in node.iter() if local(c.tag)=='permittedPrimitives']
            prefix=(f"S-101 Feature Catalogue feature definition. Feature code: {field('code')}. "
                    f"Feature name: {field('name')}. Definition: {field('definition')}. "
                    f"Aliases: {', '.join(aliases) if aliases else 'none'}. "
                    f"Permitted primitives: {', '.join(primitives) if primitives else 'not specified'}. ")
        if attr:
            for n in nodes[0].iter():
                if local(n.tag)=='listedValue':facts.append({local(c.tag):(c.text or '').strip() for c in n if local(c.tag) in {'code','value','label'}})
        else:
            for n in nodes[0]:
                if local(n.tag).endswith('Binding'):
                    for c in n:
                        facts.extend(dict(kind=local(n.tag),node=local(c.tag),ref=v) for k,v in c.attrib.items() if local(k)=='ref')
        if facts!=meta['source_fields']:raise ValueError('XML field set differs')
        marker='Listed values: ' if attr else 'Attribute/information bindings: '
        tail=', '.join(str(v.get('value') or v.get('code'))+'='+v.get('label','') for v in facts) if attr else ', '.join(sorted({v['ref'] for v in facts}))
        if text!=prefix+marker+tail+'.':raise ValueError('FC source rendering differs')
    elif method=='pdf_source_span_revision_v1':
        if 'reader' not in source:
            from pypdf import PdfReader
            source['reader']=PdfReader(p);source['pages']={}
        pages=[]
        for loc in meta['source_locators']:
            if not re.fullmatch(r'page:\d+',loc):raise ValueError('Unsupported PDF locator')
            number=int(loc.split(':')[1])
            if number not in source['pages']:source['pages'][number]=source['reader'].pages[number-1].extract_text() or ''
            pages.append(source['pages'][number])
        raw='\n'.join(pages)
        if sha(raw.encode())!=meta['source_extracted_pages_sha256'] or raw[meta['source_char_start']:meta['source_char_end']]!=text:raise ValueError('PDF source span differs')
        def numbers(value):return re.findall(r'\d+(?:[.,]\d+)*',value)
        if numbers(old['content'])!=numbers(text):raise ValueError('PDF numeric lexemes changed')
    else:raise ValueError('Unsupported source extraction revision')
    return dict(chunk_id=candidate['chunk_id'],source_sha256=source['sha'],content_sha256=sha(text.encode()),method=method)


def prepare(before_file,candidates_file,output):
    before=read(before_file);candidates=read(candidates_file)['rows'];validate_candidates(candidates)
    if before['database']!='gbhd_s101' or digest(before['rows'])!=before['rows_sha256'] or before['candidates_sha256']!=sha(Path(candidates_file).read_bytes()):raise ValueError('Export or reviewed candidates changed')
    old={r['chunk_id']:r for r in before['rows']};cache={};checks=[verify_source(r,old[old_id(r)],cache) for r in candidates]
    plan=dict(stage='PREPARED',batch_id='source-fields-v3-'+digest(candidates)[:16],before=before,candidates=candidates,source_validation=checks,source_validation_sha256=digest(checks),model=MODEL,model_digest=DIGEST,dimension=DIM)
    plan['prepared_sha256']=digest(plan);write_new(output,plan)


def validate_plan(plan):
    clone={k:v for k,v in plan.items() if k not in {'prepared_sha256','embeddings'}};clone['stage']='PREPARED'
    if digest(clone)!=plan['prepared_sha256']:raise ValueError('Prepared plan changed')
    validate_candidates(plan['candidates'])
    if digest(plan['before']['rows'])!=plan['before']['rows_sha256'] or digest(plan['source_validation'])!=plan['source_validation_sha256']:raise ValueError('Preserved provenance changed')
    if (plan['model'],plan['model_digest'],plan['dimension'])!=(MODEL,DIGEST,DIM):raise ValueError('Model contract changed')


def check_receipt(receipt,candidate,plan):
    if (receipt['chunk_id']!=candidate['chunk_id'] or receipt['plan_sha256']!=plan['prepared_sha256'] or receipt['input_sha256']!=sha(candidate['text'].encode()) or receipt['model']!=MODEL or receipt['model_digest']!=DIGEST or receipt['dimension']!=DIM or receipt['truncate'] is not False):raise ValueError('Embedding receipt changed')
    validate_vectors([receipt['embedding']],1)


def embed(prepared,output):
    plan=read(prepared);validate_plan(plan)
    if plan['stage']!='PREPARED':raise ValueError('Expected PREPARED')
    if Path(output).exists():raise FileExistsError('Completed output already exists')
    folder=Path(str(output)+'.checkpoints');folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'worker.lock'
    with lock.open('x') as f:f.write(plan['prepared_sha256'])
    try:
        check_current_model();receipts=[]
        for candidate in plan['candidates']:
            p=folder/(candidate['chunk_id']+'.json')
            if p.exists():receipt=read(p)
            else:
                response=api('/api/embed',dict(model=MODEL,input=[candidate['text']],truncate=False))
                validate_vectors(response.get('embeddings',[]),1)
                receipt=dict(chunk_id=candidate['chunk_id'],plan_sha256=plan['prepared_sha256'],input_sha256=sha(candidate['text'].encode()),model=MODEL,model_digest=DIGEST,dimension=DIM,truncate=False,embedding=response['embeddings'][0],generated_at=datetime.now(timezone.utc).isoformat(),response_sha256=digest(response))
                write_new(p,receipt)
            check_receipt(receipt,candidate,plan);receipts.append(receipt)
        check_current_model();plan.update(stage='EMBEDDED',embeddings=receipts);write_new(output,plan)
    finally:lock.unlink()


def build_new_rows(plan):
    validate_plan(plan)
    if plan['stage']!='EMBEDDED':raise ValueError('Embedding incomplete')
    old={r['chunk_id']:r for r in plan['before']['rows']};receipts={r['chunk_id']:r for r in plan['embeddings']}
    if len(receipts)!=len(plan['candidates']) or len(plan['embeddings'])!=len(receipts):raise ValueError('Embedding receipt cardinality mismatch')
    result=[]
    for candidate in plan['candidates']:
        receipt=receipts[candidate['chunk_id']];check_receipt(receipt,candidate,plan)
        row=copy.deepcopy(old[old_id(candidate)]);meta=copy.deepcopy(candidate['metadata'])
        meta.update(retrieval_status='ACTIVE',revision_batch_id=plan['batch_id'],supersedes_chunk_ids=[old_id(candidate)],embedding={k:v for k,v in receipt.items() if k!='embedding'},requires_new_embedding=False)
        row.update(chunk_id=candidate['chunk_id'],content=candidate['text'],metadata=meta,embedding=json.dumps(receipt['embedding']),created_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat());result.append(row)
    return result


def apply(artifact,expected_sha,output):
    from psycopg2.extras import Json
    if Path(output).exists() or Path(str(output)+'.pending.json').exists():raise FileExistsError('Receipt already exists')
    if sha(Path(artifact).read_bytes())!=expected_sha:raise ValueError('Reviewed artifact SHA differs')
    plan=read(artifact);new=build_new_rows(plan);check_current_model();ids=sorted(old_id(r) for r in plan['candidates'])
    sources={r['source_file']:r['source_sha256'] for r in plan['candidates']}
    for source,expected in sources.items():
        if sha((ROOT/source).read_bytes())!=expected:raise ValueError('Source changed after preparation')
    with connect(False) as conn,conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20261102006)')
        old=fetch_rows(cur,ids,lock=True)
        if digest(old)!=plan['before']['rows_sha256']:raise ValueError('CAS original rows changed')
        if fetch_rows(cur,[r['chunk_id'] for r in new]):raise ValueError('Revision already applied')
        archived(cur,plan['batch_id'],'BEFORE',old)
        for row in new:cur.execute('INSERT INTO knowledge.document_chunks SELECT * FROM jsonb_populate_record(NULL::knowledge.document_chunks,%s::jsonb)',(Json(row),))
        for c in plan['candidates']:
            cur.execute("UPDATE knowledge.document_chunks SET metadata=metadata||%s::jsonb WHERE chunk_id=%s",(Json(dict(retrieval_status='SUPERSEDED',revision_batch_id=plan['batch_id'],superseded_by_chunk_ids=[c['chunk_id']])),old_id(c)))
        after=fetch_rows(cur,ids+[r['chunk_id'] for r in new]);archived(cur,plan['batch_id'],'AFTER',after)
        if len(after)!=len(ids)*2:raise ValueError('After count mismatch')
        receipt=dict(stage='APPLIED',database='gbhd_s101',batch_id=plan['batch_id'],artifact_sha256=expected_sha,old_ids=ids,new_ids=[r['chunk_id'] for r in new],before_sha256=digest(old),after_sha256=digest(after),after_rows=after)
        write_new(str(output)+'.pending.json',{**receipt,'stage':'TRANSACTION_PENDING'})
    write_new(output,receipt)


def rollback(receipt_file,expected_sha,output):
    from psycopg2 import sql
    from psycopg2.extras import Json
    if Path(output).exists() or Path(str(output)+'.pending.json').exists():raise FileExistsError('Receipt already exists')
    if sha(Path(receipt_file).read_bytes())!=expected_sha:raise ValueError('Reviewed rollback SHA differs')
    receipt=read(receipt_file)
    if receipt.get('database')!='gbhd_s101' or receipt.get('stage')!='APPLIED':raise ValueError('Not an operational apply receipt')
    with connect(False) as conn,conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20261102006)')
        current=fetch_rows(cur,receipt['old_ids']+receipt['new_ids'],lock=True)
        if digest(current)!=receipt['after_sha256']:raise ValueError('Rows changed after apply')
        cur.execute("SELECT row_data,row_sha256 FROM knowledge.document_chunk_revision_archive WHERE batch_id=%s AND revision_role='BEFORE' ORDER BY chunk_id",(receipt['batch_id'],))
        old=[]
        for row,h in cur.fetchall():
            if digest(row)!=h:raise ValueError('Archive hash changed')
            old.append(row)
        if digest(old)!=receipt['before_sha256'] or [r['chunk_id'] for r in old]!=sorted(receipt['old_ids']):raise ValueError('Archive identity differs')
        archived(cur,receipt['batch_id'],'BEFORE_ROLLBACK',current)
        for row in old:
            assignments=sql.SQL(',').join(sql.SQL('{}=r.{}').format(sql.Identifier(k),sql.Identifier(k)) for k in row if k!='chunk_id')
            cur.execute(sql.SQL('UPDATE knowledge.document_chunks d SET {} FROM jsonb_populate_record(NULL::knowledge.document_chunks,%s::jsonb) r WHERE d.chunk_id=r.chunk_id').format(assignments),(Json(row),))
        cur.execute("UPDATE knowledge.document_chunks SET metadata=metadata||%s::jsonb WHERE chunk_id=ANY(%s)",(Json(dict(retrieval_status='SUPERSEDED',rollback_batch_id=receipt['batch_id'])),receipt['new_ids']))
        if digest(fetch_rows(cur,receipt['old_ids']))!=receipt['before_sha256']:raise ValueError('Lossless restoration failed')
        result=dict(stage='ROLLED_BACK',batch_id=receipt['batch_id'],database='gbhd_s101',restored_before_sha256=receipt['before_sha256'],new_vectors_preserved=True)
        write_new(str(output)+'.pending.json',{**result,'stage':'TRANSACTION_PENDING'})
    write_new(output,result)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['export','prepare','embed','apply','rollback']);ap.add_argument('--input');ap.add_argument('--candidates');ap.add_argument('--output',required=True);ap.add_argument('--sha256');a=ap.parse_args()
    if a.mode=='export':export(a.candidates,a.output)
    elif a.mode=='prepare':prepare(a.input,a.candidates,a.output)
    elif a.mode=='embed':embed(a.input,a.output)
    elif a.mode=='apply':apply(a.input,a.sha256,a.output)
    else:rollback(a.input,a.sha256,a.output)


if __name__=='__main__':main()
