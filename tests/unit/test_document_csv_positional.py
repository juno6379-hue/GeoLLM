import csv
import hashlib
from io import StringIO
from scripts import build_document_rag_chunks as module


def make(tmp_path, monkeypatch, text):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    path=tmp_path/'source.csv';path.write_text(text,encoding='utf-8',newline='')
    module.HASH_CACHE.clear()
    return module.csv_chunks(path,'source')


def test_duplicate_empty_headers_preserve_both_values_and_new_identity(tmp_path,monkeypatch):
    rows=make(tmp_path,monkeypatch,'name,,\nport,N,2013-10-29\n')
    row=rows[0];meta=row['metadata']
    assert row['text']=='columns: name |  | \nport | N | 2013-10-29'
    assert meta['duplicate_header_column_indexes']==[1,2]
    assert meta['requires_new_embedding'] is True
    old_id=hashlib.sha256(f"{meta['source_id']}:0".encode()).hexdigest()[:24]
    assert row['chunk_id']!=old_id


def test_duplicate_named_headers_preserve_position(tmp_path,monkeypatch):
    rows=make(tmp_path,monkeypatch,'value,value\nfirst,second\n')
    assert rows[0]['text']=='columns: value | value\nfirst | second'


def test_ordinary_csv_preserves_legacy_body_and_id(tmp_path,monkeypatch):
    text='name,date\nBusan,2020-01-01\nIncheon,2021-02-03\n'
    rows=make(tmp_path,monkeypatch,text)
    old=list(csv.DictReader(text.splitlines()));columns=list(old[0])
    expected='columns: '+' | '.join(columns)+'\n'+'\n'.join(' | '.join(r[c] for c in columns) for r in old)
    assert rows[0]['text']==expected
    assert rows[0]['chunk_id']==hashlib.sha256(f"{rows[0]['metadata']['source_id']}:0".encode()).hexdigest()[:24]
    assert 'requires_new_embedding' not in rows[0]['metadata']


def test_quoted_multiline_and_extra_cells_are_not_lost(tmp_path,monkeypatch):
    rows=make(tmp_path,monkeypatch,'name,value\nport,"first\nsecond",extra\n')
    assert rows[0]['text']=='columns: name | value\nport | first\nsecond | extra'
    assert rows[0]['metadata']['extraction_revision']=='csv_positional_v2'


def test_chunk_boundary_preserves_whole_rows(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'WORD_TARGET',8)
    rows=make(tmp_path,monkeypatch,'name,value\na,one\nb,two\nc,three\n')
    assert [(r['metadata']['source_row_start'],r['metadata']['source_row_end']) for r in rows]==[(1,1),(2,2),(3,3)]
    assert all(len(r['text'].splitlines())==2 for r in rows)
