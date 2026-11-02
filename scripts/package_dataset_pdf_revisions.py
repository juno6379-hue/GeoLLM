"""Create unapplied, content-addressed PDF revisions with exact source spans.

Only numeric-preserving candidates are packaged. This tool does not embed, write
DB rows, or switch verification pointers. Old IDs/rows remain intact.
"""
import argparse
import gzip
import json
from pathlib import Path
from scripts.verify_dataset_pdf_followup import BASE, digest


def revision(row, check):
    candidate=check.get('candidate')
    if not candidate or not candidate.get('numeric_lexemes_equal'):
        return None
    if digest(row['content'].encode())!=check['content_sha256'] or row['source_sha256']!=check['source_sha256']:
        raise ValueError('Original chunk identity changed')
    text=candidate['text']
    if digest(text.encode())!=candidate['text_sha256'] or text==row['content']:
        return None
    key=json.dumps([row['chunk_id'],row['source_sha256'],check['source_locator'],
                    candidate['start'],candidate['end'],candidate['text_sha256']],ensure_ascii=False,separators=(',',':'))
    metadata=dict(row['metadata'])
    metadata.update(extraction_method='pdf_source_span_revision_v1',
        original_char_offset=metadata.get('char_offset'),char_offset=candidate['start'],
        source_locators=check['source_locator'],source_char_start=candidate['start'],source_char_end=candidate['end'],
        source_extracted_pages_sha256=check['extracted_pages_sha256'],
        source_extractor='pypdf '+check['extractor_version'],
        original_chunk_id=row['chunk_id'],original_content_sha256=check['content_sha256'],
        content_sha256=candidate['text_sha256'],semantic_authority=False,coordinate_authority=False)
    return dict(chunk_id='pdf_span_v1_'+digest(key.encode()),text=text,metadata=metadata,
                original_chunk_id=row['chunk_id'],original_content_sha256=check['content_sha256'],
                source_file=row['source_file'],source_sha256=row['source_sha256'],
                document_type=row['document_type'],title=row['title'],section=row['section'],
                page_no=row['page_no'],source_id=row['source_id'],requires_new_embedding=True,
                status='PREPARED_NOT_APPLIED')


def main(candidate_path,verified_path,output):
    if output.exists():raise RuntimeError('Existing output preserved')
    checks={r['chunk_id']:r for s in candidate_path.open(encoding='utf-8') if (r:=json.loads(s))}
    verified={r['chunk_id'] for s in verified_path.open(encoding='utf-8') if (r:=json.loads(s))['status']=='VERIFIED_TEXT'}
    rows=[]
    with gzip.open(BASE/'full_current_document_chunks.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['chunk_id'] in checks and row['chunk_id'] not in verified:
                value=revision(row,checks[row['chunk_id']])
                if value:rows.append(value)
    if len({r['chunk_id'] for r in rows})!=len(rows):raise ValueError('Duplicate revision IDs')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(dict(status='PREPARED_NOT_APPLIED',rows=rows,count=len(rows),
            source_candidates_sha256=digest(candidate_path.read_bytes()),
            verified_exclusions_sha256=digest(verified_path.read_bytes()),
            original_rows_preserved=True,requires_model_digest_check=True,
            requires_current_db_compare_and_swap=True,requires_fullrow_vector_archive=True,
            automatic_embedding_or_db_write=False),stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(count=len(rows),sha256=digest(output.read_bytes()))))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidates',type=Path,required=True)
    parser.add_argument('--verified',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    main(args.candidates,args.verified,args.output)
