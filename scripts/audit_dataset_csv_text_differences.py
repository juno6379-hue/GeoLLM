"""Preserve CSV extraction differences and propose source-bound replacement text.

No database write or vector reuse. Replacement text requires new embedding before
it can be published as an embedded document.
"""
import difflib
import json
from scripts.audit_dataset_locations import ROOT, DEFAULT, source_sections, norm, sha, file_sha, write


def render(records,start,end):
    return 'columns: '+' | '.join(records[0])+'\n'+'\n'.join(' | '.join(r) for r in records[start:end+1])


def main():
    chunks={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'))}
    checks=[r for r in map(json.loads,(DEFAULT/'chunk_checks.jsonl').open(encoding='utf-8')) if r['text_status']=='TEXT_MISMATCH' and str(r['source_file']).lower().endswith('.csv')]
    diagnosis=[];candidates=[]
    for check in checks:
        row=chunks[check['chunk_id']];path=ROOT/row['source_file'];meta=row['metadata'];start=meta['source_row_start'];end=meta['source_row_end']
        if file_sha(path)!=row['source_sha256']:raise RuntimeError('Original source changed')
        records=source_sections(path,[row])['csv_rows'];full=render(records,start,end)
        # Diagnose the historical emitter dropping a terminal empty CSV column.
        reduced=[r[:-1] if r and not r[-1] else r for r in records]
        expected=norm(render(reduced,start,end));actual=norm(row['content'])
        match=actual==expected
        diffs=[dict(operation=op,stored_text=actual[i:j],source_text=expected[k:l],stored_span=[i,j]) for op,i,j,k,l in difflib.SequenceMatcher(None,actual,expected,autojunk=False).get_opcodes() if op!='equal']
        diagnosis.append(dict(chunk_id=row['chunk_id'],source_file=row['source_file'],source_rows=[start,end],exact_normalized_match_after_single_trailing_empty_column_removed=match,remaining_differences=diffs))
        candidates.append(dict(original_chunk_id=row['chunk_id'],original_content_sha256=sha(row['content'].encode()),source_file=row['source_file'],source_sha256=row['source_sha256'],source_locator=dict(row_start=start,row_end=end,header_row=0),candidate_content=full,candidate_content_sha256=sha(full.encode()),reason='Preserve all original CSV columns and rows in stated locator',applied=False,requires_new_embedding=True,reuse_old_embedding_allowed=False))
    write(DEFAULT/'csv_empty_column_diagnosis.json',diagnosis)
    with (DEFAULT/'csv_text_repair_candidates.jsonl').open('w',encoding='utf-8') as stream:
        for row in candidates:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(json.dumps(dict(checked=len(diagnosis),empty_column_only=sum(r['exact_normalized_match_after_single_trailing_empty_column_removed'] for r in diagnosis),field_differences=sum(not r['exact_normalized_match_after_single_trailing_empty_column_removed'] for r in diagnosis))))


if __name__=='__main__':main()
