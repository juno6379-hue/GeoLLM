"""Lossless, staged replacement of the six audited administrative CSV chunks.

Only gbhd_s101 is accepted. Export/prepare are read-only; embed never writes DB.
Apply requires an externally reviewed artifact hash. Historical vector models
remain unknown. Old rows and vectors remain stored and have a full-row archive.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from scripts.complete_dataset_embeddings import DIGEST, DIM, MODEL, api, validate_vectors

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'Dataset/해양수산부_행정규칙_20240909.csv'
SOURCE_SHA = '36895adb1d01cf67943246f7559c7c07b43d294e2152a799bec6a1ba5706d382'
OLD_IDS = sorted(['1af3a5245ac27f47bf724316','3d6e099b2d6b06bf86b9c466',
    '69c915a7221c60acbfd2ef1d','9769a3b53e202c69084d8e15',
    'dbb43817b2667240e4b21f83','e2b0617c320afe3dd4d099aa'])
TABLE = 'knowledge.document_chunks'
ARCHIVE = 'knowledge.document_chunk_revision_archive'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write_new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def connect(readonly=True):
    import psycopg2
    connection = psycopg2.connect(os.environ['S101_DB_URL'], connect_timeout=5)
    connection.set_session(readonly=readonly, isolation_level='SERIALIZABLE')
    with connection.cursor() as cur:
        cur.execute('SELECT current_database()')
        if cur.fetchone()[0] != 'gbhd_s101':
            connection.close()
            raise ValueError('Operational database identity mismatch; research DB forbidden')
        cur.execute("SELECT set_config('statement_timeout','15000',true)")
        cur.execute("SELECT set_config('lock_timeout','3000',true)")
    return connection


def fetch_rows(cur, ids, lock=False):
    cur.execute('SELECT row_to_json(d) FROM knowledge.document_chunks d WHERE chunk_id=ANY(%s) ORDER BY chunk_id' +
                (' FOR UPDATE' if lock else ''), (list(ids),))
    return [row[0] for row in cur.fetchall()]


def validate_before(rows):
    if sorted(row['chunk_id'] for row in rows) != OLD_IDS:
        raise ValueError('Audited original six IDs must match exactly')
    if any(row['source_sha256'] != SOURCE_SHA or row['document_type'] != 'law'
           or row['source_file'].replace('\\', '/') != SOURCE
           or row['metadata'].get('retrieval_status', 'ACTIVE') != 'ACTIVE'
           or not row.get('embedding') for row in rows):
        raise ValueError('Original source or vector identity changed')


def export(output):
    with connect() as conn, conn.cursor() as cur:
        rows = fetch_rows(cur, OLD_IDS)
        validate_before(rows)
        cur.execute('SELECT count(*) FROM knowledge.document_chunks WHERE source_sha256=%s', (SOURCE_SHA,))
        if cur.fetchone()[0] != 6:
            raise ValueError('Source inventory changed')
    write_new(output, {'database': 'gbhd_s101', 'rows': rows, 'rows_sha256': digest(rows),
                       'historical_embedding_model': None, 'source_sha256': SOURCE_SHA})


def prepare(before_file, candidates_file, output):
    from scripts.build_document_rag_chunks import csv_chunks
    before = read(before_file); candidates = read(candidates_file)['rows']
    validate_before(before['rows'])
    if digest(before['rows']) != before['rows_sha256']:
        raise ValueError('Before export changed')
    source = ROOT / SOURCE
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Source bytes changed')
    actual = csv_chunks(source, source.stem)
    def identity(row):
        metadata = {k:v for k,v in row['metadata'].items() if k != 'generated_at'}
        return {'chunk_id': row['chunk_id'], 'text': row['text'], 'metadata': metadata}
    if [identity(row) for row in actual] != [identity(row) for row in candidates]:
        raise ValueError('Fresh full source extraction differs from reviewed candidates')
    if len(actual) != 6 or set(OLD_IDS) & {row['chunk_id'] for row in actual}:
        raise ValueError('Revision IDs must be six new IDs')
    batch = 'csv-positional-v2-' + digest([identity(row) for row in actual])[:16]
    write_new(output, {'version': 1, 'batch_id': batch, 'database': 'gbhd_s101',
        'source_sha256': SOURCE_SHA, 'before': before, 'candidates': actual,
        'input_identity_sha256': digest([identity(row) for row in actual]),
        'stage': 'PREPARED', 'historical_embedding_model': None})


def check_current_model():
    name = os.getenv('EMBEDDING_MODEL', 'bge-m3')
    if name not in {'bge-m3', MODEL}:
        raise ValueError('Current query embedding model differs')
    from services.llm_config import ollama_base_url
    endpoint = os.getenv('OLLAMA_EMBEDDING_URL', ollama_base_url() + '/api/embed')
    if endpoint != ollama_base_url() + '/api/embed':
        raise ValueError('Query embedding endpoint differs from pinned local endpoint')
    row = next((r for r in api('/api/tags')['models'] if r['name'] == MODEL), None)
    if not row or row.get('digest') != DIGEST:
        raise ValueError('Current model digest differs')
    return name


def embed(prepared, output):
    plan = read(prepared)
    if plan['stage'] != 'PREPARED':
        raise ValueError('Expected prepared revision')
    query_model = check_current_model()
    receipts = []
    for row in plan['candidates']:
        result = api('/api/embed', {'model': MODEL, 'input': [row['text']], 'truncate': False})
        vectors = result.get('embeddings', [])
        validate_vectors(vectors, 1)
        receipts.append({'chunk_id': row['chunk_id'], 'embedding': vectors[0],
            'input_sha256': hashlib.sha256(row['text'].encode()).hexdigest(),
            'model': MODEL, 'model_digest': DIGEST, 'dimension': DIM,
            'query_model_name': query_model, 'truncate': False,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'purpose': 'new_revision_with_current_query_model',
            'historical_embedding_model_verified': False,
            'response_sha256': digest(result)})
        # Preserve partial work even if a later model call fails; no silent retries.
        write_new(str(output) + '.' + row['chunk_id'] + '.receipt.json', receipts[-1])
    check_current_model()
    plan.update(stage='EMBEDDED', embeddings=receipts)
    write_new(output, plan)


def build_new_rows(plan):
    before = plan['before']['rows']; validate_before(before)
    if digest(before) != plan['before']['rows_sha256'] or plan['stage'] != 'EMBEDDED':
        raise ValueError('Before export or stage mismatch')
    embeddings = {row['chunk_id']: row for row in plan['embeddings']}
    if len(embeddings) != 6 or len(plan['candidates']) != 6:
        raise ValueError('Expected six distinct embedding receipts')
    output = []
    for candidate in plan['candidates']:
        meta = copy.deepcopy(candidate['metadata']); receipt = embeddings[candidate['chunk_id']]
        text = candidate['text']
        if (receipt['input_sha256'] != hashlib.sha256(text.encode()).hexdigest()
                or receipt['model_digest'] != DIGEST or receipt['model'] != MODEL
                or receipt['dimension'] != DIM or receipt['truncate'] is not False
                or meta['source_sha256'] != SOURCE_SHA
                or meta.get('extraction_revision') != 'csv_positional_v2'):
            raise ValueError('Embedding/input/source receipt mismatch')
        validate_vectors([receipt['embedding']], 1)
        row = {key: meta.get(key) for key in before[0]}
        meta.update(retrieval_status='ACTIVE', revision_batch_id=plan['batch_id'],
                    supersedes_chunk_ids=OLD_IDS, requires_new_embedding=False,
                    embedding={k:v for k,v in receipt.items() if k not in {'embedding','chunk_id'}},
                    historical_embedding_model=None)
        row.update(chunk_id=candidate['chunk_id'], content=text, metadata=meta,
                   embedding=json.dumps(receipt['embedding']),
                   created_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
        output.append(row)
    if len({row['chunk_id'] for row in output}) != 6 or set(OLD_IDS) & {row['chunk_id'] for row in output}:
        raise ValueError('Revision identity collision')
    return output


def archived(cur, batch, role, rows):
    from psycopg2.extras import Json
    cur.execute('''CREATE TABLE IF NOT EXISTS knowledge.document_chunk_revision_archive (
        batch_id text NOT NULL, revision_role text NOT NULL, chunk_id text NOT NULL,
        row_data jsonb NOT NULL, row_sha256 text NOT NULL,
        archived_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY(batch_id,revision_role,chunk_id))''')
    for row in rows:
        cur.execute('INSERT INTO knowledge.document_chunk_revision_archive(batch_id,revision_role,chunk_id,row_data,row_sha256) VALUES(%s,%s,%s,%s,%s)',
                    (batch, role, row['chunk_id'], Json(row), digest(row)))


def apply(artifact, expected_sha, output):
    from psycopg2.extras import Json
    if Path(output).exists() or Path(str(output)+'.pending.json').exists():
        raise FileExistsError('Receipt path already exists')
    if hashlib.sha256(Path(artifact).read_bytes()).hexdigest() != expected_sha:
        raise ValueError('Reviewed artifact hash mismatch')
    plan = read(artifact); new = build_new_rows(plan); check_current_model()
    with connect(False) as conn, conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20261102006)')
        old = fetch_rows(cur, OLD_IDS, lock=True)
        if digest(old) != plan['before']['rows_sha256']:
            raise ValueError('Original rows changed since lossless export')
        cur.execute('SELECT count(*) FROM knowledge.document_chunks WHERE source_sha256=%s', (SOURCE_SHA,))
        if cur.fetchone()[0] != 6:
            raise ValueError('Source inventory changed')
        if fetch_rows(cur, [r['chunk_id'] for r in new]):
            raise ValueError('New revision already present')
        archived(cur, plan['batch_id'], 'BEFORE', old)
        for row in new:
            cur.execute('INSERT INTO knowledge.document_chunks SELECT * FROM jsonb_populate_record(NULL::knowledge.document_chunks,%s::jsonb)', (Json(row),))
        cur.execute("UPDATE knowledge.document_chunks SET metadata=metadata || %s::jsonb WHERE chunk_id=ANY(%s)",
            (Json({'retrieval_status':'SUPERSEDED','revision_batch_id':plan['batch_id'],
                   'superseded_by_chunk_ids':[r['chunk_id'] for r in new]}), OLD_IDS))
        after = fetch_rows(cur, OLD_IDS + [r['chunk_id'] for r in new])
        if len(after) != 12:
            raise ValueError('Post-insert row count mismatch')
        archived(cur, plan['batch_id'], 'AFTER', after)
        cur.execute("SELECT count(*),count(*) FILTER(WHERE COALESCE(metadata->>'retrieval_status','ACTIVE') <> 'SUPERSEDED') FROM knowledge.document_chunks")
        stored, active = cur.fetchone()
        receipt = {'batch_id':plan['batch_id'], 'database':'gbhd_s101', 'stage':'APPLIED',
            'artifact_sha256':expected_sha, 'before_sha256':digest(old), 'after_sha256':digest(after),
            'after_rows':after, 'stored_count':stored, 'active_count':active,
            'old_ids':OLD_IDS, 'new_ids':[r['chunk_id'] for r in new]}
        # A prepared receipt is not a commit receipt if PostgreSQL commit fails.
        write_new(str(output)+'.pending.json', {**receipt, 'stage':'TRANSACTION_PENDING'})
    write_new(output, receipt)


def rollback(receipt_file, expected_sha, output):
    from psycopg2 import sql
    from psycopg2.extras import Json
    if Path(output).exists() or Path(str(output)+'.pending.json').exists():
        raise FileExistsError('Receipt path already exists')
    if hashlib.sha256(Path(receipt_file).read_bytes()).hexdigest() != expected_sha:
        raise ValueError('Rollback receipt hash mismatch')
    receipt = read(receipt_file); batch = receipt['batch_id']
    with connect(False) as conn, conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(20261102006)')
        current = fetch_rows(cur, receipt['old_ids'] + receipt['new_ids'], lock=True)
        if digest(current) != receipt['after_sha256']:
            raise ValueError('Rows changed after apply; rollback refused')
        cur.execute("SELECT row_data,row_sha256 FROM knowledge.document_chunk_revision_archive WHERE batch_id=%s AND revision_role='BEFORE' ORDER BY chunk_id", (batch,))
        old = []
        for row, expected in cur.fetchall():
            if digest(row) != expected: raise ValueError('Archive hash changed')
            old.append(row)
        validate_before(old)
        if digest(old) != receipt['before_sha256']: raise ValueError('Archive differs from export')
        archived(cur, batch, 'BEFORE_ROLLBACK', current)
        for row in old:
            columns = [key for key in row if key != 'chunk_id']
            assignments = sql.SQL(',').join(sql.SQL('{}=r.{}').format(sql.Identifier(k),sql.Identifier(k)) for k in columns)
            cur.execute(sql.SQL('UPDATE knowledge.document_chunks d SET {} FROM jsonb_populate_record(NULL::knowledge.document_chunks,%s::jsonb) r WHERE d.chunk_id=r.chunk_id').format(assignments), (Json(row),))
        cur.execute("UPDATE knowledge.document_chunks SET metadata=metadata || %s::jsonb WHERE chunk_id=ANY(%s)",
                    (Json({'retrieval_status':'SUPERSEDED','rollback_batch_id':batch}), receipt['new_ids']))
        if digest(fetch_rows(cur, OLD_IDS)) != receipt['before_sha256']:
            raise ValueError('Lossless restoration failed')
        final = {'stage':'ROLLED_BACK','batch_id':batch,
            'restored_before_sha256':receipt['before_sha256'], 'new_vectors_preserved':True}
        write_new(str(output)+'.pending.json', {**final, 'stage':'TRANSACTION_PENDING'})
    write_new(output, final)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['export','prepare','embed','apply','rollback'])
    parser.add_argument('--output',required=True); parser.add_argument('--input'); parser.add_argument('--candidates'); parser.add_argument('--sha256')
    args=parser.parse_args()
    if args.mode=='export': export(args.output)
    elif args.mode=='prepare': prepare(args.input,args.candidates,args.output)
    elif args.mode=='embed': embed(args.input,args.output)
    elif args.mode=='apply': apply(args.input,args.sha256,args.output)
    else: rollback(args.input,args.sha256,args.output)


if __name__=='__main__': main()
