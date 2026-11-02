"""Package new content-addressed FC rows; no model calls or DB changes."""
import argparse,gzip,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from scripts.repair_source_document_revisions import verify_source,write_new


def main(evidence,snapshot,output):
    facts={x['chunk_id']:x for s in evidence.open(encoding='utf-8') if (x:=json.loads(s))}
    rows=[];cache={}
    for s in gzip.open(snapshot,'rt',encoding='utf-8'):
        old=json.loads(s)
        if old['chunk_id'] not in facts:continue
        q=facts[old['chunk_id']];attr=old['document_type']=='attribute_catalogue';marker='Listed values: ' if attr else 'Attribute/information bindings: '
        values=q['raw_xml_fields']
        tail=', '.join(str(v.get('value') or v.get('code'))+'='+v.get('label','') for v in values) if attr else ', '.join(sorted({v['ref'] for v in values}))
        text=old['content'].split(marker)[0]+marker+tail+'.'
        h=hashlib.sha256(text.encode()).hexdigest()
        cid='fc_fields_v3_'+hashlib.sha256((q['source_sha256']+':'+q['locator']+':'+h).encode()).hexdigest()[:24]
        meta=dict(old['metadata']);meta.update(extraction_method='fc_direct_xml_fields_v3',source_locator=q['locator'],source_element_sha256=q['element_sha256'],content_sha256=h,supersedes_chunk_id=old['chunk_id'],retrieval_status='ACTIVE',source_field_count=len(values),source_fields=values,semantic_authority=False,coordinate_authority=False,generated_at=datetime.now(timezone.utc).isoformat())
        row={k:old.get(k) for k in ['source_sha256','source_file','source_id','document_type','title','section','page_no']}
        row.update(chunk_id=cid,text=text,content=text,metadata=meta,old_chunk_id=old['chunk_id'],old_content_sha256=hashlib.sha256(old['content'].encode()).hexdigest())
        # Only source-field checks here: actual full-row/vector export is mandatory later.
        verify_source(row,{**old,'embedding':'PRESENCE_ONLY_SOURCE_CHECK'},cache)
        rows.append(row)
    if len(rows)!=len(facts):raise ValueError('Evidence snapshot identity mismatch')
    write_new(output,dict(rows=rows,rows_count=len(rows),db_modified=False,embedding_required=True,evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest()))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.evidence,a.snapshot,a.output)
