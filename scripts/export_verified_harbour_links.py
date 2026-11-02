from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import hashlib,json,os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
p=output_argument();refuse_existing(p/'verified_chunk_object_links_v3.jsonl')
geometry_receipt=json.loads((p/'geometry_reconciliation.json').read_text(encoding='utf8'))['transform_comparisons']['small_harbour_guide']
source_receipt=json.loads((p/'source_reconciliation.json').read_text(encoding='utf8'))['small_harbour_guide']
assert geometry_receipt['compared']==geometry_receipt['expected']==geometry_receipt['topology_equal']==source_receipt['source_rows']==source_receipt['db_rows']
assert not source_receipt['issues'] and not source_receipt['db_without_source']
c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
with c.cursor(cursor_factory=RealDictCursor) as q:
 q.execute("SET LOCAL statement_timeout='30s'")
 q.execute("SELECT d.chunk_id,d.source_id AS object_id,p.name AS object_name,p.properties->>'NAME' AS raw_object_name,d.source_sha256,d.section AS source_field,(d.metadata->>'row_index')::integer AS source_row_index,d.content,p.properties->>d.section AS raw_source_field FROM knowledge.document_chunks d JOIN serving.small_harbour_guide p USING(source_id) WHERE d.document_type='small_harbour_guide' AND d.source_sha256=p.provenance->>'source_sha256' AND p.properties ? d.section")
 rows=[dict(r) for r in q.fetchall()]
verified=[]
for r in rows:
 content=r.pop('content');raw=r.pop('raw_source_field');raw_name=r.pop('raw_object_name')
 assert r['object_name']==raw_name.strip()
 if raw.strip() and raw.strip() in content:
  r.update(predicate='describesHarbourRecord',authority='source_field_verified_retrieval_only',geometry_role='harbour_reference_point_not_entrance',normalization='none' if raw in content else 'source_field_outer_whitespace_strip',content_sha256=hashlib.sha256(content.encode()).hexdigest(),source_field_sha256=hashlib.sha256(raw.encode()).hexdigest(),raw_geometry_transform_verified=True)
  r['object_relation']='serving.small_harbour_guide';verified.append(r)
(p/'verified_chunk_object_links_v3.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in verified),encoding='utf8');print(len(verified));c.rollback()
